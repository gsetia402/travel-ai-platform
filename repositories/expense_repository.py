import uuid
import logging
from typing import List, Optional, Dict

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from models.expense import ExpenseTable

logger = logging.getLogger(__name__)


def create_expense(db: Session, trip_id: str, **kwargs) -> ExpenseTable:
    expense = ExpenseTable(
        expense_id=str(uuid.uuid4()),
        trip_id=trip_id,
        **kwargs,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    logger.info(f"Created expense {expense.expense_id} for trip {trip_id}")
    return expense


def get_expense_by_id(db: Session, expense_id: str) -> Optional[ExpenseTable]:
    return db.query(ExpenseTable).filter(ExpenseTable.expense_id == expense_id).first()


def get_expenses_by_trip(db: Session, trip_id: str) -> List[ExpenseTable]:
    return (
        db.query(ExpenseTable)
        .filter(ExpenseTable.trip_id == trip_id)
        .order_by(ExpenseTable.created_at.desc())
        .all()
    )


def update_expense(db: Session, expense_id: str, update_data: dict) -> Optional[ExpenseTable]:
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        return None
    for field, value in update_data.items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    logger.info(f"Updated expense: {expense_id}")
    return expense


def delete_expense(db: Session, expense_id: str) -> bool:
    expense = get_expense_by_id(db, expense_id)
    if not expense:
        return False
    db.delete(expense)
    db.commit()
    logger.info(f"Deleted expense: {expense_id}")
    return True


def sum_expenses_by_trip(db: Session, trip_id: str) -> float:
    result = (
        db.query(sa_func.coalesce(sa_func.sum(ExpenseTable.amount), 0.0))
        .filter(ExpenseTable.trip_id == trip_id)
        .scalar()
    )
    return float(result)


def count_expenses_by_trip(db: Session, trip_id: str) -> int:
    return db.query(ExpenseTable).filter(ExpenseTable.trip_id == trip_id).count()


def expense_breakdown_by_trip(db: Session, trip_id: str) -> Dict[str, float]:
    rows = (
        db.query(ExpenseTable.category, sa_func.sum(ExpenseTable.amount))
        .filter(ExpenseTable.trip_id == trip_id)
        .group_by(ExpenseTable.category)
        .all()
    )
    return {cat: float(total) for cat, total in rows}
