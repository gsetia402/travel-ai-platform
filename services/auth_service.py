import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import get_db
from models.auth import (
    OrganizationTable,
    UserTable,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    OrganizationResponse,
)

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "tripops-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# --- Register ---

def register_user(db: Session, request: RegisterRequest) -> TokenResponse:
    existing = db.query(UserTable).filter(UserTable.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_count_before = db.query(UserTable).count()
    logger.info(f"[register] user count BEFORE create: {user_count_before}")

    org = OrganizationTable(
        organization_id=str(uuid.uuid4()),
        name=request.organization_name,
        organization_type=request.organization_type.value,
    )
    db.add(org)
    db.flush()

    user = UserTable(
        user_id=str(uuid.uuid4()),
        organization_id=org.organization_id,
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
        password_hash=hash_password(request.password),
        role=request.role.value,
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    # Verify persistence — read back from DB in same session
    user_count_after = db.query(UserTable).count()
    verify = db.query(UserTable).filter(UserTable.user_id == user.user_id).first()
    logger.info(
        f"[register] user count AFTER commit: {user_count_after} | "
        f"verify user_id={user.user_id} exists={verify is not None} | "
        f"email={request.email} | db_bind={db.bind.url.host if hasattr(db.bind.url, 'host') else 'sqlite'}"
    )
    if not verify:
        logger.critical(f"[register] PERSISTENCE FAILURE — user {user.user_id} not found after commit!")

    token = create_access_token(user.user_id, org.organization_id, user.role)
    logger.info(f"Registered user {user.email} in org {org.name}")

    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        organization_id=org.organization_id,
        organization_name=org.name,
    )


# --- Login ---

def login_user(db: Session, request: LoginRequest) -> TokenResponse:
    user = db.query(UserTable).filter(UserTable.email == request.email).first()
    logger.info(
        f"[login] email={request.email} | found={user is not None} | "
        f"db_bind={db.bind.url.host if hasattr(db.bind.url, 'host') else 'sqlite'} | "
        f"total_users={db.query(UserTable).count()}"
    )
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    org = db.query(OrganizationTable).filter(OrganizationTable.organization_id == user.organization_id).first()
    token = create_access_token(user.user_id, user.organization_id, user.role)

    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org.name if org else "",
    )


# --- Get Current User (dependency) ---

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> UserTable:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(UserTable).filter(UserTable.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[UserTable]:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(UserTable).filter(UserTable.user_id == user_id).first()
    except Exception:
        return None


# --- Get User Info ---

def get_me(db: Session, user: UserTable) -> UserResponse:
    org = db.query(OrganizationTable).filter(OrganizationTable.organization_id == user.organization_id).first()
    return UserResponse(
        user_id=user.user_id,
        organization_id=user.organization_id,
        organization_name=org.name if org else "",
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
    )


# --- Seed Demo Data ---

def seed_demo_data(db: Session):
    existing = db.query(UserTable).filter(UserTable.email == "demo@tripops.app").first()
    if existing:
        return

    org = OrganizationTable(
        organization_id=str(uuid.uuid4()),
        name="TripOps Demo Agency",
        organization_type="TRAVEL_AGENCY",
    )
    db.add(org)
    db.flush()

    user = UserTable(
        user_id=str(uuid.uuid4()),
        organization_id=org.organization_id,
        full_name="Demo Coordinator",
        email="demo@tripops.app",
        phone="9999999999",
        password_hash=hash_password("demo123"),
        role="COORDINATOR",
        active=True,
    )
    db.add(user)
    db.commit()
    logger.info("Seeded demo user: demo@tripops.app / demo123")
