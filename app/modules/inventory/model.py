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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class InventoryMovementType(str, enum.Enum):
    ENTRY = "entry"
    EXIT = "exit"
    ADJUSTMENT_IN = "adjustment_in"
    ADJUSTMENT_OUT = "adjustment_out"
    CONSUMPTION = "consumption"
    RETURN_IN = "return_in"
    RETURN_OUT = "return_out"


class ProductCategory(Base):
    __tablename__ = "product_categories"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "name",
            name="uq_product_categories_company_name",
        ),
        Index(
            "ix_product_categories_company_active",
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

    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_products_company_code",
        ),
        UniqueConstraint(
            "company_id",
            "barcode",
            name="uq_products_company_barcode",
        ),
        CheckConstraint(
            "purchase_price >= 0",
            name="ck_products_purchase_price_non_negative",
        ),
        CheckConstraint(
            "sale_price >= 0",
            name="ck_products_sale_price_non_negative",
        ),
        CheckConstraint(
            "current_stock >= 0",
            name="ck_products_current_stock_non_negative",
        ),
        CheckConstraint(
            "minimum_stock >= 0",
            name="ck_products_minimum_stock_non_negative",
        ),
        CheckConstraint(
            "maximum_stock IS NULL OR maximum_stock >= minimum_stock",
            name="ck_products_maximum_stock_valid",
        ),
        Index(
            "ix_products_company_active",
            "company_id",
            "is_active",
        ),
        Index(
            "ix_products_company_name",
            "company_id",
            "name",
        ),
        Index(
            "ix_products_company_category",
            "company_id",
            "category_id",
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

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    sale_price: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    current_stock: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )

    minimum_stock: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )

    maximum_stock: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
        ),
        nullable=True,
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unit",
        server_default="unit",
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

    category: Mapped[ProductCategory] = relationship(
        "ProductCategory",
        back_populates="products",
    )

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    __table_args__ = (
        Index(
            "ix_inventory_movements_company_created",
            "company_id",
            "created_at",
        ),
        Index(
            "ix_inventory_movements_company_type",
            "company_id",
            "movement_type",
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

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    movement_type: Mapped[InventoryMovementType] = mapped_column(
        Enum(
            InventoryMovementType,
            name="inventory_movement_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
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

    company = relationship("Company")

    user = relationship("User")

    details: Mapped[list["InventoryMovementDetail"]] = relationship(
        "InventoryMovementDetail",
        back_populates="movement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class InventoryMovementDetail(Base):
    __tablename__ = "inventory_movement_details"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_inventory_movement_details_quantity_positive",
        ),
        CheckConstraint(
            "stock_before >= 0",
            name="ck_inventory_movement_details_stock_before_non_negative",
        ),
        CheckConstraint(
            "stock_after >= 0",
            name="ck_inventory_movement_details_stock_after_non_negative",
        ),
        UniqueConstraint(
            "movement_id",
            "product_id",
            name="uq_inventory_movement_details_movement_product",
        ),
        Index(
            "ix_inventory_movement_details_product_created",
            "product_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    movement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "inventory_movements.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=14,
            scale=3,
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

    unit_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    movement: Mapped["InventoryMovement"] = relationship(
        "InventoryMovement",
        back_populates="details",
    )

    product: Mapped["Product"] = relationship(
        "Product",
    )