"""Pydantic schemas for sales and point-of-sale operations."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.modules.sale.model import (
    SaleItemType,
    SalePaymentMethod,
    SaleStatus,
)


class SaleSchema(BaseModel):
    """Shared configuration for sale schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class SaleDetailCreate(SaleSchema):
    """Product or service requested in a new sale."""

    item_type: SaleItemType

    product_id: UUID | None = None
    service_id: UUID | None = None

    quantity: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )

    unit_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=14,
        decimal_places=2,
        description=(
            "Precio personalizado. Cuando no se proporciona, "
            "se utiliza el precio vigente del catálogo."
        ),
    )

    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    tax_rate: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )

    @model_validator(mode="after")
    def validate_item_reference(self) -> Self:
        """Require exactly one catalog reference."""

        if self.item_type == SaleItemType.PRODUCT:
            if self.product_id is None:
                raise ValueError(
                    "Los detalles de producto requieren product_id."
                )

            if self.service_id is not None:
                raise ValueError(
                    "Un detalle de producto no puede incluir service_id."
                )

        elif self.item_type == SaleItemType.SERVICE:
            if self.service_id is None:
                raise ValueError(
                    "Los detalles de servicio requieren service_id."
                )

            if self.product_id is not None:
                raise ValueError(
                    "Un detalle de servicio no puede incluir product_id."
                )

        return self


class SalePaymentCreate(SaleSchema):
    """Payment applied to a new sale."""

    payment_method: SalePaymentMethod

    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
        description="Valor del pago aplicado al total de la venta.",
    )

    tendered_amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=14,
        decimal_places=2,
        description=(
            "Dinero entregado por el cliente. "
            "Solo se utiliza para pagos en efectivo."
        ),
    )

    reference: str | None = Field(
        default=None,
        max_length=150,
    )

    notes: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator(
        "reference",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: object,
    ) -> object:
        """Convert blank optional strings to None."""

        if isinstance(value, str):
            normalized = value.strip()

            return normalized or None

        return value

    @model_validator(mode="after")
    def validate_tendered_amount(self) -> Self:
        """Validate cash and non-cash payment behavior."""

        if self.payment_method == SalePaymentMethod.CASH:
            if self.tendered_amount is None:
                raise ValueError(
                    "Los pagos en efectivo requieren tendered_amount."
                )

            if self.tendered_amount < self.amount:
                raise ValueError(
                    "El dinero entregado no puede ser menor "
                    "que el valor aplicado en efectivo."
                )

        elif self.tendered_amount is not None:
            raise ValueError(
                "tendered_amount solo se permite "
                "para pagos en efectivo."
            )

        return self


class SaleCreate(SaleSchema):
    """Request used to complete a sale transaction."""

    sale_number: str = Field(
        min_length=1,
        max_length=100,
    )

    customer_id: UUID | None = None

    cash_session_id: UUID

    notes: str | None = None

    details: list[SaleDetailCreate] = Field(
        min_length=1,
    )

    payments: list[SalePaymentCreate] = Field(
        min_length=1,
    )

    @field_validator("sale_number")
    @classmethod
    def normalize_sale_number(
        cls,
        value: str,
    ) -> str:
        """Normalize the internal sale number."""

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "El número de venta no puede estar vacío."
            )

        return normalized

    @field_validator(
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_notes(
        cls,
        value: object,
    ) -> object:
        """Convert blank notes to None."""

        if isinstance(value, str):
            normalized = value.strip()

            return normalized or None

        return value

    @model_validator(mode="after")
    def validate_sale_collections(self) -> Self:
        """Reject duplicate items and ambiguous cash payments."""

        item_references: set[
            tuple[SaleItemType, UUID]
        ] = set()

        for detail in self.details:
            reference_id = (
                detail.product_id
                if detail.item_type == SaleItemType.PRODUCT
                else detail.service_id
            )

            if reference_id is None:
                continue

            reference = (
                detail.item_type,
                reference_id,
            )

            if reference in item_references:
                raise ValueError(
                    "No se permiten productos o servicios "
                    "duplicados dentro de una venta."
                )

            item_references.add(reference)

        cash_payment_count = sum(
            1
            for payment in self.payments
            if payment.payment_method
            == SalePaymentMethod.CASH
        )

        if cash_payment_count > 1:
            raise ValueError(
                "La venta solo puede incluir un pago en efectivo."
            )

        return self


class SaleCancelRequest(SaleSchema):
    """Request used to cancel a completed sale."""

    reason: str = Field(
        min_length=3,
        max_length=500,
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str,
    ) -> str:
        """Normalize and validate the cancellation reason."""

        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError(
                "El motivo de cancelación debe tener "
                "al menos tres caracteres."
            )

        return normalized


class SaleDetailResponse(BaseModel):
    """Sale detail returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    sale_id: UUID

    item_type: SaleItemType

    product_id: UUID | None
    service_id: UUID | None

    item_code: str | None
    item_name: str
    item_description: str | None
    unit: str

    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal

    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal

    line_subtotal: Decimal
    line_total: Decimal

    created_at: datetime


class SalePaymentResponse(BaseModel):
    """Sale payment returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    sale_id: UUID

    payment_method: SalePaymentMethod

    amount: Decimal
    tendered_amount: Decimal | None

    reference: str | None
    notes: str | None

    created_at: datetime


class SaleResponse(BaseModel):
    """Complete sale representation."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    company_id: UUID

    customer_id: UUID | None
    cash_session_id: UUID

    created_by_user_id: UUID
    cancelled_by_user_id: UUID | None

    inventory_movement_id: UUID | None
    cash_transaction_id: UUID | None

    cancellation_inventory_movement_id: UUID | None
    cancellation_cash_transaction_id: UUID | None

    sale_number: str
    status: SaleStatus

    company_name: str
    company_tax_id: str
    company_email: str | None
    company_phone: str | None

    customer_name: str | None
    customer_document: str | None
    customer_email: str | None
    customer_phone: str | None

    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    paid_amount: Decimal
    change_amount: Decimal

    notes: str | None

    cancellation_reason: str | None

    sold_at: datetime
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    details: list[SaleDetailResponse]
    payments: list[SalePaymentResponse]


class SaleListResponse(BaseModel):
    """Paginated sale list."""

    total: int
    items: list[SaleResponse]
