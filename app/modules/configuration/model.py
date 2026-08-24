"""Database model for company-level ERP configuration."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompanySetting(Base):
    """General, fiscal and visual preferences for one company."""

    __tablename__ = "company_settings"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            name="uq_company_settings_company_id",
        ),
        CheckConstraint(
            "tax_rate >= 0 AND tax_rate <= 100",
            name="ck_company_settings_tax_rate",
        ),
        CheckConstraint(
            "next_sale_number >= 1",
            name="ck_company_settings_next_sale_number",
        ),
        CheckConstraint(
            "sale_number_padding >= 1 "
            "AND sale_number_padding <= 12",
            name="ck_company_settings_sale_number_padding",
        ),
        CheckConstraint(
            "appointment_slot_minutes >= 5 "
            "AND appointment_slot_minutes <= 240",
            name="ck_company_settings_appointment_slot",
        ),
        CheckConstraint(
            "low_stock_threshold >= 0",
            name="ck_company_settings_low_stock_threshold",
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
    )

    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ======================================================
    # Company information
    # ======================================================

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="CO",
        server_default="CO",
    )

    postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ======================================================
    # Taxes and currency
    # ======================================================

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="COP",
        server_default="COP",
    )

    currency_symbol: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="$",
        server_default="$",
    )

    tax_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="IVA",
        server_default="IVA",
    )

    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )

    prices_include_tax: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    # ======================================================
    # Internal sale numbering
    # ======================================================

    sale_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="VTA",
        server_default="VTA",
    )

    next_sale_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )

    sale_number_padding: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=6,
        server_default=text("6"),
    )

    # ======================================================
    # Regional preferences
    # ======================================================

    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="America/Bogota",
        server_default="America/Bogota",
    )

    locale: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="es_CO",
        server_default="es_CO",
    )

    date_format: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DD/MM/YYYY",
        server_default="DD/MM/YYYY",
    )

    time_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="24h",
        server_default="24h",
    )

    # ======================================================
    # Visual identity
    # ======================================================

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    primary_color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#17324D",
        server_default="#17324D",
    )

    secondary_color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#2F918C",
        server_default="#2F918C",
    )

    # ======================================================
    # Operational parameters
    # ======================================================

    appointment_slot_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default=text("30"),
    )

    allow_appointment_overlap: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    low_stock_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("5.000"),
        server_default=text("5.000"),
    )

    require_customer_for_sale: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    send_email_receipts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    send_whatsapp_receipts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
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