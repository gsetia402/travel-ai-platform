import logging
from typing import List, Dict

from sqlalchemy.orm import Session

from models.expense import (
    ExpenseCreateRequest,
    ExpenseUpdateRequest,
    ExpenseResponse,
    FinancialSummaryResponse,
    BudgetStatusResponse,
    BudgetStatus,
)
from repositories.expense_repository import (
    create_expense,
    get_expense_by_id,
    get_expenses_by_trip,
    update_expense,
    delete_expense,
    sum_expenses_by_trip,
    count_expenses_by_trip,
    expense_breakdown_by_trip,
)
from repositories.trip_repository import get_trip_by_id
from services.storage_provider import get_storage_provider, _content_type_from_filename

logger = logging.getLogger(__name__)


def add_expense(db: Session, trip_id: str, request: ExpenseCreateRequest) -> ExpenseResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    expense = create_expense(
        db,
        trip_id=trip_id,
        category=request.category.value,
        description=request.description,
        amount=request.amount,
        vendor_name=request.vendor_name,
        paid_by=request.paid_by,
        expense_date=request.expense_date,
        notes=request.notes,
    )
    return ExpenseResponse.model_validate(expense)


def list_expenses(db: Session, trip_id: str) -> List[ExpenseResponse]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")
    expenses = get_expenses_by_trip(db, trip_id)
    return [ExpenseResponse.model_validate(e) for e in expenses]


def get_expense(db: Session, expense_id: str) -> ExpenseResponse:
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        raise ValueError(f"Expense not found: {expense_id}")
    return ExpenseResponse.model_validate(expense)


def modify_expense(db: Session, expense_id: str, request: ExpenseUpdateRequest) -> ExpenseResponse:
    existing = get_expense_by_id(db, expense_id)
    if not existing:
        raise ValueError(f"Expense not found: {expense_id}")

    update_data = request.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].value

    expense = update_expense(db, expense_id, update_data)
    return ExpenseResponse.model_validate(expense)


def remove_expense(db: Session, expense_id: str) -> bool:
    deleted = delete_expense(db, expense_id)
    if not deleted:
        raise ValueError(f"Expense not found: {expense_id}")
    return True


def get_financial_summary(db: Session, trip_id: str) -> FinancialSummaryResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    total_budget = trip.budget
    amount_spent = sum_expenses_by_trip(db, trip_id)
    expense_count = count_expenses_by_trip(db, trip_id)
    breakdown = expense_breakdown_by_trip(db, trip_id)

    expenses = get_expenses_by_trip(db, trip_id)
    largest = max((e.amount for e in expenses), default=0.0)
    avg = amount_spent / expense_count if expense_count > 0 else 0.0
    utilization = round((amount_spent / total_budget) * 100, 1) if total_budget > 0 else 0.0

    return FinancialSummaryResponse(
        total_budget=total_budget,
        amount_spent=amount_spent,
        remaining_budget=total_budget - amount_spent,
        expense_count=expense_count,
        utilization_pct=utilization,
        average_expense=round(avg, 2),
        largest_expense=largest,
        category_breakdown=breakdown,
    )


def get_expense_breakdown(db: Session, trip_id: str) -> Dict[str, float]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")
    return expense_breakdown_by_trip(db, trip_id)


def upload_receipt(db: Session, expense_id: str, file_name: str, file_content: bytes) -> ExpenseResponse:
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        raise ValueError(f"Expense not found: {expense_id}")

    storage = get_storage_provider()
    content_type = _content_type_from_filename(file_name)
    key = f"receipts/{expense.trip_id}/{expense_id}/{file_name}"
    storage.upload(key, file_content, content_type)

    updated = update_expense(db, expense_id, {"receipt_path": key})
    return ExpenseResponse.model_validate(updated)


def get_budget_status(db: Session, trip_id: str) -> BudgetStatusResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    total_budget = trip.budget
    amount_spent = sum_expenses_by_trip(db, trip_id)

    if total_budget <= 0:
        percentage = 100.0 if amount_spent > 0 else 0.0
    else:
        percentage = round((amount_spent / total_budget) * 100, 2)

    if percentage > 100:
        status = BudgetStatus.RED
    elif percentage >= 80:
        status = BudgetStatus.AMBER
    else:
        status = BudgetStatus.GREEN

    return BudgetStatusResponse(
        budget_status=status.value,
        percentage_used=percentage,
    )
