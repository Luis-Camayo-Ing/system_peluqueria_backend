"""Sales and point-of-sale database models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SaleStatus(str, enum.Enum):
    """Supported sale lifecycle states."""

    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SaleItemType(str, enum.Enum):
    """Type of catalog item included in a sale."""

    PRODUCT = "product"
    SERVICE = "service"


class SalePaymentMethod(str, enum.Enum):
    """Payment methods supported by the POS."""

    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    OTHER = "other"


class Sale(Base):
    """Completed commercial transaction."""

    __tablename__ = "sales"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "sale_number",
            name="uq_sales_company_number",
        ),
        CheckConstraint(
            "char_length(trim(sale_number)) > 0",
            name="ck_sales_number_not_blank",
        ),
        CheckConstraint(
            "char_length(trim(company_name)) > 0",
            name="ck_sales_company_name_not_blank",
        ),
        CheckConstraint(
            "char_length(trim(company_tax_id)) > 0",
            name="ck_sales_company_tax_id_not_blank",
        ),
        CheckConstraint(
            "subtotal > 0",
            name="ck_sales_subtotal_positive",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_sales_discount_non_negative",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="ck_sales_tax_non_negative",
        ),
        CheckConstraint(
            "total_amount > 0",
            name="ck_sales_total_positive",
        ),
        CheckConstraint(
            "paid_amount > 0",
            name="ck_sales_paid_positive",
        ),
        CheckConstraint(
            "change_amount >= 0",
            name="ck_sales_change_non_negative",
        ),
        CheckConstraint(
            "discount_amount <= subtotal",
            name="ck_sales_discount_not_greater_than_subtotal",
        ),
        CheckConstraint(
            """
            (
                status = 'completed'
                AND cancelled_by_user_id IS NULL
                AND cancelled_at IS NULL
                AND cancellation_reason IS NULL
            )
            OR
            (
                status = 'cancelled'
                AND cancelled_by_user_id IS NOT NULL
                AND cancelled_at IS NOT NULL
                AND cancellation_reason IS NOT NULL
                AND char_length(trim(cancellation_reason)) > 0
            )
            """,
            name="ck_sales_status_cancellation_data",
        ),
        Index(
            "ix_sales_company_status_sold",
            "company_id",
            "status",
            "sold_at",
        ),
        Index(
            "ix_sales_company_customer_sold",
            "company_id",
            "customer_id",
            "sold_at",
        ),
        Index(
            "ix_sales_company_session_sold",
            "company_id",
            "cash_session_id",
            "sold_at",
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

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    cash_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cash_sessions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    inventory_movement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "inventory_movements.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        unique=True,
    )

    cash_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cash_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        unique=True,
    )

    cancellation_inventory_movement_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "inventory_movements.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        unique=True,
    )

    cancellation_cash_transaction_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cash_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        unique=True,
    )

    sale_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[SaleStatus] = mapped_column(
        Enum(
            SaleStatus,
            name="sale_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=SaleStatus.COMPLETED,
        server_default=SaleStatus.COMPLETED.value,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    company_tax_id: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    company_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    company_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    customer_name: Mapped[str | None] = mapped_column(
        String(201),
        nullable=True,
    )

    customer_document: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    customer_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customer_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    change_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    sold_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    customer = relationship(
        "Customer",
    )

    cash_session = relationship(
        "CashSession",
    )

    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )

    cancelled_by_user = relationship(
        "User",
        foreign_keys=[cancelled_by_user_id],
    )

    inventory_movement = relationship(
        "InventoryMovement",
        foreign_keys=[inventory_movement_id],
    )

    cash_transaction = relationship(
        "CashTransaction",
        foreign_keys=[cash_transaction_id],
    )

    cancellation_inventory_movement = relationship(
        "InventoryMovement",
        foreign_keys=[cancellation_inventory_movement_id],
    )

    cancellation_cash_transaction = relationship(
        "CashTransaction",
        foreign_keys=[cancellation_cash_transaction_id],
    )

    details: Mapped[list["SaleDetail"]] = relationship(
        "SaleDetail",
        back_populates="sale",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SaleDetail.created_at",
    )

    payments: Mapped[list["SalePayment"]] = relationship(
        "SalePayment",
        back_populates="sale",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SalePayment.created_at",
    )


class SaleDetail(Base):
    """Immutable snapshot of a product or service sold."""

    __tablename__ = "sale_details"

    __table_args__ = (
        CheckConstraint(
            """
            (
                item_type = 'product'
                AND product_id IS NOT NULL
                AND service_id IS NULL
            )
            OR
            (
                item_type = 'service'
                AND service_id IS NOT NULL
                AND product_id IS NULL
            )
            """,
            name="ck_sale_details_item_reference",
        ),
        CheckConstraint(
            "char_length(trim(item_name)) > 0",
            name="ck_sale_details_name_not_blank",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_sale_details_quantity_positive",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_sale_details_unit_price_non_negative",
        ),
        CheckConstraint(
            "unit_cost >= 0",
            name="ck_sale_details_unit_cost_non_negative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_sale_details_discount_non_negative",
        ),
        CheckConstraint(
            "tax_rate >= 0 AND tax_rate <= 100",
            name="ck_sale_details_tax_rate_valid",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="ck_sale_details_tax_non_negative",
        ),
        CheckConstraint(
            "line_subtotal >= 0",
            name="ck_sale_details_subtotal_non_negative",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="ck_sale_details_total_non_negative",
        ),
        CheckConstraint(
            "discount_amount <= line_subtotal",
            name="ck_sale_details_discount_not_greater_than_subtotal",
        ),
        Index(
            "ix_sale_details_sale_type",
            "sale_id",
            "item_type",
        ),
        Index(
            "ix_sale_details_product_created",
            "product_id",
            "created_at",
        ),
        Index(
            "ix_sale_details_service_created",
            "service_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "sales.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    item_type: Mapped[SaleItemType] = mapped_column(
        Enum(
            SaleItemType,
            name="sale_item_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "services.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    item_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    item_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    item_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unit",
        server_default="unit",
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=5,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    line_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    sale: Mapped["Sale"] = relationship(
        "Sale",
        back_populates="details",
    )

    product = relationship(
        "Product",
    )

    service = relationship(
        "Service",
    )


class SalePayment(Base):
    """Payment applied to a sale."""

    __tablename__ = "sale_payments"

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_sale_payments_amount_positive",
        ),
        CheckConstraint(
            """
            (
                payment_method = 'cash'
                AND tendered_amount IS NOT NULL
                AND tendered_amount >= amount
            )
            OR
            (
                payment_method <> 'cash'
                AND tendered_amount IS NULL
            )
            """,
            name="ck_sale_payments_tendered_amount",
        ),
        Index(
            "ix_sale_payments_sale_method",
            "sale_id",
            "payment_method",
        ),
        Index(
            "ix_sale_payments_reference",
            "reference",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "sales.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    payment_method: Mapped[SalePaymentMethod] = mapped_column(
        Enum(
            SalePaymentMethod,
            name="sale_payment_method",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=False,
    )

    tendered_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=14,
            scale=2,
        ),
        nullable=True,
    )

    reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    sale: Mapped["Sale"] = relationship(
        "Sale",
        back_populates="payments",
    )
