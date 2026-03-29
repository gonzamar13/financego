from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.account import Account
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_account = Account(
        user_id=current_user.id,
        name=data.name,
        type=data.type
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.get("", response_model=List[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.execute(
        select(Account).where(Account.user_id == current_user.id)
    ).scalars().all()

    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    if data.name is not None:
        account.name = data.name

    if data.type is not None:
        account.type = data.type

    if data.is_active is not None:
        account.is_active = data.is_active

    db.commit()
    db.refresh(account)

    return account


@router.delete("/{account_id}")
def delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    account.is_active = False

    db.commit()
    db.refresh(account)

    return {"message": "Cuenta desactivada correctamente"}