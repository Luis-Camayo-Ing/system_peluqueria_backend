import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    ProductCategoryCreate,
    ProductCategoryListResponse,
    ProductCategoryResponse,
    ProductCategoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.modules.inventory.service import InventoryService
from app.modules.rbac.constants import (
    INVENTORY_CREATE,
    INVENTORY_DELETE,
    INVENTORY_READ,
    INVENTORY_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.user.model import User


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


# ==========================================================
# Dependencies
# ==========================================================


def get_inventory_service(
    db: Session = Depends(get_db),
) -> InventoryService:
    repository = InventoryRepository(db)

    return InventoryService(
        repository=repository,
    )


def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:
    return AuditService(
        AuditRepository(db),
    )


# ==========================================================
# Product Categories
# ==========================================================


@router.post(
    "/categories",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: ProductCategoryCreate,
    current_user: User = Depends(
        require_permission(INVENTORY_CREATE)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    category = inventory_service.create_category(
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="inventory",
        action="create_category",
        entity_type="ProductCategory",
        entity_id=str(category.id),
        description="Se creó una categoría de productos.",
        details={
            "name": category.name,
            "is_active": category.is_active,
        },
    )

    return category


@router.get(
    "/categories",
    response_model=ProductCategoryListResponse,
)
def list_categories(
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
        require_permission(INVENTORY_READ)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
):
    return inventory_service.list_categories(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )


@router.get(
    "/categories/{category_id}",
    response_model=ProductCategoryResponse,
)
def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(INVENTORY_READ)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
):
    return inventory_service.get_category(
        category_id=category_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/categories/{category_id}",
    response_model=ProductCategoryResponse,
)
def update_category(
    category_id: uuid.UUID,
    data: ProductCategoryUpdate,
    current_user: User = Depends(
        require_permission(INVENTORY_UPDATE)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    category = inventory_service.update_category(
        category_id=category_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="inventory",
        action="update_category",
        entity_type="ProductCategory",
        entity_id=str(category.id),
        description="Se actualizó una categoría de productos.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
        },
    )

    return category


@router.delete(
    "/categories/{category_id}",
    response_model=ProductCategoryResponse,
)
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(INVENTORY_DELETE)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    category = inventory_service.delete_category(
        category_id=category_id,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="inventory",
        action="deactivate_category",
        entity_type="ProductCategory",
        entity_id=str(category.id),
        description="Se desactivó una categoría de productos.",
        details={
            "name": category.name,
            "is_active": category.is_active,
        },
    )

    return category


# ==========================================================
# Products
# ==========================================================


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    current_user: User = Depends(
        require_permission(INVENTORY_CREATE)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    product = inventory_service.create_product(
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="inventory",
        action="create_product",
        entity_type="Product",
        entity_id=str(product.id),
        description="Se creó un producto.",
        details={
            "code": product.code,
            "barcode": product.barcode,
            "name": product.name,
            "category_id": str(product.category_id),
            "purchase_price": str(product.purchase_price),
            "sale_price": str(product.sale_price),
            "current_stock": str(product.current_stock),
            "unit": product.unit,
            "is_active": product.is_active,
        },
    )

    return product


@router.get(
    "/products",
    response_model=ProductListResponse,
)
def list_products(
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
        max_length=150,
    ),
    category_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    low_stock: bool | None = Query(default=None),
    current_user: User = Depends(
        require_permission(INVENTORY_READ)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
):
    return inventory_service.list_products(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        is_active=is_active,
        low_stock=low_stock,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(INVENTORY_READ)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
):
    return inventory_service.get_product(
        product_id=product_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: User = Depends(
        require_permission(INVENTORY_UPDATE)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    product = inventory_service.update_product(
        product_id=product_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="inventory",
        action="update_product",
        entity_type="Product",
        entity_id=str(product.id),
        description="Se actualizó un producto.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
        },
    )

    return product


@router.delete(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(INVENTORY_DELETE)
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    product = inventory_service.delete_product(
        product_id=product_id,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="inventory",
        action="deactivate_product",
        entity_type="Product",
        entity_id=str(product.id),
        description="Se desactivó un producto.",
        details={
            "code": product.code,
            "name": product.name,
            "is_active": product.is_active,
        },
    )

    return product