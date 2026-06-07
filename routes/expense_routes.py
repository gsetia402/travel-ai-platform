from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import TripTable
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
    upload_receipt,
)
from services.auth_service import get_current_user
from dependencies import require_trip_access

router = APIRouter(tags=["Expenses"])


@router.post("/trips/{trip_id}/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(trip_id: str, request: ExpenseCreateRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return add_expense(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/expenses", response_model=List[ExpenseResponse])
def get_expenses(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return list_expenses(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense_detail(expense_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return get_expense(db, expense_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: str, request: ExpenseUpdateRequest, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return modify_expense(db, expense_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/expenses/{expense_id}", status_code=200)
def delete_expense(expense_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        remove_expense(db, expense_id)
        return {"message": f"Expense {expense_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/financial-summary", response_model=FinancialSummaryResponse)
def financial_summary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_financial_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/expense-breakdown", response_model=Dict[str, float])
def expense_breakdown(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_expense_breakdown(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/budget-status", response_model=BudgetStatusResponse)
def budget_status(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_budget_status(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/expenses/{expense_id}/receipt", response_model=ExpenseResponse)
async def upload_expense_receipt(expense_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    allowed = (".pdf", ".jpg", ".jpeg", ".png")
    if not any(file.filename.lower().endswith(ext) for ext in allowed):
        raise HTTPException(status_code=400, detail="Only PDF, JPG, and PNG files are accepted.")
    try:
        content = await file.read()
        return upload_receipt(db, expense_id, file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/expenses/{expense_id}/receipt")
def download_receipt(expense_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    from services.storage_provider import get_storage_provider, _content_type_from_filename
    from repositories.expense_repository import get_expense_by_id as get_exp
    expense = get_exp(db, expense_id)
    if not expense or not expense.receipt_path:
        raise HTTPException(status_code=404, detail="Receipt not found")
    storage = get_storage_provider()
    data = storage.download(expense.receipt_path)
    ct = _content_type_from_filename(expense.receipt_path)
    filename = expense.receipt_path.rsplit("/", 1)[-1]
    return StreamingResponse(
        iter([data]),
        media_type=ct,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
