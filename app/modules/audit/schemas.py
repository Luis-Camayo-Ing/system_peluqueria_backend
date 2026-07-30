from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Base Schema
# ==========================================================

class AuditBase(BaseModel):
    module: str = Field(
        ...,
        max_length=50,
    )

    action: str = Field(
        ...,
        max_length=50,
    )

    entity_type: str = Field(
        ...,
        max_length=100,
    )

    entity_id: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str

    details: dict[str, Any] | None = None

    success: bool = True


# ==========================================================
# Create
# ==========================================================

class AuditCreate(AuditBase):
    company_id: UUID
    user_id: UUID | None = None


# ==========================================================
# Response
# ==========================================================

class AuditResponse(AuditBase):
    id: UUID
    company_id: UUID
    user_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ==========================================================
# Filters
# ==========================================================

class AuditFilter(BaseModel):
    company_id: UUID | None = None

    user_id: UUID | None = None

    module: str | None = None

    action: str | None = None

    entity_type: str | None = None

    entity_id: str | None = None

    success: bool | None = None

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
    )