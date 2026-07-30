from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.rbac.model import Permission, Role
from app.modules.user.model import User


class RBACRepository:

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================
    # Roles
    # ==========================================================

    def create_role(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_role_by_id(
        self,
        role_id: UUID,
    ) -> Role | None:
        return self.db.get(Role, role_id)

    def get_role_by_name(
        self,
        company_id: UUID,
        name: str,
    ) -> Role | None:
        stmt = select(Role).where(
            Role.company_id == company_id,
            Role.name == name,
        )

        return self.db.scalar(stmt)

    def get_roles_by_company(
        self,
        company_id: UUID,
    ) -> list[Role]:
        stmt = (
            select(Role)
            .where(Role.company_id == company_id)
            .order_by(Role.name)
        )

        return list(self.db.scalars(stmt).all())

    def update_role(
        self,
        role: Role,
    ) -> Role:
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(
        self,
        role: Role,
    ) -> None:
        self.db.delete(role)
        self.db.commit()

    # ==========================================================
    # Permissions
    # ==========================================================

    def create_permission(
        self,
        permission: Permission,
    ) -> Permission:
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def get_permission_by_id(
        self,
        permission_id: UUID,
    ) -> Permission | None:
        return self.db.get(
            Permission,
            permission_id,
        )

    def get_permission_by_name(
        self,
        name: str,
    ) -> Permission | None:
        stmt = select(Permission).where(
            Permission.name == name
        )

        return self.db.scalar(stmt)

    def get_all_permissions(
        self,
    ) -> list[Permission]:
        stmt = (
            select(Permission)
            .order_by(Permission.name)
        )

        return list(self.db.scalars(stmt).all())

    def update_permission(
        self,
        permission: Permission,
    ) -> Permission:
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def delete_permission(
        self,
        permission: Permission,
    ) -> None:
        self.db.delete(permission)
        self.db.commit()

    # ==========================================================
    # User
    # ==========================================================

    def get_user_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        return self.db.get(User, user_id)

    # ==========================================================
    # Assignments
    # ==========================================================

    def assign_role_to_user(
        self,
        user: User,
        role: Role,
    ) -> None:

        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()

    def assign_permission_to_role(
        self,
        role: Role,
        permission: Permission,
    ) -> None:

        if permission not in role.permissions:
            role.permissions.append(permission)
            self.db.commit()

    def remove_role_from_user(
        self,
        user: User,
        role: Role,
    ) -> None:

        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()

    def remove_permission_from_role(
        self,
        role: Role,
        permission: Permission,
    ) -> None:

        if permission in role.permissions:
            role.permissions.remove(permission)
            self.db.commit()