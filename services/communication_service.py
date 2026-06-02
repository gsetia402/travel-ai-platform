import logging
from typing import List

from sqlalchemy.orm import Session

from models.communication import (
    AudienceType,
    CommunicationCreateRequest,
    CommunicationResponse,
    CommunicationDetailResponse,
    RecipientInfo,
    InboxMessageResponse,
    CommunicationSummaryResponse,
)
from models.group_trip import TravellerTable
from models.communication import CommunicationRecipientTable, ReadStatus
from models.consent import ConsentTable
from models.room import RoomAllocationTable
from repositories.communication_repository import (
    create_communication,
    add_recipients_bulk,
    get_communication_by_id,
    get_communications_by_trip,
    get_recipients_by_communication,
    get_inbox_for_traveller,
    mark_as_read,
    count_communications_by_trip,
    count_recipients_by_trip,
    count_recipients_by_trip_and_status,
    count_recipient_stats,
)
from repositories.trip_repository import get_trip_by_id
from repositories.traveller_repository import get_traveller_by_id

logger = logging.getLogger(__name__)


def _resolve_audience(db: Session, trip_id: str, request: CommunicationCreateRequest) -> List[str]:
    audience = request.audience_type

    if audience == AudienceType.ALL_TRAVELLERS:
        travellers = db.query(TravellerTable.traveller_id).filter(TravellerTable.trip_id == trip_id).all()
        return [t[0] for t in travellers]

    elif audience == AudienceType.INDIVIDUAL:
        if not request.traveller_id:
            raise ValueError("traveller_id is required for INDIVIDUAL audience")
        traveller = get_traveller_by_id(db, request.traveller_id)
        if not traveller:
            raise ValueError(f"Traveller not found: {request.traveller_id}")
        return [request.traveller_id]

    elif audience == AudienceType.ROOM:
        if not request.room_id:
            raise ValueError("room_id is required for ROOM audience")
        allocations = (
            db.query(RoomAllocationTable.traveller_id)
            .filter(RoomAllocationTable.room_id == request.room_id)
            .all()
        )
        if not allocations:
            raise ValueError(f"No travellers found in room: {request.room_id}")
        return [a[0] for a in allocations]

    elif audience == AudienceType.PENDING_CONSENTS:
        rows = (
            db.query(ConsentTable.traveller_id)
            .join(TravellerTable, ConsentTable.traveller_id == TravellerTable.traveller_id)
            .filter(TravellerTable.trip_id == trip_id, ConsentTable.status == "PENDING")
            .distinct()
            .all()
        )
        if not rows:
            raise ValueError("No travellers with pending consents found")
        return [r[0] for r in rows]

    elif audience == AudienceType.UNALLOCATED_TRAVELLERS:
        allocated_ids = (
            db.query(RoomAllocationTable.traveller_id)
            .join(TravellerTable, RoomAllocationTable.traveller_id == TravellerTable.traveller_id)
            .filter(TravellerTable.trip_id == trip_id)
            .subquery()
        )
        rows = (
            db.query(TravellerTable.traveller_id)
            .filter(TravellerTable.trip_id == trip_id)
            .filter(~TravellerTable.traveller_id.in_(db.query(allocated_ids.c.traveller_id)))
            .all()
        )
        if not rows:
            raise ValueError("No unallocated travellers found")
        return [r[0] for r in rows]

    raise ValueError(f"Unsupported audience type: {audience}")


def send_communication(db: Session, trip_id: str, request: CommunicationCreateRequest) -> CommunicationResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    traveller_ids = _resolve_audience(db, trip_id, request)

    comm = create_communication(
        db,
        trip_id=trip_id,
        title=request.title,
        message=request.message,
        audience_type=request.audience_type.value,
        created_by=request.created_by,
    )
    count = add_recipients_bulk(db, comm.communication_id, traveller_ids)
    db.commit()
    db.refresh(comm)

    logger.info(f"Sent communication {comm.communication_id} to {count} recipients")

    return CommunicationResponse(
        communication_id=comm.communication_id,
        trip_id=comm.trip_id,
        title=comm.title,
        message=comm.message,
        audience_type=comm.audience_type,
        created_by=comm.created_by,
        created_at=comm.created_at,
        recipient_count=count,
    )


def list_communications(db: Session, trip_id: str) -> List[CommunicationResponse]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    comms = get_communications_by_trip(db, trip_id)
    results = []
    for c in comms:
        stats = count_recipient_stats(db, c.communication_id)
        results.append(CommunicationResponse(
            communication_id=c.communication_id,
            trip_id=c.trip_id,
            title=c.title,
            message=c.message,
            audience_type=c.audience_type,
            created_by=c.created_by,
            created_at=c.created_at,
            recipient_count=stats["total"],
        ))
    return results


def get_communication_detail(db: Session, communication_id: str) -> CommunicationDetailResponse:
    comm = get_communication_by_id(db, communication_id)
    if not comm:
        raise ValueError(f"Communication not found: {communication_id}")

    recips = get_recipients_by_communication(db, communication_id)
    stats = count_recipient_stats(db, communication_id)

    recipient_infos = []
    for r in recips:
        traveller = get_traveller_by_id(db, r.traveller_id)
        name = f"{traveller.first_name} {traveller.last_name}" if traveller else "Unknown"
        recipient_infos.append(RecipientInfo(
            recipient_id=r.recipient_id,
            traveller_id=r.traveller_id,
            traveller_name=name,
            read_status=r.read_status,
            read_at=r.read_at,
        ))

    return CommunicationDetailResponse(
        communication_id=comm.communication_id,
        trip_id=comm.trip_id,
        title=comm.title,
        message=comm.message,
        audience_type=comm.audience_type,
        created_by=comm.created_by,
        created_at=comm.created_at,
        recipients=recipient_infos,
        total_recipients=stats["total"],
        read_count=stats["read"],
        unread_count=stats["unread"],
    )


def get_traveller_inbox(db: Session, traveller_id: str) -> List[InboxMessageResponse]:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    rows = get_inbox_for_traveller(db, traveller_id)
    return [InboxMessageResponse(**r) for r in rows]


def mark_message_read(db: Session, communication_id: str, traveller_id: str) -> dict:
    comm = get_communication_by_id(db, communication_id)
    if not comm:
        raise ValueError(f"Communication not found: {communication_id}")

    recip = mark_as_read(db, communication_id, traveller_id)
    if not recip:
        raise ValueError(f"Recipient not found for communication {communication_id} and traveller {traveller_id}")

    return {"message": "Marked as read", "read_at": str(recip.read_at)}


def get_communication_summary(db: Session, trip_id: str) -> CommunicationSummaryResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    total_messages = count_communications_by_trip(db, trip_id)
    total_recipients = count_recipients_by_trip(db, trip_id)
    read_count = count_recipients_by_trip_and_status(db, trip_id, ReadStatus.READ.value)
    unread_count = total_recipients - read_count
    read_pct = round((read_count / total_recipients) * 100, 2) if total_recipients > 0 else 0.0

    return CommunicationSummaryResponse(
        total_messages=total_messages,
        total_recipients=total_recipients,
        read_count=read_count,
        unread_count=unread_count,
        read_percentage=read_pct,
    )
