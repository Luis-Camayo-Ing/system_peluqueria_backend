from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.exception_handlers import register_exception_handlers


app = FastAPI(
    title="Sistema de Peluquería",
    description="API para gestionar clientes, empleados, servicios y citas.",
    version="0.1.0",
)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/", tags=["Inicio"])
def inicio() -> dict[str, str]:
    return {
        "mensaje": "API del sistema de peluquería funcionando"
    }


register_exception_handlers(app)