import logging
from typing import List

from sqlalchemy.orm import Session

from models.group_trip import (
    TripCreateRequest,
    TripResponse,
    TripSummaryResponse,
    RiskSummaryResponse,
)
from repositories.trip_repository import (
    create_trip,
    get_all_trips,
    get_trip_by_id,
    delete_trip,
)
from repositories.traveller_repository import (
    count_travellers_by_trip,
    count_travellers_by_status,
    count_travellers_with_medical,
    count_travellers_with_special_requirements,
)
from repositories.room_repository import count_rooms_by_trip, count_allocated_travellers_by_trip
from repositories.consent_repository import count_consents_by_trip_and_status
from repositories.expense_repository import sum_expenses_by_trip
from repositories.registration_repository import is_link_active
from services.document_service import calculate_trip_readiness_percentage

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
    rooms_allocated = count_rooms_by_trip(db, trip_id)
    allocated_travellers = count_allocated_travellers_by_trip(db, trip_id)
    unallocated = max(0, registered - allocated_travellers)

    confirmed = count_travellers_by_status(db, trip_id, "CONFIRMED")
    invited = count_travellers_by_status(db, trip_id, "INVITED")
    pending_consents = count_consents_by_trip_and_status(db, trip_id, "PENDING")
    approved_consents = count_consents_by_trip_and_status(db, trip_id, "APPROVED")

    return TripSummaryResponse(
        trip_name=trip.trip_name,
        destination=trip.destination,
        traveller_count=trip.traveller_count,
        budget=trip.budget,
        registered_travellers=registered,
        pending_travellers=pending,
        rooms_allocated=rooms_allocated,
        unallocated_travellers=unallocated,
        confirmed_travellers=confirmed,
        pending_confirmations=invited,
        pending_consents=pending_consents,
        approved_consents=approved_consents,
        total_budget=trip.budget,
        amount_spent=sum_expenses_by_trip(db, trip_id),
        remaining_budget=trip.budget - sum_expenses_by_trip(db, trip_id),
        registration_link_active=is_link_active(db, trip_id),
        trip_ready_percentage=calculate_trip_readiness_percentage(db, trip_id),
    )


def get_risk_summary(db: Session, trip_id: str) -> RiskSummaryResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    medical = count_travellers_with_medical(db, trip_id)
    special = count_travellers_with_special_requirements(db, trip_id)
    pending_consents = count_consents_by_trip_and_status(db, trip_id, "PENDING")
    high_risk = medical  # travellers with medical conditions are considered high-risk

    return RiskSummaryResponse(
        medical_cases=medical,
        travellers_with_special_requirements=special,
        pending_consents=pending_consents,
        high_risk_travellers=high_risk,
    )
