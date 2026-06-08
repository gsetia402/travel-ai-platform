"""Repository functions for payment tracking."""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.payment import PaymentTable, TripPaymentConfigTable


# --------------- Payments ---------------

def create_payment(db: Session, trip_id: str, traveller_id: Optional[str], payment_type: str,
                   amount: float, payment_date=None, notes: str = None, sponsor_name: str = None) -> PaymentTable:
    payment = PaymentTable(
        payment_id=str(uuid.uuid4()),
        trip_id=trip_id,
        traveller_id=traveller_id,
        payment_type=payment_type,
        amount=amount,
        payment_date=payment_date,
        notes=notes,
        sponsor_name=sponsor_name,
        status="APPROVED",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment_by_id(db: Session, payment_id: str) -> Optional[PaymentTable]:
    return db.query(PaymentTable).filter(PaymentTable.payment_id == payment_id).first()


def get_payments_by_trip(db: Session, trip_id: str) -> List[PaymentTable]:
    return db.query(PaymentTable).filter(PaymentTable.trip_id == trip_id).order_by(PaymentTable.created_at.desc()).all()


def get_payments_by_traveller(db: Session, trip_id: str, traveller_id: str) -> List[PaymentTable]:
    return db.query(PaymentTable).filter(
        PaymentTable.trip_id == trip_id,
        PaymentTable.traveller_id == traveller_id,
    ).order_by(PaymentTable.created_at.desc()).all()


def get_approved_payments_by_trip(db: Session, trip_id: str) -> List[PaymentTable]:
    return db.query(PaymentTable).filter(
        PaymentTable.trip_id == trip_id,
        PaymentTable.status == "APPROVED",
    ).all()


def sum_approved_payments_by_trip(db: Session, trip_id: str) -> float:
    result = db.query(func.coalesce(func.sum(PaymentTable.amount), 0)).filter(
        PaymentTable.trip_id == trip_id,
        PaymentTable.status == "APPROVED",
    ).scalar()
    return float(result)


def sum_approved_payments_by_traveller(db: Session, trip_id: str, traveller_id: str) -> float:
    result = db.query(func.coalesce(func.sum(PaymentTable.amount), 0)).filter(
        PaymentTable.trip_id == trip_id,
        PaymentTable.traveller_id == traveller_id,
        PaymentTable.status == "APPROVED",
    ).scalar()
    return float(result)


def sum_sponsor_payments(db: Session, trip_id: str) -> float:
    result = db.query(func.coalesce(func.sum(PaymentTable.amount), 0)).filter(
        PaymentTable.trip_id == trip_id,
        PaymentTable.payment_type == "SPONSOR_PAYMENT",
        PaymentTable.status == "APPROVED",
    ).scalar()
    return float(result)


def reject_payment(db: Session, payment_id: str, reason: str = None) -> Optional[PaymentTable]:
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        return None
    payment.status = "REJECTED"
    payment.rejected_reason = reason
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, payment_id: str) -> bool:
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        return False
    db.delete(payment)
    db.commit()
    return True


# --------------- Payment Config ---------------

def get_payment_config(db: Session, trip_id: str) -> Optional[TripPaymentConfigTable]:
    return db.query(TripPaymentConfigTable).filter(TripPaymentConfigTable.trip_id == trip_id).first()


def upsert_payment_config(db: Session, trip_id: str, **kwargs) -> TripPaymentConfigTable:
    config = get_payment_config(db, trip_id)
    if config:
        for key, value in kwargs.items():
            if value is not None:
                setattr(config, key, value)
    else:
        config = TripPaymentConfigTable(trip_id=trip_id, **{k: v for k, v in kwargs.items() if v is not None})
        db.add(config)
    db.commit()
    db.refresh(config)
    return config
