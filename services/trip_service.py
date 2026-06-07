import logging
from typing import List

from sqlalchemy.orm import Session

from models.group_trip import (
    TripCreateRequest,
    TripUpdateRequest,
    TripResponse,
    TripSummaryResponse,
    RiskSummaryResponse,
)
from repositories.trip_repository import (
    create_trip,
    get_all_trips,
    get_trip_by_id,
    update_trip as repo_update_trip,
    delete_trip,
)
from repositories.traveller_repository import (
    count_travellers_by_trip,
    count_travellers_by_status,
    count_travellers_by_membership,
    count_travellers_with_medical,
    count_travellers_with_special_requirements,
)
from repositories.room_repository import count_rooms_by_trip, count_allocated_travellers_by_trip
from repositories.consent_repository import count_consents_by_trip_and_status
from repositories.expense_repository import sum_expenses_by_trip
from repositories.registration_repository import is_link_active
from services.document_service import calculate_trip_readiness_percentage

logger = logging.getLogger(__name__)


def create_new_trip(db: Session, request: TripCreateRequest, organization_id: str = None) -> TripResponse:
    trip = create_trip(db, request, organization_id=organization_id)
    return TripResponse.model_validate(trip)


def list_trips(db: Session, organization_id: str = None) -> List[TripResponse]:
    trips = get_all_trips(db, organization_id=organization_id)
    return [TripResponse.model_validate(t) for t in trips]


def get_trip(db: Session, trip_id: str) -> TripResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")
    return TripResponse.model_validate(trip)


def update_existing_trip(db: Session, trip_id: str, request: TripUpdateRequest) -> TripResponse:
    trip = repo_update_trip(db, trip_id, request)
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
    active_members = count_travellers_by_membership(db, trip_id, "ACTIVE")
    opted_out = count_travellers_by_membership(db, trip_id, "OPTED_OUT")
    removed = count_travellers_by_membership(db, trip_id, "REMOVED_BY_ORGANIZER")
    pending_consents = count_consents_by_trip_and_status(db, trip_id, "PENDING")
    approved_consents = count_consents_by_trip_and_status(db, trip_id, "APPROVED")

    return TripSummaryResponse(
        trip_name=trip.trip_name,
        origin_city=trip.origin_city,
        destination=trip.destination,
        traveller_count=trip.traveller_count,
        budget=trip.budget,
        registered_travellers=registered,
        pending_travellers=pending,
        rooms_allocated=rooms_allocated,
        unallocated_travellers=unallocated,
        confirmed_travellers=confirmed,
        pending_confirmations=invited,
        active_travellers=active_members,
        opted_out_travellers=opted_out,
        removed_travellers=removed,
        pending_consents=pending_consents,
        approved_consents=approved_consents,
        total_budget=trip.budget,
        amount_spent=sum_expenses_by_trip(db, trip_id),
        remaining_budget=trip.budget - sum_expenses_by_trip(db, trip_id),
        registration_link_active=is_link_active(db, trip_id),
        trip_ready_percentage=calculate_trip_readiness_percentage(db, trip_id),
    )


def get_all_trips_with_summaries(db: Session, organization_id: str = None) -> List[dict]:
    """Return all trips with their summary data in one call — eliminates N+1 on Dashboard."""
    trips = get_all_trips(db, organization_id=organization_id)
    results = []
    for trip in trips:
        try:
            summary = get_trip_summary(db, trip.trip_id)
            results.append({
                **TripResponse.model_validate(trip).model_dump(),
                "summary": summary.model_dump(),
            })
        except Exception:
            results.append({
                **TripResponse.model_validate(trip).model_dump(),
                "summary": None,
            })
    return results


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
