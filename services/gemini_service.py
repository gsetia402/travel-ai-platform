import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from models.itinerary import ItineraryRequest, ItineraryResponse

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_model():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={"response_mime_type": "application/json"},
    )


def _clean_json_text(raw_text: str) -> str:
    text = raw_text.strip()

    # Strip markdown fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Remove control characters except newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    return text


def _build_preferences_section(request: ItineraryRequest) -> str:
    if not request.preferences:
        return ""

    prefs = request.preferences
    lines = ["\nUser Preferences:\n"]
    if prefs.budget:
        lines.append(f"Budget: {prefs.budget} INR")
    if prefs.trip_type:
        lines.append(f"Trip Type: {prefs.trip_type.capitalize()}")
    if prefs.accommodation:
        lines.append(f"Accommodation: {prefs.accommodation.capitalize()}")
    if prefs.food_preference:
        lines.append(f"Food Preference: {prefs.food_preference.capitalize()}")
    lines.append("\nGenerate itinerary based on these preferences.\n")
    return "\n".join(lines)


def build_prompt(request: ItineraryRequest) -> str:
    preferences_section = _build_preferences_section(request)

    return (
        f"Generate a realistic and detailed travel itinerary.\n\n"
        f"Destination: {request.destination}\n"
        f"Days: {request.days}\n"
        f"Budget: {request.budget} INR\n\n"

        f"{preferences_section}"

        f"Requirements:\n"
        f"- Use real attractions and places.\n"
        f"- Include Morning, Afternoon, and Evening activities.\n"
        f"- Keep the itinerary realistic and geographically practical.\n"
        f"- Stay within the provided budget.\n"
        f"- Include local food and cultural experiences.\n"
        f"- Avoid generic activities.\n"
        f"- Recommend actual tourist attractions.\n\n"

        f"Return the response strictly as JSON with this structure:\n"

        f'{{\n'
        f'  "destination": "{request.destination}",\n'
        f'  "days": {request.days},\n'
        f'  "budget": {request.budget},\n'
        f'  "itinerary": [\n'
        f'    {{\n'
        f'      "day": 1,\n'
        f'      "activities": [\n'
        f'        "Morning: Activity",\n'
        f'        "Afternoon: Activity",\n'
        f'        "Evening: Activity"\n'
        f'      ]\n'
        f'    }}\n'
        f'  ]\n'
        f'}}\n\n'

        f"Return ONLY valid JSON.\n"
        f"No markdown.\n"
        f"No code blocks.\n"
        f"No explanation.\n"
    )


def generate_itinerary_with_gemini(
        request: ItineraryRequest
) -> ItineraryResponse:

    print("***** GEMINI SERVICE CALLED *****")

    try:
        model = get_model()

        response = model.generate_content(
            build_prompt(request)
        )

        raw_text = _clean_json_text(response.text)

        data = json.loads(raw_text)

        return ItineraryResponse(**data)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse Gemini JSON response: {str(e)}"
        )

    except Exception as e:
        raise ValueError(
            f"Failed to generate itinerary: {str(e)}"
        )
