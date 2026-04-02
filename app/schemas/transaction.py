from enum import Enum
from decimal import Decimal
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionCreate(BaseModel):
    account_id: UUID
    category_id: Optional[UUID] = None
    type: TransactionType
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionUpdate(BaseModel):
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    type: Optional[TransactionType] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    description: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    category_id: Optional[UUID]
    type: TransactionType
    amount: Decimal
    description: Optional[str]
    transaction_date: datetime
    created_at: datetime


class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal

class AccountBalanceItem(BaseModel):
    account_id: UUID
    account_name: str
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class CategorySummaryItem(BaseModel):
    category_id: UUID
    category_name: str
    type: str
    total: Decimal