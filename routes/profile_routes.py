from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.group_trip import TravellerResponse, TravellerUpdateRequest
from services.profile_service import get_traveller_profile, update_traveller_profile

router = APIRouter(tags=["Traveller Profiles"])


@router.get("/travellers/{traveller_id}", response_model=TravellerResponse)
def get_profile(traveller_id: str, db: Session = Depends(get_db)):
    try:
        return get_traveller_profile(db, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/travellers/{traveller_id}", response_model=TravellerResponse)
def update_profile(traveller_id: str, request: TravellerUpdateRequest, db: Session = Depends(get_db)):
    try:
        return update_traveller_profile(db, traveller_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
