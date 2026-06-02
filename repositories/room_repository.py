import uuid
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from models.room import RoomTable, RoomAllocationTable

logger = logging.getLogger(__name__)


def create_room(db: Session, trip_id: str, room_number: str, room_type: str, capacity: int, gender: Optional[str] = None) -> RoomTable:
    room = RoomTable(
        room_id=str(uuid.uuid4()),
        trip_id=trip_id,
        room_number=room_number,
        room_type=room_type,
        capacity=capacity,
        gender=gender,
    )
    db.add(room)
    return room


def create_rooms_bulk(db: Session, rooms: List[RoomTable]) -> None:
    db.add_all(rooms)


def create_allocation(db: Session, room_id: str, traveller_id: str) -> RoomAllocationTable:
    allocation = RoomAllocationTable(
        allocation_id=str(uuid.uuid4()),
        room_id=room_id,
        traveller_id=traveller_id,
    )
    db.add(allocation)
    return allocation


def create_allocations_bulk(db: Session, allocations: List[RoomAllocationTable]) -> None:
    db.add_all(allocations)


def get_rooms_by_trip(db: Session, trip_id: str) -> List[RoomTable]:
    return db.query(RoomTable).filter(RoomTable.trip_id == trip_id).order_by(RoomTable.room_number).all()


def get_room_by_id(db: Session, room_id: str) -> Optional[RoomTable]:
    return db.query(RoomTable).filter(RoomTable.room_id == room_id).first()


def delete_room(db: Session, room_id: str) -> bool:
    room = get_room_by_id(db, room_id)
    if not room:
        return False
    db.delete(room)
    db.commit()
    logger.info(f"Deleted room: {room_id}")
    return True


def delete_rooms_by_trip(db: Session, trip_id: str) -> int:
    rooms = get_rooms_by_trip(db, trip_id)
    count = len(rooms)
    for room in rooms:
        db.delete(room)
    db.commit()
    return count


def get_allocation_by_traveller(db: Session, traveller_id: str) -> Optional[RoomAllocationTable]:
    return db.query(RoomAllocationTable).filter(
        RoomAllocationTable.traveller_id == traveller_id
    ).first()


def get_allocations_by_room(db: Session, room_id: str) -> List[RoomAllocationTable]:
    return db.query(RoomAllocationTable).filter(
        RoomAllocationTable.room_id == room_id
    ).all()


def count_allocations_by_room(db: Session, room_id: str) -> int:
    return db.query(RoomAllocationTable).filter(
        RoomAllocationTable.room_id == room_id
    ).count()


def delete_allocation_by_traveller(db: Session, traveller_id: str) -> bool:
    alloc = get_allocation_by_traveller(db, traveller_id)
    if not alloc:
        return False
    db.delete(alloc)
    return True


def count_rooms_by_trip(db: Session, trip_id: str) -> int:
    return db.query(RoomTable).filter(RoomTable.trip_id == trip_id).count()


def count_allocated_travellers_by_trip(db: Session, trip_id: str) -> int:
    return (
        db.query(RoomAllocationTable)
        .join(RoomTable, RoomAllocationTable.room_id == RoomTable.room_id)
        .filter(RoomTable.trip_id == trip_id)
        .count()
    )
