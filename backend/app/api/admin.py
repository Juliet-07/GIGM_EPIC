from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import TripStatus
from app.schemas import AdminTripOut, StatusUpdate
from app.services import trips

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _to_out(trip, bookings_count: int) -> AdminTripOut:
    return AdminTripOut(
        id=trip.id, origin=trip.origin, destination=trip.destination,
        departure_time=trip.departure_time, capacity=trip.capacity,
        seats_booked=trip.seats_booked, seats_available=trip.seats_available,
        bookings_count=bookings_count, status=trip.status,
        next_status=trips.NEXT_STATUS[trip.status],
    )


@router.get("/trips", response_model=list[AdminTripOut], summary="Dashboard: every trip")
def dashboard(status: TripStatus | None = None, db: Session = Depends(get_db)):
    return [_to_out(t, n) for t, n in trips.admin_dashboard(db, status)]


@router.patch("/trips/{trip_id}/status", response_model=AdminTripOut,
              summary="Move a trip to its next lifecycle state")
def update_status(trip_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    trips.advance_status(db, trip_id, body.status)
    return _to_out(*trips.admin_dashboard(db, trip_id=trip_id)[0])