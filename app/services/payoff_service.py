# Convención: interest_rate en Debt es tasa NOMINAL ANUAL en porcentaje.
# El motor convierte a mensual: monthly_rate = interest_rate / 12 / 100
# Ejemplo: 24% anual → 24 / 12 / 100 = 0.02 (2 % mensual)

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.payoff import PayoffRequest, StrategyType

MAX_MONTHS = 600
ZERO = Decimal("0")
CENT = Decimal("0.01")


@dataclass
class _DebtState:
    debt_id: UUID
    name: str
    debt_type: str          # "loan" | "credit_card"
    balance: Decimal
    annual_rate: Decimal    # porcentaje, ej: 24.000
    installment: Decimal    # cuota fija (loans); 0 para credit_card
    paid_off_month: Optional[int] = None
    paid_off_date: Optional[date] = None
    interest_accrued: Decimal = field(default_factory=lambda: Decimal("0"))

    @property
    def monthly_rate(self) -> Decimal:
        if self.annual_rate is None or self.annual_rate == ZERO:
            return ZERO
        return self.annual_rate / 12 / 100


def _monthly_budget_suggestion(db: Session, user: User) -> Decimal:
    today = date.today()

    income = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user.id,
            Transaction.type == "income",
            extract("year", Transaction.transaction_date) == today.year,
            extract("month", Transaction.transaction_date) == today.month,
        )
    ).scalar_one()

    expense = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user.id,
            Transaction.type == "expense",
            extract("year", Transaction.transaction_date) == today.year,
            extract("month", Transaction.transaction_date) == today.month,
        )
    ).scalar_one()

    result = Decimal(income) - Decimal(expense)
    return result if result > ZERO else ZERO


def _advance_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _month_date(year: int, month: int) -> date:
    last_day = monthrange(year, month)[1]
    return date(year, month, last_day)


def _simulate(
    debts: list[_DebtState],
    monthly_budget: Decimal,
    strategy: StrategyType,
) -> dict:
    today = date.today()
    year, month = today.year, today.month

    snapshots = []
    feasible = True

    for m in range(1, MAX_MONTHS + 1):
        year, month = _advance_month(year, month)
        snapshot_date = _month_date(year, month)

        # Aplicar interés mensual a todas las deudas activas
        for d in debts:
            if d.balance <= ZERO:
                continue
            interest = (d.balance * d.monthly_rate).quantize(CENT, ROUND_HALF_UP)
            d.balance += interest
            d.interest_accrued += interest

        # Primero: cuotas fijas de los préstamos (no negociables)
        budget_left = monthly_budget
        for d in debts:
            if d.balance <= ZERO or d.debt_type != "loan":
                continue
            payment = min(d.installment, d.balance, budget_left)
            d.balance = (d.balance - payment).quantize(CENT, ROUND_HALF_UP)
            budget_left -= payment
            if d.balance <= ZERO:
                d.balance = ZERO
                if d.paid_off_month is None:
                    d.paid_off_month = m
                    d.paid_off_date = snapshot_date

        # Segundo: tarjetas de crédito con el remanente, ordenadas por estrategia
        cards = [d for d in debts if d.debt_type == "credit_card" and d.balance > ZERO]
        if strategy == StrategyType.SNOWBALL:
            cards.sort(key=lambda d: d.balance)
        else:
            cards.sort(key=lambda d: d.annual_rate or ZERO, reverse=True)

        for d in cards:
            if budget_left <= ZERO:
                break
            payment = min(d.balance, budget_left)
            d.balance = (d.balance - payment).quantize(CENT, ROUND_HALF_UP)
            budget_left -= payment
            if d.balance <= ZERO:
                d.balance = ZERO
                if d.paid_off_month is None:
                    d.paid_off_month = m
                    d.paid_off_date = snapshot_date

        total_remaining = sum((d.balance for d in debts), ZERO)
        snapshots.append({
            "month": m,
            "date": snapshot_date,
            "total_remaining": total_remaining.quantize(CENT, ROUND_HALF_UP),
        })

        if total_remaining <= ZERO:
            break

        # Guard de inviabilidad: si llegamos al tope sin saldar
        if m == MAX_MONTHS:
            feasible = False

    debt_free_date = None
    if feasible and snapshots:
        debt_free_date = snapshots[-1]["date"]

    return {
        "feasible": feasible,
        "months": snapshots,
        "debts": [
            {
                "debt_id": d.debt_id,
                "name": d.name,
                "paid_off_month": d.paid_off_month,
                "paid_off_date": d.paid_off_date,
                "total_interest": d.interest_accrued.quantize(CENT, ROUND_HALF_UP),
            }
            for d in debts
        ],
        "debt_free_date": debt_free_date,
        "total_interest": sum(
            (d.interest_accrued for d in debts), ZERO
        ).quantize(CENT, ROUND_HALF_UP),
        "total_months": len(snapshots),
    }


def compute_payoff_plan(
    db: Session,
    user: User,
    request: PayoffRequest,
    enriched_debts: list[dict],
) -> dict:
    suggested_budget = _monthly_budget_suggestion(db, user)
    monthly_budget = (
        request.monthly_budget
        if request.monthly_budget is not None
        else suggested_budget
    )

    active = [d for d in enriched_debts if d["is_active"] and d["remaining_balance"] > ZERO]

    debt_states = [
        _DebtState(
            debt_id=d["id"],
            name=d["name"],
            debt_type=d["type"],
            balance=Decimal(str(d["remaining_balance"])),
            annual_rate=Decimal(str(d["interest_rate"])) if d["interest_rate"] else ZERO,
            installment=Decimal(str(d["installment_amount"])) if d["installment_amount"] else ZERO,
        )
        for d in active
    ]

    result = _simulate(debt_states, monthly_budget, request.strategy)

    return {
        **result,
        "suggested_budget": suggested_budget,
        "monthly_budget": monthly_budget,
    }
