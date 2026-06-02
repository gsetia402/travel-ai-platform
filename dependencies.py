"""
Shared dependencies for multi-tenant authorization.
"""
import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import TripTable
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)


def require_trip_access(trip_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)) -> TripTable:
    """
    Verify that the trip exists AND belongs to the current user's organization.
    Returns the trip if authorized, raises 403 otherwise.
    Trips with NULL organization_id are claimed by the first org that accesses them (migration).
    """
    trip = db.query(TripTable).filter(TripTable.trip_id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Migration: claim orphan trips (created before multi-tenant was enforced)
    if trip.organization_id is None:
        trip.organization_id = user.organization_id
        db.commit()
        db.refresh(trip)
        logger.info(f"Claimed orphan trip {trip_id} for org {user.organization_id}")
        return trip

    if trip.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: trip belongs to another organization")
    return trip
