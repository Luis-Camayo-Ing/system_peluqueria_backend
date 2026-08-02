from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.purchase.model import PurchaseOrderStatus
from app.modules.purchase.repository import PurchaseRepository
from app.modules.purchase.schemas import (
    PurchaseOrderCancel,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseReceiptCreate,
    PurchaseReceiptListResponse,
    PurchaseReceiptResponse,
)
from app.modules.purchase.service import PurchaseService
from app.modules.rbac.constants import (
    PURCHASES_APPROVE,
    PURCHASES_CANCEL,
    PURCHASES_CREATE,
    PURCHASES_READ,
    PURCHASES_RECEIVE,
    PURCHASES_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.user.model import User


router = APIRouter(
    prefix="/purchases",
    tags=["Compras"],
)


# ==========================================================
# Dependencies
# ==========================================================


def get_purchase_service(
    db: Session = Depends(get_db),
) -> PurchaseService:
    repository = PurchaseRepository(db)

    return PurchaseService(
        repository=repository,
    )


def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:
    repository = AuditRepository(db)

    return AuditService(repository)


# ==========================================================
# Purchase Orders
# ==========================================================


@router.post(
    "/orders",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_order(
    data: PurchaseOrderCreate,
    current_user: User = Depends(
        require_permission(PURCHASES_CREATE)
    ),
    service: PurchaseService = Depends(get_purchase_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    order = service.create_order(
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="purchases",
        action="create_order",
        entity_type="PurchaseOrder",
        entity_id=str(order.id),
        description="Se creó una orden de compra.",
        details={
            "order_number": order.order_number,
            "supplier_id": str(order.supplier_id),
            "status": order.status.value,
            "products_count": len(order.details),
            "subtotal": str(order.subtotal),
            "tax_amount": str(order.tax_amount),
            "discount_amount": str(order.discount_amount),
            "total_amount": str(order.total_amount),
        },
    )

    return order


@router.get(
    "/orders",
    response_model=PurchaseOrderListResponse,
)
def list_purchase_orders(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    order_status: PurchaseOrderStatus | None = Query(
        default=None,
        alias="status",
    ),
    supplier_id: UUID | None = Query(
        default=None,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=150,
    ),
    current_user: User = Depends(
        require_permission(PURCHASES_READ)
    ),
    service: PurchaseService = Depends(get_purchase_service),
):
    return service.list_orders(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        status=order_status,
        supplier_id=supplier_id,
        search=search,
    )


@router.get(
    "/orders/{order_id}",
    response_model=PurchaseOrderResponse,
)
def get_purchase_order(
    order_id: UUID,
    current_user: User = Depends(
        require_permission(PURCHASES_READ)
    ),
    service: PurchaseService = Depends(get_purchase_service),
):
    return service.get_order(
        order_id=order_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/orders/{order_id}",
    response_model=PurchaseOrderResponse,
)
def update_purchase_order(
    order_id: UUID,
    data: PurchaseOrderUpdate,
    current_user: User = Depends(
        require_permission(PURCHASES_UPDATE)
    ),
    service: PurchaseService = Depends(get_purchase_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    order = service.update_order(
        order_id=order_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="purchases",
        action="update_order",
        entity_type="PurchaseOrder",
        entity_id=str(order.id),
        description="Se actualizó una orden de compra.",
        details={
            "order_number": order.order_number,
            "status": order.status.value,
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
            "total_amount": str(order.total_amount),
        },
    )

    return order


@router.post(
    "/orders/{order_id}/approve",
    response_model=PurchaseOrderResponse,
)
def approve_purchase_order(
    order_id: UUID,
    current_user: User = Depends(
        require_permission(PURCHASES_APPROVE)
    ),
    service: PurchaseService = Depends(get_purchase_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    order = service.approve_order(
        order_id=order_id,
        company_id=current_user.company_id,
        user_id=current_user.id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="purchases",
        action="approve_order",
        entity_type="PurchaseOrder",
        entity_id=str(order.id),
        description="Se aprobó una orden de compra.",
        details={
            "order_number": order.order_number,
            "status": order.status.value,
            "approved_by_user_id": str(
                order.approved_by_user_id
            ),
            "approved_at": (
                order.approved_at.isoformat()
                if order.approved_at is not None
                else None
            ),
            "total_amount": str(order.total_amount),
        },
    )

    return order


@router.post(
    "/orders/{order_id}/cancel",
    response_model=PurchaseOrderResponse,
)
def cancel_purchase_order(
    order_id: UUID,
    data: PurchaseOrderCancel,
    current_user: User = Depends(
        require_permission(PURCHASES_CANCEL)
    ),
    service: PurchaseService = Depends(get_purchase_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    order = service.cancel_order(
        order_id=order_id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="purchases",
        action="cancel_order",
        entity_type="PurchaseOrder",
        entity_id=str(order.id),
        description="Se canceló una orden de compra.",
        details={
            "order_number": order.order_number,
            "status": order.status.value,
            "reason": order.cancellation_reason,
            "cancelled_by_user_id": str(
                order.cancelled_by_user_id
            ),
            "cancelled_at": (
                order.cancelled_at.isoformat()
                if order.cancelled_at is not None
                else None
            ),
        },
    )

    return order


# ==========================================================
# Purchase Receipts
# ==========================================================


@router.post(
    "/orders/{order_id}/receipts",
    response_model=PurchaseReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def receive_purchase_order(
    order_id: UUID,
    data: PurchaseReceiptCreate,
    current_user: User = Depends(
        require_permission(PURCHASES_RECEIVE)
    ),
    service: PurchaseService = Depends(get_purchase_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    receipt = service.receive_order(
        order_id=order_id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="purchases",
        action="receive_order",
        entity_type="PurchaseReceipt",
        entity_id=str(receipt.id),
        description=(
            "Se registró una recepción de compra y su "
            "entrada automática al inventario."
        ),
        details={
            "purchase_order_id": str(
                receipt.purchase_order_id
            ),
            "receipt_number": receipt.receipt_number,
            "supplier_invoice_number": (
                receipt.supplier_invoice_number
            ),
            "inventory_movement_id": str(
                receipt.inventory_movement_id
            ),
            "products_count": len(receipt.details),
            "subtotal": str(receipt.subtotal),
            "tax_amount": str(receipt.tax_amount),
            "discount_amount": str(
                receipt.discount_amount
            ),
            "total_amount": str(receipt.total_amount),
        },
    )

    return receipt


@router.get(
    "/receipts",
    response_model=PurchaseReceiptListResponse,
)
def list_purchase_receipts(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    order_id: UUID | None = Query(
        default=None,
    ),
    supplier_id: UUID | None = Query(
        default=None,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=150,
    ),
    received_from: datetime | None = Query(
        default=None,
    ),
    received_to: datetime | None = Query(
        default=None,
    ),
    current_user: User = Depends(
        require_permission(PURCHASES_READ)
    ),
    service: PurchaseService = Depends(get_purchase_service),
):
    return service.list_receipts(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        order_id=order_id,
        supplier_id=supplier_id,
        search=search,
        received_from=received_from,
        received_to=received_to,
    )


@router.get(
    "/receipts/{receipt_id}",
    response_model=PurchaseReceiptResponse,
)
def get_purchase_receipt(
    receipt_id: UUID,
    current_user: User = Depends(
        require_permission(PURCHASES_READ)
    ),
    service: PurchaseService = Depends(get_purchase_service),
):
    return service.get_receipt(
        receipt_id=receipt_id,
        company_id=current_user.company_id,
    )