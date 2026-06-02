from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.expense import (
    ExpenseCreateRequest,
    ExpenseUpdateRequest,
    ExpenseResponse,
    FinancialSummaryResponse,
    BudgetStatusResponse,
)
from services.expense_service import (
    add_expense,
    list_expenses,
    get_expense,
    modify_expense,
    remove_expense,
    get_financial_summary,
    get_expense_breakdown,
    get_budget_status,
)

router = APIRouter(tags=["Expenses"])


@router.post("/trips/{trip_id}/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(trip_id: str, request: ExpenseCreateRequest, db: Session = Depends(get_db)):
    try:
        return add_expense(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/expenses", response_model=List[ExpenseResponse])
def get_expenses(trip_id: str, db: Session = Depends(get_db)):
    try:
        return list_expenses(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense_detail(expense_id: str, db: Session = Depends(get_db)):
    try:
        return get_expense(db, expense_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: str, request: ExpenseUpdateRequest, db: Session = Depends(get_db)):
    try:
        return modify_expense(db, expense_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/expenses/{expense_id}", status_code=200)
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    try:
        remove_expense(db, expense_id)
        return {"message": f"Expense {expense_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/financial-summary", response_model=FinancialSummaryResponse)
def financial_summary(trip_id: str, db: Session = Depends(get_db)):
    try:
        return get_financial_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/expense-breakdown", response_model=Dict[str, float])
def expense_breakdown(trip_id: str, db: Session = Depends(get_db)):
    try:
        return get_expense_breakdown(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/budget-status", response_model=BudgetStatusResponse)
def budget_status(trip_id: str, db: Session = Depends(get_db)):
    try:
        return get_budget_status(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
