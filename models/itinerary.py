from typing import Optional

from pydantic import BaseModel


class UserPreferences(BaseModel):
    budget: Optional[int] = None
    trip_type: Optional[str] = None
    accommodation: Optional[str] = None
    food_preference: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    activities: list[str]


class ItineraryRequest(BaseModel):
    destination: str
    days: int
    budget: int
    preferences: Optional[UserPreferences] = None


class ItineraryResponse(BaseModel):
    destination: str
    days: int
    budget: int
    itinerary: list[DayPlan]
