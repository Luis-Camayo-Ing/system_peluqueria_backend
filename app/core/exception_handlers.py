from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.modules.company.exceptions import (
    CompanyAlreadyExistsError,
    CompanyNotFoundError,
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