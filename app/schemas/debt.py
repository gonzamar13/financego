from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DebtType(str, Enum):
    LOAN = "loan"
    CREDIT_CARD = "credit_card"


class DebtCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: DebtType
    lender: Optional[str] = Field(default=None, max_length=120)
    principal_amount: Decimal = Field(gt=0)
    interest_rate: Optional[Decimal] = Field(default=None, ge=0, le=999)
    total_installments: Optional[int] = Field(default=None, ge=1, le=600)
    installment_amount: Optional[Decimal] = Field(default=None, gt=0)
    start_date: date
    due_day: Optional[int] = Field(default=None, ge=1, le=31)


class DebtUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    type: Optional[DebtType] = None
    lender: Optional[str] = Field(default=None, max_length=120)
    principal_amount: Optional[Decimal] = Field(default=None, gt=0)
    interest_rate: Optional[Decimal] = Field(default=None, ge=0, le=999)
    total_installments: Optional[int] = Field(default=None, ge=1, le=600)
    installment_amount: Optional[Decimal] = Field(default=None, gt=0)
    start_date: Optional[date] = None
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
    is_active: Optional[bool] = None


class DebtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    type: DebtType
    lender: Optional[str]
    principal_amount: Decimal
    interest_rate: Optional[Decimal]
    total_installments: Optional[int]
    installment_amount: Optional[Decimal]
    start_date: date
    due_day: Optional[int]
    is_active: bool
    created_at: datetime

    # Campos derivados (calculados en el service)
    total_paid: Decimal
    remaining_balance: Decimal
    installments_paid: int
    next_due_date: Optional[date] = None
    progress_percent: float


class DebtPaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_date: Optional[datetime] = None
    installment_number: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=255)


class DebtPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    debt_id: UUID
    user_id: UUID
    amount: Decimal
    payment_date: datetime
    installment_number: Optional[int]
    notes: Optional[str]
    created_at: datetime


class DebtSummary(BaseModel):
    total_principal: Decimal
    total_paid: Decimal
    total_remaining: Decimal
    active_debts: int
    overdue_debts: int
