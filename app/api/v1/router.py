from fastapi import APIRouter

from app.api.v1.endpoints import salud
from app.modules.auth.router import router as auth_router
from app.modules.company.router import router as company_router
from app.modules.user.router import router as user_router
from app.modules.customer.router import router as customer_router


api_router = APIRouter()

api_router.include_router(
    salud.router,
    tags=["Salud"],
)

api_router.include_router(company_router)
api_router.include_router(user_router)
api_router.include_router(auth_router)
api_router.include_router(customer_router)