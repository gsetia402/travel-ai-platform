import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class DocumentType(str, enum.Enum):
    PASSPORT = "PASSPORT"
    VISA = "VISA"
    GOVERNMENT_ID = "GOVERNMENT_ID"
    ID_PROOF = "ID_PROOF"
    STUDENT_ID = "STUDENT_ID"
    INSURANCE = "INSURANCE"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    VACCINATION = "VACCINATION"
    CONSENT_FORM = "CONSENT_FORM"
    FLIGHT_TICKET = "FLIGHT_TICKET"
    TRAVEL_PERMIT = "TRAVEL_PERMIT"
    OTHER = "OTHER"


class VerificationStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    REJECTED = "REJECTED"
    # Legacy aliases kept for backward compat
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"


# --------------- SQLAlchemy ORM Models ---------------

class TravellerDocumentTable(Base):
    __tablename__ = "traveller_documents"

    document_id = Column(String, primary_key=True, index=True)
    traveller_id = Column(String, ForeignKey("travellers.traveller_id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_status = Column(String, nullable=False, default="COMPLETED")
    verification_status = Column(String, nullable=False, default="UPLOADED")
    uploaded_at = Column(DateTime, server_default=func.now())
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)
    remarks = Column(String, nullable=True)


class TripDocumentRequirementTable(Base):
    __tablename__ = "trip_document_requirements"

    requirement_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String, nullable=False)
    mandatory = Column(Boolean, default=True, nullable=False)


# --------------- Pydantic Request / Response Models ---------------

class DocumentUploadResponse(BaseModel):
    document_id: str
    traveller_id: str
    document_type: str
    file_name: str
    file_path: str
    upload_status: str
    verification_status: str
    uploaded_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class VerifyRequest(BaseModel):
    verified_by: Optional[str] = None
    remarks: Optional[str] = None


class RequirementCreateRequest(BaseModel):
    document_type: DocumentType
    mandatory: bool = True


class RequirementResponse(BaseModel):
    requirement_id: str
    trip_id: str
    document_type: str
    mandatory: bool

    class Config:
        from_attributes = True


class DocumentSummaryResponse(BaseModel):
    required_documents: int
    uploaded_documents: int
    verified_documents: int
    pending_documents: int = 0
    rejected_documents: int = 0
    missing_documents: int


class TravellerReadinessResponse(BaseModel):
    profile_completed: bool
    consents_completed: bool
    documents_completed: bool
    trip_ready: bool
    missing_items: List[str] = []
    completed_count: int = 0
    total_requirements: int = 0


class DocumentTypeStats(BaseModel):
    document_type: str
    mandatory: bool
    uploaded_count: int
    missing_count: int
    total_travellers: int


class TripDocumentStatsResponse(BaseModel):
    total_travellers: int
    document_types: List[DocumentTypeStats]
