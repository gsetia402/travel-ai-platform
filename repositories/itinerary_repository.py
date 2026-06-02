import uuid
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.trip_itinerary import TripItineraryTable

logger = logging.getLogger(__name__)


def get_itinerary(db: Session, trip_id: str) -> Optional[TripItineraryTable]:
    return db.query(TripItineraryTable).filter(TripItineraryTable.trip_id == trip_id).first()


def save_itinerary(db: Session, trip_id: str, itinerary_json: str) -> TripItineraryTable:
    existing = get_itinerary(db, trip_id)
    if existing:
        existing.itinerary_json = itinerary_json
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated itinerary for trip {trip_id}")
        return existing

    row = TripItineraryTable(
        id=str(uuid.uuid4()),
        trip_id=trip_id,
        itinerary_json=itinerary_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(f"Created itinerary for trip {trip_id}")
    return row
