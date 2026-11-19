from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_now
from app.config import Settings
from app.main import create_app
from app.models import Booking, Town, Trip, TripStatus
from app.seed import TOWNS

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=timezone.utc)  # pinned clock for every test


class World:
    """Tiny test-data builder on top of a real (temp-file) SQLite database."""

    def __init__(self, session_factory):
        self.sf = session_factory
        with self.sf() as db:
            db.add_all(Town(name=n, zone=z) for n, z in TOWNS)
            db.commit()
            self.town = {t.name: t.id for t in db.query(Town)}

    def trip(self, origin="Lagos", dest="Enugu", hours=24, capacity=44,
             status=TripStatus.SCHEDULED, booked=0, departure=None) -> int:
        with self.sf() as db:
            t = Trip(origin_id=self.town[origin], destination_id=self.town[dest],
                     departure_time=departure or NOW + timedelta(hours=hours),
                     capacity=capacity, seats_booked=booked, status=status)
            db.add(t)
            db.commit()
            return t.id

    def trip_state(self, trip_id):
        """(seats_booked counter, SUM of booking seats, number of bookings) read fresh."""
        with self.sf() as db:
            trip = db.get(Trip, trip_id)
            seats = [b.seats for b in db.query(Booking).filter_by(trip_id=trip_id)]
            return trip.seats_booked, sum(seats), len(seats)


@pytest.fixture
def app(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", auto_seed=False,
                        cors_origins=("http://localhost:5173",))
    application = create_app(settings)
    application.dependency_overrides[get_now] = lambda: NOW
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:  # entering the context runs lifespan -> creates tables
        yield c


@pytest.fixture
def world(app, client):
    return World(app.state.session_factory)


@pytest.fixture
def session_factory(app, client):
    return app.state.session_factory