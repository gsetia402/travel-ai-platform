import uuid
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from models.document import (
    TravellerDocumentTable,
    TripDocumentRequirementTable,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


# --- Document CRUD ---

def create_document(db: Session, traveller_id: str, document_type: str, file_name: str, file_path: str) -> TravellerDocumentTable:
    doc = TravellerDocumentTable(
        document_id=str(uuid.uuid4()),
        traveller_id=traveller_id,
        document_type=document_type,
        file_name=file_name,
        file_path=file_path,
        upload_status="COMPLETED",
        verification_status=VerificationStatus.PENDING.value,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info(f"Uploaded document {doc.document_id} for traveller {traveller_id}")
    return doc


def get_document_by_id(db: Session, document_id: str) -> Optional[TravellerDocumentTable]:
    return db.query(TravellerDocumentTable).filter(TravellerDocumentTable.document_id == document_id).first()


def get_documents_by_traveller(db: Session, traveller_id: str) -> List[TravellerDocumentTable]:
    return (
        db.query(TravellerDocumentTable)
        .filter(TravellerDocumentTable.traveller_id == traveller_id)
        .order_by(TravellerDocumentTable.uploaded_at.desc())
        .all()
    )


def verify_document(db: Session, document_id: str, verified_by: str = None, remarks: str = None) -> Optional[TravellerDocumentTable]:
    doc = get_document_by_id(db, document_id)
    if not doc:
        return None
    doc.verification_status = VerificationStatus.VERIFIED.value
    doc.verified_at = datetime.utcnow()
    doc.verified_by = verified_by
    doc.remarks = remarks
    db.commit()
    db.refresh(doc)
    return doc


def reject_document(db: Session, document_id: str, verified_by: str = None, remarks: str = None) -> Optional[TravellerDocumentTable]:
    doc = get_document_by_id(db, document_id)
    if not doc:
        return None
    doc.verification_status = VerificationStatus.REJECTED.value
    doc.verified_at = datetime.utcnow()
    doc.verified_by = verified_by
    doc.remarks = remarks
    db.commit()
    db.refresh(doc)
    return doc


# --- Requirements ---

def add_requirement(db: Session, trip_id: str, document_type: str, mandatory: bool = True) -> TripDocumentRequirementTable:
    req = TripDocumentRequirementTable(
        requirement_id=str(uuid.uuid4()),
        trip_id=trip_id,
        document_type=document_type,
        mandatory=mandatory,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_requirements_by_trip(db: Session, trip_id: str) -> List[TripDocumentRequirementTable]:
    return db.query(TripDocumentRequirementTable).filter(TripDocumentRequirementTable.trip_id == trip_id).all()


# --- Aggregation ---

def count_documents_by_traveller_and_type(db: Session, traveller_id: str, document_type: str) -> int:
    return (
        db.query(TravellerDocumentTable)
        .filter(
            TravellerDocumentTable.traveller_id == traveller_id,
            TravellerDocumentTable.document_type == document_type,
        )
        .count()
    )


def count_uploaded_by_trip(db: Session, trip_id: str) -> int:
    from models.group_trip import TravellerTable
    return (
        db.query(TravellerDocumentTable)
        .join(TravellerTable, TravellerDocumentTable.traveller_id == TravellerTable.traveller_id)
        .filter(TravellerTable.trip_id == trip_id)
        .count()
    )


def count_verified_by_trip(db: Session, trip_id: str) -> int:
    from models.group_trip import TravellerTable
    return (
        db.query(TravellerDocumentTable)
        .join(TravellerTable, TravellerDocumentTable.traveller_id == TravellerTable.traveller_id)
        .filter(TravellerTable.trip_id == trip_id, TravellerDocumentTable.verification_status == VerificationStatus.VERIFIED.value)
        .count()
    )


def count_pending_by_trip(db: Session, trip_id: str) -> int:
    from models.group_trip import TravellerTable
    return (
        db.query(TravellerDocumentTable)
        .join(TravellerTable, TravellerDocumentTable.traveller_id == TravellerTable.traveller_id)
        .filter(TravellerTable.trip_id == trip_id, TravellerDocumentTable.verification_status == VerificationStatus.PENDING.value)
        .count()
    )


def get_uploaded_types_for_traveller(db: Session, traveller_id: str) -> List[str]:
    rows = (
        db.query(TravellerDocumentTable.document_type)
        .filter(TravellerDocumentTable.traveller_id == traveller_id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]
