import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.cash_register.model import (
    CashSessionStatus,
    CashTransactionSource,
    CashTransactionType,
)


class TextNormalizationMixin(BaseModel):
    @field_validator(
        "code",
        "name",
        "description",
        "reference",
        "opening_notes",
        "closing_notes",
        "notes",
        check_fields=False,
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


# ==========================================================
# Cash Registers
# ==========================================================


class CashRegisterCreate(TextNormalizationMixin):
    code: str = Field(
        min_length=1,
        max_length=50,
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=255,
    )
    is_active: bool = True


class CashRegisterUpdate(TextNormalizationMixin):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=255,
    )
    is_active: bool | None = None


class CashRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CashRegisterListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[CashRegisterResponse]


# ==========================================================
# Cash Sessions
# ==========================================================


class CashSessionOpen(TextNormalizationMixin):
    cash_register_id: uuid.UUID
    opening_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    opening_notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class CashSessionClose(TextNormalizationMixin):
    counted_amount: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    closing_notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class CashSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    cash_register_id: uuid.UUID
    opened_by_user_id: uuid.UUID
    closed_by_user_id: uuid.UUID | None
    status: CashSessionStatus
    opening_amount: Decimal
    expected_amount: Decimal | None
    counted_amount: Decimal | None
    difference_amount: Decimal | None
    opening_notes: str | None
    closing_notes: str | None
    opened_at: datetime
    closed_at: datetime | None


class CashSessionListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[CashSessionResponse]


# ==========================================================
# Cash Transactions
# ==========================================================


class CashTransactionCreate(TextNormalizationMixin):
    transaction_type: CashTransactionType
    source: CashTransactionSource = CashTransactionSource.MANUAL
    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    reference: str | None = Field(
        default=None,
        max_length=100,
    )
    description: str = Field(
        min_length=1,
        max_length=500,
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class CashTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    cash_session_id: uuid.UUID
    user_id: uuid.UUID
    transaction_type: CashTransactionType
    source: CashTransactionSource
    amount: Decimal
    reference: str | None
    description: str
    notes: str | None
    created_at: datetime


class CashTransactionListResponse(BaseModel):
    total: int = Field(ge=0)
    items: list[CashTransactionResponse]


# ==========================================================
# Cash Session summaries
# ==========================================================


class CashSessionSummaryResponse(BaseModel):
    session: CashSessionResponse
    total_income: Decimal = Field(ge=0)
    total_expense: Decimal = Field(ge=0)
    expected_amount: Decimal = Field(ge=0)


class CashSessionDetailResponse(BaseModel):
    session: CashSessionResponse
    transactions: list[CashTransactionResponse]
    summary: CashSessionSummaryResponse