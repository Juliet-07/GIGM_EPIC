from sqlalchemy import func, select

from app.models import Booking, Town, Trip, TripStatus
from app.fares import fare_cents
from app.seed import reset, seed, seed_if_empty
from tests.conftest import NOW


def counts(db):
    return [db.scalar(select(func.count()).select_from(m)) for m in (Town, Trip, Booking)]


def test_seed_matches_the_brief(session_factory):
    with session_factory() as db:
        seed(db, now=NOW)
        assert counts(db) == [6, 10, 15]
        statuses = [t.status for t in db.scalars(select(Trip))]
        assert statuses.count(TripStatus.SCHEDULED) >= 6            
        assert TripStatus.DEPARTED in statuses and TripStatus.ARRIVED in statuses
        assert {t.capacity for t in db.scalars(select(Trip))} <= {40, 44}


def test_seeded_counters_match_bookings_and_nothing_is_oversold(session_factory):
    with session_factory() as db:
        seed(db, now=NOW)
        for trip in db.scalars(select(Trip)):
            booked = sum(b.seats for b in trip.bookings)
            assert trip.seats_booked == booked <= trip.capacity


def test_seeded_fares_follow_the_fare_rules(session_factory):
    with session_factory() as db:
        seed(db, now=NOW)
        for b in db.scalars(select(Booking)):
            expected = fare_cents(b.trip.origin.zone, b.trip.destination.zone)
            assert b.fare_per_seat_cents == expected and b.total_cents == expected * b.seats


def test_seed_if_empty_is_idempotent(session_factory):
    with session_factory() as db:
        assert seed_if_empty(db) is True
        assert seed_if_empty(db) is False
        assert counts(db) == [6, 10, 15]


def test_reset_wipes_and_reseeds(app, session_factory):
    with session_factory() as db:
        seed(db, now=NOW)
        db.add(Booking(reference="BK-EXTRA000", trip_id=1, passenger_name="X", seats=1,
                       fare_per_seat_cents=100, total_cents=100))
        db.commit()
    reset(app.state.engine, session_factory)
    with session_factory() as db:
        assert counts(db) == [6, 10, 15]