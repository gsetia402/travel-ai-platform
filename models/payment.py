"""Payment models for tracking traveller and sponsor payments."""
import uuid
from datetime import date, datetime
from typing import Optional, List, Dict
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class PaymentType(str, Enum):
    TRAVELLER_PAYMENT = "TRAVELLER_PAYMENT"
    SPONSOR_PAYMENT = "SPONSOR_PAYMENT"
    REGISTRATION_FEE = "REGISTRATION_FEE"


class PaymentStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TravellerPaymentStatus(str, Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"


# --------------- ORM Tables ---------------

class PaymentTable(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    traveller_id = Column(String, ForeignKey("travellers.traveller_id", ondelete="CASCADE"), nullable=True, index=True)
    payment_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)
    proof_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default="APPROVED")
    rejected_reason = Column(String, nullable=True)
    sponsor_name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class TripPaymentConfigTable(Base):
    __tablename__ = "trip_payment_config"

    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), primary_key=True)
    expected_amount_per_traveller = Column(Float, nullable=True, default=0)
    registration_fee_enabled = Column(Boolean, nullable=False, default=False)
    registration_fee_amount = Column(Float, nullable=True, default=0)
    sponsor_name = Column(String, nullable=True)
    sponsor_commitment = Column(Float, nullable=True, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# --------------- Pydantic Request / Response Models ---------------

class PaymentCreateRequest(BaseModel):
    traveller_id: Optional[str] = None
    payment_type: PaymentType = PaymentType.TRAVELLER_PAYMENT
    amount: float = Field(gt=0)
    payment_date: Optional[date] = None
    notes: Optional[str] = None
    sponsor_name: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: str
    trip_id: str
    traveller_id: Optional[str] = None
    payment_type: str
    amount: float
    payment_date: Optional[date] = None
    notes: Optional[str] = None
    proof_path: Optional[str] = None
    status: str = "APPROVED"
    rejected_reason: Optional[str] = None
    sponsor_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentConfigRequest(BaseModel):
    expected_amount_per_traveller: Optional[float] = None
    registration_fee_enabled: Optional[bool] = None
    registration_fee_amount: Optional[float] = None
    sponsor_name: Optional[str] = None
    sponsor_commitment: Optional[float] = None


class PaymentConfigResponse(BaseModel):
    trip_id: str
    expected_amount_per_traveller: float = 0
    registration_fee_enabled: bool = False
    registration_fee_amount: float = 0
    sponsor_name: Optional[str] = None
    sponsor_commitment: float = 0

    class Config:
        from_attributes = True


class TravellerPaymentSummary(BaseModel):
    traveller_id: str
    traveller_name: str
    expected_amount: float
    amount_paid: float
    outstanding_amount: float
    payment_status: str
    registration_fee_paid: bool = False


class PaymentDashboard(BaseModel):
    financial_model: str
    total_budget: float
    amount_received: float
    outstanding_amount: float
    expenses: float
    available_balance: float
    paid_count: int = 0
    partial_count: int = 0
    pending_count: int = 0
    total_travellers: int = 0
    sponsor_name: Optional[str] = None
    sponsor_commitment: float = 0
    sponsor_received: float = 0
    sponsor_outstanding: float = 0
