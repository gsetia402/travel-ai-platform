import uuid
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from models.group_trip import TravellerTable, TravellerCreateRequest, TravellerUpdateRequest

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
        date_of_birth=request.date_of_birth,
        age=request.age,
        emergency_contact_name=request.emergency_contact_name,
        emergency_contact_phone=request.emergency_contact_phone,
        emergency_relationship=request.emergency_relationship,
        medical_conditions=request.medical_conditions,
        allergies=request.allergies,
        special_requirements=request.special_requirements,
        dietary_preferences=request.dietary_preferences,
        passport_number=request.passport_number,
        nationality=request.nationality,
        participation_status=request.participation_status or "INVITED",
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
            date_of_birth=req.date_of_birth,
            age=req.age,
            emergency_contact_name=req.emergency_contact_name,
            emergency_contact_phone=req.emergency_contact_phone,
            emergency_relationship=req.emergency_relationship,
            medical_conditions=req.medical_conditions,
            allergies=req.allergies,
            special_requirements=req.special_requirements,
            dietary_preferences=req.dietary_preferences,
            passport_number=req.passport_number,
            nationality=req.nationality,
            participation_status=req.participation_status or "INVITED",
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


def delete_travellers_bulk(db: Session, trip_id: str, traveller_ids: List[str]) -> int:
    count = db.query(TravellerTable).filter(
        TravellerTable.traveller_id.in_(traveller_ids),
        TravellerTable.trip_id == trip_id,
    ).delete(synchronize_session=False)
    db.commit()
    logger.info(f"Bulk deleted {count} travellers from trip {trip_id}")
    return count


def count_travellers_by_trip(db: Session, trip_id: str) -> int:
    return db.query(TravellerTable).filter(TravellerTable.trip_id == trip_id).count()


def update_traveller(db: Session, traveller_id: str, request: TravellerUpdateRequest) -> Optional[TravellerTable]:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        return None
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(traveller, field, value)
    db.commit()
    db.refresh(traveller)
    logger.info(f"Updated traveller: {traveller_id}")
    return traveller


def count_travellers_by_status(db: Session, trip_id: str, status: str) -> int:
    return db.query(TravellerTable).filter(
        TravellerTable.trip_id == trip_id,
        TravellerTable.participation_status == status,
    ).count()


def count_travellers_with_medical(db: Session, trip_id: str) -> int:
    return db.query(TravellerTable).filter(
        TravellerTable.trip_id == trip_id,
        TravellerTable.medical_conditions.isnot(None),
        TravellerTable.medical_conditions != "",
    ).count()


def count_travellers_with_special_requirements(db: Session, trip_id: str) -> int:
    return db.query(TravellerTable).filter(
        TravellerTable.trip_id == trip_id,
        TravellerTable.special_requirements.isnot(None),
        TravellerTable.special_requirements != "",
    ).count()
