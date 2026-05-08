from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category_id: UUID
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0)
    alert_threshold: int = Field(default=80, ge=0, le=100)


class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0)
    alert_threshold: Optional[int] = Field(default=None, ge=0, le=100)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID
    category_name: str
    year: int
    month: int
    amount: Decimal
    alert_threshold: int
    created_at: datetime

    # Derivados
    spent: Decimal
    remaining: Decimal
    progress_percent: float
    status: str  # "ok" | "warning" | "exceeded"


class BudgetAlert(BaseModel):
    budget_id: UUID
    category_id: UUID
    category_name: str
    year: int
    month: int
    amount: Decimal
    spent: Decimal
    progress_percent: float
    status: str  # "warning" | "exceeded"
    message: str
