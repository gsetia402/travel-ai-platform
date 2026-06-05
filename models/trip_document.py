"""Models for Trip Documents (coordinator-shared documents like vouchers, tickets, guides)."""
import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class TripDocumentType(str, enum.Enum):
    HOTEL_VOUCHER = "HOTEL_VOUCHER"
    FLIGHT_ITINERARY = "FLIGHT_ITINERARY"
    BOARDING_PASS = "BOARDING_PASS"
    BUS_TICKET = "BUS_TICKET"
    TRAIN_TICKET = "TRAIN_TICKET"
    EVENT_TICKET = "EVENT_TICKET"
    TRIP_GUIDE = "TRIP_GUIDE"
    PACKING_GUIDE = "PACKING_GUIDE"
    EMERGENCY_CONTACTS = "EMERGENCY_CONTACTS"
    TRAVEL_INSURANCE = "TRAVEL_INSURANCE"
    OTHER = "OTHER"


class TripDocumentVisibility(str, enum.Enum):
    ALL_TRAVELLERS = "ALL_TRAVELLERS"
    SELECTED_TRAVELLERS = "SELECTED_TRAVELLERS"


# --------------- SQLAlchemy ORM ---------------

class TripDocumentTable(Base):
    __tablename__ = "trip_documents"

    document_id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, nullable=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    document_type = Column(String, nullable=False, index=True)

    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)

    storage_provider = Column(String, nullable=False, default="local")
    storage_key = Column(String, nullable=False)

    visibility = Column(String, nullable=False, default=TripDocumentVisibility.ALL_TRAVELLERS.value)

    uploaded_by = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# --------------- Pydantic Schemas ---------------

class TripDocumentUploadResponse(BaseModel):
    document_id: str
    trip_id: str
    title: str
    description: Optional[str] = None
    document_type: str
    file_name: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_provider: str
    visibility: str
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TripDocumentListResponse(BaseModel):
    document_id: str
    trip_id: str
    title: str
    description: Optional[str] = None
    document_type: str
    file_name: str
    file_size: Optional[int] = None
    visibility: str
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
