from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.modules.purchase.model import PurchaseOrderStatus


class TextNormalizationMixin(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def normalize_text_fields(cls, value):
        if isinstance(value, str):
            normalized_value = value.strip()

            if not normalized_value:
                return None

            return normalized_value

        return value


# ==========================================================
# Purchase Orders
# ==========================================================


class PurchaseOrderDetailCreate(BaseModel):
    product_id: UUID

    ordered_quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )

    unit_cost: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )


class PurchaseOrderCreate(TextNormalizationMixin):
    supplier_id: UUID

    order_number: str = Field(
        min_length=1,
        max_length=50,
    )

    expected_at: datetime | None = None

    tax_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    details: list[PurchaseOrderDetailCreate] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_unique_products(self):
        product_ids = [
            detail.product_id
            for detail in self.details
        ]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Un producto no puede repetirse dentro "
                "de la misma orden de compra."
            )

        subtotal = sum(
            (
                detail.ordered_quantity * detail.unit_cost
                for detail in self.details
            ),
            Decimal("0.00"),
        )

        if self.discount_amount > subtotal + self.tax_amount:
            raise ValueError(
                "El descuento no puede superar el subtotal "
                "más los impuestos."
            )

        return self


class PurchaseOrderUpdate(TextNormalizationMixin):
    supplier_id: UUID | None = None

    order_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    expected_at: datetime | None = None

    tax_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    discount_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    details: list[PurchaseOrderDetailCreate] | None = Field(
        default=None,
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_unique_products(self):
        if self.details is None:
            return self

        product_ids = [
            detail.product_id
            for detail in self.details
        ]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Un producto no puede repetirse dentro "
                "de la misma orden de compra."
            )

        return self


class PurchaseOrderCancel(TextNormalizationMixin):
    reason: str = Field(
        min_length=3,
        max_length=500,
    )


class PurchaseOrderDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    product_id: UUID
    ordered_quantity: Decimal
    received_quantity: Decimal
    pending_quantity: Decimal
    unit_cost: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    supplier_id: UUID
    created_by_user_id: UUID
    approved_by_user_id: UUID | None
    cancelled_by_user_id: UUID | None
    order_number: str
    status: PurchaseOrderStatus
    expected_at: datetime | None
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    notes: str | None
    cancellation_reason: str | None
    approved_at: datetime | None
    cancelled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    details: list[PurchaseOrderDetailResponse]


class PurchaseOrderListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[PurchaseOrderResponse]


# ==========================================================
# Purchase Receipts
# ==========================================================


class PurchaseReceiptDetailCreate(BaseModel):
    purchase_order_detail_id: UUID

    quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )

    unit_cost: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )


class PurchaseReceiptCreate(TextNormalizationMixin):
    receipt_number: str = Field(
        min_length=1,
        max_length=50,
    )

    supplier_invoice_number: str | None = Field(
        default=None,
        max_length=100,
    )

    tax_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    details: list[PurchaseReceiptDetailCreate] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_unique_order_details(self):
        order_detail_ids = [
            detail.purchase_order_detail_id
            for detail in self.details
        ]

        if len(order_detail_ids) != len(set(order_detail_ids)):
            raise ValueError(
                "Un detalle de la orden no puede repetirse "
                "dentro de la misma recepción."
            )

        return self


class PurchaseReceiptDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_receipt_id: UUID
    purchase_order_detail_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_cost: Decimal
    line_total: Decimal
    stock_before: Decimal
    stock_after: Decimal
    created_at: datetime


class PurchaseReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    purchase_order_id: UUID
    received_by_user_id: UUID
    inventory_movement_id: UUID | None
    receipt_number: str
    supplier_invoice_number: str | None
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    notes: str | None
    received_at: datetime
    created_at: datetime
    details: list[PurchaseReceiptDetailResponse]


class PurchaseReceiptListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[PurchaseReceiptResponse]