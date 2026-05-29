# Travel AI Platform

AI-powered travel planning platform using FastAPI, Gemini AI, OpenWeather, memory-driven personalization, budget estimation, recommendations, and multi-agent orchestration.

---

## Overview

This platform uses a multi-agent architecture where specialized AI agents collaborate to create personalized travel plans. A Supervisor Agent orchestrates the flow — loading user preferences, checking weather, estimating budgets, and generating day-wise itineraries using Google Gemini.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  POST /plan-trip                 │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │ Supervisor Agent │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │  Memory  │ │ Weather  │ │  Budget  │
  │  Agent   │ │  Agent   │ │  Agent   │
  └──────────┘ └──────────┘ └──────────┘
        │                         │
        └────────────┬────────────┘
                     ▼
            ┌─────────────────┐
            │ Itinerary Agent │
            │   (Gemini AI)   │
            └─────────────────┘
```

### Agent Flow (Supervisor)

```
Memory Agent → Weather Agent → Budget Agent → Itinerary Agent
```

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Web framework & API layer |
| **Google Gemini** | AI-powered itinerary, budget & recommendation generation |
| **OpenWeather API** | Real-time weather data |
| **SQLite** | Persistent user preference storage |
| **SQLAlchemy** | ORM & database management |
| **Pydantic** | Data validation & serialization |

---

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Memory Agent** | Store & retrieve user preferences |
| **Recommendation Agent** | Suggest destinations based on preferences & season |
| **Weather Agent** | Fetch real-time weather for destinations |
| **Budget Agent** | Estimate trip costs with breakdown |
| **Itinerary Agent** | Generate personalized day-wise itinerary |
| **Supervisor Agent** | Orchestrate all agents into a unified trip plan |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/memory/save` | Save user preferences |
| GET | `/memory/{user_id}` | Get user preferences |
| POST | `/recommend` | Get destination recommendations |
| POST | `/weather` | Get weather for a destination |
| POST | `/budget` | Get budget estimation |
| POST | `/itinerary` | Generate itinerary |
| POST | `/plan-trip` | Full trip planning (Supervisor) |

---

## Sample Requests & Responses

### Save Preferences

```bash
POST /memory/save
```
```json
{
  "user_id": "gaurav",
  "budget": 30000,
  "trip_type": "mountains",
  "accommodation": "homestay",
  "food_preference": "vegetarian"
}
```
Response:
```json
{ "message": "Preferences saved successfully" }
```

### Get Recommendations

```bash
POST /recommend
```
```json
{
  "user_id": "gaurav",
  "month": "July",
  "days": 7
}
```
Response:
```json
{
  "recommendations": [
    { "destination": "Jibhi", "reason": "Pleasant weather and fits budget" },
    { "destination": "Manali", "reason": "Great for mountain lovers in July" }
  ]
}
```

### Plan Trip (Supervisor)

```bash
POST /plan-trip
```
```json
{
  "user_id": "gaurav",
  "destination": "Manali",
  "days": 5
}
```
Response:
```json
{
  "destination": "Manali",
  "user_preferences": {
    "budget": 30000,
    "trip_type": "mountains",
    "accommodation": "homestay",
    "food_preference": "vegetarian"
  },
  "weather": {
    "destination": "Manali",
    "temperature": 18,
    "condition": "Clear",
    "recommendation": "Great weather! Carry sunscreen"
  },
  "budget_estimation": {
    "currency": "INR",
    "cost_breakdown": {
      "stay": 10000,
      "food": 5000,
      "local_transport": 4000,
      "activities": 6000,
      "miscellaneous": 2000,
      "total": 27000
    },
    "budget_status": "WITHIN_BUDGET"
  },
  "itinerary": {
    "destination": "Manali",
    "days": 5,
    "budget": 30000,
    "itinerary": [
      { "day": 1, "activities": ["Morning: Arrival", "Afternoon: Mall Road", "Evening: Cafe hopping"] }
    ]
  },
  "travel_advice": [
    "Good conditions for sightseeing",
    "Carry sunscreen and sunglasses",
    "Stay hydrated"
  ]
}
```

---

## Project Structure

```
ai-agents/
├── main.py                          # FastAPI app & endpoints
├── config.py                        # Centralized configuration
├── database.py                      # SQLAlchemy engine & session
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker image definition
├── docker-compose.yml               # Docker Compose setup
├── render.yaml                      # Render deployment config
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── RELEASE_NOTES.md                 # Version history
├── README.md                        # Documentation
│
├── models/
│   ├── itinerary.py                 # Itinerary & UserPreferences models
│   ├── weather.py                   # Weather models
│   ├── trip.py                      # TripPlan request/response
│   ├── budget.py                    # Budget models
│   ├── recommendation.py           # Recommendation models
│   └── user_preference.py          # SQLAlchemy table & Pydantic models
│
├── services/
│   ├── gemini_service.py            # Gemini AI integration
│   ├── itinerary_service.py         # Itinerary generation
│   ├── weather_service.py           # OpenWeather integration
│   ├── budget_service.py            # Budget estimation
│   ├── recommendation_service.py   # Destination recommendations
│   ├── memory_service.py            # User preference CRUD
│   └── supervisor_service.py        # Multi-agent orchestration
│
└── agents/                          # Reserved for future agent modules
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Gemini API Key ([Get one here](https://aistudio.google.com/apikey))
- OpenWeather API Key ([Get one here](https://openweathermap.org/appid))

### Setup

```bash
# Clone the repository
git clone https://github.com/gsetia402/travel-ai-platform.git
cd travel-ai-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Run the server
uvicorn main:app --reload --port 8000
```

### Access

- API: http://localhost:8000
- Docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc

---

## Deployment

### Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Render

1. Connect your GitHub repo on [Render](https://render.com)
2. Select **Web Service**
3. Render auto-detects `render.yaml`
4. Add environment variables in Render dashboard:
   - `GEMINI_API_KEY`
   - `OPENWEATHER_API_KEY`
5. Deploy

---

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | `development` or `production` |
| `APP_PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OPENWEATHER_API_KEY` | — | OpenWeather API key |

---

## Future Roadmap

- [ ] Android App (Kotlin/Jetpack Compose)
- [ ] iOS App (Swift/SwiftUI)
- [ ] Web App (React/Next.js)
- [ ] Firebase Authentication
- [ ] LangGraph Integration
- [ ] Hotel Booking Agent
- [ ] Transportation Agent
- [ ] Multi-city Trip Planning
- [ ] Trip History & Analytics

---

## License

This project is open source and available under the [MIT License](LICENSE).
