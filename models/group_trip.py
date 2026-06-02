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
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    traveller_count = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    travellers = relationship("TravellerTable", back_populates="trip", cascade="all, delete-orphan")


class TravellerTable(Base):
    __tablename__ = "travellers"

    traveller_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    department = Column(String, nullable=True)
    city = Column(String, nullable=True)

    trip = relationship("TripTable", back_populates="travellers")


# --------------- Pydantic Request / Response Models ---------------

# --- Trip ---

class TripCreateRequest(BaseModel):
    trip_name: str
    organization_name: str
    destination: str
    start_date: date
    end_date: date
    days: int = Field(gt=0)
    traveller_count: int = Field(gt=0)
    budget: float = Field(gt=0)


class TripResponse(BaseModel):
    trip_id: str
    trip_name: str
    organization_name: str
    destination: str
    start_date: date
    end_date: date
    days: int
    traveller_count: int
    budget: float
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

    class Config:
        from_attributes = True


# --- CSV Upload ---

class CSVUploadResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: Optional[List[str]] = None


# --- Dashboard Summary ---

class TripSummaryResponse(BaseModel):
    trip_name: str
    destination: str
    traveller_count: int
    budget: float
    registered_travellers: int
    pending_travellers: int
