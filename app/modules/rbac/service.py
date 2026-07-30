from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.rbac.exceptions import (
    PermissionAlreadyAssignedException,
    PermissionAlreadyExistsException,
    PermissionNotFoundException,
    RoleAlreadyExistsException,
    RoleNotFoundException,
    SystemRoleDeletionException,
    SystemRoleModificationException,
    UserRoleAlreadyAssignedException,
)
from app.modules.rbac.model import Permission, Role
from app.modules.rbac.repository import RBACRepository
from app.modules.rbac.schemas import (
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
)


class RBACService:

    def __init__(self, db: Session):
        self.repository = RBACRepository(db)

    # ==========================================================
    # Roles
    # ==========================================================

    def create_role(self, data: RoleCreate) -> Role:

        existing = self.repository.get_role_by_name(
            data.company_id,
            data.name,
        )

        if existing:
            raise RoleAlreadyExistsException()

        role = Role(
            company_id=data.company_id,
            name=data.name,
            description=data.description,
            is_system_role=data.is_system_role,
            is_active=data.is_active,
        )

        if data.permission_ids:

            for permission_id in data.permission_ids:

                permission = self.repository.get_permission_by_id(
                    permission_id,
                )

                if permission is None:
                    raise PermissionNotFoundException()

                role.permissions.append(permission)

        return self.repository.create_role(role)

    def get_role(
        self,
        role_id: UUID,
    ) -> Role:

        role = self.repository.get_role_by_id(role_id)

        if role is None:
            raise RoleNotFoundException()

        return role

    def get_roles_by_company(
        self,
        company_id: UUID,
    ) -> list[Role]:

        return self.repository.get_roles_by_company(
            company_id,
        )

    def update_role(
        self,
        role_id: UUID,
        data: RoleUpdate,
    ) -> Role:

        role = self.get_role(role_id)

        if role.is_system_role:
            raise SystemRoleModificationException()

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"permission_ids"},
        )

        for key, value in update_data.items():
            setattr(role, key, value)

        if data.permission_ids is not None:

            role.permissions.clear()

            for permission_id in data.permission_ids:

                permission = self.repository.get_permission_by_id(
                    permission_id,
                )

                if permission is None:
                    raise PermissionNotFoundException()

                role.permissions.append(permission)

        return self.repository.update_role(role)

    def delete_role(
        self,
        role_id: UUID,
    ) -> None:

        role = self.get_role(role_id)

        if role.is_system_role:
            raise SystemRoleDeletionException()

        self.repository.delete_role(role)

    # ==========================================================
    # Permissions
    # ==========================================================

    def create_permission(
        self,
        data: PermissionCreate,
    ) -> Permission:

        existing = self.repository.get_permission_by_name(
            data.name,
        )

        if existing:
            raise PermissionAlreadyExistsException()

        permission = Permission(
            name=data.name,
            description=data.description,
            is_active=data.is_active,
        )

        return self.repository.create_permission(permission)

    def get_permission(
        self,
        permission_id: UUID,
    ) -> Permission:

        permission = self.repository.get_permission_by_id(
            permission_id,
        )

        if permission is None:
            raise PermissionNotFoundException()

        return permission

    def get_permissions(
        self,
    ) -> list[Permission]:

        return self.repository.get_all_permissions()

    def update_permission(
        self,
        permission_id: UUID,
        data: PermissionUpdate,
    ) -> Permission:

        permission = self.get_permission(permission_id)

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(permission, key, value)

        return self.repository.update_permission(permission)

    def delete_permission(
        self,
        permission_id: UUID,
    ) -> None:

        permission = self.get_permission(permission_id)

        self.repository.delete_permission(permission)

    # ==========================================================
    # Assignments
    # ==========================================================

    def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
    ) -> None:

        user = self.repository.get_user_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        role = self.get_role(role_id)

        if role in user.roles:
            raise UserRoleAlreadyAssignedException()

        self.repository.assign_role_to_user(
            user,
            role,
        )

    def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:

        role = self.get_role(role_id)

        permission = self.get_permission(
            permission_id,
        )

        if permission in role.permissions:
            raise PermissionAlreadyAssignedException()

        self.repository.assign_permission_to_role(
            role,
            permission,
        )