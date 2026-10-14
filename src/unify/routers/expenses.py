from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from unify.db import get_session
from unify.models import Expense
from unify.schemas import ExpenseCreate, ExpenseRead, ExpenseUpdate
from unify.services import expenses

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseRead])
def list_expenses(
    include_deleted: bool = False,
    since: datetime | None = None,
    until: datetime | None = None,
    db: Session = Depends(get_session),  # noqa: B008
) -> list[Expense]:
    return expenses.list_expenses(
        db,
        include_deleted=include_deleted,
        since=since,
        until=until,
    )


@router.get("/summary")
def expense_summary(
    month: str,
    db: Session = Depends(get_session),  # noqa: B008
) -> dict[str, object]:
    try:
        totals = expenses.summary_by_category(db, month=month)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"month": month, "total_minor": sum(totals.values()), "by_category": totals}


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(
    expense_id: UUID,
    db: Session = Depends(get_session),  # noqa: B008
) -> Expense:
    expense = expenses.get_expense(db, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_session),  # noqa: B008
) -> Expense:
    return expenses.create_expense(db, data)


@router.patch("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: UUID,
    data: ExpenseUpdate,
    db: Session = Depends(get_session),  # noqa: B008
) -> Expense:
    expense = expenses.update_expense(db, expense_id, data)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: UUID,
    hard: bool = False,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not expenses.delete_expense(db, expense_id, hard=hard):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
