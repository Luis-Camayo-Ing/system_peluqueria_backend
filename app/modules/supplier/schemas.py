from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


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


class SupplierCreate(TextNormalizationMixin):
    tax_id: str = Field(
        min_length=3,
        max_length=50,
    )

    business_name: str = Field(
        min_length=2,
        max_length=150,
    )

    trade_name: str | None = Field(
        default=None,
        max_length=150,
    )

    contact_name: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    email: EmailStr | None = None

    address: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool = True


class SupplierUpdate(TextNormalizationMixin):
    tax_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    business_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    trade_name: str | None = Field(
        default=None,
        max_length=150,
    )

    contact_name: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    email: EmailStr | None = None

    address: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_required_fields_when_provided(self):
        if (
            "tax_id" in self.model_fields_set
            and self.tax_id is None
        ):
            raise ValueError(
                "La identificación fiscal no puede quedar vacía."
            )

        if (
            "business_name" in self.model_fields_set
            and self.business_name is None
        ):
            raise ValueError(
                "La razón social no puede quedar vacía."
            )

        return self


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    tax_id: str
    business_name: str
    trade_name: str | None
    contact_name: str | None
    phone: str | None
    email: str | None
    address: str | None
    city: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(BaseModel):
    total: int
    items: list[SupplierResponse]