"""Customer-facing endpoints."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_now
from app.schemas import BookingCreate, BookingOut, FareQuote, TownOut, TripOut
from app.services import bookings, trips

router = APIRouter(prefix="/api", tags=["customer"])


@router.get("/towns", response_model=list[TownOut])
def towns(db: Session = Depends(get_db)):
    return trips.list_towns(db)


@router.get("/fares", response_model=FareQuote, summary="Price a journey between two towns")
def fare(origin_id: int, destination_id: int, db: Session = Depends(get_db)):
    origin, destination, cents = trips.quote(db, origin_id, destination_id)
    return FareQuote(origin=origin, destination=destination, fare_cents=cents)


@router.get("/trips", response_model=list[TripOut], summary="Search bookable trips on a route")
def search(origin_id: int, destination_id: int,
           day: date | None = Query(None, alias="date",
                                    description="Local (Nigerian) calendar day, YYYY-MM-DD"),
           db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    return [
        TripOut(
            id=t.id, origin=t.origin, destination=t.destination, departure_time=t.departure_time,
            capacity=t.capacity, seats_available=t.seats_available, fare_cents=fare_cents,
            status=t.status,
        )
        for t, fare_cents in trips.search_trips(db, origin_id, destination_id, day, now)
    ]
    
@router.post("/bookings", response_model=BookingOut, status_code=201,
             summary="Book seats on a trip")
def book(body: BookingCreate, response: Response,
         idempotency_key: str | None = Header(None, max_length=64),
         db: Session = Depends(get_db), now: datetime = Depends(get_now)):
    booking, created = bookings.create_booking(
        db, trip_id=body.trip_id, passenger_name=body.passenger_name, seats=body.seats,
        now=now, idempotency_key=idempotency_key,
    )
    if not created:
        response.status_code = 200  # replay of an earlier identical request
    return booking


@router.get("/bookings/{reference}", response_model=BookingOut)
def booking_detail(reference: str, db: Session = Depends(get_db)):
    return bookings.get_booking(db, reference)