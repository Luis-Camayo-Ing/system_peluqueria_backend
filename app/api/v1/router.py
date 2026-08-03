from fastapi import APIRouter

from app.api.v1.endpoints import salud

from app.modules.appointment.router import router as appointment_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.cash_register.router import router as cash_register_router
from app.modules.company.router import router as company_router
from app.modules.customer.router import router as customer_router
from app.modules.employee.router import router as employee_router
from app.modules.inventory.router import router as inventory_router
from app.modules.purchase.router import router as purchase_router
from app.modules.sale.router import router as sale_router
from app.modules.service.router import router as service_router
from app.modules.supplier.router import router as supplier_router
from app.modules.user.router import router as user_router


api_router = APIRouter()

api_router.include_router(
    salud.router,
    tags=["Salud"],
)

api_router.include_router(company_router)

api_router.include_router(user_router)

api_router.include_router(auth_router)

api_router.include_router(customer_router)

api_router.include_router(supplier_router)

api_router.include_router(purchase_router)

api_router.include_router(sale_router)

api_router.include_router(service_router)

api_router.include_router(
    employee_router,
    prefix="/employees",
    tags=["Employees"],
)

api_router.include_router(audit_router)

api_router.include_router(appointment_router)

api_router.include_router(inventory_router)

api_router.include_router(cash_register_router)