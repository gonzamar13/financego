from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum
from uuid import UUID

class DocumentType(str, Enum):
    CI = "CI"
    DNI = "DNI"
    PASSPORT = "PASSPORT"
    RUC = "RUC"

class RegisterRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    document_type: DocumentType
    document_number: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    document_type: DocumentType
    document_number: str
    username: str
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"