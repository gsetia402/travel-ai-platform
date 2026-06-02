import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class ConsentType(str, enum.Enum):
    PARENTAL_CONSENT = "PARENTAL_CONSENT"
    MEDICAL_CONSENT = "MEDICAL_CONSENT"
    LIABILITY_WAIVER = "LIABILITY_WAIVER"
    CORPORATE_APPROVAL = "CORPORATE_APPROVAL"
    TRAVEL_CONFIRMATION = "TRAVEL_CONFIRMATION"


class ConsentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# --------------- SQLAlchemy ORM Model ---------------

class ConsentTable(Base):
    __tablename__ = "consents"

    consent_id = Column(String, primary_key=True, index=True)
    traveller_id = Column(String, ForeignKey("travellers.traveller_id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    signed_by = Column(String, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    traveller = relationship("TravellerTable", back_populates="consents")


# --------------- Pydantic Request / Response Models ---------------

class ConsentCreateRequest(BaseModel):
    consent_type: ConsentType
    signed_by: Optional[str] = None
    notes: Optional[str] = None


class ConsentResponse(BaseModel):
    consent_id: str
    traveller_id: str
    consent_type: str
    status: str
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
