from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.debt import (
    DebtCreate,
    DebtPaymentCreate,
    DebtPaymentResponse,
    DebtResponse,
    DebtSummary,
    DebtUpdate,
)
from app.services.debt_service import (
    create_debt,
    create_payment,
    delete_debt,
    delete_payment,
    get_debt,
    get_summary,
    list_debts,
    list_payments,
    update_debt,
)

router = APIRouter(prefix="/debts", tags=["debts"])


@router.post("", response_model=DebtResponse)
def create_debt_route(
    data: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_debt(db, current_user, data)


@router.get("", response_model=list[DebtResponse])
def list_debts_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_debts(db, current_user)


@router.get("/summary", response_model=DebtSummary)
def summary_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_summary(db, current_user)


@router.get("/{debt_id}", response_model=DebtResponse)
def get_debt_route(
    debt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_debt(db, current_user, debt_id)


@router.put("/{debt_id}", response_model=DebtResponse)
def update_debt_route(
    debt_id: UUID,
    data: DebtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_debt(db, current_user, debt_id, data)


@router.delete("/{debt_id}")
def delete_debt_route(
    debt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_debt(db, current_user, debt_id)
    return {"message": "Deuda eliminada correctamente"}


# Pagos

@router.post("/{debt_id}/payments", response_model=DebtPaymentResponse)
def create_payment_route(
    debt_id: UUID,
    data: DebtPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_payment(db, current_user, debt_id, data)


@router.get("/{debt_id}/payments", response_model=list[DebtPaymentResponse])
def list_payments_route(
    debt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_payments(db, current_user, debt_id)


@router.delete("/{debt_id}/payments/{payment_id}")
def delete_payment_route(
    debt_id: UUID,
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_payment(db, current_user, debt_id, payment_id)
    return {"message": "Pago eliminado correctamente"}
