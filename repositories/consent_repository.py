import uuid
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from models.consent import ConsentTable, ConsentStatus

logger = logging.getLogger(__name__)


def create_consent(db: Session, traveller_id: str, consent_type: str, signed_by: Optional[str] = None, notes: Optional[str] = None) -> ConsentTable:
    consent = ConsentTable(
        consent_id=str(uuid.uuid4()),
        traveller_id=traveller_id,
        consent_type=consent_type,
        status=ConsentStatus.PENDING.value,
        signed_by=signed_by,
        notes=notes,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    logger.info(f"Created consent {consent.consent_id} for traveller {traveller_id}")
    return consent


def get_consent_by_id(db: Session, consent_id: str) -> Optional[ConsentTable]:
    return db.query(ConsentTable).filter(ConsentTable.consent_id == consent_id).first()


def get_consents_by_traveller(db: Session, traveller_id: str) -> List[ConsentTable]:
    return db.query(ConsentTable).filter(ConsentTable.traveller_id == traveller_id).order_by(ConsentTable.created_at.desc()).all()


def update_consent_status(db: Session, consent_id: str, status: ConsentStatus) -> Optional[ConsentTable]:
    consent = get_consent_by_id(db, consent_id)
    if not consent:
        return None
    consent.status = status.value
    if status == ConsentStatus.APPROVED:
        consent.signed_at = datetime.utcnow()
    db.commit()
    db.refresh(consent)
    logger.info(f"Updated consent {consent_id} to {status.value}")
    return consent


def count_consents_by_trip_and_status(db: Session, trip_id: str, status: str) -> int:
    from models.group_trip import TravellerTable
    return (
        db.query(ConsentTable)
        .join(TravellerTable, ConsentTable.traveller_id == TravellerTable.traveller_id)
        .filter(TravellerTable.trip_id == trip_id, ConsentTable.status == status)
        .count()
    )


def count_consents_by_trip(db: Session, trip_id: str) -> int:
    from models.group_trip import TravellerTable
    return (
        db.query(ConsentTable)
        .join(TravellerTable, ConsentTable.traveller_id == TravellerTable.traveller_id)
        .filter(TravellerTable.trip_id == trip_id)
        .count()
    )
