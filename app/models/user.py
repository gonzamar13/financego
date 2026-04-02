import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )

    first_name: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )

    document_type: Mapped[str] = mapped_column(
    String(20),
    nullable=False
    )

    document_number: Mapped[str] = mapped_column(
    String(30),
    unique=True,
    nullable=False
    )

    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )

    accounts = relationship("Account", back_populates="user")
    categories = relationship("Category", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")