"""Routes for the Traveller Portal — login, profile, trip info, documents, communications."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models.group_trip import TravellerTable, TripTable
from models.traveller_portal import (
    TravellerLoginRequest,
    TravellerTokenResponse,
    TravellerMeResponse,
    TravellerProfileUpdateRequest,
    TravellerTripResponse,
    TravellerRoomResponse,
    VisibilitySettingsRequest,
    VisibilitySettingsResponse,
    OptOutRequest,
)
from models.document import DocumentUploadResponse, DocumentType, TravellerReadinessResponse
from models.communication import InboxMessageResponse
from services.traveller_portal_service import (
    traveller_login,
    get_current_traveller,
    get_traveller_profile,
    update_traveller_profile,
    get_traveller_trip,
    get_traveller_room,
    get_visibility_settings,
    update_visibility_settings,
)
from services.document_service import (
    list_traveller_documents,
    upload_document,
    get_traveller_readiness,
)
from services.communication_service import get_traveller_inbox, mark_message_read
from dependencies import require_trip_access
from models.auth import UserTable
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traveller", tags=["Traveller Portal"])


# ---------- Auth ----------

@router.post("/login", response_model=TravellerTokenResponse)
def login(request: TravellerLoginRequest, db: Session = Depends(get_db)):
    try:
        return traveller_login(db, request)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=TravellerMeResponse)
def me(traveller: TravellerTable = Depends(get_current_traveller)):
    return get_traveller_profile(traveller)


# ---------- Profile ----------

@router.get("/profile", response_model=TravellerMeResponse)
def profile(traveller: TravellerTable = Depends(get_current_traveller)):
    return get_traveller_profile(traveller)


@router.put("/profile", response_model=TravellerMeResponse)
def update_profile(
    updates: TravellerProfileUpdateRequest,
    db: Session = Depends(get_db),
    traveller: TravellerTable = Depends(get_current_traveller),
):
    return update_traveller_profile(db, traveller, updates)


# ---------- Trip ----------

@router.get("/trips", response_model=TravellerTripResponse)
def trip_info(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    return get_traveller_trip(db, traveller)


@router.post("/opt-out")
def opt_out_of_trip(
    payload: OptOutRequest,
    db: Session = Depends(get_db),
    traveller: TravellerTable = Depends(get_current_traveller),
):
    """Allow a traveller to opt out of their trip."""
    import uuid as _uuid
    from datetime import datetime
    from models.group_trip import MembershipAuditTable
    if traveller.membership_status == "OPTED_OUT":
        raise HTTPException(status_code=400, detail="Already opted out")
    old_status = traveller.membership_status
    traveller.membership_status = "OPTED_OUT"
    traveller.participation_status = "OPTED_OUT"
    traveller.opt_out_reason = payload.reason
    traveller.membership_updated_at = datetime.utcnow()
    traveller.membership_updated_by = traveller.traveller_id
    db.add(MembershipAuditTable(
        id=str(_uuid.uuid4()),
        traveller_id=traveller.traveller_id,
        trip_id=traveller.trip_id,
        old_status=old_status,
        new_status="OPTED_OUT",
        reason=payload.reason,
        updated_by=traveller.traveller_id,
    ))
    db.commit()
    return {"status": "OPTED_OUT", "message": "You have opted out of this trip."}


# ---------- Itinerary ----------

@router.get("/itinerary")
def itinerary(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    vis = get_visibility_settings(db, traveller.trip_id)
    if not vis.show_itinerary:
        raise HTTPException(status_code=403, detail="Itinerary is not visible for this trip")
    import json
    from models.trip_itinerary import TripItineraryTable
    row = db.query(TripItineraryTable).filter(TripItineraryTable.trip_id == traveller.trip_id).order_by(TripItineraryTable.updated_at.desc()).first()
    if not row:
        return {"trip_id": traveller.trip_id, "days": []}
    try:
        days = json.loads(row.itinerary_json)
    except Exception:
        days = []
    return {"trip_id": traveller.trip_id, "days": days}


# ---------- Room ----------

@router.get("/room", response_model=TravellerRoomResponse)
def room(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    vis = get_visibility_settings(db, traveller.trip_id)
    if not vis.show_room_details:
        raise HTTPException(status_code=403, detail="Room details are not visible for this trip")
    return get_traveller_room(db, traveller)


# ---------- Documents ----------

@router.get("/documents", response_model=List[DocumentUploadResponse])
def documents(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    return list_traveller_documents(db, traveller.traveller_id)


@router.post("/documents", response_model=DocumentUploadResponse, status_code=201)
async def upload_doc(
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    traveller: TravellerTable = Depends(get_current_traveller),
):
    try:
        content = await file.read()
        return upload_document(db, traveller.traveller_id, document_type.value, file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Communications ----------

@router.get("/communications", response_model=List[InboxMessageResponse])
def communications(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    vis = get_visibility_settings(db, traveller.trip_id)
    if not vis.show_communications:
        raise HTTPException(status_code=403, detail="Communications are not visible for this trip")
    return get_traveller_inbox(db, traveller.traveller_id)


@router.post("/communications/{communication_id}/read", status_code=200)
def read_communication(
    communication_id: str,
    db: Session = Depends(get_db),
    traveller: TravellerTable = Depends(get_current_traveller),
):
    try:
        return mark_message_read(db, communication_id, traveller.traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------- Readiness ----------

@router.get("/readiness", response_model=TravellerReadinessResponse)
def readiness(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    return get_traveller_readiness(db, traveller.traveller_id)


# ---------- Visibility Settings (Coordinator) ----------

@router.get("/visibility/{trip_id}", response_model=VisibilitySettingsResponse)
def get_visibility(trip_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return get_visibility_settings(db, trip_id)


@router.put("/visibility/{trip_id}", response_model=VisibilitySettingsResponse)
def set_visibility(
    trip_id: str,
    request: VisibilitySettingsRequest,
    db: Session = Depends(get_db),
    trip: TripTable = Depends(require_trip_access),
):
    return update_visibility_settings(db, trip_id, request.model_dump(exclude_unset=True))
