import enum
from datetime import date, datetime
from typing import Optional, Dict

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


# --------------- Enums ---------------

class ExpenseCategory(str, enum.Enum):
    HOTEL = "HOTEL"
    TRANSPORT = "TRANSPORT"
    FOOD = "FOOD"
    ACTIVITIES = "ACTIVITIES"
    FLIGHTS = "FLIGHTS"
    INSURANCE = "INSURANCE"
    VISA = "VISA"
    EVENTS = "EVENTS"
    MISCELLANEOUS = "MISCELLANEOUS"


class BudgetStatus(str, enum.Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


# --------------- SQLAlchemy ORM Model ---------------

class ExpenseTable(Base):
    __tablename__ = "expenses"

    expense_id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trips.trip_id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    vendor_name = Column(String, nullable=True)
    paid_by = Column(String, nullable=True)
    expense_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# --------------- Pydantic Request / Response Models ---------------

class ExpenseCreateRequest(BaseModel):
    category: ExpenseCategory
    description: str
    amount: float = Field(gt=0, description="Must be positive")
    vendor_name: Optional[str] = None
    paid_by: Optional[str] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None


class ExpenseUpdateRequest(BaseModel):
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0, description="Must be positive")
    vendor_name: Optional[str] = None
    paid_by: Optional[str] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    expense_id: str
    trip_id: str
    category: str
    description: str
    amount: float
    vendor_name: Optional[str] = None
    paid_by: Optional[str] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FinancialSummaryResponse(BaseModel):
    total_budget: float
    amount_spent: float
    remaining_budget: float
    expense_count: int


class BudgetStatusResponse(BaseModel):
    budget_status: str
    percentage_used: float
