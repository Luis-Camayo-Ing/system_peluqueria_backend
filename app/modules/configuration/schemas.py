"""Pydantic schemas for company configuration."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)


DateFormat = Literal[
    "DD/MM/YYYY",
    "MM/DD/YYYY",
    "YYYY-MM-DD",
]

TimeFormat = Literal[
    "12h",
    "24h",
]


class CompanySettingValues(BaseModel):
    """Complete configurable values with system defaults."""

    # ======================================================
    # Company information
    # ======================================================

    address: str | None = Field(
        default=None,
        max_length=255,
        examples=["Carrera 7 # 10-25"],
    )

    city: str | None = Field(
        default=None,
        max_length=100,
        examples=["Popayán"],
    )

    state: str | None = Field(
        default=None,
        max_length=100,
        examples=["Cauca"],
    )

    country_code: str = Field(
        default="CO",
        min_length=2,
        max_length=2,
        pattern=r"^[A-Za-z]{2}$",
        examples=["CO"],
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
        examples=["190001"],
    )

    website: str | None = Field(
        default=None,
        max_length=255,
        examples=["https://erpbeautypro.com"],
    )

    # ======================================================
    # Taxes and currency
    # ======================================================

    currency_code: str = Field(
        default="COP",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
        examples=["COP"],
    )

    currency_symbol: str = Field(
        default="$",
        min_length=1,
        max_length=10,
        examples=["$"],
    )

    tax_name: str = Field(
        default="IVA",
        min_length=1,
        max_length=50,
        examples=["IVA"],
    )

    tax_rate: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
        examples=["19.00"],
    )

    prices_include_tax: bool = Field(
        default=False,
        examples=[False],
    )

    # ======================================================
    # Internal sale numbering
    # ======================================================

    sale_prefix: str = Field(
        default="VTA",
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["VTA"],
    )

    next_sale_number: int = Field(
        default=1,
        ge=1,
        le=999_999_999_999,
        examples=[1],
    )

    sale_number_padding: int = Field(
        default=6,
        ge=1,
        le=12,
        examples=[6],
    )

    # ======================================================
    # Regional preferences
    # ======================================================

    timezone: str = Field(
        default="America/Bogota",
        min_length=1,
        max_length=100,
        examples=["America/Bogota"],
    )

    locale: str = Field(
        default="es_CO",
        min_length=5,
        max_length=20,
        pattern=r"^[a-z]{2}_[A-Z]{2}$",
        examples=["es_CO"],
    )

    date_format: DateFormat = Field(
        default="DD/MM/YYYY",
        examples=["DD/MM/YYYY"],
    )

    time_format: TimeFormat = Field(
        default="24h",
        examples=["24h"],
    )

    # ======================================================
    # Visual identity
    # ======================================================

    logo_url: str | None = Field(
        default=None,
        max_length=500,
        examples=[
            "https://erpbeautypro.com/assets/logo.png"
        ],
    )

    primary_color: str = Field(
        default="#17324D",
        min_length=7,
        max_length=7,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        examples=["#17324D"],
    )

    secondary_color: str = Field(
        default="#2F918C",
        min_length=7,
        max_length=7,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        examples=["#2F918C"],
    )

    # ======================================================
    # Operational parameters
    # ======================================================

    appointment_slot_minutes: int = Field(
        default=30,
        ge=5,
        le=240,
        examples=[30],
    )

    allow_appointment_overlap: bool = Field(
        default=False,
        examples=[False],
    )

    low_stock_threshold: Decimal = Field(
        default=Decimal("5.000"),
        ge=Decimal("0.000"),
        max_digits=12,
        decimal_places=3,
        examples=["5.000"],
    )

    require_customer_for_sale: bool = Field(
        default=False,
        examples=[False],
    )

    send_email_receipts: bool = Field(
        default=False,
        examples=[False],
    )

    send_whatsapp_receipts: bool = Field(
        default=False,
        examples=[False],
    )

    @field_validator(
        "address",
        "city",
        "state",
        "postal_code",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: object,
    ) -> object:
        """Strip optional text and convert empty strings to null."""

        if value is None:
            return None

        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None

        return value

    @field_validator(
        "currency_symbol",
        "tax_name",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: object,
    ) -> object:
        """Remove surrounding whitespace from required text."""

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator(
        "country_code",
        "currency_code",
        mode="before",
    )
    @classmethod
    def normalize_codes(
        cls,
        value: object,
    ) -> object:
        """Normalize ISO country and currency codes."""

        if isinstance(value, str):
            return value.strip().upper()

        return value

    @field_validator(
        "sale_prefix",
        mode="before",
    )
    @classmethod
    def normalize_sale_prefix(
        cls,
        value: object,
    ) -> object:
        """Normalize the internal sale prefix."""

        if isinstance(value, str):
            return value.strip().upper()

        return value

    @field_validator(
        "locale",
        mode="before",
    )
    @classmethod
    def normalize_locale(
        cls,
        value: object,
    ) -> object:
        """Normalize locale values to language_COUNTRY."""

        if not isinstance(value, str):
            return value

        normalized = value.strip().replace("-", "_")
        parts = normalized.split("_", maxsplit=1)

        if len(parts) != 2:
            return normalized

        return f"{parts[0].lower()}_{parts[1].upper()}"

    @field_validator(
        "timezone",
        mode="before",
    )
    @classmethod
    def validate_timezone(
        cls,
        value: object,
    ) -> object:
        """Validate that the value is an existing IANA timezone."""

        if not isinstance(value, str):
            return value

        normalized = value.strip()

        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError as error:
            raise ValueError(
                "La zona horaria no pertenece al catálogo IANA."
            ) from error

        return normalized

    @field_validator(
        "website",
        "logo_url",
        mode="before",
    )
    @classmethod
    def validate_http_url(
        cls,
        value: object,
    ) -> object:
        """Validate optional HTTP or HTTPS URLs."""

        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        validated_url = TypeAdapter(
            AnyHttpUrl
        ).validate_python(normalized)

        if validated_url.scheme not in {"http", "https"}:
            raise ValueError(
                "La URL debe utilizar HTTP o HTTPS."
            )

        return normalized

    @field_validator(
        "primary_color",
        "secondary_color",
        mode="before",
    )
    @classmethod
    def normalize_hex_color(
        cls,
        value: object,
    ) -> object:
        """Normalize hexadecimal colors to uppercase."""

        if isinstance(value, str):
            return value.strip().upper()

        return value


class CompanySettingUpdate(BaseModel):
    """Partial configuration update for the authenticated company."""

    _NON_NULLABLE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "country_code",
            "currency_code",
            "currency_symbol",
            "tax_name",
            "tax_rate",
            "prices_include_tax",
            "sale_prefix",
            "next_sale_number",
            "sale_number_padding",
            "timezone",
            "locale",
            "date_format",
            "time_format",
            "primary_color",
            "secondary_color",
            "appointment_slot_minutes",
            "allow_appointment_overlap",
            "low_stock_threshold",
            "require_customer_for_sale",
            "send_email_receipts",
            "send_whatsapp_receipts",
        }
    )

    address: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        pattern=r"^[A-Za-z]{2}$",
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )

    website: str | None = Field(
        default=None,
        max_length=255,
    )

    currency_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
    )

    currency_symbol: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
    )

    tax_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    tax_rate: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
    )

    prices_include_tax: bool | None = None

    sale_prefix: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    next_sale_number: int | None = Field(
        default=None,
        ge=1,
        le=999_999_999_999,
    )

    sale_number_padding: int | None = Field(
        default=None,
        ge=1,
        le=12,
    )

    timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    locale: str | None = Field(
        default=None,
        min_length=5,
        max_length=20,
        pattern=r"^[a-z]{2}_[A-Z]{2}$",
    )

    date_format: DateFormat | None = None
    time_format: TimeFormat | None = None

    logo_url: str | None = Field(
        default=None,
        max_length=500,
    )

    primary_color: str | None = Field(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )

    secondary_color: str | None = Field(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )

    appointment_slot_minutes: int | None = Field(
        default=None,
        ge=5,
        le=240,
    )

    allow_appointment_overlap: bool | None = None

    low_stock_threshold: Decimal | None = Field(
        default=None,
        ge=Decimal("0.000"),
        max_digits=12,
        decimal_places=3,
    )

    require_customer_for_sale: bool | None = None
    send_email_receipts: bool | None = None
    send_whatsapp_receipts: bool | None = None

    @field_validator(
        "address",
        "city",
        "state",
        "postal_code",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: object,
    ) -> object:
        """Strip optional text and convert empty strings to null."""

        return CompanySettingValues.normalize_optional_text(value)

    @field_validator(
        "currency_symbol",
        "tax_name",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: object,
    ) -> object:
        """Remove surrounding whitespace from required text."""

        if value is None:
            return None

        return CompanySettingValues.normalize_required_text(value)

    @field_validator(
        "country_code",
        "currency_code",
        mode="before",
    )
    @classmethod
    def normalize_codes(
        cls,
        value: object,
    ) -> object:
        """Normalize optional ISO codes."""

        if value is None:
            return None

        return CompanySettingValues.normalize_codes(value)

    @field_validator(
        "sale_prefix",
        mode="before",
    )
    @classmethod
    def normalize_sale_prefix(
        cls,
        value: object,
    ) -> object:
        """Normalize the optional sale prefix."""

        if value is None:
            return None

        return CompanySettingValues.normalize_sale_prefix(value)

    @field_validator(
        "locale",
        mode="before",
    )
    @classmethod
    def normalize_locale(
        cls,
        value: object,
    ) -> object:
        """Normalize an optional locale."""

        if value is None:
            return None

        return CompanySettingValues.normalize_locale(value)

    @field_validator(
        "timezone",
        mode="before",
    )
    @classmethod
    def validate_timezone(
        cls,
        value: object,
    ) -> object:
        """Validate an optional IANA timezone."""

        if value is None:
            return None

        return CompanySettingValues.validate_timezone(value)

    @field_validator(
        "website",
        "logo_url",
        mode="before",
    )
    @classmethod
    def validate_http_url(
        cls,
        value: object,
    ) -> object:
        """Validate optional HTTP or HTTPS URLs."""

        return CompanySettingValues.validate_http_url(value)

    @field_validator(
        "primary_color",
        "secondary_color",
        mode="before",
    )
    @classmethod
    def normalize_hex_color(
        cls,
        value: object,
    ) -> object:
        """Normalize optional hexadecimal colors."""

        if value is None:
            return None

        return CompanySettingValues.normalize_hex_color(value)

    @model_validator(mode="after")
    def validate_update_payload(
        self,
    ) -> "CompanySettingUpdate":
        """Reject empty payloads and null required settings."""

        if not self.model_fields_set:
            raise ValueError(
                "Debe proporcionar al menos un parámetro "
                "para actualizar."
            )

        invalid_null_fields = sorted(
            field_name
            for field_name in self.model_fields_set
            if (
                field_name in self._NON_NULLABLE_FIELDS
                and getattr(self, field_name) is None
            )
        )

        if invalid_null_fields:
            raise ValueError(
                "Los siguientes parámetros no aceptan null: "
                + ", ".join(invalid_null_fields)
            )

        return self


class CompanySettingResponse(CompanySettingValues):
    """Persisted configuration returned by the API."""

    id: uuid.UUID
    company_id: uuid.UUID
    updated_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )