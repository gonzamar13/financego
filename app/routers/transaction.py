from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionSummary,
    AccountBalanceItem,
    CategorySummaryItem,
)
from app.services.transaction_service import (
    create_transaction,
    list_transactions,
    get_transaction,
    update_transaction,
    delete_transaction,
    get_transaction_summary,
    get_account_balances,
    get_category_summary,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse)
def create_transaction_route(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_transaction(db, current_user, data)


@router.get("/", response_model=list[TransactionResponse])
def list_transactions_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_transactions(db, current_user)


@router.get("/summary", response_model=TransactionSummary)
def get_transaction_summary_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transaction_summary(db, current_user)


@router.get("/account-balances", response_model=list[AccountBalanceItem])
def get_account_balances_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_account_balances(db, current_user)


@router.get("/category-summary", response_model=list[CategorySummaryItem])
def get_category_summary_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_category_summary(db, current_user)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_route(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transaction(db, current_user, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction_route(
    transaction_id: UUID,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_transaction(db, current_user, transaction_id, data)


@router.delete("/{transaction_id}")
def delete_transaction_route(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_transaction(db, current_user, transaction_id)
    return {"message": "Transacción eliminada correctamente"}