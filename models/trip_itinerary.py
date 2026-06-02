from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


# --------------- SQLAlchemy ORM ---------------

class TripItineraryTable(Base):
    __tablename__ = "trip_itineraries"

    id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    itinerary_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# --------------- Pydantic Schemas ---------------

class Activity(BaseModel):
    time_of_day: str  # Morning, Afternoon, Evening
    activity: str
    description: Optional[str] = None

class DayItinerary(BaseModel):
    day: int
    title: Optional[str] = None
    activities: List[Activity]

class TripItineraryRequest(BaseModel):
    days: List[DayItinerary]

class TripItineraryResponse(BaseModel):
    trip_id: str
    days: List[DayItinerary]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
