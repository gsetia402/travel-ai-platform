from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from services.auth_service import register_user, login_user, get_current_user, get_me
from models.auth import UserTable

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, request)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, request)


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_me(db, user)
