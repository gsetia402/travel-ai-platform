import logging

from models.budget import BudgetRequest, BudgetEstimation
from models.itinerary import ItineraryRequest, UserPreferences
from models.weather import WeatherRequest, WeatherResponse
from models.trip import TripPlanRequest, TripPlanResponse
from services.budget_service import estimate_budget
from services.itinerary_service import generate_itinerary
from services.weather_service import get_weather
from services.memory_service import get_preferences
from database import SessionLocal

logger = logging.getLogger(__name__)

TRAVEL_ADVICE = {
    "Rain": [
        "Carry rain jacket",
        "Keep buffer time for travel",
        "Pack waterproof bags for electronics",
    ],
    "Drizzle": [
        "Carry an umbrella",
        "Wear waterproof footwear",
    ],
    "Thunderstorm": [
        "Avoid outdoor activities during storms",
        "Stay indoors if possible",
        "Keep emergency contacts handy",
    ],
    "Snow": [
        "Carry winter clothing",
        "Pack thermal layers and snow boots",
        "Check road conditions before travel",
    ],
    "Clear": [
        "Good conditions for sightseeing",
        "Carry sunscreen and sunglasses",
        "Stay hydrated",
    ],
    "Clouds": [
        "Light jacket recommended",
        "Good for outdoor walks",
    ],
    "Mist": [
        "Drive carefully, low visibility expected",
        "Carry a flashlight for early mornings",
    ],
    "Fog": [
        "Drive carefully, low visibility expected",
        "Avoid early morning travel if possible",
    ],
    "Haze": [
        "Carry a mask if sensitive to air quality",
        "Limit prolonged outdoor exposure",
    ],
}

DEFAULT_ADVICE = ["Check local weather updates before heading out"]


def _generate_travel_advice(weather: WeatherResponse) -> list[str]:
    return TRAVEL_ADVICE.get(weather.condition, DEFAULT_ADVICE)


def plan_trip(request: TripPlanRequest) -> TripPlanResponse:
    logger.info(f"Planning trip to {request.destination} for {request.days} days (user: {request.user_id})")

    weather = None
    itinerary = None
    budget_estimation: BudgetEstimation | None = None
    travel_advice: list[str] = []
    user_preferences: UserPreferences | None = None

    # 1. Load user preferences from Memory Agent
    try:
        logger.info(f"Loading preferences for user: {request.user_id}")
        db = SessionLocal()
        try:
            prefs = get_preferences(db, request.user_id)
            if prefs:
                user_preferences = UserPreferences(
                    budget=prefs.budget,
                    trip_type=prefs.trip_type,
                    accommodation=prefs.accommodation,
                    food_preference=prefs.food_preference,
                )
                logger.info(f"User preferences loaded: {user_preferences}")
            else:
                logger.info(f"No preferences found for user: {request.user_id}, continuing without")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Memory agent failed: {e}. Continuing without preferences.")

    # 2. Call Weather Agent
    try:
        logger.info(f"Fetching weather for {request.destination}")
        weather = get_weather(WeatherRequest(destination=request.destination))
        travel_advice = _generate_travel_advice(weather)
        logger.info(f"Weather fetched: {weather.condition}, {weather.temperature}°C")
    except Exception as e:
        logger.error(f"Weather agent failed: {e}")
        travel_advice = DEFAULT_ADVICE

    # Determine budget from preferences
    budget = user_preferences.budget if user_preferences and user_preferences.budget else 50000

    # 3. Call Budget Agent
    try:
        logger.info(f"Estimating budget for {request.destination}")
        budget_response = estimate_budget(
            BudgetRequest(
                destination=request.destination,
                days=request.days,
                budget=budget,
                trip_type=user_preferences.trip_type if user_preferences else None,
                accommodation=user_preferences.accommodation if user_preferences else None,
            )
        )
        budget_estimation = BudgetEstimation(
            cost_breakdown=budget_response.cost_breakdown,
            budget_status=budget_response.budget_status,
        )
        logger.info(f"Budget estimated: total={budget_response.cost_breakdown.total}, status={budget_response.budget_status}")
    except Exception as e:
        logger.error(f"Budget agent failed: {e}. Continuing without budget estimation.")

    # 4. Call Itinerary Agent with preferences
    try:
        logger.info(f"Generating itinerary for {request.destination}")
        itinerary = generate_itinerary(
            ItineraryRequest(
                destination=request.destination,
                days=request.days,
                budget=budget,
                preferences=user_preferences,
            )
        )
        logger.info(f"Itinerary generated: {len(itinerary.itinerary)} days")
    except Exception as e:
        logger.error(f"Itinerary agent failed: {e}")

    return TripPlanResponse(
        destination=request.destination,
        user_preferences=user_preferences,
        weather=weather,
        budget_estimation=budget_estimation,
        itinerary=itinerary,
        travel_advice=travel_advice,
    )
