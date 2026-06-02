import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class RoomType(str, enum.Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    QUAD = "QUAD"


ROOM_CAPACITY = {
    RoomType.SINGLE: 1,
    RoomType.DOUBLE: 2,
    RoomType.TRIPLE: 3,
    RoomType.QUAD: 4,
}


class AllocationStrategy(str, enum.Enum):
    SAME_GENDER = "SAME_GENDER"
    SAME_DEPARTMENT = "SAME_DEPARTMENT"
    SAME_CITY = "SAME_CITY"
    EXECUTIVE_SINGLE_ROOM = "EXECUTIVE_SINGLE_ROOM"
    CUSTOM = "CUSTOM"


# --------------- SQLAlchemy ORM Models ---------------

class RoomTable(Base):
    __tablename__ = "rooms"

    room_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    room_number = Column(String, nullable=False)
    room_type = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    gender = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    allocations = relationship("RoomAllocationTable", back_populates="room", cascade="all, delete-orphan")


class RoomAllocationTable(Base):
    __tablename__ = "room_allocations"

    allocation_id = Column(String, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.room_id", ondelete="CASCADE"), nullable=False, index=True)
    traveller_id = Column(String, ForeignKey("travellers.traveller_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    allocated_at = Column(DateTime, server_default=func.now())

    room = relationship("RoomTable", back_populates="allocations")


# --------------- Pydantic Request / Response Models ---------------

class RoomAllocateRequest(BaseModel):
    room_type: RoomType = RoomType.DOUBLE
    capacity: Optional[int] = None
    strategy: AllocationStrategy = AllocationStrategy.SAME_GENDER


class RoomAllocateResponse(BaseModel):
    rooms_created: int
    travellers_allocated: int


class OccupantInfo(BaseModel):
    traveller_id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class RoomResponse(BaseModel):
    room_id: str
    room_number: str
    room_type: str
    capacity: int
    gender: Optional[str] = None
    occupants: List[OccupantInfo] = []

    class Config:
        from_attributes = True


class RoomDetailResponse(BaseModel):
    room_id: str
    room_number: str
    room_type: str
    capacity: int
    gender: Optional[str] = None
    trip_id: str
    created_at: Optional[datetime] = None
    occupants: List[OccupantInfo] = []

    class Config:
        from_attributes = True


class MoveResponse(BaseModel):
    message: str
    room_id: str
    traveller_id: str
