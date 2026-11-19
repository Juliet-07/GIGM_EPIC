import re
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.errors import (IdempotencyConflict, InsufficientSeats, NotFound, TripNotBookable)
from app.models import TripStatus
from app.services import bookings
from tests.conftest import NOW


def book(sf, trip_id, seats=1, name="Ada", key=None):
    with sf() as db:
        return bookings.create_booking(db, trip_id=trip_id, passenger_name=name,
        seats=seats, now=NOW, idempotency_key=key)


def test_booking_claims_seats_and_snapshots_the_fare(world, session_factory):
    trip = world.trip("Lagos", "Enugu", capacity=44)            
    booking, created = book(session_factory, trip, seats=3)
    assert created
    assert re.fullmatch(r"BK-[2-9A-HJKMNP-Z]{8}", booking.reference)
    assert booking.fare_per_seat_cents == 1800
    assert booking.total_cents == 5400
    assert world.trip_state(trip) == (3, 3, 1)


def test_reference_lookup_is_case_insensitive(world, session_factory):
    trip = world.trip()
    booking, _ = book(session_factory, trip)
    with session_factory() as db:
        assert bookings.get_booking(db, booking.reference.lower()).id == booking.id
        with pytest.raises(NotFound):
            bookings.get_booking(db, "BK-NOPE0000")


def test_references_are_unique(world, session_factory):
    trip = world.trip(capacity=200)
    refs = {book(session_factory, trip)[0].reference for _ in range(150)}
    assert len(refs) == 150


def test_can_fill_the_bus_exactly_then_it_is_sold_out(world, session_factory):
    trip = world.trip(capacity=10, booked=6)
    book(session_factory, trip, seats=4)                     
    assert world.trip_state(trip)[0] == 10
    with pytest.raises(InsufficientSeats) as e:
        book(session_factory, trip, seats=1)
    assert e.value.extra["seats_available"] == 0


def test_requesting_more_than_remaining_is_all_or_nothing(world, session_factory):
    trip = world.trip(capacity=10, booked=8)
    with pytest.raises(InsufficientSeats) as e:
        book(session_factory, trip, seats=3)                    
    assert e.value.extra["seats_available"] == 2
    assert world.trip_state(trip) == (8, 0, 0)                  


@pytest.mark.parametrize("status", [s for s in TripStatus if s != TripStatus.SCHEDULED])
def test_only_scheduled_trips_accept_bookings(world, session_factory, status):
    trip = world.trip(status=status)
    with pytest.raises(TripNotBookable):
        book(session_factory, trip)
    assert world.trip_state(trip) == (0, 0, 0)


def test_trip_whose_departure_time_has_passed_is_closed_even_if_still_scheduled(world, session_factory):
    trip = world.trip(hours=-1)                                
    with pytest.raises(TripNotBookable):
        book(session_factory, trip)


def test_unknown_trip(world, session_factory):
    with pytest.raises(NotFound):
        book(session_factory, 9999)


def _race(sf, trip_id, n_threads, seats_each=1):
    """Release n threads at the same instant, each booking through its own session."""
    barrier = threading.Barrier(n_threads)
    outcomes = []

    def worker(i):
        barrier.wait()
        try:
            book(sf, trip_id, seats=seats_each, name=f"P{i}")
            return "ok"
        except InsufficientSeats:
            return "sold_out"

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        outcomes = list(pool.map(worker, range(n_threads)))
    return outcomes


def test_two_customers_race_for_the_last_seat(world, session_factory):
    for _ in range(20):
        trip = world.trip(capacity=10, booked=9)
        outcomes = _race(session_factory, trip, n_threads=2)
        assert sorted(outcomes) == ["ok", "sold_out"]
        assert world.trip_state(trip) == (10, 1, 1)


def test_many_customers_never_oversell(world, session_factory):
    trip = world.trip(capacity=20)
    outcomes = _race(session_factory, trip, n_threads=40)
    assert outcomes.count("ok") == 20
    assert outcomes.count("sold_out") == 20
    assert world.trip_state(trip) == (20, 20, 20)


def test_concurrent_multi_seat_requests_keep_counter_equal_to_bookings(world, session_factory):
    trip = world.trip(capacity=5)
    outcomes = _race(session_factory, trip, n_threads=8, seats_each=2)
    assert outcomes.count("ok") == 2                           
    counter, summed, _ = world.trip_state(trip)
    assert counter == summed == 4 <= 5

def test_same_idempotency_key_returns_the_original_booking(world, session_factory):
    trip = world.trip()
    first, created1 = book(session_factory, trip, seats=2, key="abc")
    second, created2 = book(session_factory, trip, seats=2, key="abc")
    assert (created1, created2) == (True, False)
    assert first.reference == second.reference
    assert world.trip_state(trip) == (2, 2, 1)                 


def test_idempotency_key_reused_for_a_different_request_is_rejected(world, session_factory):
    trip = world.trip()
    book(session_factory, trip, seats=2, key="abc")
    with pytest.raises(IdempotencyConflict):
        book(session_factory, trip, seats=3, key="abc")
    assert world.trip_state(trip) == (2, 2, 1)


def test_concurrent_double_submit_with_same_key_books_once(world, session_factory):
    trip = world.trip()
    barrier = threading.Barrier(6)

    def worker(_):
        barrier.wait()
        return book(session_factory, trip, seats=2, key="double-click")

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(worker, range(6)))
    assert len({b.reference for b, _ in results}) == 1
    assert sum(1 for _, created in results if created) == 1
    assert world.trip_state(trip) == (2, 2, 1)


def test_reference_collision_retries_and_does_not_leak_seats(world, session_factory, monkeypatch):
    trip = world.trip(capacity=10)
    refs = iter(["BK-AAAAAAAA", "BK-AAAAAAAA", "BK-BBBBBBBB"]) 
    monkeypatch.setattr(bookings, "new_reference", lambda: next(refs))
    book(session_factory, trip, seats=2)
    second, _ = book(session_factory, trip, seats=3)
    assert second.reference == "BK-BBBBBBBB"
    assert world.trip_state(trip) == (5, 5, 2)                 