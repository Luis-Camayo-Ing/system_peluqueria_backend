from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.constants import (
    PERMISSIONS_ASSIGN,
    PERMISSIONS_CREATE,
    PERMISSIONS_DELETE,
    PERMISSIONS_READ,
    PERMISSIONS_UPDATE,
    ROLES_ASSIGN,
    ROLES_CREATE,
    ROLES_DELETE,
    ROLES_READ,
    ROLES_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.rbac.exceptions import RBACCompanyScopeException
from app.modules.rbac.schemas import (
    AssignPermissionSchema,
    AssignRoleSchema,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.modules.rbac.service import RBACService
from app.modules.user.model import User


router = APIRouter()


# ==========================================================
# Roles
# ==========================================================

@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(ROLES_CREATE),
        )
    ],
)
def create_role(
    data: RoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoleResponse:
    return RBACService(db).create_role(
        data,
        company_id=current_user.company_id,
    )


@router.get(
    "/roles/company/{company_id}",
    response_model=list[RoleResponse],
    dependencies=[
        Depends(
            require_permission(ROLES_READ),
        )
    ],
)
def get_roles(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    if company_id != current_user.company_id:
        raise RBACCompanyScopeException()

    return RBACService(db).get_roles_by_company(company_id)


@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[
        Depends(
            require_permission(ROLES_READ),
        )
    ],
)
def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoleResponse:
    return RBACService(db).get_role(
        role_id,
        company_id=current_user.company_id,
    )


@router.put(
    "/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[
        Depends(
            require_permission(ROLES_UPDATE),
        )
    ],
)
def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoleResponse:
    return RBACService(db).update_role(
        role_id=role_id,
        data=data,
        company_id=current_user.company_id,
    )


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_permission(ROLES_DELETE),
        )
    ],
)
def delete_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    RBACService(db).delete_role(
        role_id,
        company_id=current_user.company_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ==========================================================
# Permissions
# ==========================================================

@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(PERMISSIONS_CREATE),
        )
    ],
)
def create_permission(
    data: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PermissionResponse:
    return RBACService(db).create_permission(data)


@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
    dependencies=[
        Depends(
            require_permission(PERMISSIONS_READ),
        )
    ],
)
def get_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PermissionResponse]:
    return RBACService(db).get_permissions()


@router.put(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[
        Depends(
            require_permission(PERMISSIONS_UPDATE),
        )
    ],
)
def update_permission(
    permission_id: UUID,
    data: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PermissionResponse:
    return RBACService(db).update_permission(
        permission_id=permission_id,
        data=data,
    )


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_permission(PERMISSIONS_DELETE),
        )
    ],
)
def delete_permission(
    permission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    RBACService(db).delete_permission(permission_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ==========================================================
# Assignments
# ==========================================================

@router.post(
    "/roles/assign-user",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_permission(ROLES_ASSIGN),
        )
    ],
)
def assign_role(
    data: AssignRoleSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    RBACService(db).assign_role_to_user(
        user_id=data.user_id,
        role_id=data.role_id,
        company_id=current_user.company_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "/roles/assign-permission",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_permission(PERMISSIONS_ASSIGN),
        )
    ],
)
def assign_permission(
    data: AssignPermissionSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    RBACService(db).assign_permission_to_role(
        role_id=data.role_id,
        permission_id=data.permission_id,
        company_id=current_user.company_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
