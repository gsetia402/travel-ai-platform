import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.group_trip import TripTable
from models.trip_itinerary import TripItineraryRequest, TripItineraryResponse
from repositories.itinerary_repository import get_itinerary, save_itinerary
from dependencies import require_trip_access

router = APIRouter(tags=["Trip Itinerary"])


@router.get("/trips/{trip_id}/itinerary", response_model=TripItineraryResponse)
def get_trip_itinerary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    row = get_itinerary(db, trip_id)
    if not row:
        raise HTTPException(status_code=404, detail="No itinerary saved for this trip")

    days = json.loads(row.itinerary_json)
    return TripItineraryResponse(trip_id=trip_id, days=days, created_at=row.created_at, updated_at=row.updated_at)


@router.post("/trips/{trip_id}/itinerary", response_model=TripItineraryResponse, status_code=201)
def create_trip_itinerary(trip_id: str, request: TripItineraryRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    itinerary_json = json.dumps([d.model_dump() for d in request.days])
    row = save_itinerary(db, trip_id, itinerary_json)
    days = json.loads(row.itinerary_json)
    return TripItineraryResponse(trip_id=trip_id, days=days, created_at=row.created_at, updated_at=row.updated_at)


@router.put("/trips/{trip_id}/itinerary", response_model=TripItineraryResponse)
def update_trip_itinerary(trip_id: str, request: TripItineraryRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    itinerary_json = json.dumps([d.model_dump() for d in request.days])
    row = save_itinerary(db, trip_id, itinerary_json)
    days = json.loads(row.itinerary_json)
    return TripItineraryResponse(trip_id=trip_id, days=days, created_at=row.created_at, updated_at=row.updated_at)
