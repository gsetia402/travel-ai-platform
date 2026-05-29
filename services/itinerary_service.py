import logging

from models.itinerary import DayPlan, ItineraryRequest, ItineraryResponse
from services.gemini_service import generate_itinerary_with_gemini

logger = logging.getLogger(__name__)

DEFAULT_ACTIVITIES: list[list[str]] = [
    ["Arrival", "City Tour"],
    ["Local Sightseeing", "Cultural Experience"],
    ["Adventure Activity", "Local Cuisine Tasting"],
    ["Day Trip to Nearby Attraction", "Relaxation"],
    ["Souvenir Shopping", "Departure"],
]


def _fallback_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    itinerary: list[DayPlan] = []
    for day_num in range(1, request.days + 1):
        index = (day_num - 1) % len(DEFAULT_ACTIVITIES)
        itinerary.append(DayPlan(day=day_num, activities=DEFAULT_ACTIVITIES[index]))

    return ItineraryResponse(
        destination=request.destination,
        days=request.days,
        budget=request.budget,
        itinerary=itinerary,
    )


def generate_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    try:
        return generate_itinerary_with_gemini(request)
    except Exception as e:
        logger.error(f"Gemini API failed: {e}. Returning fallback itinerary.")
        return _fallback_itinerary(request)
