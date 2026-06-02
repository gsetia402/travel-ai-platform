from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.group_trip import (
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
)

router = APIRouter(tags=["Trips"])


@router.post("/trips", response_model=TripResponse, status_code=201)
def create_trip(request: TripCreateRequest, db: Session = Depends(get_db)):
    try:
        return create_new_trip(db, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips", response_model=List[TripResponse])
def get_all_trips(db: Session = Depends(get_db)):
    return list_trips(db)


@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip_by_id(trip_id: str, db: Session = Depends(get_db)):
    try:
        return get_trip(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/trips/{trip_id}", response_model=TripResponse)
def update_trip(trip_id: str, request: TripUpdateRequest, db: Session = Depends(get_db)):
    try:
        return update_existing_trip(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/trips/{trip_id}", status_code=200)
def delete_trip(trip_id: str, db: Session = Depends(get_db)):
    try:
        remove_trip(db, trip_id)
        return {"message": f"Trip {trip_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/summary", response_model=TripSummaryResponse)
def trip_summary(trip_id: str, db: Session = Depends(get_db)):
    try:
        return get_trip_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/risk-summary", response_model=RiskSummaryResponse)
def risk_summary(trip_id: str, db: Session = Depends(get_db)):
    try:
        return get_risk_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
