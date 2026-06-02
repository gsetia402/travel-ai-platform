import os
import logging
from typing import List

from sqlalchemy.orm import Session

from models.document import (
    DocumentUploadResponse,
    VerifyRequest,
    RequirementCreateRequest,
    RequirementResponse,
    DocumentSummaryResponse,
    TravellerReadinessResponse,
    VerificationStatus,
)
from repositories.document_repository import (
    create_document,
    get_document_by_id,
    get_documents_by_traveller,
    verify_document,
    reject_document,
    add_requirement,
    get_requirements_by_trip,
    count_uploaded_by_trip,
    count_verified_by_trip,
    count_pending_by_trip,
    count_rejected_by_trip,
    get_uploaded_types_for_traveller,
)
from repositories.trip_repository import get_trip_by_id
from repositories.traveller_repository import get_traveller_by_id, count_travellers_by_trip
from repositories.consent_repository import count_consents_by_traveller_and_status

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")


class ConflictError(Exception):
    pass


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


# --- Upload ---

def upload_document(db: Session, traveller_id: str, document_type: str, file_name: str, file_content: bytes) -> DocumentUploadResponse:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    _ensure_upload_dir()
    traveller_dir = os.path.join(UPLOAD_DIR, traveller_id)
    os.makedirs(traveller_dir, exist_ok=True)

    file_path = os.path.join(traveller_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(file_content)

    doc = create_document(db, traveller_id, document_type, file_name, file_path)
    return DocumentUploadResponse.model_validate(doc)


# --- List ---

def list_traveller_documents(db: Session, traveller_id: str) -> List[DocumentUploadResponse]:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    docs = get_documents_by_traveller(db, traveller_id)
    return [DocumentUploadResponse.model_validate(d) for d in docs]


# --- Verify / Reject ---

def verify_doc(db: Session, document_id: str, request: VerifyRequest) -> DocumentUploadResponse:
    existing = get_document_by_id(db, document_id)
    if not existing:
        raise ValueError(f"Document not found: {document_id}")
    if existing.verification_status == VerificationStatus.VERIFIED.value:
        raise ConflictError(f"Document {document_id} is already verified")

    doc = verify_document(db, document_id, request.verified_by, request.remarks)
    return DocumentUploadResponse.model_validate(doc)


def reject_doc(db: Session, document_id: str, request: VerifyRequest) -> DocumentUploadResponse:
    existing = get_document_by_id(db, document_id)
    if not existing:
        raise ValueError(f"Document not found: {document_id}")
    if existing.verification_status == VerificationStatus.REJECTED.value:
        raise ConflictError(f"Document {document_id} is already rejected")

    doc = reject_document(db, document_id, request.verified_by, request.remarks)
    return DocumentUploadResponse.model_validate(doc)


# --- Requirements ---

def add_trip_requirement(db: Session, trip_id: str, request: RequirementCreateRequest) -> RequirementResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    req = add_requirement(db, trip_id, request.document_type.value, request.mandatory)
    return RequirementResponse.model_validate(req)


def list_trip_requirements(db: Session, trip_id: str) -> List[RequirementResponse]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    reqs = get_requirements_by_trip(db, trip_id)
    return [RequirementResponse.model_validate(r) for r in reqs]


# --- Document Summary ---

def get_document_summary(db: Session, trip_id: str) -> DocumentSummaryResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    reqs = get_requirements_by_trip(db, trip_id)
    mandatory_count = sum(1 for r in reqs if r.mandatory)
    traveller_count = count_travellers_by_trip(db, trip_id)

    required_total = mandatory_count * traveller_count
    uploaded = count_uploaded_by_trip(db, trip_id)
    verified = count_verified_by_trip(db, trip_id)
    pending = count_pending_by_trip(db, trip_id)
    rejected = count_rejected_by_trip(db, trip_id)
    missing = max(0, required_total - uploaded)

    return DocumentSummaryResponse(
        required_documents=required_total,
        uploaded_documents=uploaded,
        verified_documents=verified,
        pending_documents=pending,
        rejected_documents=rejected,
        missing_documents=missing,
    )


# --- Traveller Readiness ---

def get_traveller_readiness(db: Session, traveller_id: str) -> TravellerReadinessResponse:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    profile_completed = all([
        traveller.first_name,
        traveller.last_name,
        traveller.phone,
        traveller.email,
        traveller.emergency_contact_name,
        traveller.emergency_contact_phone,
    ])

    pending_consents = count_consents_by_traveller_and_status(db, traveller_id, "PENDING")
    consents_completed = pending_consents == 0

    trip_id = traveller.trip_id
    reqs = get_requirements_by_trip(db, trip_id)
    mandatory_types = {r.document_type for r in reqs if r.mandatory}
    uploaded_types = set(get_uploaded_types_for_traveller(db, traveller_id))
    documents_completed = mandatory_types.issubset(uploaded_types)

    trip_ready = profile_completed and consents_completed and documents_completed

    return TravellerReadinessResponse(
        profile_completed=profile_completed,
        consents_completed=consents_completed,
        documents_completed=documents_completed,
        trip_ready=trip_ready,
    )


# --- Trip Readiness Percentage ---

def calculate_trip_readiness_percentage(db: Session, trip_id: str) -> float:
    from repositories.traveller_repository import get_travellers_by_trip

    travellers = get_travellers_by_trip(db, trip_id)
    if not travellers:
        return 0.0

    ready_count = 0
    for t in travellers:
        try:
            readiness = get_traveller_readiness(db, t.traveller_id)
            if readiness.trip_ready:
                ready_count += 1
        except Exception:
            pass

    return round((ready_count / len(travellers)) * 100, 2)
