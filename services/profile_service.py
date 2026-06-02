import logging

from sqlalchemy.orm import Session

from models.group_trip import TravellerResponse, TravellerUpdateRequest
from repositories.traveller_repository import get_traveller_by_id, update_traveller

logger = logging.getLogger(__name__)


def get_traveller_profile(db: Session, traveller_id: str) -> TravellerResponse:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")
    return TravellerResponse.model_validate(traveller)


def update_traveller_profile(db: Session, traveller_id: str, request: TravellerUpdateRequest) -> TravellerResponse:
    traveller = update_traveller(db, traveller_id, request)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")
    return TravellerResponse.model_validate(traveller)
