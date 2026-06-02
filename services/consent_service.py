import logging
from typing import List

from sqlalchemy.orm import Session

from models.consent import ConsentCreateRequest, ConsentResponse, ConsentStatus
from repositories.consent_repository import (
    create_consent,
    get_consent_by_id,
    get_consents_by_traveller,
    update_consent_status,
)
from repositories.traveller_repository import get_traveller_by_id

logger = logging.getLogger(__name__)


def create_traveller_consent(db: Session, traveller_id: str, request: ConsentCreateRequest) -> ConsentResponse:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    consent = create_consent(
        db,
        traveller_id=traveller_id,
        consent_type=request.consent_type.value,
        signed_by=request.signed_by,
        notes=request.notes,
    )
    return ConsentResponse.model_validate(consent)


def list_traveller_consents(db: Session, traveller_id: str) -> List[ConsentResponse]:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    consents = get_consents_by_traveller(db, traveller_id)
    return [ConsentResponse.model_validate(c) for c in consents]


def approve_consent(db: Session, consent_id: str) -> ConsentResponse:
    consent = get_consent_by_id(db, consent_id)
    if not consent:
        raise ValueError(f"Consent not found: {consent_id}")
    if consent.status == ConsentStatus.APPROVED.value:
        raise ConflictError(f"Consent {consent_id} is already approved")

    updated = update_consent_status(db, consent_id, ConsentStatus.APPROVED)
    return ConsentResponse.model_validate(updated)


def reject_consent(db: Session, consent_id: str) -> ConsentResponse:
    consent = get_consent_by_id(db, consent_id)
    if not consent:
        raise ValueError(f"Consent not found: {consent_id}")
    if consent.status == ConsentStatus.REJECTED.value:
        raise ConflictError(f"Consent {consent_id} is already rejected")

    updated = update_consent_status(db, consent_id, ConsentStatus.REJECTED)
    return ConsentResponse.model_validate(updated)


class ConflictError(Exception):
    pass
