from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.modules.auth.dependencies import get_current_user
from app.modules.user.model import User


def require_role(role_name: str):
    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        has_role = any(
            role.name == role_name and role.is_active
            for role in current_user.roles
        )

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes el rol requerido.",
            )

        return current_user

    return dependency


def require_permission(permission_name: str):
    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        has_permission = any(
            permission.name == permission_name
            and permission.is_active
            and role.is_active
            for role in current_user.roles
            for permission in role.permissions
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes el permiso requerido.",
            )

        return current_user

    return dependency