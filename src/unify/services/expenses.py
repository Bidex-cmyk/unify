from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, col, select

from unify.models import Expense, _utcnow
from unify.schemas import ExpenseCreate, ExpenseUpdate


def list_expenses(
    db: Session,
    *,
    include_deleted: bool = False,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[Expense]:
    statement = select(Expense)
    if not include_deleted:
        statement = statement.where(col(Expense.deleted_at).is_(None))
    if since is not None:
        statement = statement.where(col(Expense.occurred_at) >= since)
    if until is not None:
        statement = statement.where(col(Expense.occurred_at) <= until)
    statement = statement.order_by(col(Expense.occurred_at).desc())
    return list(db.exec(statement).all())


def get_expense(db: Session, expense_id: UUID) -> Expense | None:
    expense = db.get(Expense, expense_id)
    if expense is None or expense.deleted_at is not None:
        return None
    return expense


def create_expense(db: Session, data: ExpenseCreate) -> Expense:
    values = data.model_dump()
    if values["occurred_at"] is None:
        values["occurred_at"] = _utcnow()
    expense = Expense.model_validate(values)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update_expense(db: Session, expense_id: UUID, data: ExpenseUpdate) -> Expense | None:
    expense = get_expense(db, expense_id)
    if expense is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(expense, field, value)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: UUID, *, hard: bool = False) -> bool:
    expense = db.get(Expense, expense_id)
    if expense is None or (expense.deleted_at is not None and not hard):
        return False
    if hard:
        db.delete(expense)
    else:
        expense.deleted_at = datetime.now(UTC)
        db.add(expense)
    db.commit()
    return True


def summary_by_category(db: Session, *, month: str) -> dict[str, int]:
    try:
        start = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError("month must be in YYYY-MM format") from exc
    if start.strftime("%Y-%m") != month:
        raise ValueError("month must be in YYYY-MM format")

    if start.month == 12:
        end = datetime(start.year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(start.year, start.month + 1, 1, tzinfo=UTC)

    statement = select(Expense).where(
        col(Expense.deleted_at).is_(None),
        col(Expense.occurred_at) >= start,
        col(Expense.occurred_at) < end,
    )
    totals: dict[str, int] = {}
    for expense in db.exec(statement).all():
        totals[expense.category] = totals.get(expense.category, 0) + expense.amount_minor
    return totals
