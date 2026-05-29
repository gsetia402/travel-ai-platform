import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.user_preference import (
    UserPreferenceTable,
    UserPreferenceRequest,
    UserPreferenceResponse,
    MemorySaveResponse,
)

logger = logging.getLogger(__name__)


def save_preferences(db: Session, request: UserPreferenceRequest) -> MemorySaveResponse:
    logger.info(f"Saving preferences for user: {request.user_id}")

    try:
        existing = db.query(UserPreferenceTable).filter(
            UserPreferenceTable.user_id == request.user_id
        ).first()

        if existing:
            existing.budget = request.budget
            existing.trip_type = request.trip_type
            existing.accommodation = request.accommodation
            existing.food_preference = request.food_preference
            logger.info(f"Updated preferences for user: {request.user_id}")
        else:
            new_pref = UserPreferenceTable(
                user_id=request.user_id,
                budget=request.budget,
                trip_type=request.trip_type,
                accommodation=request.accommodation,
                food_preference=request.food_preference,
            )
            db.add(new_pref)
            logger.info(f"Created preferences for user: {request.user_id}")

        db.commit()
        return MemorySaveResponse(message="Preferences saved successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save preferences for user {request.user_id}: {e}")
        raise ValueError(f"Database error: {str(e)}")


def get_preferences(db: Session, user_id: str) -> Optional[UserPreferenceResponse]:
    logger.info(f"Fetching preferences for user: {user_id}")

    try:
        record = db.query(UserPreferenceTable).filter(
            UserPreferenceTable.user_id == user_id
        ).first()

        if not record:
            logger.info(f"No preferences found for user: {user_id}")
            return None

        return UserPreferenceResponse.model_validate(record)

    except Exception as e:
        logger.error(f"Failed to fetch preferences for user {user_id}: {e}")
        raise ValueError(f"Database error: {str(e)}")
