import logging
import secrets
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.errors import (IdempotencyConflict, InsufficientSeats, NotFound,
                        TripNotBookable)
from app.fares import fare_for_towns
from app.models import Booking, Trip, TripStatus

log = logging.getLogger("bookings")

# No 0/O/1/I/L: references get read aloud and typed from SMS/paper.
_REF_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_MAX_REF_ATTEMPTS = 5


def new_reference() -> str:
    return "BK-" + "".join(secrets.choice(_REF_ALPHABET) for _ in range(8))


def _load_booking(db: Session, **filters) -> Booking | None:
    stmt = select(Booking).options(
        joinedload(Booking.trip).joinedload(Trip.origin),
        joinedload(Booking.trip).joinedload(Trip.destination),
    )
    for col, val in filters.items():
        stmt = stmt.where(getattr(Booking, col) == val)
    return db.scalars(stmt).unique().first()


def get_booking(db: Session, reference: str) -> Booking:
    booking = _load_booking(db, reference=reference.upper())
    if booking is None:
        raise NotFound(f"No booking with reference {reference}")
    return booking


def _explain_rejection(db: Session, trip_id: int, seats: int, now: datetime):
    """The guarded UPDATE matched nothing. Work out *why*, so the customer gets a useful error.
    This read happens after the fact and is only used to pick the message; the decision to
    reject was already made atomically by the UPDATE."""
    db.rollback()
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise NotFound(f"Trip {trip_id} does not exist")
    if trip.status != TripStatus.SCHEDULED or trip.departure_time <= now:
        raise TripNotBookable("This trip is no longer open for booking", status=trip.status.value)
    available = trip.seats_available
    if available == 0:
        raise InsufficientSeats("This trip is sold out", seats_available=0)
    raise InsufficientSeats(
        f"Only {available} seat{'s' if available != 1 else ''} left on this trip",
        seats_available=available,
    )


def create_booking(db: Session, *, trip_id: int, passenger_name: str, seats: int,
                   now: datetime, idempotency_key: str | None = None) -> tuple[Booking, bool]:
    """Returns (booking, created). `created` is False when an Idempotency-Key replay
    returned an earlier booking instead of making a new one."""

    # --- idempotent replay (double-click, client retry after a timeout) -----------------
    if idempotency_key:
        existing = _load_booking(db, idempotency_key=idempotency_key)
        if existing:
            return _replay(existing, trip_id, passenger_name, seats), False

    trip = db.scalars(
        select(Trip).options(joinedload(Trip.origin), joinedload(Trip.destination))
        .where(Trip.id == trip_id)
    ).first()
    if trip is None:
        raise NotFound(f"Trip {trip_id} does not exist")

    fare = fare_for_towns(trip.origin, trip.destination)  # price snapshot, integer cents

    for _attempt in range(_MAX_REF_ATTEMPTS):
        # 1) atomic claim of the seats
        claimed = db.execute(
            update(Trip)
            .where(
                Trip.id == trip_id,
                Trip.status == TripStatus.SCHEDULED,
                Trip.departure_time > now,
                Trip.seats_booked + seats <= Trip.capacity,
            )
            .values(seats_booked=Trip.seats_booked + seats)
        )
        if claimed.rowcount == 0:
            log.info("booking_rejected trip_id=%s seats=%s", trip_id, seats)
            _explain_rejection(db, trip_id, seats, now)  # always raises

        # 2) the booking row, in the same transaction
        booking = Booking(
            reference=new_reference(), trip_id=trip_id, passenger_name=passenger_name,
            seats=seats, fare_per_seat_cents=fare, total_cents=fare * seats,
            idempotency_key=idempotency_key,
        )
        db.add(booking)
        try:
            db.commit()
        except IntegrityError:
            # Rolls back the seat claim too. Either (a) a concurrent request with the same
            # Idempotency-Key won the race, or (b) a reference collision (1 in ~10^12).
            db.rollback()
            if idempotency_key:
                existing = _load_booking(db, idempotency_key=idempotency_key)
                if existing:
                    return _replay(existing, trip_id, passenger_name, seats), False
            continue

        log.info("booking_created reference=%s trip_id=%s seats=%s total_cents=%s",
                 booking.reference, trip_id, seats, booking.total_cents)
        return _load_booking(db, id=booking.id), True

    raise RuntimeError("could not generate a unique booking reference")  # practically unreachable


def _replay(existing: Booking, trip_id: int, passenger_name: str, seats: int) -> Booking:
    same = (existing.trip_id, existing.passenger_name, existing.seats) == (trip_id, passenger_name, seats)
    if not same:
        raise IdempotencyConflict("This Idempotency-Key was already used for a different booking request")
    return existing