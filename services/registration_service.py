import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from models.registration import (
    GenerateLinkRequest,
    RegistrationLinkResponse,
    FormConfigRequest,
    FormConfigResponse,
    PublicTripInfoResponse,
    SelfRegisterRequest,
    InvitationCreateRequest,
    InvitationResponse,
    RegistrationSummaryResponse,
)
from models.group_trip import TravellerResponse, TravellerCreateRequest
from repositories.registration_repository import (
    create_registration_link,
    get_link_by_trip,
    get_link_by_code,
    deactivate_link,
    upsert_form_config,
    get_form_config,
    traveller_exists_by_phone,
    traveller_exists_by_email,
    create_invitation,
    get_invitations_by_trip,
)
from repositories.trip_repository import get_trip_by_id
from repositories.traveller_repository import add_traveller, count_travellers_by_trip

logger = logging.getLogger(__name__)


class DuplicateError(Exception):
    pass


class LinkInactiveError(Exception):
    pass


# --- Registration Link ---

def generate_link(db: Session, trip_id: str, request: GenerateLinkRequest) -> RegistrationLinkResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    link = create_registration_link(db, trip_id, expires_at=request.expires_at)
    return RegistrationLinkResponse(
        registration_link_id=link.registration_link_id,
        trip_id=link.trip_id,
        registration_code=link.registration_code,
        registration_url=f"/register/{link.registration_code}",
        active=link.active,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )


def get_registration_link(db: Session, trip_id: str) -> RegistrationLinkResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    link = get_link_by_trip(db, trip_id)
    if not link:
        raise ValueError(f"No registration link found for trip: {trip_id}")

    return RegistrationLinkResponse(
        registration_link_id=link.registration_link_id,
        trip_id=link.trip_id,
        registration_code=link.registration_code,
        registration_url=f"/register/{link.registration_code}",
        active=link.active,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )


def deactivate_registration_link(db: Session, code: str) -> RegistrationLinkResponse:
    link = deactivate_link(db, code)
    if not link:
        raise ValueError(f"Registration link not found: {code}")

    return RegistrationLinkResponse(
        registration_link_id=link.registration_link_id,
        trip_id=link.trip_id,
        registration_code=link.registration_code,
        registration_url=f"/register/{link.registration_code}",
        active=link.active,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )


# --- Form Config ---

def save_form_config(db: Session, trip_id: str, request: FormConfigRequest) -> FormConfigResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    config = upsert_form_config(db, trip_id, **request.model_dump())
    return FormConfigResponse.model_validate(config)


def get_trip_form_config(db: Session, trip_id: str) -> FormConfigResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    config = get_form_config(db, trip_id)
    if not config:
        config = upsert_form_config(db, trip_id)
    return FormConfigResponse.model_validate(config)


# --- Public Registration ---

def _build_required_fields(config) -> List[str]:
    fields = ["first_name", "last_name", "phone", "email"]
    if config and config.collect_emergency_contact:
        fields.extend(["emergency_contact_name", "emergency_contact_phone"])
    if config and config.collect_medical_information:
        fields.extend(["medical_conditions", "allergies"])
    if config and config.collect_dietary_preferences:
        fields.append("dietary_preferences")
    if config and config.collect_passport_details:
        fields.extend(["passport_number", "nationality"])
    if config and config.require_date_of_birth:
        fields.append("date_of_birth")
    return fields


def _validate_link(link) -> None:
    if not link:
        raise ValueError("Invalid registration code")
    if not link.active:
        raise LinkInactiveError("Registration link is no longer active")
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise LinkInactiveError("Registration link has expired")


def get_public_trip_info(db: Session, code: str) -> PublicTripInfoResponse:
    link = get_link_by_code(db, code)
    _validate_link(link)

    trip = get_trip_by_id(db, link.trip_id)
    if not trip:
        raise ValueError("Trip not found")

    config = get_form_config(db, link.trip_id)
    required_fields = _build_required_fields(config)

    return PublicTripInfoResponse(
        trip_name=trip.trip_name,
        origin_city=trip.origin_city,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        days=trip.days,
        required_fields=required_fields,
    )


def self_register(db: Session, code: str, request: SelfRegisterRequest) -> TravellerResponse:
    link = get_link_by_code(db, code)
    _validate_link(link)

    trip_id = link.trip_id

    if traveller_exists_by_phone(db, trip_id, request.phone):
        raise DuplicateError(f"Phone number already registered for this trip: {request.phone}")
    if traveller_exists_by_email(db, trip_id, request.email):
        raise DuplicateError(f"Email already registered for this trip: {request.email}")

    create_req = TravellerCreateRequest(
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        email=request.email,
        gender=request.gender,
        city=request.city,
        department=request.department,
        date_of_birth=request.date_of_birth,
        emergency_contact_name=request.emergency_contact_name,
        emergency_contact_phone=request.emergency_contact_phone,
        emergency_relationship=request.emergency_relationship,
        medical_conditions=request.medical_conditions,
        allergies=request.allergies,
        dietary_preferences=request.dietary_preferences,
        passport_number=request.passport_number,
        nationality=request.nationality,
        participation_status="ACTIVE",
    )

    traveller = add_traveller(db, trip_id, create_req)
    logger.info(f"Self-registered traveller {traveller.traveller_id} via code {code}")
    return TravellerResponse.model_validate(traveller)


# --- Invitation ---

def create_trip_invitation(db: Session, trip_id: str, request: InvitationCreateRequest) -> InvitationResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    inv = create_invitation(db, trip_id, request.recipient_name, request.phone, request.email)
    return InvitationResponse.model_validate(inv)


def list_trip_invitations(db: Session, trip_id: str) -> List[InvitationResponse]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    invs = get_invitations_by_trip(db, trip_id)
    return [InvitationResponse.model_validate(i) for i in invs]


# --- Registration Dashboard ---

def get_registration_summary(db: Session, trip_id: str) -> RegistrationSummaryResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    registered = count_travellers_by_trip(db, trip_id)
    total = trip.traveller_count
    pending = max(0, total - registered)
    pct = round((registered / total) * 100, 2) if total > 0 else 0.0

    return RegistrationSummaryResponse(
        total_registered=registered,
        pending_registrations=pending,
        registration_completion_percentage=pct,
    )
