"""Models for Traveller Portal authentication and visibility settings."""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func

from database import Base


# --------------- SQLAlchemy ORM: Trip Visibility Settings ---------------

class TripVisibilityTable(Base):
    __tablename__ = "trip_visibility_settings"

    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), primary_key=True)
    show_itinerary = Column(Boolean, nullable=False, default=True)
    show_room_details = Column(Boolean, nullable=False, default=True)
    show_communications = Column(Boolean, nullable=False, default=True)
    show_traveller_directory = Column(Boolean, nullable=False, default=False)
    show_budget = Column(Boolean, nullable=False, default=False)
    show_expenses = Column(Boolean, nullable=False, default=False)


# --------------- Pydantic Schemas ---------------

class TravellerLoginRequest(BaseModel):
    phone: str
    date_of_birth: str  # YYYY-MM-DD


class TravellerTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    traveller_id: str
    trip_id: str
    name: str


class TravellerMeResponse(BaseModel):
    traveller_id: str
    trip_id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    department: Optional[str] = None
    city: Optional[str] = None
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


class TravellerProfileUpdateRequest(BaseModel):
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_relationship: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    dietary_preferences: Optional[str] = None


class TravellerTripResponse(BaseModel):
    trip_id: str
    trip_name: str
    organization_name: str
    origin_city: Optional[str] = None
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days: int
    status: str


class TravellerRoomResponse(BaseModel):
    room_id: Optional[str] = None
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    occupants: List[dict] = []


class VisibilitySettingsRequest(BaseModel):
    show_itinerary: Optional[bool] = None
    show_room_details: Optional[bool] = None
    show_communications: Optional[bool] = None
    show_traveller_directory: Optional[bool] = None
    show_budget: Optional[bool] = None
    show_expenses: Optional[bool] = None


class VisibilitySettingsResponse(BaseModel):
    trip_id: str
    show_itinerary: bool = True
    show_room_details: bool = True
    show_communications: bool = True
    show_traveller_directory: bool = False
    show_budget: bool = False
    show_expenses: bool = False

    class Config:
        from_attributes = True
