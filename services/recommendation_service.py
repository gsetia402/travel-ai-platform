import json
import logging

from database import SessionLocal
from models.recommendation import RecommendationRequest, RecommendationResponse
from services.gemini_service import get_model, _clean_json_text
from services.memory_service import get_preferences

logger = logging.getLogger(__name__)


def _build_recommendation_prompt(
    request: RecommendationRequest,
    budget: int | None = None,
    trip_type: str | None = None,
    food_preference: str | None = None,
) -> str:
    lines = [
        "Recommend the top 5 travel destinations in India.\n",
        f"Month of travel: {request.month}",
        f"Number of days: {request.days}",
    ]

    if budget:
        lines.append(f"Budget: {budget} INR")
    if trip_type:
        lines.append(f"Trip type preference: {trip_type}")
    if food_preference:
        lines.append(f"Food preference: {food_preference}")

    lines.append(
        "\nFor each destination provide a short reason why it is a good fit."
    )
    lines.append(
        "\nReturn the response strictly as JSON with this structure:\n"
        '{\n'
        '  "recommendations": [\n'
        '    {\n'
        '      "destination": "Place Name",\n'
        '      "reason": "Short reason"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Return ONLY valid JSON.\n"
        "No markdown.\n"
        "No code blocks.\n"
        "No explanation."
    )

    return "\n".join(lines)


def _parse_gemini_response(raw_text: str) -> RecommendationResponse:
    text = _clean_json_text(raw_text)
    data = json.loads(text)
    return RecommendationResponse(**data)


def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    logger.info(f"Generating recommendations for user: {request.user_id}, month: {request.month}, days: {request.days}")

    budget = None
    trip_type = None
    food_preference = None

    # Load user preferences from Memory Agent
    try:
        db = SessionLocal()
        try:
            prefs = get_preferences(db, request.user_id)
            if prefs:
                budget = prefs.budget
                trip_type = prefs.trip_type
                food_preference = prefs.food_preference
                logger.info(f"User preferences loaded for {request.user_id}")
            else:
                logger.info(f"No preferences found for user: {request.user_id}, continuing without")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Memory agent failed: {e}. Continuing without preferences.")

    # Call Gemini
    try:
        model = get_model()
        prompt = _build_recommendation_prompt(request, budget, trip_type, food_preference)
        logger.info("Calling Gemini for destination recommendations")

        response = model.generate_content(prompt)
        result = _parse_gemini_response(response.text)
        logger.info(f"Gemini returned {len(result.recommendations)} recommendations")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini recommendation response: {e}")
        raise ValueError(f"Failed to parse Gemini response: {str(e)}")
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise ValueError(f"Failed to generate recommendations: {str(e)}")
