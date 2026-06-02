from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import TripTable
from models.communication import (
    CommunicationCreateRequest,
    CommunicationResponse,
    CommunicationDetailResponse,
    InboxMessageResponse,
    CommunicationSummaryResponse,
)
from services.communication_service import (
    send_communication,
    list_communications,
    get_communication_detail,
    get_traveller_inbox,
    mark_message_read,
    get_communication_summary,
)
from services.auth_service import get_current_user
from dependencies import require_trip_access

router = APIRouter(tags=["Communications"])


@router.post("/trips/{trip_id}/communications", response_model=CommunicationResponse, status_code=201)
def create_communication(trip_id: str, request: CommunicationCreateRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return send_communication(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trips/{trip_id}/communications", response_model=List[CommunicationResponse])
def get_communications(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return list_communications(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/communications/{communication_id}", response_model=CommunicationDetailResponse)
def get_communication(communication_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return get_communication_detail(db, communication_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/travellers/{traveller_id}/communications", response_model=List[InboxMessageResponse])
def traveller_inbox(traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return get_traveller_inbox(db, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/communications/{communication_id}/read/{traveller_id}", status_code=200)
def read_message(communication_id: str, traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return mark_message_read(db, communication_id, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/communication-summary", response_model=CommunicationSummaryResponse)
def communication_summary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_communication_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
