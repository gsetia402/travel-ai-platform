import logging
from typing import List

from sqlalchemy.orm import Session

from models.group_trip import (
    TripCreateRequest,
    TripResponse,
    TripSummaryResponse,
)
from repositories.trip_repository import (
    create_trip,
    get_all_trips,
    get_trip_by_id,
    delete_trip,
)
from repositories.traveller_repository import count_travellers_by_trip

logger = logging.getLogger(__name__)


def create_new_trip(db: Session, request: TripCreateRequest) -> TripResponse:
    trip = create_trip(db, request)
    return TripResponse.model_validate(trip)


def list_trips(db: Session) -> List[TripResponse]:
    trips = get_all_trips(db)
    return [TripResponse.model_validate(t) for t in trips]


def get_trip(db: Session, trip_id: str) -> TripResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")
    return TripResponse.model_validate(trip)


def remove_trip(db: Session, trip_id: str) -> bool:
    deleted = delete_trip(db, trip_id)
    if not deleted:
        raise ValueError(f"Trip not found: {trip_id}")
    return True


def get_trip_summary(db: Session, trip_id: str) -> TripSummaryResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    registered = count_travellers_by_trip(db, trip_id)
    pending = max(0, trip.traveller_count - registered)

    return TripSummaryResponse(
        trip_name=trip.trip_name,
        destination=trip.destination,
        traveller_count=trip.traveller_count,
        budget=trip.budget,
        registered_travellers=registered,
        pending_travellers=pending,
    )
