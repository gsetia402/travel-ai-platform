"""Phase 17 — Traveller Directory & Groups models."""
import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from database import Base


# --------------- SQLAlchemy ORM Models ---------------

class TravellerMasterTable(Base):
    """Organization-level master traveller record. One per person, reused across trips."""
    __tablename__ = "traveller_master"

    master_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    city = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_relationship = Column(String, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)
    dietary_preferences = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TravellerGroupTable(Base):
    """Reusable group (e.g. Class 7A, Cricket Team)."""
    __tablename__ = "traveller_groups"

    group_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GroupMemberTable(Base):
    """Many-to-many: traveller_master <-> traveller_groups."""
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey("traveller_groups.group_id", ondelete="CASCADE"), nullable=False, index=True)
    master_id = Column(String, ForeignKey("traveller_master.master_id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(DateTime, server_default=func.now())


class TripTravellerTable(Base):
    """Many-to-many: traveller_master <-> trips. Maps master records to trips."""
    __tablename__ = "trip_travellers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    master_id = Column(String, ForeignKey("traveller_master.master_id", ondelete="CASCADE"), nullable=False, index=True)
    added_via = Column(String, nullable=True)  # 'group:{group_id}', 'manual', 'csv'
    added_at = Column(DateTime, server_default=func.now())


# --------------- Pydantic Schemas ---------------

# --- Traveller Master ---

class TravellerMasterCreate(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None


class TravellerMasterUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None


class TravellerMasterResponse(BaseModel):
    master_id: str
    organization_id: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None
    passport_number: Optional[str] = None
    created_at: Optional[datetime] = None
    groups: List[str] = []  # group names

    class Config:
        from_attributes = True


# --- Group ---

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupResponse(BaseModel):
    group_id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    member_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GroupDetailResponse(GroupResponse):
    members: List[TravellerMasterResponse] = []


# --- Trip Traveller ---

class TripTravellerResponse(BaseModel):
    id: str
    trip_id: str
    master_id: str
    added_via: Optional[str] = None
    added_at: Optional[datetime] = None
    traveller: Optional[TravellerMasterResponse] = None

    class Config:
        from_attributes = True
