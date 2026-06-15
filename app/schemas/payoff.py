from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    SNOWBALL = "snowball"      # menor saldo primero
    AVALANCHE = "avalanche"    # mayor tasa anual primero


class PayoffRequest(BaseModel):
    monthly_budget: Optional[Decimal] = Field(default=None, gt=0)
    strategy: StrategyType = StrategyType.AVALANCHE


class MonthPaymentDetail(BaseModel):
    debt_id: UUID
    name: str
    paid: Decimal
    remaining: Decimal


class MonthSnapshot(BaseModel):
    month: int
    date: date
    total_remaining: Decimal
    payments: list[MonthPaymentDetail]


class DebtPayoffDetail(BaseModel):
    debt_id: UUID
    name: str
    paid_off_month: Optional[int] = None
    paid_off_date: Optional[date] = None
    total_interest: Decimal


class PayoffResponse(BaseModel):
    feasible: bool
    suggested_budget: Decimal
    monthly_budget: Decimal
    months: list[MonthSnapshot]
    debts: list[DebtPayoffDetail]
    debt_free_date: Optional[date] = None
    total_interest: Decimal
    total_months: int
