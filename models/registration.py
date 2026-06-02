import enum
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class InvitationStatus(str, enum.Enum):
    SENT = "SENT"
    OPENED = "OPENED"
    REGISTERED = "REGISTERED"


# --------------- SQLAlchemy ORM Models ---------------

class RegistrationLinkTable(Base):
    __tablename__ = "registration_links"

    registration_link_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    registration_code = Column(String, unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class RegistrationFormConfigTable(Base):
    __tablename__ = "registration_form_configs"

    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), primary_key=True)
    collect_emergency_contact = Column(Boolean, default=False)
    collect_medical_information = Column(Boolean, default=False)
    collect_dietary_preferences = Column(Boolean, default=False)
    collect_passport_details = Column(Boolean, default=False)
    require_consent = Column(Boolean, default=False)
    require_date_of_birth = Column(Boolean, default=False)


class InvitationTable(Base):
    __tablename__ = "invitations"

    invitation_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    invitation_status = Column(String, nullable=False, default="SENT")
    sent_at = Column(DateTime, server_default=func.now())


# --------------- Pydantic Request / Response Models ---------------

# --- Registration Link ---

class RegistrationLinkResponse(BaseModel):
    registration_link_id: str
    trip_id: str
    registration_code: str
    registration_url: str
    active: bool
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class GenerateLinkRequest(BaseModel):
    expires_at: Optional[datetime] = None


# --- Form Config ---

class FormConfigRequest(BaseModel):
    collect_emergency_contact: bool = False
    collect_medical_information: bool = False
    collect_dietary_preferences: bool = False
    collect_passport_details: bool = False
    require_consent: bool = False
    require_date_of_birth: bool = False


class FormConfigResponse(BaseModel):
    trip_id: str
    collect_emergency_contact: bool
    collect_medical_information: bool
    collect_dietary_preferences: bool
    collect_passport_details: bool
    require_consent: bool
    require_date_of_birth: bool

    class Config:
        from_attributes = True


# --- Public Registration ---

class PublicTripInfoResponse(BaseModel):
    trip_name: str
    destination: str
    start_date: date
    end_date: date
    days: int
    required_fields: List[str]


class SelfRegisterRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    gender: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None


# --- Invitation ---

class InvitationCreateRequest(BaseModel):
    recipient_name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class InvitationResponse(BaseModel):
    invitation_id: str
    trip_id: str
    recipient_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    invitation_status: str
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Registration Dashboard ---

class RegistrationSummaryResponse(BaseModel):
    total_registered: int
    pending_registrations: int
    registration_completion_percentage: float
