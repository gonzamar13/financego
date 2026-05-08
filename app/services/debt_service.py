from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.debt import Debt
from app.models.debt_payment import DebtPayment
from app.models.user import User
from app.schemas.debt import DebtCreate, DebtPaymentCreate, DebtUpdate


def _get_user_debt(db: Session, user_id: UUID, debt_id: UUID) -> Debt:
    debt = db.execute(
        select(Debt).where(Debt.id == debt_id, Debt.user_id == user_id)
    ).scalar_one_or_none()
    if not debt:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    return debt


def _compute_next_due_date(debt: Debt, total_paid: Decimal) -> Optional[date]:
    """Calcula la próxima fecha de vencimiento aproximada.

    Para préstamos: si quedan cuotas y hay due_day, próximo mes desde hoy.
    Para tarjetas: el próximo due_day futuro.
    """
    if debt.due_day is None:
        return None
    if not debt.is_active:
        return None
    if total_paid >= debt.principal_amount and debt.type == "loan":
        return None

    today = date.today()
    year = today.year
    month = today.month
    # si ya pasó el due_day este mes, ir al siguiente
    if today.day > debt.due_day:
        month += 1
        if month > 12:
            month = 1
            year += 1
    try:
        return date(year, month, debt.due_day)
    except ValueError:
        # día inexistente (ej: 31 en febrero) — usar último día del mes
        from calendar import monthrange
        last_day = monthrange(year, month)[1]
        return date(year, month, min(debt.due_day, last_day))


def _enrich_debt(db: Session, debt: Debt) -> dict:
    total_paid = db.execute(
        select(func.coalesce(func.sum(DebtPayment.amount), 0))
        .where(DebtPayment.debt_id == debt.id)
    ).scalar_one()
    total_paid = Decimal(total_paid)

    installments_paid = db.execute(
        select(func.count(DebtPayment.id))
        .where(DebtPayment.debt_id == debt.id)
    ).scalar_one() or 0

    remaining = debt.principal_amount - total_paid
    if remaining < 0:
        remaining = Decimal(0)

    progress = 0.0
    if debt.principal_amount and debt.principal_amount > 0:
        progress = float(min(total_paid / debt.principal_amount, Decimal(1))) * 100

    return {
        "id": debt.id,
        "user_id": debt.user_id,
        "name": debt.name,
        "type": debt.type,
        "lender": debt.lender,
        "principal_amount": debt.principal_amount,
        "interest_rate": debt.interest_rate,
        "total_installments": debt.total_installments,
        "installment_amount": debt.installment_amount,
        "start_date": debt.start_date,
        "due_day": debt.due_day,
        "is_active": debt.is_active,
        "created_at": debt.created_at,
        "total_paid": total_paid,
        "remaining_balance": remaining,
        "installments_paid": int(installments_paid),
        "next_due_date": _compute_next_due_date(debt, total_paid),
        "progress_percent": round(progress, 2),
    }


def create_debt(db: Session, current_user: User, data: DebtCreate) -> dict:
    debt = Debt(
        user_id=current_user.id,
        name=data.name,
        type=data.type.value,
        lender=data.lender,
        principal_amount=data.principal_amount,
        interest_rate=data.interest_rate,
        total_installments=data.total_installments,
        installment_amount=data.installment_amount,
        start_date=data.start_date,
        due_day=data.due_day,
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return _enrich_debt(db, debt)


def list_debts(db: Session, current_user: User) -> list[dict]:
    debts = db.execute(
        select(Debt)
        .where(Debt.user_id == current_user.id)
        .order_by(Debt.is_active.desc(), Debt.created_at.desc())
    ).scalars().all()
    return [_enrich_debt(db, d) for d in debts]


def get_debt(db: Session, current_user: User, debt_id: UUID) -> dict:
    debt = _get_user_debt(db, current_user.id, debt_id)
    return _enrich_debt(db, debt)


def update_debt(db: Session, current_user: User, debt_id: UUID, data: DebtUpdate) -> dict:
    debt = _get_user_debt(db, current_user.id, debt_id)

    if data.name is not None:
        debt.name = data.name
    if data.type is not None:
        debt.type = data.type.value
    if data.lender is not None:
        debt.lender = data.lender
    if data.principal_amount is not None:
        debt.principal_amount = data.principal_amount
    if data.interest_rate is not None:
        debt.interest_rate = data.interest_rate
    if data.total_installments is not None:
        debt.total_installments = data.total_installments
    if data.installment_amount is not None:
        debt.installment_amount = data.installment_amount
    if data.start_date is not None:
        debt.start_date = data.start_date
    if data.due_day is not None:
        debt.due_day = data.due_day
    if data.is_active is not None:
        debt.is_active = data.is_active

    db.commit()
    db.refresh(debt)
    return _enrich_debt(db, debt)


def delete_debt(db: Session, current_user: User, debt_id: UUID):
    debt = _get_user_debt(db, current_user.id, debt_id)
    db.delete(debt)
    db.commit()


# Pagos

def create_payment(
    db: Session,
    current_user: User,
    debt_id: UUID,
    data: DebtPaymentCreate,
) -> DebtPayment:
    debt = _get_user_debt(db, current_user.id, debt_id)
    if not debt.is_active:
        raise HTTPException(status_code=400, detail="La deuda no está activa")

    payment = DebtPayment(
        user_id=current_user.id,
        debt_id=debt.id,
        amount=data.amount,
        payment_date=data.payment_date or datetime.now(timezone.utc),
        installment_number=data.installment_number,
        notes=data.notes,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def list_payments(db: Session, current_user: User, debt_id: UUID) -> list[DebtPayment]:
    _get_user_debt(db, current_user.id, debt_id)
    payments = db.execute(
        select(DebtPayment)
        .where(DebtPayment.debt_id == debt_id)
        .order_by(DebtPayment.payment_date.desc())
    ).scalars().all()
    return list(payments)


def delete_payment(db: Session, current_user: User, debt_id: UUID, payment_id: UUID):
    _get_user_debt(db, current_user.id, debt_id)
    payment = db.execute(
        select(DebtPayment).where(
            DebtPayment.id == payment_id,
            DebtPayment.debt_id == debt_id,
        )
    ).scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    db.delete(payment)
    db.commit()


def get_summary(db: Session, current_user: User) -> dict:
    debts = db.execute(
        select(Debt).where(Debt.user_id == current_user.id, Debt.is_active == True)
    ).scalars().all()

    total_principal = Decimal(0)
    total_paid = Decimal(0)
    overdue = 0
    today = date.today()

    for d in debts:
        paid = Decimal(
            db.execute(
                select(func.coalesce(func.sum(DebtPayment.amount), 0))
                .where(DebtPayment.debt_id == d.id)
            ).scalar_one()
        )
        total_principal += d.principal_amount
        total_paid += paid

        next_due = _compute_next_due_date(d, paid)
        if next_due and next_due < today:
            overdue += 1

    total_remaining = total_principal - total_paid
    if total_remaining < 0:
        total_remaining = Decimal(0)

    return {
        "total_principal": total_principal,
        "total_paid": total_paid,
        "total_remaining": total_remaining,
        "active_debts": len(debts),
        "overdue_debts": overdue,
    }
