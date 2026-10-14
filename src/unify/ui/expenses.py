from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from sqlmodel import Session
from starlette.responses import HTMLResponse

from unify.db import get_session
from unify.schemas import ExpenseCreate
from unify.services import expenses
from unify.ui.auth import require_ui_session
from unify.ui.templating import templates

router = APIRouter(
    prefix="/ui/expenses",
    tags=["ui"],
    dependencies=[Depends(require_ui_session)],
)


def _money_display(amount_minor: int) -> str:
    units, cents = divmod(amount_minor, 100)
    return f"{units}.{cents:02d}"


def _month_bounds(now: datetime) -> tuple[str, datetime, datetime]:
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
    if now.month == 12:
        month_end = datetime(now.year + 1, 1, 1, tzinfo=UTC)
    else:
        month_end = datetime(now.year, now.month + 1, 1, tzinfo=UTC)
    return now.strftime("%Y-%m"), month_start, month_end


@router.get("")
def list_expenses_ui(
    request: Request,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    month, since, end = _month_bounds(datetime.now(UTC))
    until = end.replace(microsecond=0)
    month_expenses = [
        expense
        for expense in expenses.list_expenses(db, since=since, until=until)
        if expense.occurred_at < end
    ]
    summary = expenses.summary_by_category(db, month=month)
    total_minor = sum(summary.values())
    max_value = max(summary.values(), default=0)
    chart_rows = [
        (
            category,
            amount,
            f"{amount * 1000 // max_value // 10}.{amount * 1000 // max_value % 10}",
            _money_display(amount),
        )
        for category, amount in summary.items()
        if max_value > 0
    ]
    currency = month_expenses[0].currency if month_expenses else "USD"
    return templates.TemplateResponse(
        request=request,
        name="expenses.html",
        context={
            "expenses": month_expenses,
            "summary": summary,
            "total_minor": total_minor,
            "total_display": _money_display(total_minor),
            "chart_rows": chart_rows,
            "month": month,
            "currency": currency,
        },
    )


@router.post("")
def create_expense_ui(
    request: Request,
    amount: str = Form(""),
    currency: str = Form("USD"),
    category: str = Form("uncategorized"),
    note: str = Form(""),
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    try:
        amount_minor = int((Decimal(amount) * 100).quantize(Decimal("1")))
        if amount_minor <= 0:
            raise ValueError("Amount must be greater than zero")
        data = ExpenseCreate(
            amount_minor=amount_minor,
            currency=currency,
            category=category or "uncategorized",
            note=note,
        )
    except (InvalidOperation, ValueError):
        return HTMLResponse(
            '<p class="error">Enter a valid amount greater than zero.</p>',
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    expense = expenses.create_expense(db, data)
    return templates.TemplateResponse(
        request=request,
        name="partials/_expense_row.html",
        context={"expense": expense, "expense_display": _money_display(expense.amount_minor)},
        headers={"HX-Retarget": "#expenses-list", "HX-Reswap": "afterbegin"},
    )


@router.delete("/{expense_id}")
def delete_expense_ui(
    expense_id: UUID,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not expenses.delete_expense(db, expense_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return Response(status_code=status.HTTP_200_OK)
