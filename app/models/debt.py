import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, Date, Numeric, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Debt(Base):
    __tablename__ = "debts"

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

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    # "loan" | "credit_card"
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    lender: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True
    )

    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 3),
        nullable=True
    )

    total_installments: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    installment_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    due_day: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="debts")
    payments = relationship(
        "DebtPayment",
        back_populates="debt",
        cascade="all, delete-orphan"
    )
