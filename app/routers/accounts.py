from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.account import Account
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse, AccountType


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.type in [AccountType.BANK, AccountType.FINANCIAL, AccountType.COOPERATIVE]:
        existing_account = db.execute(
            select(Account).where(
                Account.user_id == current_user.id,
                Account.account_number == data.account_number,
                Account.is_active == True
            )
        ).scalar_one_or_none()

        if existing_account:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una cuenta activa con ese número de cuenta"
            )

    new_account = Account(
        user_id=current_user.id,
        account_name=data.account_name,
        type=data.type.value,
        financial_institution=data.financial_institution,
        account_number=data.account_number
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
        select(Account).where(
            Account.user_id == current_user.id,
            Account.is_active == True
        )
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
            Account.user_id == current_user.id,
            Account.is_active == True
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
            Account.user_id == current_user.id,
            Account.is_active == True
        )
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    new_type = data.type.value if data.type is not None else account.type
    new_account_name = data.account_name if data.account_name is not None else account.account_name
    new_financial_institution = (
        data.financial_institution
        if data.financial_institution is not None
        else account.financial_institution
    )
    new_account_number = (
        data.account_number
        if data.account_number is not None
        else account.account_number
    )

    if new_type in ["bank", "financial", "cooperative"]:
        if not new_financial_institution or not new_account_number:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Para cuentas bancarias, financieras o cooperativas, "
                    "financial_institution y account_number son obligatorios"
                )
            )

        existing_account = db.execute(
            select(Account).where(
                Account.user_id == current_user.id,
                Account.account_number == new_account_number,
                Account.is_active == True,
                Account.id != account_id
            )
        ).scalar_one_or_none()

        if existing_account:
            raise HTTPException(
                status_code=400,
                detail="Ya existe otra cuenta activa con ese número de cuenta"
            )

    elif new_type == "cash":
        new_financial_institution = None
        new_account_number = None

    account.account_name = new_account_name
    account.type = new_type
    account.financial_institution = new_financial_institution
    account.account_number = new_account_number

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
            Account.user_id == current_user.id,
            Account.is_active == True
        )
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    account.is_active = False

    db.commit()
    db.refresh(account)

    return {"message": "Cuenta desactivada correctamente"}