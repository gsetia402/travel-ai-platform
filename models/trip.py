from typing import Optional

from pydantic import BaseModel

from models.budget import BudgetEstimation
from models.itinerary import ItineraryResponse, UserPreferences
from models.weather import WeatherResponse


class TripPlanRequest(BaseModel):
    user_id: str
    destination: str
    days: int


class TripPlanResponse(BaseModel):
    destination: str
    user_preferences: Optional[UserPreferences] = None
    weather: Optional[WeatherResponse] = None
    budget_estimation: Optional[BudgetEstimation] = None
    itinerary: Optional[ItineraryResponse] = None
    travel_advice: list[str] = []
