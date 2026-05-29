# Release Notes

## v1.0.0 — Phase 1 Release

**Release Date:** May 2026

---

### Features

- **Memory Agent** — Store and retrieve user travel preferences (SQLite + SQLAlchemy)
- **Recommendation Agent** — AI-powered destination suggestions based on preferences, season, and duration
- **Weather Agent** — Real-time weather data via OpenWeather API
- **Budget Agent** — AI-estimated trip cost breakdown with budget status
- **Itinerary Agent** — Personalized day-wise itinerary generation via Google Gemini
- **Supervisor Agent** — Multi-agent orchestration for unified trip planning

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with version & environment |
| POST | `/memory/save` | Save user preferences |
| GET | `/memory/{user_id}` | Retrieve user preferences |
| POST | `/recommend` | Get destination recommendations |
| POST | `/weather` | Get weather for a destination |
| POST | `/budget` | Get budget estimation |
| POST | `/itinerary` | Generate itinerary |
| POST | `/plan-trip` | Full trip planning (Supervisor) |

### Infrastructure

- CORS support for frontend integration
- Environment-based configuration (development/production)
- Centralized config management
- Structured logging
- Docker & Docker Compose support
- Render deployment ready
- Graceful error handling across all agents

### Tech Stack

- FastAPI 0.115
- Google Gemini (gemini-2.5-flash)
- OpenWeather API
- SQLite + SQLAlchemy 2.0
- Pydantic v2
- Python 3.11+

---

### Known Limitations

- SQLite is not recommended for high-concurrency production use
- No authentication (planned for v2.0)
- Single-region deployment

---

### Upgrade Notes

First release — no upgrade path required.
