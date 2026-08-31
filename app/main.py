from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import SecurityHeadersMiddleware


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description=(
            "API para gestionar clientes, empleados, servicios, citas "
            "y la operación integral de ERP Beauty Pro."
        ),
        version=settings.app_version,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=(
            None if settings.is_production else "/openapi.json"
        ),
    )

    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    application.add_middleware(SecurityHeadersMiddleware)

    if settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    application.include_router(
        api_router,
        prefix="/api/v1",
    )

    @application.get("/", tags=["Inicio"])
    def inicio() -> dict[str, str]:
        return {
            "mensaje": "API del sistema de peluquería funcionando"
        }

    register_exception_handlers(application)
    return application


app = create_application()
