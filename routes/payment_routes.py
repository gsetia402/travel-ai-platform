"""Payment tracking API routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from database import get_db
from models.auth import UserTable
from models.payment import (
    PaymentCreateRequest, PaymentResponse, PaymentConfigRequest, PaymentConfigResponse,
    TravellerPaymentSummary, PaymentDashboard,
)
from services.payment_service import (
    add_payment, list_payments, list_traveller_payments, reject_payment_record,
    upload_payment_proof, update_payment_config, get_config,
    get_traveller_payment_summaries, get_payment_dashboard,
)
from repositories.payment_repository import get_payment_by_id
from services.storage_provider import get_storage_provider, _content_type_from_filename
from services.auth_service import get_current_user

router = APIRouter(tags=["Payments"])

ALLOWED_PROOF_TYPES = {"pdf", "jpg", "jpeg", "png"}


# --------------- Payment Config ---------------

@router.get("/trips/{trip_id}/payment-config", response_model=PaymentConfigResponse)
def get_payment_config_route(trip_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return get_config(db, trip_id)


@router.put("/trips/{trip_id}/payment-config", response_model=PaymentConfigResponse)
def update_payment_config_route(trip_id: str, request: PaymentConfigRequest, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return update_payment_config(db, trip_id, request)


# --------------- Payment CRUD ---------------

@router.post("/trips/{trip_id}/payments", response_model=PaymentResponse, status_code=201)
def record_payment(trip_id: str, request: PaymentCreateRequest, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return add_payment(db, trip_id, request)


@router.get("/trips/{trip_id}/payments", response_model=List[PaymentResponse])
def get_payments(trip_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return list_payments(db, trip_id)


@router.get("/trips/{trip_id}/travellers/{traveller_id}/payments", response_model=List[PaymentResponse])
def get_traveller_payments_route(trip_id: str, traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return list_traveller_payments(db, trip_id, traveller_id)


# --------------- Payment Verification ---------------

@router.post("/payments/{payment_id}/reject")
def reject_payment_route(payment_id: str, reason: Optional[str] = None, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    result = reject_payment_record(db, payment_id, reason)
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result


# --------------- Payment Proof ---------------

@router.post("/payments/{payment_id}/proof", response_model=PaymentResponse)
async def upload_proof(payment_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in ALLOWED_PROOF_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_PROOF_TYPES)}")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    return upload_payment_proof(db, payment_id, file.filename, data)


@router.get("/payments/{payment_id}/proof")
def download_proof(payment_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    payment = get_payment_by_id(db, payment_id)
    if not payment or not payment.proof_path:
        raise HTTPException(status_code=404, detail="Proof not found")
    storage = get_storage_provider()
    data = storage.download(payment.proof_path)
    content_type = _content_type_from_filename(payment.proof_path)
    return StreamingResponse(io.BytesIO(data), media_type=content_type)


# --------------- Dashboard & Summaries ---------------

@router.get("/trips/{trip_id}/payment-dashboard", response_model=PaymentDashboard)
def payment_dashboard(trip_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return get_payment_dashboard(db, trip_id)


@router.get("/trips/{trip_id}/traveller-payment-summaries", response_model=List[TravellerPaymentSummary])
def traveller_summaries(trip_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    return get_traveller_payment_summaries(db, trip_id)
