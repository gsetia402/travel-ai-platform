import uuid
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from models.communication import CommunicationTable, CommunicationRecipientTable, ReadStatus

logger = logging.getLogger(__name__)


def create_communication(db: Session, trip_id: str, title: str, message: str, audience_type: str, created_by: Optional[str] = None) -> CommunicationTable:
    comm = CommunicationTable(
        communication_id=str(uuid.uuid4()),
        trip_id=trip_id,
        title=title,
        message=message,
        audience_type=audience_type,
        created_by=created_by,
    )
    db.add(comm)
    db.flush()
    logger.info(f"Created communication {comm.communication_id} for trip {trip_id}")
    return comm


def add_recipients_bulk(db: Session, communication_id: str, traveller_ids: List[str]) -> int:
    records = []
    for tid in traveller_ids:
        records.append(CommunicationRecipientTable(
            recipient_id=str(uuid.uuid4()),
            communication_id=communication_id,
            traveller_id=tid,
            read_status=ReadStatus.UNREAD.value,
        ))
    db.add_all(records)
    return len(records)


def get_communication_by_id(db: Session, communication_id: str) -> Optional[CommunicationTable]:
    return db.query(CommunicationTable).filter(CommunicationTable.communication_id == communication_id).first()


def get_communications_by_trip(db: Session, trip_id: str) -> List[CommunicationTable]:
    return (
        db.query(CommunicationTable)
        .filter(CommunicationTable.trip_id == trip_id)
        .order_by(CommunicationTable.created_at.desc())
        .all()
    )


def get_recipients_by_communication(db: Session, communication_id: str) -> List[CommunicationRecipientTable]:
    return (
        db.query(CommunicationRecipientTable)
        .filter(CommunicationRecipientTable.communication_id == communication_id)
        .all()
    )


def get_inbox_for_traveller(db: Session, traveller_id: str) -> List[dict]:
    rows = (
        db.query(CommunicationTable, CommunicationRecipientTable)
        .join(CommunicationRecipientTable, CommunicationTable.communication_id == CommunicationRecipientTable.communication_id)
        .filter(CommunicationRecipientTable.traveller_id == traveller_id)
        .order_by(CommunicationTable.created_at.desc())
        .all()
    )
    results = []
    for comm, recip in rows:
        results.append({
            "communication_id": comm.communication_id,
            "title": comm.title,
            "message": comm.message,
            "audience_type": comm.audience_type,
            "created_by": comm.created_by,
            "created_at": comm.created_at,
            "read_status": recip.read_status,
            "read_at": recip.read_at,
        })
    return results


def mark_as_read(db: Session, communication_id: str, traveller_id: str) -> Optional[CommunicationRecipientTable]:
    recip = (
        db.query(CommunicationRecipientTable)
        .filter(
            CommunicationRecipientTable.communication_id == communication_id,
            CommunicationRecipientTable.traveller_id == traveller_id,
        )
        .first()
    )
    if not recip:
        return None
    recip.read_status = ReadStatus.READ.value
    recip.read_at = datetime.utcnow()
    db.commit()
    db.refresh(recip)
    return recip


def count_recipients_by_trip(db: Session, trip_id: str) -> int:
    return (
        db.query(CommunicationRecipientTable)
        .join(CommunicationTable, CommunicationRecipientTable.communication_id == CommunicationTable.communication_id)
        .filter(CommunicationTable.trip_id == trip_id)
        .count()
    )


def count_recipients_by_trip_and_status(db: Session, trip_id: str, status: str) -> int:
    return (
        db.query(CommunicationRecipientTable)
        .join(CommunicationTable, CommunicationRecipientTable.communication_id == CommunicationTable.communication_id)
        .filter(CommunicationTable.trip_id == trip_id, CommunicationRecipientTable.read_status == status)
        .count()
    )


def count_communications_by_trip(db: Session, trip_id: str) -> int:
    return db.query(CommunicationTable).filter(CommunicationTable.trip_id == trip_id).count()


def count_recipient_stats(db: Session, communication_id: str) -> dict:
    total = db.query(CommunicationRecipientTable).filter(CommunicationRecipientTable.communication_id == communication_id).count()
    read = db.query(CommunicationRecipientTable).filter(
        CommunicationRecipientTable.communication_id == communication_id,
        CommunicationRecipientTable.read_status == ReadStatus.READ.value,
    ).count()
    return {"total": total, "read": read, "unread": total - read}
