import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# --------------- SQLAlchemy ORM Models ---------------

class TripTable(Base):
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True, index=True)
    trip_name = Column(String, nullable=False)
    organization_name = Column(String, nullable=False)
    organization_id = Column(String, nullable=True, index=True)
    origin_city = Column(String, nullable=True)
    origin_state = Column(String, nullable=True)
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    traveller_count = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    financial_model = Column(String, nullable=False, default="SPONSORED")
    status = Column(String, nullable=False, default="DRAFT", index=True)
    created_at = Column(DateTime, server_default=func.now())

    travellers = relationship("TravellerTable", back_populates="trip", cascade="all, delete-orphan")


class TravellerTable(Base):
    __tablename__ = "travellers"

    traveller_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    gender = Column(String, nullable=True)
    department = Column(String, nullable=True)
    city = Column(String, nullable=True)

    # Phase 4: Profile fields
    date_of_birth = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_relationship = Column(String, nullable=True)
    medical_conditions = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    special_requirements = Column(String, nullable=True)
    dietary_preferences = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    participation_status = Column(String, nullable=True, default="ACTIVE", index=True)
    membership_status = Column(String, nullable=True, default="ACTIVE", index=True)
    membership_updated_at = Column(DateTime, nullable=True)
    membership_updated_by = Column(String, nullable=True)
    opt_out_reason = Column(String, nullable=True)

    trip = relationship("TripTable", back_populates="travellers")
    consents = relationship("ConsentTable", back_populates="traveller", cascade="all, delete-orphan")


class MembershipAuditTable(Base):
    __tablename__ = "membership_audit"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    traveller_id = Column(String, ForeignKey("travellers.traveller_id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(String, nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now())


# --------------- Pydantic Request / Response Models ---------------

# --- Trip ---

class FinancialModel(str):
    SPONSORED = "SPONSORED"
    FIXED_PACKAGE = "FIXED_PACKAGE"
    SHARED_COST = "SHARED_COST"


class TripCreateRequest(BaseModel):
    trip_name: str
    organization_name: str
    origin_city: str = ""
    origin_state: Optional[str] = None
    destination: str
    start_date: date
    end_date: date
    days: int = Field(gt=0)
    traveller_count: int = Field(gt=0)
    budget: float = Field(gt=0)
    financial_model: str = "SPONSORED"


class TripUpdateRequest(BaseModel):
    trip_name: Optional[str] = None
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: Optional[int] = None
    traveller_count: Optional[int] = None
    budget: Optional[float] = None
    financial_model: Optional[str] = None
    status: Optional[str] = None


class TripResponse(BaseModel):
    trip_id: str
    trip_name: str
    organization_name: str
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    destination: str
    start_date: date
    end_date: date
    days: int
    traveller_count: int
    budget: float
    financial_model: str = "SPONSORED"
    status: str = "DRAFT"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Traveller ---

class TravellerCreateRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    gender: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    participation_status: Optional[str] = "ACTIVE"


class TravellerResponse(BaseModel):
    traveller_id: str
    trip_id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    gender: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    participation_status: Optional[str] = None
    membership_status: Optional[str] = None
    opt_out_reason: Optional[str] = None
    membership_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TravellerReadinessSummary(BaseModel):
    profile_completed: bool = False
    consents_completed: bool = False
    documents_completed: bool = False
    trip_ready: bool = False
    missing_items: List[str] = []
    completed_count: int = 0
    total_requirements: int = 0


class TravellerEnrichedResponse(BaseModel):
    traveller_id: str
    trip_id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    gender: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    participation_status: Optional[str] = None
    membership_status: Optional[str] = None
    opt_out_reason: Optional[str] = None
    membership_updated_at: Optional[datetime] = None
    readiness: Optional[TravellerReadinessSummary] = None

    class Config:
        from_attributes = True


class TravellerUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    participation_status: Optional[str] = None
    membership_status: Optional[str] = None


# --- CSV Upload ---

class CSVUploadResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: Optional[List[str]] = None


# --- Dashboard Summary ---

class TripSummaryResponse(BaseModel):
    trip_name: str
    origin_city: Optional[str] = None
    destination: str
    traveller_count: int
    budget: float
    registered_travellers: int
    pending_travellers: int
    rooms_allocated: int = 0
    unallocated_travellers: int = 0
    confirmed_travellers: int = 0
    pending_confirmations: int = 0
    active_travellers: int = 0
    opted_out_travellers: int = 0
    removed_travellers: int = 0
    pending_consents: int = 0
    approved_consents: int = 0
    total_budget: float = 0
    amount_spent: float = 0
    remaining_budget: float = 0
    registration_link_active: bool = False
    trip_ready_percentage: float = 0


# --- Risk Summary ---

class RiskSummaryResponse(BaseModel):
    medical_cases: int
    travellers_with_special_requirements: int
    pending_consents: int
    high_risk_travellers: int
