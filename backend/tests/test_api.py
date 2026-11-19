from datetime import datetime, timedelta, timezone

import pytest

from app.models import TripStatus
from tests.conftest import NOW


def post_booking(client, trip_id, name="Ada Obi", seats=1, key=None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post("/api/bookings", json={"trip_id": trip_id, "passenger_name": name, "seats": seats}, headers=headers)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_towns(world, client):
    towns = client.get("/api/towns").json()
    assert len(towns) == 6
    assert {t["name"]: t["zone"] for t in towns} == {
        "Lagos": 1, "Ibadan": 1, "Enugu": 2, "Onitsha": 2, "Abuja": 3, "Kano": 4}


def test_fare_quote(world, client):
    r = client.get("/api/fares", params={"origin_id": world.town["Lagos"], "destination_id": world.town["Kano"]})
    assert r.status_code == 200
    assert r.json()["fare_cents"] == 3500 and r.json()["currency"] == "USD"


def test_fare_quote_same_town_is_422(world, client):
    r = client.get("/api/fares", params={"origin_id": world.town["Lagos"], "destination_id": world.town["Lagos"]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_route"


def test_fare_quote_unknown_town_is_404(world, client):
    r = client.get("/api/fares", params={"origin_id": 999, "destination_id": world.town["Lagos"]})
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def search(client, world, o, d, date=None):
    params = {"origin_id": world.town[o], "destination_id": world.town[d]}
    if date:
        params["date"] = date
    return client.get("/api/trips", params=params)


def test_search_returns_fare_departure_and_seats(world, client):
    t = world.trip("Lagos", "Abuja", hours=24, capacity=44, booked=4)
    [trip] = search(client, world, "Lagos", "Abuja", "2026-11-15").json()
    assert trip["id"] == t
    assert trip["fare_cents"] == 2500
    assert trip["seats_available"] == 40 and trip["capacity"] == 44
    assert trip["departure_time"] == "2026-11-15T09:00:00Z"


def test_search_is_direction_specific(world, client):
    world.trip("Lagos", "Abuja")
    assert search(client, world, "Abuja", "Lagos").json() == []


def test_search_hides_trips_that_cannot_be_booked(world, client):
    ok = world.trip("Lagos", "Ibadan", hours=5)
    world.trip("Lagos", "Ibadan", hours=6, status=TripStatus.BOARDING)
    world.trip("Lagos", "Ibadan", hours=7, status=TripStatus.DEPARTED)
    world.trip("Lagos", "Ibadan", hours=-2)  
    assert [t["id"] for t in search(client, world, "Lagos", "Ibadan").json()] == [ok]


def test_search_shows_sold_out_trips_with_zero_seats(world, client):
    world.trip("Lagos", "Ibadan", capacity=10, booked=10)
    [trip] = search(client, world, "Lagos", "Ibadan").json()
    assert trip["seats_available"] == 0


def test_search_orders_by_departure(world, client):
    late = world.trip("Lagos", "Ibadan", hours=30)
    early = world.trip("Lagos", "Ibadan", hours=26)
    assert [t["id"] for t in search(client, world, "Lagos", "Ibadan").json()] == [early, late]


def test_date_filter_uses_nigerian_local_day_not_utc(world, client):
    late_14th = world.trip("Lagos", "Ibadan", departure=datetime(2026, 11, 14, 22, 30, tzinfo=timezone.utc))
    early_15th = world.trip("Lagos", "Ibadan", departure=datetime(2026, 11, 14, 23, 30, tzinfo=timezone.utc))
    ids = lambda day: [t["id"] for t in search(client, world, "Lagos", "Ibadan", day).json()]
    assert ids("2026-11-14") == [late_14th]
    assert ids("2026-11-15") == [early_15th]


def test_search_validation(world, client):
    same = search(client, world, "Lagos", "Lagos")
    assert same.status_code == 422 and same.json()["error"]["code"] == "invalid_route"
    assert client.get("/api/trips").json()["error"]["code"] == "validation_error"
    bad_date = client.get("/api/trips", params={"origin_id": 1, "destination_id": 2, "date": "15/11/2026"})
    assert bad_date.status_code == 422
    assert client.get("/api/trips", params={"origin_id": 999, "destination_id": 1}).status_code == 404


def test_book_returns_reference_and_reduces_availability(world, client):
    trip = world.trip("Lagos", "Enugu", capacity=44)
    r = post_booking(client, trip, "  Ngozi Eze  ", seats=2)
    assert r.status_code == 201
    body = r.json()
    assert body["reference"].startswith("BK-")
    assert body["passenger_name"] == "Ngozi Eze"            
    assert body["total_cents"] == 3600 and body["fare_per_seat_cents"] == 1800
    assert body["trip"]["origin"]["name"] == "Lagos"
    [t] = search(client, world, "Lagos", "Enugu").json()
    assert t["seats_available"] == 42
    assert client.get(f"/api/bookings/{body['reference']}").json()["reference"] == body["reference"]


def test_booking_lookup_unknown_reference(world, client):
    assert client.get("/api/bookings/BK-ZZZZZZZZ").status_code == 404


@pytest.mark.parametrize("payload", [
    {"passenger_name": "A", "seats": 0},
    {"passenger_name": "A", "seats": -1},
    {"passenger_name": "A", "seats": 11},          
    {"passenger_name": "A", "seats": 2.5},
    {"passenger_name": "A", "seats": "two"},
    {"passenger_name": "", "seats": 1},
    {"passenger_name": "    ", "seats": 1},        
    {"passenger_name": "x" * 101, "seats": 1},
    {"seats": 1},
    {"passenger_name": "A"},
])
def test_invalid_booking_payloads_are_rejected_and_change_nothing(world, client, payload):
    trip = world.trip()
    r = client.post("/api/bookings", json={"trip_id": trip, **payload})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert world.trip_state(trip) == (0, 0, 0)


def test_booking_unknown_trip_is_404(world, client):
    assert post_booking(client, 424242).status_code == 404


def test_insufficient_seats_is_409_with_remaining_count(world, client):
    trip = world.trip(capacity=10, booked=9)
    r = post_booking(client, trip, seats=2)
    assert r.status_code == 409
    assert r.json()["error"] == {"code": "insufficient_seats", "message": "Only 1 seat left on this trip", "seats_available": 1}


def test_booking_closed_trip_is_409(world, client):
    trip = world.trip(status=TripStatus.BOARDING)
    r = post_booking(client, trip)
    assert r.status_code == 409 and r.json()["error"]["code"] == "trip_not_bookable"


def test_idempotent_replay_returns_200_and_same_reference(world, client):
    trip = world.trip()
    first = post_booking(client, trip, seats=2, key="k-1")
    again = post_booking(client, trip, seats=2, key="k-1")
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["reference"] == again.json()["reference"]
    assert world.trip_state(trip) == (2, 2, 1)
    clash = post_booking(client, trip, seats=3, key="k-1")
    assert clash.status_code == 422 and clash.json()["error"]["code"] == "idempotency_key_reuse"


def test_dashboard_shows_route_time_capacity_bookings_status(world, client):
    t = world.trip("Kano", "Lagos", capacity=44)
    post_booking(client, t, "A", 3)
    post_booking(client, t, "B", 2)
    world.trip("Abuja", "Kano", status=TripStatus.DEPARTED)
    rows = client.get("/api/admin/trips").json()
    assert len(rows) == 2
    row = next(r for r in rows if r["id"] == t)
    assert (row["origin"]["name"], row["destination"]["name"]) == ("Kano", "Lagos")
    assert row["capacity"] == 44 and row["seats_booked"] == 5 and row["bookings_count"] == 2
    assert row["seats_available"] == 39 and row["status"] == "scheduled"
    assert row["next_status"] == "boarding" and row["departure_time"].endswith("Z")


def test_dashboard_includes_trips_with_no_bookings_and_non_bookable_trips(world, client):
    world.trip(status=TripStatus.ARRIVED, hours=-30)
    world.trip()
    rows = client.get("/api/admin/trips").json()
    assert sorted(r["status"] for r in rows) == ["arrived", "scheduled"]
    assert all(r["bookings_count"] == 0 for r in rows)


def test_dashboard_status_filter(world, client):
    world.trip(); world.trip(status=TripStatus.DEPARTED)
    assert [r["status"] for r in client.get("/api/admin/trips", params={"status": "departed"}).json()] == ["departed"]
    assert client.get("/api/admin/trips", params={"status": "bogus"}).status_code == 422


# ------------------------------------------------------------------ lifecycle
def set_status(client, trip, status):
    return client.patch(f"/api/admin/trips/{trip}/status", json={"status": status})


def test_trip_walks_the_whole_lifecycle_in_order(world, client):
    trip = world.trip()
    for step in ["boarding", "departed", "in_transit", "arrived", "completed"]:
        r = set_status(client, trip, step)
        assert r.status_code == 200 and r.json()["status"] == step
    assert r.json()["next_status"] is None


@pytest.mark.parametrize("current,target", [
    (TripStatus.SCHEDULED, "departed"),      
    (TripStatus.SCHEDULED, "completed"),
    (TripStatus.SCHEDULED, "scheduled"),     
    (TripStatus.DEPARTED, "boarding"),       
    (TripStatus.ARRIVED, "scheduled"),
    (TripStatus.COMPLETED, "arrived"),       
])
def test_illegal_transitions_are_409_and_change_nothing(world, client, current, target):
    trip = world.trip(status=current)
    r = set_status(client, trip, target)
    assert r.status_code == 409 and r.json()["error"]["code"] == "invalid_transition"
    row = next(x for x in client.get("/api/admin/trips").json() if x["id"] == trip)
    assert row["status"] == current.value


def test_status_update_errors(world, client):
    assert set_status(client, 999, "boarding").status_code == 404
    assert set_status(client, world.trip(), "flying").status_code == 422


def test_once_boarding_starts_new_bookings_are_refused(world, client):
    trip = world.trip()
    assert post_booking(client, trip).status_code == 201
    set_status(client, trip, "boarding")
    assert post_booking(client, trip).status_code == 409

def test_cors_allows_the_configured_frontend_origin(client):
    r = client.options("/api/bookings", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,idempotency-key"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_other_origins(client):
    r = client.get("/api/towns", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_backend_no_longer_serves_a_frontend(client):
    assert client.get("/").status_code == 404