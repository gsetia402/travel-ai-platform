import uuid
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from models.group_trip import TripTable, TripCreateRequest, TripUpdateRequest

logger = logging.getLogger(__name__)


def create_trip(db: Session, request: TripCreateRequest) -> TripTable:
    trip = TripTable(
        trip_id=str(uuid.uuid4()),
        trip_name=request.trip_name,
        organization_name=request.organization_name,
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        days=request.days,
        traveller_count=request.traveller_count,
        budget=request.budget,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    logger.info(f"Created trip: {trip.trip_id} — {trip.trip_name}")
    return trip


def get_all_trips(db: Session) -> List[TripTable]:
    return db.query(TripTable).order_by(TripTable.created_at.desc()).all()


def get_trip_by_id(db: Session, trip_id: str) -> Optional[TripTable]:
    return db.query(TripTable).filter(TripTable.trip_id == trip_id).first()


def update_trip(db: Session, trip_id: str, request: TripUpdateRequest) -> Optional[TripTable]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        return None
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    db.commit()
    db.refresh(trip)
    logger.info(f"Updated trip: {trip_id}")
    return trip


def delete_trip(db: Session, trip_id: str) -> bool:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        return False
    db.delete(trip)
    db.commit()
    logger.info(f"Deleted trip: {trip_id}")
    return True
