"""Service layer for the Traveller Portal — auth, profile, trip info."""
import os
import logging
from datetime import datetime, timedelta, date
from typing import Optional, List

from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import get_db
from models.group_trip import TravellerTable, TripTable
from models.traveller_portal import (
    TravellerLoginRequest,
    TravellerTokenResponse,
    TravellerMeResponse,
    TravellerProfileUpdateRequest,
    TravellerTripResponse,
    TravellerRoomResponse,
    TripVisibilityTable,
    VisibilitySettingsResponse,
)
from models.room import RoomTable, RoomAllocationTable

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "tripops-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

traveller_security = HTTPBearer(auto_error=False)


# ---------- Auth ----------

def create_traveller_token(traveller_id: str, trip_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS * 7)  # 7 days
    payload = {
        "sub": traveller_id,
        "trip_id": trip_id,
        "role": "traveller",
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def traveller_login(db: Session, request: TravellerLoginRequest) -> TravellerTokenResponse:
    """Authenticate traveller by phone + date_of_birth."""
    phone = request.phone.strip()
    try:
        dob = date.fromisoformat(request.date_of_birth.strip())
    except ValueError:
        raise ValueError("Invalid date_of_birth format. Use YYYY-MM-DD.")

    traveller = (
        db.query(TravellerTable)
        .filter(TravellerTable.phone == phone, TravellerTable.date_of_birth == dob)
        .first()
    )
    if not traveller:
        raise ValueError("No traveller found with this phone and date of birth.")

    token = create_traveller_token(traveller.traveller_id, traveller.trip_id)
    return TravellerTokenResponse(
        access_token=token,
        traveller_id=traveller.traveller_id,
        trip_id=traveller.trip_id,
        name=f"{traveller.first_name} {traveller.last_name}",
    )


def get_current_traveller(
    credentials: HTTPAuthorizationCredentials = Depends(traveller_security),
    db: Session = Depends(get_db),
) -> TravellerTable:
    """Decode JWT and return the authenticated TravellerTable record."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        traveller_id = payload.get("sub")
        role = payload.get("role")
        if not traveller_id or role != "traveller":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    traveller = db.query(TravellerTable).filter(TravellerTable.traveller_id == traveller_id).first()
    if not traveller:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Traveller not found")
    return traveller


# ---------- Profile ----------

def get_traveller_profile(traveller: TravellerTable) -> TravellerMeResponse:
    return TravellerMeResponse(
        traveller_id=traveller.traveller_id,
        trip_id=traveller.trip_id,
        first_name=traveller.first_name,
        last_name=traveller.last_name,
        phone=traveller.phone,
        email=traveller.email,
        gender=traveller.gender,
        date_of_birth=str(traveller.date_of_birth) if traveller.date_of_birth else None,
        department=traveller.department,
        city=traveller.city,
        emergency_contact_name=traveller.emergency_contact_name,
        emergency_contact_phone=traveller.emergency_contact_phone,
        emergency_relationship=traveller.emergency_relationship,
        medical_conditions=traveller.medical_conditions,
        allergies=traveller.allergies,
        special_requirements=traveller.special_requirements,
        dietary_preferences=traveller.dietary_preferences,
        passport_number=traveller.passport_number,
        nationality=traveller.nationality,
        participation_status=traveller.participation_status,
        membership_status=traveller.membership_status,
        opt_out_reason=traveller.opt_out_reason,
    )


def update_traveller_profile(db: Session, traveller: TravellerTable, updates: TravellerProfileUpdateRequest) -> TravellerMeResponse:
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(traveller, field, value)
    db.commit()
    db.refresh(traveller)
    return get_traveller_profile(traveller)


# ---------- Trip Info ----------

def get_traveller_trip(db: Session, traveller: TravellerTable) -> TravellerTripResponse:
    trip = db.query(TripTable).filter(TripTable.trip_id == traveller.trip_id).first()
    if not trip:
        raise ValueError("Trip not found")
    return TravellerTripResponse(
        trip_id=trip.trip_id,
        trip_name=trip.trip_name,
        organization_name=trip.organization_name,
        origin_city=trip.origin_city,
        destination=trip.destination,
        start_date=str(trip.start_date) if trip.start_date else None,
        end_date=str(trip.end_date) if trip.end_date else None,
        days=trip.days,
        status=trip.status,
    )


# ---------- Room ----------

def get_traveller_room(db: Session, traveller: TravellerTable) -> TravellerRoomResponse:
    allocation = (
        db.query(RoomAllocationTable)
        .filter(RoomAllocationTable.traveller_id == traveller.traveller_id)
        .first()
    )
    if not allocation:
        return TravellerRoomResponse()

    room = db.query(RoomTable).filter(RoomTable.room_id == allocation.room_id).first()
    if not room:
        return TravellerRoomResponse()

    # Get all occupants in same room
    allocs = db.query(RoomAllocationTable).filter(RoomAllocationTable.room_id == room.room_id).all()
    occupants = []
    for a in allocs:
        t = db.query(TravellerTable).filter(TravellerTable.traveller_id == a.traveller_id).first()
        if t:
            occupants.append({
                "traveller_id": t.traveller_id,
                "first_name": t.first_name,
                "last_name": t.last_name,
                "gender": t.gender,
            })

    return TravellerRoomResponse(
        room_id=room.room_id,
        room_number=room.room_number,
        room_type=room.room_type,
        occupants=occupants,
    )


# ---------- Visibility ----------

def get_visibility_settings(db: Session, trip_id: str) -> VisibilitySettingsResponse:
    settings = db.query(TripVisibilityTable).filter(TripVisibilityTable.trip_id == trip_id).first()
    if not settings:
        return VisibilitySettingsResponse(trip_id=trip_id)
    return VisibilitySettingsResponse.model_validate(settings)


def update_visibility_settings(db: Session, trip_id: str, updates: dict) -> VisibilitySettingsResponse:
    settings = db.query(TripVisibilityTable).filter(TripVisibilityTable.trip_id == trip_id).first()
    if not settings:
        settings = TripVisibilityTable(trip_id=trip_id)
        db.add(settings)

    for field, value in updates.items():
        if value is not None and hasattr(settings, field):
            setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return VisibilitySettingsResponse.model_validate(settings)
