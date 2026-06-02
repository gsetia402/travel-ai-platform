from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import TripTable, TravellerResponse
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
from services.registration_service import (
    generate_link,
    get_registration_link,
    deactivate_registration_link,
    save_form_config,
    get_trip_form_config,
    get_public_trip_info,
    self_register,
    create_trip_invitation,
    list_trip_invitations,
    get_registration_summary,
    DuplicateError,
    LinkInactiveError,
)
from services.auth_service import get_current_user
from dependencies import require_trip_access

router = APIRouter(tags=["Registration & Invitations"])


# --- Registration Link ---

@router.post("/trips/{trip_id}/registration-link", response_model=RegistrationLinkResponse, status_code=201)
def create_link(trip_id: str, request: GenerateLinkRequest = GenerateLinkRequest(), db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return generate_link(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/registration-link", response_model=RegistrationLinkResponse)
def get_link(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_registration_link(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/registration-links/{registration_code}/deactivate", response_model=RegistrationLinkResponse)
def deactivate_link(registration_code: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return deactivate_registration_link(db, registration_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Form Config ---

@router.put("/trips/{trip_id}/registration-form-config", response_model=FormConfigResponse)
def set_form_config(trip_id: str, request: FormConfigRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return save_form_config(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/registration-form-config", response_model=FormConfigResponse)
def get_form_config(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_trip_form_config(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Public Registration ---

@router.get("/register/{registration_code}", response_model=PublicTripInfoResponse)
def public_trip_info(registration_code: str, db: Session = Depends(get_db)):
    try:
        return get_public_trip_info(db, registration_code)
    except LinkInactiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/register/{registration_code}", response_model=TravellerResponse, status_code=201)
def register_traveller(registration_code: str, request: SelfRegisterRequest, db: Session = Depends(get_db)):
    try:
        return self_register(db, registration_code, request)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except LinkInactiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Public Document Upload (during registration) ---

@router.post("/register/{registration_code}/documents/{traveller_id}", status_code=201)
async def upload_registration_document(
    registration_code: str,
    traveller_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a document during public registration. Document is auto-verified."""
    from repositories.registration_repository import get_link_by_code
    from services.registration_service import _validate_link, LinkInactiveError
    from services.document_service import upload_document

    link = get_link_by_code(db, registration_code)
    if not link:
        raise HTTPException(status_code=404, detail="Registration link not found")
    try:
        _validate_link(link)
    except LinkInactiveError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        content = await file.read()
        doc = upload_document(db, traveller_id, document_type, file.filename, content)
        return {"document_id": doc.document_id, "status": doc.verification_status, "file_name": doc.file_name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Invitations ---

@router.post("/trips/{trip_id}/invitations", response_model=InvitationResponse, status_code=201)
def create_invitation(trip_id: str, request: InvitationCreateRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return create_trip_invitation(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/invitations", response_model=List[InvitationResponse])
def list_invitations(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return list_trip_invitations(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Registration Dashboard ---

@router.get("/trips/{trip_id}/registration-summary", response_model=RegistrationSummaryResponse)
def registration_summary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_registration_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
