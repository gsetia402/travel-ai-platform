from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.room import (
    RoomAllocateRequest,
    RoomAllocateResponse,
    RoomResponse,
    RoomDetailResponse,
    MoveResponse,
)
from services.room_service import (
    allocate_rooms,
    list_rooms,
    get_room_detail,
    remove_room,
    move_traveller_to_room,
    CapacityExceededError,
)

router = APIRouter(tags=["Rooms"])


@router.post("/trips/{trip_id}/rooms/allocate", response_model=RoomAllocateResponse)
def allocate_trip_rooms(trip_id: str, request: RoomAllocateRequest, db: Session = Depends(get_db)):
    try:
        return allocate_rooms(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips/{trip_id}/rooms", response_model=List[RoomResponse])
def get_trip_rooms(trip_id: str, db: Session = Depends(get_db)):
    try:
        return list_rooms(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rooms/{room_id}", response_model=RoomDetailResponse)
def get_room(room_id: str, db: Session = Depends(get_db)):
    try:
        return get_room_detail(db, room_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/rooms/{room_id}", status_code=200)
def delete_room(room_id: str, db: Session = Depends(get_db)):
    try:
        remove_room(db, room_id)
        return {"message": f"Room {room_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rooms/{room_id}/travellers/{traveller_id}", response_model=MoveResponse)
def move_traveller(room_id: str, traveller_id: str, db: Session = Depends(get_db)):
    try:
        return move_traveller_to_room(db, room_id, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CapacityExceededError as e:
        raise HTTPException(status_code=409, detail=str(e))
