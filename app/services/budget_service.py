from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate


def _get_user_budget(db: Session, user_id: UUID, budget_id: UUID) -> Budget:
    budget = db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    ).scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return budget


def _get_user_category(db: Session, user_id: UUID, category_id: UUID) -> Category:
    category = db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    ).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


def _spent_in_period(
    db: Session, user_id: UUID, category_id: UUID, year: int, month: int
) -> Decimal:
    total = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.type == "expense",
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
    ).scalar_one()
    return Decimal(total)


def _enrich_budget(db: Session, budget: Budget, category: Category | None = None) -> dict:
    if category is None:
        category = db.execute(
            select(Category).where(Category.id == budget.category_id)
        ).scalar_one()

    spent = _spent_in_period(
        db, budget.user_id, budget.category_id, budget.year, budget.month
    )
    remaining = budget.amount - spent
    progress = 0.0
    if budget.amount and budget.amount > 0:
        progress = float(spent / budget.amount) * 100

    if progress >= 100:
        status = "exceeded"
    elif progress >= budget.alert_threshold:
        status = "warning"
    else:
        status = "ok"

    return {
        "id": budget.id,
        "user_id": budget.user_id,
        "category_id": budget.category_id,
        "category_name": category.name,
        "year": budget.year,
        "month": budget.month,
        "amount": budget.amount,
        "alert_threshold": budget.alert_threshold,
        "created_at": budget.created_at,
        "spent": spent,
        "remaining": remaining,
        "progress_percent": round(progress, 2),
        "status": status,
    }


def create_budget(db: Session, current_user: User, data: BudgetCreate) -> dict:
    category = _get_user_category(db, current_user.id, data.category_id)
    if category.type != "expense":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden definir presupuestos sobre categorías de gasto",
        )

    existing = db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.category_id == data.category_id,
            Budget.year == data.year,
            Budget.month == data.month,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un presupuesto para esa categoría en ese período",
        )

    budget = Budget(
        user_id=current_user.id,
        category_id=data.category_id,
        year=data.year,
        month=data.month,
        amount=data.amount,
        alert_threshold=data.alert_threshold,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return _enrich_budget(db, budget, category)


def list_budgets(
    db: Session,
    current_user: User,
    year: int | None = None,
    month: int | None = None,
) -> list[dict]:
    stmt = select(Budget).where(Budget.user_id == current_user.id)
    if year is not None:
        stmt = stmt.where(Budget.year == year)
    if month is not None:
        stmt = stmt.where(Budget.month == month)
    stmt = stmt.order_by(Budget.year.desc(), Budget.month.desc())

    budgets = db.execute(stmt).scalars().all()
    return [_enrich_budget(db, b) for b in budgets]


def update_budget(
    db: Session, current_user: User, budget_id: UUID, data: BudgetUpdate
) -> dict:
    budget = _get_user_budget(db, current_user.id, budget_id)

    if data.amount is not None:
        budget.amount = data.amount
    if data.alert_threshold is not None:
        budget.alert_threshold = data.alert_threshold

    db.commit()
    db.refresh(budget)
    return _enrich_budget(db, budget)


def delete_budget(db: Session, current_user: User, budget_id: UUID):
    budget = _get_user_budget(db, current_user.id, budget_id)
    db.delete(budget)
    db.commit()


def list_alerts(db: Session, current_user: User) -> list[dict]:
    """Lista presupuestos del mes actual en estado warning o exceeded."""
    from datetime import date

    today = date.today()
    budgets = db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.year == today.year,
            Budget.month == today.month,
        )
    ).scalars().all()

    alerts: list[dict] = []
    for b in budgets:
        enriched = _enrich_budget(db, b)
        if enriched["status"] in ("warning", "exceeded"):
            if enriched["status"] == "exceeded":
                msg = (
                    f"Sobreconsumo en {enriched['category_name']}: "
                    f"superaste el presupuesto en "
                    f"{round(enriched['progress_percent'] - 100, 1)}%"
                )
            else:
                msg = (
                    f"Atención: ya usaste {round(enriched['progress_percent'], 1)}% "
                    f"del presupuesto de {enriched['category_name']}"
                )
            alerts.append({
                "budget_id": enriched["id"],
                "category_id": enriched["category_id"],
                "category_name": enriched["category_name"],
                "year": enriched["year"],
                "month": enriched["month"],
                "amount": enriched["amount"],
                "spent": enriched["spent"],
                "progress_percent": enriched["progress_percent"],
                "status": enriched["status"],
                "message": msg,
            })

    return alerts
