from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.errors import NotFound
from app.fares import fare_for_towns
from app.models import Town, Trip, TripStatus
from app.timeutil import local_day_bounds_utc


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