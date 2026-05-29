from typing import Optional

from pydantic import BaseModel


class BudgetRequest(BaseModel):
    destination: str
    days: int
    budget: int
    trip_type: Optional[str] = None
    accommodation: Optional[str] = None


class CostBreakdown(BaseModel):
    stay: int
    food: int
    local_transport: int
    activities: int
    miscellaneous: int
    total: int


class BudgetEstimation(BaseModel):
    currency: str = "INR"
    cost_breakdown: CostBreakdown
    budget_status: str


class BudgetResponse(BaseModel):
    destination: str
    days: int
    currency: str = "INR"
    cost_breakdown: CostBreakdown
    budget_status: str
