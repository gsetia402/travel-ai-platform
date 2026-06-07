from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import (
    TripTable,
    TravellerCreateRequest,
    TravellerUpdateRequest,
    TravellerResponse,
    TravellerEnrichedResponse,
    CSVUploadResponse,
)
from services.traveller_service import (
    create_traveller,
    list_travellers,
    list_travellers_enriched,
    get_single_traveller,
    update_traveller,
    remove_traveller,
    remove_travellers_bulk,
    upload_travellers_csv,
)
from services.auth_service import get_current_user
from dependencies import require_trip_access

router = APIRouter(tags=["Travellers"])


@router.get("/all-travellers")
def get_all_travellers_across_trips(db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    from repositories.trip_repository import get_all_trips
    trips = get_all_trips(db, organization_id=user.organization_id)
    all_travellers = []
    for trip in trips:
        travellers = list_travellers(db, trip.trip_id)
        for t in travellers:
            all_travellers.append({**t.model_dump(), "trip_name": trip.trip_name})
    return all_travellers


@router.post("/trips/{trip_id}/travellers", response_model=TravellerResponse, status_code=201)
def add_traveller(trip_id: str, request: TravellerCreateRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return create_traveller(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/travellers", response_model=List[TravellerResponse])
def get_travellers(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return list_travellers(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/travellers-enriched", response_model=List[TravellerEnrichedResponse])
def get_travellers_enriched(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return list_travellers_enriched(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/travellers/{traveller_id}", response_model=TravellerResponse)
def get_traveller(traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return get_single_traveller(db, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/travellers/{traveller_id}", response_model=TravellerResponse)
def edit_traveller(traveller_id: str, request: TravellerUpdateRequest, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return update_traveller(db, traveller_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/travellers/{traveller_id}", status_code=200)
def delete_traveller(traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        remove_traveller(db, traveller_id, removed_by=str(user.user_id))
        return {"message": f"Traveller {traveller_id} removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips/{trip_id}/travellers/bulk-delete")
def bulk_delete_travellers(
    trip_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    trip: TripTable = Depends(require_trip_access),
):
    traveller_ids = payload.get("traveller_ids", [])
    if not traveller_ids or not isinstance(traveller_ids, list):
        raise HTTPException(status_code=400, detail="traveller_ids must be a non-empty list")
    try:
        count = remove_travellers_bulk(db, trip_id, traveller_ids, removed_by=str(getattr(trip, 'organization_id', '')))
        return {"removed": count, "requested": len(traveller_ids)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips/{trip_id}/travellers/upload", response_model=CSVUploadResponse)
async def upload_csv(trip_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    try:
        content = await file.read()
        return upload_travellers_csv(db, trip_id, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
