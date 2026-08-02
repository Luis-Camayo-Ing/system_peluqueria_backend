from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "tax_id",
            name="uq_suppliers_company_tax_id",
        ),
        CheckConstraint(
            "btrim(tax_id) <> ''",
            name="ck_suppliers_tax_id_not_blank",
        ),
        CheckConstraint(
            "btrim(business_name) <> ''",
            name="ck_suppliers_business_name_not_blank",
        ),
        Index(
            "ix_suppliers_company_active",
            "company_id",
            "is_active",
        ),
        Index(
            "ix_suppliers_company_business_name",
            "company_id",
            "business_name",
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

    tax_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    business_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    trade_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contact_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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