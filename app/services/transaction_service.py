from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def _get_user_account(db: Session, user_id: UUID, account_id: UUID) -> Account:
    account = db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id
        )
    ).scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    return account


def _get_user_category(db: Session, user_id: UUID, category_id: UUID | None) -> Category | None:
    if category_id is None:
        return None

    category = db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id
        )
    ).scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    return category


def create_transaction(db: Session, current_user: User, data: TransactionCreate) -> Transaction:
    _get_user_account(db, current_user.id, data.account_id)
    _get_user_category(db, current_user.id, data.category_id)

    if data.type == "expense" and data.category_id is None:
        raise HTTPException(status_code=400, detail="Un gasto debe tener categoría")

    tx = Transaction(
        user_id=current_user.id,
        account_id=data.account_id,
        category_id=data.category_id,
        type=data.type.value,
        amount=data.amount,
        description=data.description,
        transaction_date=data.transaction_date or datetime.now(timezone.utc)
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def list_transactions(db: Session, current_user: User) -> list[Transaction]:
    transactions = db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    ).scalars().all()

    return list(transactions)


def get_transaction(db: Session, current_user: User, transaction_id: UUID) -> Transaction:
    tx = db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    return tx


def update_transaction(
    db: Session,
    current_user: User,
    transaction_id: UUID,
    data: TransactionUpdate
) -> Transaction:
    tx = get_transaction(db, current_user, transaction_id)

    new_account_id = data.account_id if data.account_id is not None else tx.account_id
    new_category_id = data.category_id if data.category_id is not None else tx.category_id
    new_type = data.type.value if data.type is not None else tx.type
    new_amount = data.amount if data.amount is not None else tx.amount
    new_description = data.description if data.description is not None else tx.description
    new_transaction_date = data.transaction_date if data.transaction_date is not None else tx.transaction_date

    _get_user_account(db, current_user.id, new_account_id)
    _get_user_category(db, current_user.id, new_category_id)

    if new_type == "expense" and new_category_id is None:
        raise HTTPException(status_code=400, detail="Un gasto debe tener categoría")

    tx.account_id = new_account_id
    tx.category_id = new_category_id
    tx.type = new_type
    tx.amount = new_amount
    tx.description = new_description
    tx.transaction_date = new_transaction_date

    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, current_user: User, transaction_id: UUID):
    tx = get_transaction(db, current_user, transaction_id)
    db.delete(tx)
    db.commit()


def get_transaction_summary(db: Session, current_user: User):
    total_income = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "income"
        )
    ).scalar_one()

    total_expense = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense"
        )
    ).scalar_one()

    return {
        "total_income": Decimal(total_income),
        "total_expense": Decimal(total_expense),
        "balance": Decimal(total_income) - Decimal(total_expense)
    }


def get_account_balances(db: Session, current_user: User):
    rows = db.execute(
        select(
            Account.id,
            Account.account_name,
            func.coalesce(
                func.sum(
                    case((Transaction.type == "income", Transaction.amount), else_=0)
                ),
                0
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case((Transaction.type == "expense", Transaction.amount), else_=0)
                ),
                0
            ).label("total_expense")
        )
        .select_from(Account)
        .outerjoin(Transaction, Transaction.account_id == Account.id)
        .where(Account.user_id == current_user.id)
        .group_by(Account.id, Account.account_name)
    ).all()

    result = []
    for row in rows:
        total_income = Decimal(row.total_income)
        total_expense = Decimal(row.total_expense)
        result.append({
            "account_id": row.id,
            "account_name": row.account_name,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense
        })

    return result


def get_category_summary(db: Session, current_user: User):
    rows = db.execute(
        select(
            Category.id,
            Category.name,
            Category.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total")
        )
        .select_from(Category)
        .outerjoin(Transaction, Transaction.category_id == Category.id)
        .where(Category.user_id == current_user.id)
        .group_by(Category.id, Category.name, Category.type)
        .order_by(Category.type, Category.name)
    ).all()

    return [
        {
            "category_id": row.id,
            "category_name": row.name,
            "type": row.type,
            "total": Decimal(row.total)
        }
        for row in rows
    ]