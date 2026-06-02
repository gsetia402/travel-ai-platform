import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class OrganizationType(str, enum.Enum):
    TRAVEL_AGENCY = "TRAVEL_AGENCY"
    CORPORATE = "CORPORATE"
    SCHOOL = "SCHOOL"
    COLLEGE = "COLLEGE"
    FAMILY_GROUP = "FAMILY_GROUP"


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    COORDINATOR = "COORDINATOR"


# --------------- SQLAlchemy ORM Models ---------------

class OrganizationTable(Base):
    __tablename__ = "organizations"

    organization_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    organization_type = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class UserTable(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="COORDINATOR")
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


# --------------- Pydantic Schemas ---------------

class OrganizationCreateRequest(BaseModel):
    name: str
    organization_type: OrganizationType


class OrganizationResponse(BaseModel):
    organization_id: str
    name: str
    organization_type: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    password: str
    organization_name: str
    organization_type: OrganizationType = OrganizationType.CORPORATE
    role: UserRole = UserRole.COORDINATOR


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    email: str
    role: str
    organization_id: str
    organization_name: str


class UserResponse(BaseModel):
    user_id: str
    organization_id: str
    organization_name: str
    full_name: str
    email: str
    phone: Optional[str] = None
    role: str
    active: bool
    created_at: Optional[datetime] = None
