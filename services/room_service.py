import logging
from typing import List

from sqlalchemy.orm import Session

from models.group_trip import TravellerTable
from models.room import (
    RoomAllocateRequest,
    RoomAllocateResponse,
    RoomResponse,
    RoomDetailResponse,
    OccupantInfo,
    MoveResponse,
    ROOM_CAPACITY,
)
from repositories.room_repository import (
    get_rooms_by_trip,
    get_room_by_id,
    delete_room,
    delete_rooms_by_trip,
    get_allocations_by_room,
    get_allocation_by_traveller,
    delete_allocation_by_traveller,
    count_allocations_by_room,
    create_allocation,
    create_rooms_bulk,
    create_allocations_bulk,
)
from repositories.trip_repository import get_trip_by_id
from repositories.traveller_repository import get_travellers_by_trip, get_traveller_by_id
from services.allocation_engine import get_strategy

logger = logging.getLogger(__name__)


def allocate_rooms(db: Session, trip_id: str, request: RoomAllocateRequest) -> RoomAllocateResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    travellers = get_travellers_by_trip(db, trip_id)
    if not travellers:
        raise ValueError(f"No travellers registered for trip: {trip_id}")

    # Remove existing allocations for a fresh allocation
    existing_rooms = get_rooms_by_trip(db, trip_id)
    if existing_rooms:
        delete_rooms_by_trip(db, trip_id)
        logger.info(f"Cleared {len(existing_rooms)} existing rooms for trip {trip_id}")

    strategy = get_strategy(request.strategy)
    rooms, allocations = strategy.allocate(trip_id, travellers, request.room_type)

    create_rooms_bulk(db, rooms)
    db.flush()
    create_allocations_bulk(db, allocations)
    db.commit()

    logger.info(f"Allocated {len(rooms)} rooms for {len(allocations)} travellers (trip: {trip_id})")

    return RoomAllocateResponse(
        rooms_created=len(rooms),
        travellers_allocated=len(allocations),
    )


def list_rooms(db: Session, trip_id: str) -> List[RoomResponse]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    rooms = get_rooms_by_trip(db, trip_id)
    result = []

    for room in rooms:
        allocations = get_allocations_by_room(db, room.room_id)
        occupants = []
        for alloc in allocations:
            traveller = get_traveller_by_id(db, alloc.traveller_id)
            if traveller:
                occupants.append(OccupantInfo(
                    traveller_id=traveller.traveller_id,
                    name=f"{traveller.first_name} {traveller.last_name}",
                ))

        result.append(RoomResponse(
            room_id=room.room_id,
            room_number=room.room_number,
            room_type=room.room_type,
            capacity=room.capacity,
            gender=room.gender,
            occupants=occupants,
        ))

    return result


def get_room_detail(db: Session, room_id: str) -> RoomDetailResponse:
    room = get_room_by_id(db, room_id)
    if not room:
        raise ValueError(f"Room not found: {room_id}")

    allocations = get_allocations_by_room(db, room.room_id)
    occupants = []
    for alloc in allocations:
        traveller = get_traveller_by_id(db, alloc.traveller_id)
        if traveller:
            occupants.append(OccupantInfo(
                traveller_id=traveller.traveller_id,
                name=f"{traveller.first_name} {traveller.last_name}",
            ))

    return RoomDetailResponse(
        room_id=room.room_id,
        room_number=room.room_number,
        room_type=room.room_type,
        capacity=room.capacity,
        gender=room.gender,
        trip_id=room.trip_id,
        created_at=room.created_at,
        occupants=occupants,
    )


def remove_room(db: Session, room_id: str) -> bool:
    deleted = delete_room(db, room_id)
    if not deleted:
        raise ValueError(f"Room not found: {room_id}")
    return True


def move_traveller_to_room(db: Session, room_id: str, traveller_id: str) -> MoveResponse:
    room = get_room_by_id(db, room_id)
    if not room:
        raise ValueError(f"Room not found: {room_id}")

    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")

    # Check room capacity
    current_count = count_allocations_by_room(db, room_id)
    if current_count >= room.capacity:
        raise CapacityExceededError(
            f"Room {room.room_number} is full ({current_count}/{room.capacity})"
        )

    # Remove existing allocation if any
    delete_allocation_by_traveller(db, traveller_id)
    db.flush()

    # Create new allocation
    create_allocation(db, room_id, traveller_id)
    db.commit()

    logger.info(f"Moved traveller {traveller_id} to room {room_id}")

    return MoveResponse(
        message=f"Traveller moved to room {room.room_number}",
        room_id=room_id,
        traveller_id=traveller_id,
    )


class CapacityExceededError(Exception):
    pass
