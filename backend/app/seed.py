import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fares import fare_cents
from app.models import Base, Booking, Town, Trip, TripStatus
from app.services.bookings import new_reference
from app.timeutil import OPERATOR_TZ, utcnow

TOWNS = [("Lagos", 1), ("Ibadan", 1), ("Enugu", 2), ("Onitsha", 2), ("Abuja", 3), ("Kano", 4)]

# (origin, destination, when, capacity, status)
# `when` is ("day", offset_days, "HH:MM" local) or ("now", offset_minutes)
S = TripStatus
TRIPS = [
    ("Lagos",   "Ibadan",  ("day", 1, "07:00"), 44, S.SCHEDULED),   # 1
    ("Lagos",   "Ibadan",  ("day", 1, "14:00"), 44, S.SCHEDULED),   # 2
    ("Ibadan",  "Lagos",   ("day", 1, "16:00"), 44, S.SCHEDULED),   # 3
    ("Lagos",   "Abuja",   ("day", 1, "06:00"), 44, S.SCHEDULED),   # 4
    ("Lagos",   "Enugu",   ("day", 1, "08:30"), 40, S.SCHEDULED),   # 5  (nearly full)
    ("Enugu",   "Abuja",   ("day", 2, "09:00"), 40, S.SCHEDULED),   # 6
    ("Kano",    "Lagos",   ("day", 2, "05:30"), 44, S.SCHEDULED),   # 7
    ("Onitsha", "Lagos",   ("now", 20),         40, S.BOARDING),    # 8
    ("Abuja",   "Kano",    ("now", -180),       44, S.DEPARTED),    # 9
    ("Enugu",   "Onitsha", ("day", -1, "10:00"), 40, S.ARRIVED),    # 10
]

# (trip number 1-based, passenger, seats)  -> 15 bookings
BOOKINGS = [
    (1, "Amaka Obi", 2), (1, "Ngozi Eze", 3),
    (2, "Chinedu Okeke", 4),
    (3, "Funke Adeyemi", 2),
    (4, "Emeka Nwosu", 2), (4, "Halima Yusuf", 3),
    (5, "Ifeoma Chukwu", 10), (5, "Obinna Eze", 10), (5, "Kelechi Anya", 10), (5, "Ada Nnamdi", 8),
    (6, "Musa Danjuma", 2),
    (8, "Bola Ige", 4),
    (9, "Aliyu Garba", 5), (9, "Zainab Bello", 3),
    (10, "Tosin Adebayo", 6),
]


def _departure(spec, now: datetime) -> datetime:
    if spec[0] == "now":
        return now + timedelta(minutes=spec[1])
    _, offset_days, hhmm = spec
    hour, minute = map(int, hhmm.split(":"))
    local_day = now.astimezone(OPERATOR_TZ).date() + timedelta(days=offset_days)
    return datetime(local_day.year, local_day.month, local_day.day, hour, minute,
                    tzinfo=OPERATOR_TZ).astimezone(timezone.utc)


def seed(db: Session, now: datetime | None = None) -> None:
    now = now or utcnow()
    towns = {name: Town(name=name, zone=zone) for name, zone in TOWNS}
    db.add_all(towns.values())
    db.flush()

    trips: list[Trip] = []
    for origin, dest, when, capacity, status in TRIPS:
        trips.append(Trip(origin_id=towns[origin].id, destination_id=towns[dest].id,
                          departure_time=_departure(when, now), capacity=capacity,
                          status=status, seats_booked=0))
    db.add_all(trips)
    db.flush()

    for n, name, seats in BOOKINGS:
        trip = trips[n - 1]
        origin_name, dest_name = TRIPS[n - 1][0], TRIPS[n - 1][1]
        fare = fare_cents(towns[origin_name].zone, towns[dest_name].zone)
        trip.seats_booked += seats       # keep the denormalised counter consistent
        db.add(Booking(reference=new_reference(), trip_id=trip.id, passenger_name=name,
                       seats=seats, fare_per_seat_cents=fare, total_cents=fare * seats,
                       created_at=now - timedelta(hours=len(name))))
    db.commit()


def seed_if_empty(db: Session) -> bool:
    if db.scalar(select(Town.id).limit(1)) is not None:
        return False
    seed(db)
    return True


def reset(engine, session_factory) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with session_factory() as db:
        seed(db)


if __name__ == "__main__":
    from app.config import get_settings
    from app.database import make_engine, make_session_factory

    engine = make_engine(get_settings().database_url)
    factory = make_session_factory(engine)
    Base.metadata.create_all(engine)
    if "--reset" in sys.argv:
        reset(engine, factory)
        print("Database reset and reseeded: 6 towns, 10 trips, 15 bookings.")
    else:
        with factory() as session:
            print("Seeded." if seed_if_empty(session) else
                  "Database already has data. Use --reset to wipe and reseed.")