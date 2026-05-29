from typing import Optional

from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    user_id: str
    month: str
    days: int


class DestinationRecommendation(BaseModel):
    destination: str
    reason: str


class RecommendationResponse(BaseModel):
    recommendations: list[DestinationRecommendation] = []
