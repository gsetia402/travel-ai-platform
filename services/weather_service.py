import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from models.weather import WeatherRequest, WeatherResponse

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

RECOMMENDATIONS = {
    "Rain": "Carry rain jacket",
    "Drizzle": "Carry an umbrella",
    "Thunderstorm": "Stay indoors if possible",
    "Snow": "Pack warm layers and snow boots",
    "Clear": "Great weather! Carry sunscreen",
    "Clouds": "Light jacket recommended",
    "Mist": "Drive carefully, low visibility",
    "Fog": "Drive carefully, low visibility",
    "Haze": "Carry a mask if sensitive to air quality",
}


def _get_recommendation(condition: str) -> str:
    return RECOMMENDATIONS.get(condition, "Check local weather updates before heading out")


def get_weather(request: WeatherRequest) -> WeatherResponse:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY not found in environment")

    try:
        resp = requests.get(
            OPENWEATHER_URL,
            params={
                "q": request.destination,
                "appid": api_key,
                "units": "metric",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        condition = data["weather"][0]["main"]
        temperature = round(data["main"]["temp"])

        return WeatherResponse(
            destination=request.destination,
            temperature=temperature,
            condition=condition,
            recommendation=_get_recommendation(condition),
        )

    except requests.RequestException as e:
        raise ValueError(f"OpenWeather API request failed: {str(e)}")
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected OpenWeather response format: {str(e)}")
