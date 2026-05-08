import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    debt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("debts.id", ondelete="CASCADE"),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    installment_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    debt = relationship("Debt", back_populates="payments")
    user = relationship("User", back_populates="debt_payments")
