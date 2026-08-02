from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.rbac.constants import (
    SUPPLIERS_CREATE,
    SUPPLIERS_DELETE,
    SUPPLIERS_READ,
    SUPPLIERS_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.supplier.repository import SupplierRepository
from app.modules.supplier.schemas import (
    SupplierCreate,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)
from app.modules.supplier.service import SupplierService
from app.modules.user.model import User


router = APIRouter(
    prefix="/suppliers",
    tags=["Proveedores"],
)


# ==========================================================
# Dependencies
# ==========================================================


def get_supplier_service(
    db: Session = Depends(get_db),
) -> SupplierService:
    repository = SupplierRepository(db)

    return SupplierService(repository)


def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:
    repository = AuditRepository(db)

    return AuditService(repository)


# ==========================================================
# Suppliers
# ==========================================================


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier(
    data: SupplierCreate,
    current_user: User = Depends(
        require_permission(SUPPLIERS_CREATE)
    ),
    service: SupplierService = Depends(get_supplier_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    supplier = service.create_supplier(
        data=data,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="suppliers",
        action="create",
        entity_type="Supplier",
        entity_id=str(supplier.id),
        description="Se creó un proveedor.",
        details={
            "tax_id": supplier.tax_id,
            "business_name": supplier.business_name,
            "trade_name": supplier.trade_name,
            "is_active": supplier.is_active,
        },
    )

    return supplier


@router.get(
    "",
    response_model=SupplierListResponse,
)
def list_suppliers(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(
        require_permission(SUPPLIERS_READ)
    ),
    service: SupplierService = Depends(get_supplier_service),
):
    return service.list_suppliers(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def get_supplier(
    supplier_id: UUID,
    current_user: User = Depends(
        require_permission(SUPPLIERS_READ)
    ),
    service: SupplierService = Depends(get_supplier_service),
):
    return service.get_supplier(
        supplier_id=supplier_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    current_user: User = Depends(
        require_permission(SUPPLIERS_UPDATE)
    ),
    service: SupplierService = Depends(get_supplier_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    supplier = service.update_supplier(
        supplier_id=supplier_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="suppliers",
        action="update",
        entity_type="Supplier",
        entity_id=str(supplier.id),
        description="Se actualizó un proveedor.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
        },
    )

    return supplier


@router.delete(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def deactivate_supplier(
    supplier_id: UUID,
    current_user: User = Depends(
        require_permission(SUPPLIERS_DELETE)
    ),
    service: SupplierService = Depends(get_supplier_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    supplier = service.deactivate_supplier(
        supplier_id=supplier_id,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="suppliers",
        action="deactivate",
        entity_type="Supplier",
        entity_id=str(supplier.id),
        description="Se desactivó un proveedor.",
        details={
            "tax_id": supplier.tax_id,
            "business_name": supplier.business_name,
            "is_active": supplier.is_active,
        },
    )

    return supplier