from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Permission Schemas
# ==========================================================

class PermissionBase(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool = True


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool | None = None


class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


# ==========================================================
# Role Schemas
# ==========================================================

class RoleBase(BaseModel):
    company_id: UUID

    name: str = Field(
        min_length=3,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    is_system_role: bool = False

    is_active: bool = True


class RoleCreate(RoleBase):
    permission_ids: list[UUID] = Field(
        default_factory=list,
    )


class RoleUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    description: str | None = None

    is_system_role: bool | None = None

    is_active: bool | None = None

    permission_ids: list[UUID] | None = None


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


# ==========================================================
# User ↔ Role
# ==========================================================

class AssignRoleSchema(BaseModel):
    user_id: UUID
    role_id: UUID


# ==========================================================
# Role ↔ Permission
# ==========================================================

class AssignPermissionSchema(BaseModel):
    role_id: UUID
    permission_id: UUID