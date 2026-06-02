from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models.group_trip import (
    TravellerCreateRequest,
    TravellerResponse,
    CSVUploadResponse,
)
from services.traveller_service import (
    create_traveller,
    list_travellers,
    remove_traveller,
    upload_travellers_csv,
)

router = APIRouter(tags=["Travellers"])


@router.post("/trips/{trip_id}/travellers", response_model=TravellerResponse, status_code=201)
def add_traveller(trip_id: str, request: TravellerCreateRequest, db: Session = Depends(get_db)):
    try:
        return create_traveller(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/travellers", response_model=List[TravellerResponse])
def get_travellers(trip_id: str, db: Session = Depends(get_db)):
    try:
        return list_travellers(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/travellers/{traveller_id}", status_code=200)
def delete_traveller(traveller_id: str, db: Session = Depends(get_db)):
    try:
        remove_traveller(db, traveller_id)
        return {"message": f"Traveller {traveller_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips/{trip_id}/travellers/upload", response_model=CSVUploadResponse)
async def upload_csv(trip_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    try:
        content = await file.read()
        return upload_travellers_csv(db, trip_id, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
