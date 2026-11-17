import enum
from datetime import datetime

from sqlalchemy import (CheckConstraint, DateTime, Enum, ForeignKey, Index,
                        Integer, String, UniqueConstraint, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator
from datetime import timezone


class Base(DeclarativeBase):
    pass


class UTCDateTime(TypeDecorator):
    """Stores naive UTC, returns timezone-aware UTC. Refuses naive input so a
    local-time datetime can never be silently saved as if it were UTC."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime not allowed; use timezone-aware UTC")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=timezone.utc)


class TripStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    COMPLETED = "completed"


class Town(Base):
    __tablename__ = "towns"
    __table_args__ = (CheckConstraint("zone BETWEEN 1 AND 4", name="ck_town_zone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    zone: Mapped[int] = mapped_column(Integer)


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_trip_capacity_positive"),
        CheckConstraint("seats_booked >= 0", name="ck_trip_seats_nonneg"),
        CheckConstraint("seats_booked <= capacity", name="ck_trip_not_oversold"),
        CheckConstraint("origin_id != destination_id", name="ck_trip_distinct_towns"),
        Index("ix_trip_route_departure", "origin_id", "destination_id", "departure_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    origin_id: Mapped[int] = mapped_column(ForeignKey("towns.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("towns.id"))
    departure_time: Mapped[datetime] = mapped_column(UTCDateTime)
    capacity: Mapped[int] = mapped_column(Integer)
    seats_booked: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, native_enum=False, length=20,
             values_callable=lambda e: [m.value for m in e]),
        default=TripStatus.SCHEDULED,
    )

    origin: Mapped[Town] = relationship(foreign_keys=[origin_id])
    destination: Mapped[Town] = relationship(foreign_keys=[destination_id])
    bookings: Mapped[list["Booking"]] = relationship(back_populates="trip")

    @property
    def seats_available(self) -> int:
        return self.capacity - self.seats_booked


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("seats > 0", name="ck_booking_seats_positive"),
        UniqueConstraint("idempotency_key", name="uq_booking_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(16), unique=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    passenger_name: Mapped[str] = mapped_column(String(100))
    seats: Mapped[int] = mapped_column(Integer)
    fare_per_seat_cents: Mapped[int] = mapped_column(Integer)
    total_cents: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.current_timestamp())

    trip: Mapped[Trip] = relationship(back_populates="bookings")