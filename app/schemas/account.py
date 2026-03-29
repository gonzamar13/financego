from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=20)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[str] = Field(default=None, min_length=1, max_length=20)
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    type: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }