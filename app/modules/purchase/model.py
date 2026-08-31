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


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "order_number",
            name="uq_purchase_orders_company_order_number",
        ),
        CheckConstraint(
            "char_length(trim(order_number)) > 0",
            name="ck_purchase_orders_order_number_not_blank",
        ),
        CheckConstraint(
            "subtotal >= 0",
            name="ck_purchase_orders_subtotal_non_negative",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="ck_purchase_orders_tax_non_negative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_purchase_orders_discount_non_negative",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_purchase_orders_total_non_negative",
        ),
        Index(
            "ix_purchase_orders_company_status_created",
            "company_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_purchase_orders_supplier_status",
            "supplier_id",
            "status",
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

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    order_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(
            PurchaseOrderStatus,
            name="purchase_order_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        server_default=PurchaseOrderStatus.DRAFT.value,
    )

    expected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    subtotal: Mapped[Decimal] = mapped_column(
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

    discount_amount: Mapped[Decimal] = mapped_column(
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

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    supplier = relationship(
        "Supplier",
    )

    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )

    approved_by_user = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )

    cancelled_by_user = relationship(
        "User",
        foreign_keys=[cancelled_by_user_id],
    )

    details: Mapped[list["PurchaseOrderDetail"]] = relationship(
        "PurchaseOrderDetail",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    receipts: Mapped[list["PurchaseReceipt"]] = relationship(
        "PurchaseReceipt",
        back_populates="purchase_order",
        passive_deletes=True,
    )


class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"

    __table_args__ = (
        CheckConstraint(
            "ordered_quantity > 0",
            name="ck_purchase_order_details_quantity_positive",
        ),
        CheckConstraint(
            "received_quantity >= 0",
            name="ck_purchase_order_details_received_non_negative",
        ),
        CheckConstraint(
            "received_quantity <= ordered_quantity",
            name="ck_purchase_order_details_received_not_exceed_ordered",
        ),
        CheckConstraint(
            "unit_cost >= 0",
            name="ck_purchase_order_details_unit_cost_non_negative",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="ck_purchase_order_details_line_total_non_negative",
        ),
        UniqueConstraint(
            "purchase_order_id",
            "product_id",
            name="uq_purchase_order_details_order_product",
        ),
        Index(
            "ix_purchase_order_details_product",
            "product_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
    )

    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="details",
    )

    product = relationship(
        "Product",
    )

    receipt_details: Mapped[list["PurchaseReceiptDetail"]] = relationship(
        "PurchaseReceiptDetail",
        back_populates="purchase_order_detail",
        passive_deletes=True,
    )

    @property
    def pending_quantity(self) -> Decimal:
        return self.ordered_quantity - self.received_quantity


class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "receipt_number",
            name="uq_purchase_receipts_company_receipt_number",
        ),
        UniqueConstraint(
            "inventory_movement_id",
            name="uq_purchase_receipts_inventory_movement",
        ),
        CheckConstraint(
            "char_length(trim(receipt_number)) > 0",
            name="ck_purchase_receipts_receipt_number_not_blank",
        ),
        CheckConstraint(
            "subtotal >= 0",
            name="ck_purchase_receipts_subtotal_non_negative",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="ck_purchase_receipts_tax_non_negative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_purchase_receipts_discount_non_negative",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_purchase_receipts_total_non_negative",
        ),
        Index(
            "ix_purchase_receipts_company_received",
            "company_id",
            "received_at",
        ),
        Index(
            "ix_purchase_receipts_order_received",
            "purchase_order_id",
            "received_at",
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

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_orders.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    received_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    inventory_movement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "inventory_movements.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    receipt_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    supplier_invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    subtotal: Mapped[Decimal] = mapped_column(
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

    discount_amount: Mapped[Decimal] = mapped_column(
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
        default=Decimal("0.00"),
        server_default="0.00",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    company = relationship(
        "Company",
    )

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="receipts",
    )

    received_by_user = relationship(
        "User",
    )

    inventory_movement = relationship(
        "InventoryMovement",
    )

    details: Mapped[list["PurchaseReceiptDetail"]] = relationship(
        "PurchaseReceiptDetail",
        back_populates="purchase_receipt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PurchaseReceiptDetail(Base):
    __tablename__ = "purchase_receipt_details"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_purchase_receipt_details_quantity_positive",
        ),
        CheckConstraint(
            "unit_cost >= 0",
            name="ck_purchase_receipt_details_unit_cost_non_negative",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="ck_purchase_receipt_details_line_total_non_negative",
        ),
        CheckConstraint(
            "stock_before >= 0",
            name="ck_purchase_receipt_details_stock_before_non_negative",
        ),
        CheckConstraint(
            "stock_after >= stock_before",
            name="ck_purchase_receipt_details_stock_after_valid",
        ),
        UniqueConstraint(
            "purchase_receipt_id",
            "purchase_order_detail_id",
            name="uq_purchase_receipt_details_receipt_order_detail",
        ),
        Index(
            "ix_purchase_receipt_details_product",
            "product_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    purchase_receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_receipts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    purchase_order_detail_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "purchase_order_details.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
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

    stock_before: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
    )

    stock_after: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    purchase_receipt: Mapped["PurchaseReceipt"] = relationship(
        "PurchaseReceipt",
        back_populates="details",
    )

    purchase_order_detail: Mapped["PurchaseOrderDetail"] = relationship(
        "PurchaseOrderDetail",
        back_populates="receipt_details",
    )

    product = relationship(
        "Product",
    )