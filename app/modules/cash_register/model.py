from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CashSessionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class CashTransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class CashTransactionSource(str, enum.Enum):
    MANUAL = "manual"
    SALE = "sale"
    PURCHASE = "purchase"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    OTHER = "other"


class CashRegister(Base):
    __tablename__ = "cash_registers"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_cash_registers_company_code",
        ),
        UniqueConstraint(
            "company_id",
            "name",
            name="uq_cash_registers_company_name",
        ),
        CheckConstraint(
            "char_length(trim(code)) > 0",
            name="ck_cash_registers_code_not_blank",
        ),
        CheckConstraint(
            "char_length(trim(name)) > 0",
            name="ck_cash_registers_name_not_blank",
        ),
        Index(
            "ix_cash_registers_company_active",
            "company_id",
            "is_active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship(
        "Company",
    )

    sessions: Mapped[list["CashSession"]] = relationship(
        "CashSession",
        back_populates="cash_register",
        passive_deletes=True,
    )


class CashSession(Base):
    __tablename__ = "cash_sessions"

    __table_args__ = (
        CheckConstraint(
            "opening_amount >= 0",
            name="ck_cash_sessions_opening_amount_non_negative",
        ),
        CheckConstraint(
            "expected_amount IS NULL OR expected_amount >= 0",
            name="ck_cash_sessions_expected_amount_non_negative",
        ),
        CheckConstraint(
            "counted_amount IS NULL OR counted_amount >= 0",
            name="ck_cash_sessions_counted_amount_non_negative",
        ),
        CheckConstraint(
            """
            (
                status = 'open'
                AND closed_at IS NULL
                AND closed_by_user_id IS NULL
                AND expected_amount IS NULL
                AND counted_amount IS NULL
                AND difference_amount IS NULL
            )
            OR
            (
                status = 'closed'
                AND closed_at IS NOT NULL
                AND closed_by_user_id IS NOT NULL
                AND expected_amount IS NOT NULL
                AND counted_amount IS NOT NULL
                AND difference_amount IS NOT NULL
            )
            """,
            name="ck_cash_sessions_status_closing_data",
        ),
        Index(
            "ix_cash_sessions_company_status_opened",
            "company_id",
            "status",
            "opened_at",
        ),
        Index(
            "ix_cash_sessions_register_status",
            "cash_register_id",
            "status",
        ),
        Index(
            "uq_cash_sessions_one_open_per_register",
            "cash_register_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    cash_register_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cash_registers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    opened_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[CashSessionStatus] = mapped_column(
        Enum(
            CashSessionStatus,
            name="cash_session_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=CashSessionStatus.OPEN,
        server_default=CashSessionStatus.OPEN.value,
        index=True,
    )

    opening_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    expected_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    counted_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    difference_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    opening_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    closing_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    company = relationship(
        "Company",
    )

    cash_register: Mapped["CashRegister"] = relationship(
        "CashRegister",
        back_populates="sessions",
    )

    opened_by_user = relationship(
        "User",
        foreign_keys=[opened_by_user_id],
    )

    closed_by_user = relationship(
        "User",
        foreign_keys=[closed_by_user_id],
    )

    transactions: Mapped[list["CashTransaction"]] = relationship(
        "CashTransaction",
        back_populates="cash_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CashTransaction(Base):
    __tablename__ = "cash_transactions"

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_cash_transactions_amount_positive",
        ),
        CheckConstraint(
            "char_length(trim(description)) > 0",
            name="ck_cash_transactions_description_not_blank",
        ),
        Index(
            "ix_cash_transactions_company_created",
            "company_id",
            "created_at",
        ),
        Index(
            "ix_cash_transactions_session_created",
            "cash_session_id",
            "created_at",
        ),
        Index(
            "ix_cash_transactions_company_type",
            "company_id",
            "transaction_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    cash_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cash_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[CashTransactionType] = mapped_column(
        Enum(
            CashTransactionType,
            name="cash_transaction_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    source: Mapped[CashTransactionSource] = mapped_column(
        Enum(
            CashTransactionSource,
            name="cash_transaction_source",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=CashTransactionSource.MANUAL,
        server_default=CashTransactionSource.MANUAL.value,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    company = relationship(
        "Company",
    )

    cash_session: Mapped["CashSession"] = relationship(
        "CashSession",
        back_populates="transactions",
    )

    user = relationship(
        "User",
    )