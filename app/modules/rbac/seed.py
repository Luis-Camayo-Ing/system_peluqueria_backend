from __future__ import annotations

import argparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

# ==========================================================
# Registro de modelos SQLAlchemy
# ==========================================================
# Estos imports permiten que SQLAlchemy conozca todas las
# clases utilizadas mediante relationship("NombreModelo").
# No deben eliminarse aunque el editor los marque como no usados.

from app.modules.company.model import Company  # noqa: F401
from app.modules.customer.model import Customer  # noqa: F401
from app.modules.employee.model import Employee  # noqa: F401
from app.modules.service.model import Service  # noqa: F401
from app.modules.user.model import User

from app.modules.rbac.constants import (
    ADMINISTRATOR_ROLE,
    SYSTEM_PERMISSIONS,
    SYSTEM_ROLES,
)
from app.modules.rbac.model import Permission, Role


# ==========================================================
# Permisos
# ==========================================================

def get_or_create_permissions(
    db: Session,
) -> list[Permission]:
    permissions: list[Permission] = []

    for permission_name in SYSTEM_PERMISSIONS:
        permission = db.scalar(
            select(Permission).where(
                Permission.name == permission_name,
            )
        )

        if permission is None:
            permission = Permission(
                name=permission_name,
                description=permission_name,
                is_active=True,
            )

            db.add(permission)
            db.flush()

            print(
                f"Permiso creado: {permission_name}"
            )
        else:
            if not permission.is_active:
                permission.is_active = True

            print(
                f"Permiso existente: {permission_name}"
            )

        permissions.append(permission)

    return permissions


# ==========================================================
# Roles
# ==========================================================

def get_or_create_roles(
    db: Session,
    company_id: UUID,
    permissions: list[Permission],
) -> list[Role]:
    roles: list[Role] = []

    for role_name in SYSTEM_ROLES:
        role = db.scalar(
            select(Role).where(
                Role.company_id == company_id,
                Role.name == role_name,
            )
        )

        if role is None:
            role = Role(
                company_id=company_id,
                name=role_name,
                description=role_name,
                is_system_role=True,
                is_active=True,
            )

            db.add(role)
            db.flush()

            print(
                f"Rol creado: {role_name}"
            )
        else:
            role.is_system_role = True
            role.is_active = True

            print(
                f"Rol existente: {role_name}"
            )

        if role_name == ADMINISTRATOR_ROLE:
            role.permissions = permissions

            print(
                "Todos los permisos fueron asignados "
                "al rol Administrator."
            )

        roles.append(role)

    return roles


# ==========================================================
# Asignación del rol Administrator
# ==========================================================

def assign_administrator_role(
    db: Session,
    company_id: UUID,
    user_id: UUID,
) -> None:
    user = db.get(User, user_id)

    if user is None:
        raise ValueError(
            f"No existe un usuario con ID: {user_id}"
        )

    if user.company_id != company_id:
        raise ValueError(
            "El usuario indicado no pertenece "
            "a la empresa proporcionada."
        )

    administrator_role = db.scalar(
        select(Role).where(
            Role.company_id == company_id,
            Role.name == ADMINISTRATOR_ROLE,
        )
    )

    if administrator_role is None:
        raise ValueError(
            "No se encontró el rol Administrator."
        )

    if administrator_role not in user.roles:
        user.roles.append(administrator_role)

        print(
            f"Rol Administrator asignado al usuario: "
            f"{user.email}"
        )
    else:
        print(
            f"El usuario {user.email} ya tiene asignado "
            "el rol Administrator."
        )


# ==========================================================
# Ejecución principal del Seeder
# ==========================================================

def seed_rbac(
    company_id: UUID,
    user_id: UUID | None = None,
) -> None:
    db = SessionLocal()

    try:
        company = db.get(Company, company_id)

        if company is None:
            raise ValueError(
                f"No existe una empresa con ID: {company_id}"
            )

        print(
            f"Inicializando RBAC para la empresa: "
            f"{company.name}"
        )

        permissions = get_or_create_permissions(db)

        get_or_create_roles(
            db=db,
            company_id=company_id,
            permissions=permissions,
        )

        if user_id is not None:
            assign_administrator_role(
                db=db,
                company_id=company_id,
                user_id=user_id,
            )

        db.commit()

        print("")
        print("RBAC inicializado correctamente.")

        if user_id is not None:
            print(
                "Rol Administrator validado y asignado "
                "correctamente."
            )

    except Exception as error:
        db.rollback()

        print("")
        print("No fue posible inicializar RBAC.")
        print(f"Error: {error}")

        raise

    finally:
        db.close()


# ==========================================================
# Argumentos de consola
# ==========================================================

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inicializa los roles y permisos del ERP."
        ),
    )

    parser.add_argument(
        "--company-id",
        required=True,
        type=UUID,
        help="UUID de la empresa.",
    )

    parser.add_argument(
        "--user-id",
        required=False,
        type=UUID,
        help=(
            "UUID del usuario al que se asignará "
            "el rol Administrator."
        ),
    )

    return parser.parse_args()


# ==========================================================
# Punto de entrada
# ==========================================================

if __name__ == "__main__":
    arguments = parse_arguments()

    seed_rbac(
        company_id=arguments.company_id,
        user_id=arguments.user_id,
    )