from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class AccountType(str, Enum):
    BANK = "bank"
    FINANCIAL = "financial"
    COOPERATIVE = "cooperative"
    CASH = "cash"


class AccountCreate(BaseModel):
    financial_institution: Optional[str] = Field(default=None, min_length=1, max_length=100)
    account_name: str = Field(min_length=1, max_length=100)
    type: AccountType
    account_number: Optional[str] = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_account_fields(self):
        if self.type in [AccountType.BANK, AccountType.FINANCIAL, AccountType.COOPERATIVE]:
            if not self.financial_institution or not self.account_number:
                raise ValueError(
                    "Para cuentas bancarias, financieras o cooperativas, "
                    "financial_institution y account_number son obligatorios"
                )

        if self.type == AccountType.CASH:
            self.financial_institution = None
            self.account_number = None

        return self


class AccountUpdate(BaseModel):
    account_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[AccountType] = None
    financial_institution: Optional[str] = Field(default=None, min_length=1, max_length=100)
    account_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_name: str
    type: AccountType
    financial_institution: Optional[str]
    account_number: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }