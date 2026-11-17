from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.config import CURRENCY, MAX_SEATS_PER_BOOKING
from app.models import TripStatus


class TownOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    zone: int


class FareQuote(BaseModel):
    origin: TownOut
    destination: TownOut
    fare_cents: int
    currency: str = CURRENCY


class TripOut(BaseModel):
    """What a customer sees when searching."""
    id: int
    origin: TownOut
    destination: TownOut
    departure_time: datetime
    capacity: int
    seats_available: int
    fare_cents: int
    currency: str = CURRENCY
    status: TripStatus


class AdminTripOut(BaseModel):
    """What the operator sees on the dashboard."""
    id: int
    origin: TownOut
    destination: TownOut
    departure_time: datetime
    capacity: int
    seats_booked: int
    seats_available: int
    bookings_count: int
    status: TripStatus
    next_status: TripStatus | None


class BookingCreate(BaseModel):
    trip_id: int
    passenger_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    seats: int = Field(ge=1, le=MAX_SEATS_PER_BOOKING)


class BookingTripSummary(BaseModel):
    id: int
    origin: TownOut
    destination: TownOut
    departure_time: datetime


class BookingOut(BaseModel):
    reference: str
    trip: BookingTripSummary
    passenger_name: str
    seats: int
    fare_per_seat_cents: int
    total_cents: int
    currency: str = CURRENCY
    created_at: datetime


class StatusUpdate(BaseModel):
    status: TripStatus