import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ==========================================================
# Product Category Schemas
# ==========================================================


class ProductCategoryBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if len(normalized_value) < 2:
            raise ValueError(
                "El nombre de la categoría debe contener "
                "al menos dos caracteres."
            )

        return normalized_value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        return normalized_value or None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if len(normalized_value) < 2:
            raise ValueError(
                "El nombre de la categoría debe contener "
                "al menos dos caracteres."
            )

        return normalized_value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        return normalized_value or None


class ProductCategoryResponse(ProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProductCategoryListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[ProductCategoryResponse]


# ==========================================================
# Product Schemas
# ==========================================================


class ProductBase(BaseModel):
    category_id: uuid.UUID

    code: str = Field(
        min_length=1,
        max_length=50,
    )

    barcode: str | None = Field(
        default=None,
        max_length=100,
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    purchase_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    sale_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    current_stock: Decimal = Field(
        default=Decimal("0.000"),
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    minimum_stock: Decimal = Field(
        default=Decimal("0.000"),
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    maximum_stock: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    unit: str = Field(
        default="unit",
        min_length=1,
        max_length=20,
    )

    is_active: bool = True

    @field_validator(
        "code",
        "name",
        "unit",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: str,
    ) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "El valor no puede estar vacío."
            )

        return normalized_value

    @field_validator(
        "barcode",
        "description",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        return normalized_value or None

    @model_validator(mode="after")
    def validate_stock_limits(self) -> "ProductBase":
        if (
            self.maximum_stock is not None
            and self.maximum_stock < self.minimum_stock
        ):
            raise ValueError(
                "El stock máximo no puede ser menor "
                "que el stock mínimo."
            )

        return self


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: uuid.UUID | None = None

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    barcode: str | None = Field(
        default=None,
        max_length=100,
    )

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    purchase_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    sale_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    current_stock: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    minimum_stock: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    maximum_stock: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    is_active: bool | None = None

    @field_validator(
        "code",
        "name",
        "unit",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                "El valor no puede estar vacío."
            )

        return normalized_value

    @field_validator(
        "barcode",
        "description",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        return normalized_value or None

    @model_validator(mode="after")
    def validate_stock_limits(self) -> "ProductUpdate":
        if (
            self.minimum_stock is not None
            and self.maximum_stock is not None
            and self.maximum_stock < self.minimum_stock
        ):
            raise ValueError(
                "El stock máximo no puede ser menor "
                "que el stock mínimo."
            )

        return self


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[ProductResponse]