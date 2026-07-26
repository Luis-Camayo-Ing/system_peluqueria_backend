import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
        examples=["Barber Premium"],
    )

    tax_id: str = Field(
        min_length=3,
        max_length=30,
        examples=["B12345678"],
    )

    email: EmailStr | None = Field(
        default=None,
        examples=["contacto@barberpremium.com"],
    )

    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=30,
        examples=["+34 600 000 000"],
    )


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    tax_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=30,
    )

    is_active: bool | None = None


class CompanyResponse(CompanyBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int