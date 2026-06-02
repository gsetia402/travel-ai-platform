import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class AudienceType(str, enum.Enum):
    ALL_TRAVELLERS = "ALL_TRAVELLERS"
    ROOM = "ROOM"
    INDIVIDUAL = "INDIVIDUAL"
    PENDING_CONSENTS = "PENDING_CONSENTS"
    UNALLOCATED_TRAVELLERS = "UNALLOCATED_TRAVELLERS"


class ReadStatus(str, enum.Enum):
    UNREAD = "UNREAD"
    READ = "READ"


# --------------- SQLAlchemy ORM Models ---------------

class CommunicationTable(Base):
    __tablename__ = "communications"

    communication_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    audience_type = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    recipients = relationship("CommunicationRecipientTable", back_populates="communication", cascade="all, delete-orphan")


class CommunicationRecipientTable(Base):
    __tablename__ = "communication_recipients"

    recipient_id = Column(String, primary_key=True, index=True)
    communication_id = Column(String, ForeignKey("communications.communication_id", ondelete="CASCADE"), nullable=False, index=True)
    traveller_id = Column(String, ForeignKey("travellers.traveller_id", ondelete="CASCADE"), nullable=False, index=True)
    read_status = Column(String, nullable=False, default="UNREAD")
    read_at = Column(DateTime, nullable=True)

    communication = relationship("CommunicationTable", back_populates="recipients")


# --------------- Pydantic Request / Response Models ---------------

class CommunicationCreateRequest(BaseModel):
    title: str
    message: str
    audience_type: AudienceType
    room_id: Optional[str] = None
    traveller_id: Optional[str] = None
    created_by: Optional[str] = None


class RecipientInfo(BaseModel):
    recipient_id: str
    traveller_id: str
    traveller_name: Optional[str] = None
    read_status: str
    read_at: Optional[datetime] = None


class CommunicationResponse(BaseModel):
    communication_id: str
    trip_id: str
    title: str
    message: str
    audience_type: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    recipient_count: int = 0

    class Config:
        from_attributes = True


class CommunicationDetailResponse(BaseModel):
    communication_id: str
    trip_id: str
    title: str
    message: str
    audience_type: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    recipients: List[RecipientInfo] = []
    total_recipients: int = 0
    read_count: int = 0
    unread_count: int = 0


class InboxMessageResponse(BaseModel):
    communication_id: str
    title: str
    message: str
    audience_type: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    read_status: str
    read_at: Optional[datetime] = None


class CommunicationSummaryResponse(BaseModel):
    total_messages: int
    total_recipients: int
    read_count: int
    unread_count: int
    read_percentage: float
