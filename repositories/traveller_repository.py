import uuid
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from models.group_trip import TravellerTable, TravellerCreateRequest

logger = logging.getLogger(__name__)


def add_traveller(db: Session, trip_id: str, request: TravellerCreateRequest) -> TravellerTable:
    traveller = TravellerTable(
        traveller_id=str(uuid.uuid4()),
        trip_id=trip_id,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        email=request.email,
        gender=request.gender,
        department=request.department,
        city=request.city,
    )
    db.add(traveller)
    db.commit()
    db.refresh(traveller)
    logger.info(f"Added traveller {traveller.traveller_id} to trip {trip_id}")
    return traveller


def add_travellers_bulk(db: Session, trip_id: str, travellers: List[TravellerCreateRequest]) -> List[TravellerTable]:
    records = []
    for req in travellers:
        record = TravellerTable(
            traveller_id=str(uuid.uuid4()),
            trip_id=trip_id,
            first_name=req.first_name,
            last_name=req.last_name,
            phone=req.phone,
            email=req.email,
            gender=req.gender,
            department=req.department,
            city=req.city,
        )
        records.append(record)
    db.add_all(records)
    db.commit()
    logger.info(f"Bulk added {len(records)} travellers to trip {trip_id}")
    return records


def get_travellers_by_trip(db: Session, trip_id: str) -> List[TravellerTable]:
    return db.query(TravellerTable).filter(TravellerTable.trip_id == trip_id).all()


def get_traveller_by_id(db: Session, traveller_id: str) -> Optional[TravellerTable]:
    return db.query(TravellerTable).filter(TravellerTable.traveller_id == traveller_id).first()


def delete_traveller(db: Session, traveller_id: str) -> bool:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        return False
    db.delete(traveller)
    db.commit()
    logger.info(f"Deleted traveller: {traveller_id}")
    return True


def count_travellers_by_trip(db: Session, trip_id: str) -> int:
    return db.query(TravellerTable).filter(TravellerTable.trip_id == trip_id).count()
