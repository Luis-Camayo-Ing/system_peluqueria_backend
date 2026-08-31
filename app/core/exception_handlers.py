from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.modules.company.exceptions import (
    CompanyAlreadyExistsError,
    CompanyNotFoundError,
)
from app.modules.rbac.exceptions import (
    PermissionAlreadyAssignedException,
    PermissionAlreadyExistsException,
    PermissionNotFoundException,
    RBACCompanyScopeException,
    RoleAlreadyExistsException,
    RoleNotFoundException,
    SystemPermissionDeletionException,
    SystemPermissionModificationException,
    SystemRoleDeletionException,
    SystemRoleModificationException,
    UserRoleAlreadyAssignedException,
)
from app.modules.user.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserCompanyScopeError,
    UserNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CompanyAlreadyExistsError)
    async def company_already_exists_handler(
        request: Request,
        exc: CompanyAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "error_code": "COMPANY_ALREADY_EXISTS",
            },
        )

    @app.exception_handler(CompanyNotFoundError)
    async def company_not_found_handler(
        request: Request,
        exc: CompanyNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(exc),
                "error_code": "COMPANY_NOT_FOUND",
            },
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentialsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": str(exc),
                "error_code": "INVALID_CREDENTIALS",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InactiveUserError)
    async def inactive_user_handler(
        request: Request,
        exc: InactiveUserError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": str(exc),
                "error_code": "INACTIVE_USER",
            },
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request,
        exc: UserNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(exc),
                "error_code": "USER_NOT_FOUND",
            },
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(
        request: Request,
        exc: UserAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "error_code": "USER_ALREADY_EXISTS",
            },
        )

    @app.exception_handler(UserCompanyScopeError)
    async def user_scope_handler(
        request: Request,
        exc: UserCompanyScopeError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": str(exc),
                "error_code": "USER_COMPANY_SCOPE",
            },
        )

    rbac_not_found = (
        RoleNotFoundException,
        PermissionNotFoundException,
    )
    rbac_conflict = (
        RoleAlreadyExistsException,
        PermissionAlreadyExistsException,
        UserRoleAlreadyAssignedException,
        PermissionAlreadyAssignedException,
    )
    rbac_forbidden = (
        SystemRoleModificationException,
        SystemRoleDeletionException,
        SystemPermissionModificationException,
        SystemPermissionDeletionException,
        RBACCompanyScopeException,
    )

    for exception_type in rbac_not_found:
        app.add_exception_handler(
            exception_type,
            _rbac_handler(status.HTTP_404_NOT_FOUND),
        )

    for exception_type in rbac_conflict:
        app.add_exception_handler(
            exception_type,
            _rbac_handler(status.HTTP_409_CONFLICT),
        )

    for exception_type in rbac_forbidden:
        app.add_exception_handler(
            exception_type,
            _rbac_handler(status.HTTP_403_FORBIDDEN),
        )


def _rbac_handler(status_code: int):
    async def handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": str(exc),
                "error_code": "RBAC_OPERATION_REJECTED",
            },
        )

    return handler
