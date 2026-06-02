from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import APP_VERSION, APP_TITLE, APP_ENV, CORS_ORIGINS, setup_logging
from database import get_db, create_tables
from models.itinerary import ItineraryRequest, ItineraryResponse
from models.weather import WeatherRequest, WeatherResponse
from models.trip import TripPlanRequest, TripPlanResponse
from models.user_preference import UserPreferenceRequest, UserPreferenceResponse, MemorySaveResponse
from services.itinerary_service import generate_itinerary
from services.weather_service import get_weather
from services.supervisor_service import plan_trip
from services.memory_service import save_preferences, get_preferences
from models.recommendation import RecommendationRequest, RecommendationResponse
from services.recommendation_service import get_recommendations
from models.budget import BudgetRequest, BudgetResponse
from services.budget_service import estimate_budget
from routes.trip_routes import router as trip_router
from routes.traveller_routes import router as traveller_router
from routes.room_routes import router as room_router
from routes.profile_routes import router as profile_router
from routes.consent_routes import router as consent_router
from routes.expense_routes import router as expense_router
from routes.communication_routes import router as communication_router
from routes.registration_routes import router as registration_router
from routes.document_routes import router as document_router
from routes.auth_routes import router as auth_router
from routes.itinerary_routes import router as itinerary_router

setup_logging()

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.include_router(trip_router)
app.include_router(traveller_router)
app.include_router(room_router)
app.include_router(profile_router)
app.include_router(consent_router)
app.include_router(expense_router)
app.include_router(communication_router)
app.include_router(registration_router)
app.include_router(document_router)
app.include_router(auth_router)
app.include_router(itinerary_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_tables()
    from services.auth_service import seed_demo_data
    from database import SessionLocal
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "app": "Travel AI Platform",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "UP",
        "version": APP_VERSION,
        "environment": APP_ENV,
    }


@app.post("/itinerary", response_model=ItineraryResponse)
def create_itinerary(request: ItineraryRequest):
    return generate_itinerary(request)


@app.post("/weather", response_model=WeatherResponse)
def fetch_weather(request: WeatherRequest):
    try:
        return get_weather(request)
    except ValueError as e:
        return WeatherResponse(
            destination=request.destination,
            temperature=0,
            condition="Unknown",
            recommendation=str(e),
        )


@app.post("/plan-trip", response_model=TripPlanResponse)
def create_trip_plan(request: TripPlanRequest):
    return plan_trip(request)


@app.post("/memory/save", response_model=MemorySaveResponse)
def save_user_preferences(request: UserPreferenceRequest, db: Session = Depends(get_db)):
    try:
        return save_preferences(db, request)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/{user_id}", response_model=UserPreferenceResponse)
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    try:
        result = get_preferences(db, user_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No preferences found for user: {user_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=RecommendationResponse)
def recommend_destinations(request: RecommendationRequest):
    try:
        return get_recommendations(request)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/budget", response_model=BudgetResponse)
def get_budget_estimate(request: BudgetRequest):
    try:
        return estimate_budget(request)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
