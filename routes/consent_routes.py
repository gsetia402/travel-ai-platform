from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.consent import ConsentCreateRequest, ConsentResponse
from services.consent_service import (
    create_traveller_consent,
    list_traveller_consents,
    approve_consent,
    reject_consent,
    ConflictError,
)

router = APIRouter(tags=["Consents"])


@router.post("/travellers/{traveller_id}/consents", response_model=ConsentResponse, status_code=201)
def create_consent(traveller_id: str, request: ConsentCreateRequest, db: Session = Depends(get_db)):
    try:
        return create_traveller_consent(db, traveller_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/travellers/{traveller_id}/consents", response_model=List[ConsentResponse])
def get_consents(traveller_id: str, db: Session = Depends(get_db)):
    try:
        return list_traveller_consents(db, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/consents/{consent_id}/approve", response_model=ConsentResponse)
def approve(consent_id: str, db: Session = Depends(get_db)):
    try:
        return approve_consent(db, consent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/consents/{consent_id}/reject", response_model=ConsentResponse)
def reject(consent_id: str, db: Session = Depends(get_db)):
    try:
        return reject_consent(db, consent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
