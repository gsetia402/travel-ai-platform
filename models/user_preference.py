from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from database import Base


# SQLAlchemy ORM model
class UserPreferenceTable(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String, primary_key=True, index=True)
    budget = Column(Integer, nullable=True)
    trip_type = Column(String, nullable=True)
    accommodation = Column(String, nullable=True)
    food_preference = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# Pydantic models
class UserPreferenceRequest(BaseModel):
    user_id: str
    budget: Optional[int] = None
    trip_type: Optional[str] = None
    accommodation: Optional[str] = None
    food_preference: Optional[str] = None


class UserPreferenceResponse(BaseModel):
    user_id: str
    budget: Optional[int] = None
    trip_type: Optional[str] = None
    accommodation: Optional[str] = None
    food_preference: Optional[str] = None

    class Config:
        from_attributes = True


class MemorySaveResponse(BaseModel):
    message: str
