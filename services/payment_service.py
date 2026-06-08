"""Payment tracking service — handles payments, proof uploads, and dashboard aggregation."""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from models.payment import (
    PaymentCreateRequest, PaymentResponse, PaymentConfigRequest, PaymentConfigResponse,
    TravellerPaymentSummary, PaymentDashboard,
)
from repositories.payment_repository import (
    create_payment, get_payment_by_id, get_payments_by_trip, get_payments_by_traveller,
    sum_approved_payments_by_trip, sum_approved_payments_by_traveller, sum_sponsor_payments,
    reject_payment, delete_payment, get_payment_config, upsert_payment_config,
)
from repositories.trip_repository import get_trip_by_id
from repositories.traveller_repository import get_travellers_by_trip
from repositories.expense_repository import sum_expenses_by_trip
from services.storage_provider import get_storage_provider, _content_type_from_filename

logger = logging.getLogger(__name__)


def add_payment(db: Session, trip_id: str, request: PaymentCreateRequest) -> PaymentResponse:
    payment = create_payment(
        db, trip_id=trip_id,
        traveller_id=request.traveller_id,
        payment_type=request.payment_type.value,
        amount=request.amount,
        payment_date=request.payment_date,
        notes=request.notes,
        sponsor_name=request.sponsor_name,
    )
    logger.info(f"Payment {payment.payment_id} recorded for trip {trip_id} — ₹{request.amount}")
    return PaymentResponse.model_validate(payment)


def list_payments(db: Session, trip_id: str) -> List[PaymentResponse]:
    payments = get_payments_by_trip(db, trip_id)
    return [PaymentResponse.model_validate(p) for p in payments]


def list_traveller_payments(db: Session, trip_id: str, traveller_id: str) -> List[PaymentResponse]:
    payments = get_payments_by_traveller(db, trip_id, traveller_id)
    return [PaymentResponse.model_validate(p) for p in payments]


def reject_payment_record(db: Session, payment_id: str, reason: str = None) -> Optional[PaymentResponse]:
    payment = reject_payment(db, payment_id, reason)
    if not payment:
        return None
    logger.info(f"Payment {payment_id} rejected: {reason or 'no reason'}")
    return PaymentResponse.model_validate(payment)


def upload_payment_proof(db: Session, payment_id: str, filename: str, file_data: bytes) -> PaymentResponse:
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise ValueError("Payment not found")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_type = _content_type_from_filename(filename)
    key = f"payment-proofs/{payment.trip_id}/{payment_id}.{ext}"

    storage = get_storage_provider()
    storage.upload(key, file_data, content_type)
    payment.proof_path = key
    db.commit()
    db.refresh(payment)
    logger.info(f"Proof uploaded for payment {payment_id}: {key}")
    return PaymentResponse.model_validate(payment)


def update_payment_config(db: Session, trip_id: str, request: PaymentConfigRequest) -> PaymentConfigResponse:
    config = upsert_payment_config(
        db, trip_id,
        expected_amount_per_traveller=request.expected_amount_per_traveller,
        registration_fee_enabled=request.registration_fee_enabled,
        registration_fee_amount=request.registration_fee_amount,
        sponsor_name=request.sponsor_name,
        sponsor_commitment=request.sponsor_commitment,
    )
    return PaymentConfigResponse.model_validate(config)


def get_config(db: Session, trip_id: str) -> PaymentConfigResponse:
    config = get_payment_config(db, trip_id)
    if config:
        return PaymentConfigResponse.model_validate(config)
    return PaymentConfigResponse(trip_id=trip_id)


def get_traveller_payment_summaries(db: Session, trip_id: str) -> List[TravellerPaymentSummary]:
    config = get_payment_config(db, trip_id)
    expected = config.expected_amount_per_traveller if config else 0
    reg_fee = config.registration_fee_amount if config and config.registration_fee_enabled else 0
    total_expected = (expected or 0) + (reg_fee or 0)

    travellers = get_travellers_by_trip(db, trip_id)
    summaries = []
    for t in travellers:
        paid = sum_approved_payments_by_traveller(db, trip_id, t.traveller_id)
        outstanding = max(total_expected - paid, 0)
        if paid >= total_expected and total_expected > 0:
            status = "PAID"
        elif paid > 0:
            status = "PARTIAL"
        else:
            status = "PENDING"

        # Check registration fee specifically
        reg_paid = paid >= reg_fee if reg_fee > 0 else True

        summaries.append(TravellerPaymentSummary(
            traveller_id=t.traveller_id,
            traveller_name=f"{t.first_name} {t.last_name}",
            expected_amount=total_expected,
            amount_paid=paid,
            outstanding_amount=outstanding,
            payment_status=status,
            registration_fee_paid=reg_paid,
        ))
    return summaries


def get_payment_dashboard(db: Session, trip_id: str) -> PaymentDashboard:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError("Trip not found")

    config = get_payment_config(db, trip_id)
    expenses = sum_expenses_by_trip(db, trip_id)
    amount_received = sum_approved_payments_by_trip(db, trip_id)

    financial_model = trip.financial_model or "SPONSORED"

    if financial_model == "TRAVELLER_FUNDED":
        expected_per = config.expected_amount_per_traveller if config else 0
        reg_fee = config.registration_fee_amount if config and config.registration_fee_enabled else 0
        total_expected_per = (expected_per or 0) + (reg_fee or 0)

        travellers = get_travellers_by_trip(db, trip_id)
        total_travellers = len(travellers)
        total_expected_all = total_expected_per * total_travellers

        outstanding = max(total_expected_all - amount_received, 0)
        available_balance = amount_received - expenses

        # Count statuses
        paid_count = partial_count = pending_count = 0
        for t in travellers:
            t_paid = sum_approved_payments_by_traveller(db, trip_id, t.traveller_id)
            if total_expected_per > 0 and t_paid >= total_expected_per:
                paid_count += 1
            elif t_paid > 0:
                partial_count += 1
            else:
                pending_count += 1

        return PaymentDashboard(
            financial_model=financial_model,
            total_budget=trip.budget,
            amount_received=amount_received,
            outstanding_amount=outstanding,
            expenses=expenses,
            available_balance=available_balance,
            paid_count=paid_count,
            partial_count=partial_count,
            pending_count=pending_count,
            total_travellers=total_travellers,
        )
    else:
        # SPONSORED
        sponsor_commitment = config.sponsor_commitment if config else 0
        sponsor_received = sum_sponsor_payments(db, trip_id)
        sponsor_outstanding = max((sponsor_commitment or 0) - sponsor_received, 0)
        available_balance = amount_received - expenses

        return PaymentDashboard(
            financial_model=financial_model,
            total_budget=trip.budget,
            amount_received=amount_received,
            outstanding_amount=sponsor_outstanding,
            expenses=expenses,
            available_balance=available_balance,
            sponsor_name=config.sponsor_name if config else None,
            sponsor_commitment=sponsor_commitment or 0,
            sponsor_received=sponsor_received,
            sponsor_outstanding=sponsor_outstanding,
        )
