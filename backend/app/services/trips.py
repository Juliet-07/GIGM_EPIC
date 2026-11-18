"""Read-side use cases: towns, fare quotes, trip search, admin dashboard, status changes."""
from datetime import date, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.errors import InvalidTransition, NotFound
from app.fares import fare_for_towns
from app.models import Booking, Town, Trip, TripStatus
from app.timeutil import local_day_bounds_utc

# The lifecycle
NEXT_STATUS: dict[TripStatus, TripStatus | None] = {
    TripStatus.SCHEDULED: TripStatus.BOARDING,
    TripStatus.BOARDING: TripStatus.DEPARTED,
    TripStatus.DEPARTED: TripStatus.IN_TRANSIT,
    TripStatus.IN_TRANSIT: TripStatus.ARRIVED,
    TripStatus.ARRIVED: TripStatus.COMPLETED,
    TripStatus.COMPLETED: None,
}


def list_towns(db: Session) -> list[Town]:
    return list(db.scalars(select(Town).order_by(Town.name)))


def _get_town(db: Session, town_id: int) -> Town:
    town = db.get(Town, town_id)
    if town is None:
        raise NotFound(f"Town {town_id} does not exist")
    return town


def quote(db: Session, origin_id: int, destination_id: int) -> tuple[Town, Town, int]:
    origin, destination = _get_town(db, origin_id), _get_town(db, destination_id)
    return origin, destination, fare_for_towns(origin, destination)


def search_trips(db: Session, origin_id: int, destination_id: int,
                 day: date | None, now: datetime) -> list[tuple[Trip, int]]:
    """Bookable trips on a route, optionally limited to one local calendar day.

    'Bookable' = still Scheduled and not yet departed by the clock. Sold-out trips
    are returned (seats_available == 0) so the customer sees *why* a trip is missing
    from the choices rather than assuming it does not exist.
    """
    _, _, fare = quote(db, origin_id, destination_id)  # validates both towns + route

    stmt = (
        select(Trip)
        .options(joinedload(Trip.origin), joinedload(Trip.destination))
        .where(
            Trip.origin_id == origin_id,
            Trip.destination_id == destination_id,
            Trip.status == TripStatus.SCHEDULED,
            Trip.departure_time > now,
        )
        .order_by(Trip.departure_time)
    )
    if day is not None:
        start, end = local_day_bounds_utc(day)
        stmt = stmt.where(Trip.departure_time >= start, Trip.departure_time < end)

    return [(trip, fare) for trip in db.scalars(stmt)]


def admin_dashboard(db: Session, status: TripStatus | None = None,
                    trip_id: int | None = None) -> list[tuple[Trip, int]]:
    counts = (
        select(Booking.trip_id, func.count(Booking.id).label("n"))
        .group_by(Booking.trip_id)
        .subquery()
    )
    stmt = (
        select(Trip, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.trip_id == Trip.id)
        .options(joinedload(Trip.origin), joinedload(Trip.destination))
        .order_by(Trip.departure_time)
    )
    if status is not None:
        stmt = stmt.where(Trip.status == status)
    if trip_id is not None:
        stmt = stmt.where(Trip.id == trip_id)
    return [(trip, n) for trip, n in db.execute(stmt).unique()]


def advance_status(db: Session, trip_id: int, target: TripStatus) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise NotFound(f"Trip {trip_id} does not exist")

    allowed = NEXT_STATUS[trip.status]
    if target != allowed:
        raise InvalidTransition(
            f"Cannot move trip from '{trip.status.value}' to '{target.value}'. "
            f"Allowed next state: {allowed.value if allowed else 'none (final state)'}",
            current=trip.status.value, allowed=allowed.value if allowed else None,
        )

    # Compare-and-set: if two admins click at once, only one wins; the other gets a 409.
    result = db.execute(
        update(Trip).where(Trip.id == trip_id, Trip.status == trip.status).values(status=target)
    )
    if result.rowcount == 0:
        db.rollback()
        raise InvalidTransition("Trip status changed concurrently; reload and retry")
    db.commit()
    db.refresh(trip)
    return trip