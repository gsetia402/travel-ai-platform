from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import (
    TripTable,
    TripCreateRequest,
    TripUpdateRequest,
    TripResponse,
    TripSummaryResponse,
    RiskSummaryResponse,
)
from services.trip_service import (
    create_new_trip,
    list_trips,
    get_trip,
    update_existing_trip,
    remove_trip,
    get_trip_summary,
    get_risk_summary,
    get_all_trips_with_summaries,
)
from services.auth_service import get_current_user
from dependencies import require_trip_access

router = APIRouter(tags=["Trips"])


@router.post("/trips", response_model=TripResponse, status_code=201)
def create_trip(request: TripCreateRequest, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return create_new_trip(db, request, organization_id=user.organization_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips", response_model=List[TripResponse])
def get_all_trips(db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return list_trips(db, organization_id=user.organization_id)


@router.get("/trips-overview")
def trips_overview(db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return get_all_trips_with_summaries(db, organization_id=user.organization_id)


@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip_by_id(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    return TripResponse.model_validate(trip)


@router.put("/trips/{trip_id}", response_model=TripResponse)
def update_trip(trip_id: str, request: TripUpdateRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return update_existing_trip(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/trips/{trip_id}", status_code=200)
def delete_trip(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        remove_trip(db, trip_id)
        return {"message": f"Trip {trip_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/summary", response_model=TripSummaryResponse)
def trip_summary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_trip_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/risk-summary", response_model=RiskSummaryResponse)
def risk_summary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_risk_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


VALID_TRANSITIONS = {
    "DRAFT": ["REGISTRATION_OPEN", "CANCELLED"],
    "REGISTRATION_OPEN": ["REGISTRATION_CLOSED", "CANCELLED"],
    "REGISTRATION_CLOSED": ["PLANNING", "REGISTRATION_OPEN", "CANCELLED"],
    "PLANNING": ["READY_TO_DEPART", "CANCELLED"],
    "READY_TO_DEPART": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": ["DRAFT"],
}


class StatusChangeRequest(BaseModel):
    status: str


@router.put("/trips/{trip_id}/status")
def change_trip_status(trip_id: str, request: StatusChangeRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    current = trip.status or "DRAFT"
    target = request.status
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current} to {target}. Allowed: {allowed}")
    trip.status = target
    db.commit()
    db.refresh(trip)
    return TripResponse.model_validate(trip)
