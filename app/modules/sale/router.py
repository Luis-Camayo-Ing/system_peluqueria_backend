"""REST endpoints for sales and point-of-sale operations."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.rbac.constants import (
    SALES_CANCEL,
    SALES_CREATE,
    SALES_READ,
    SALES_RECEIPT,
    SALES_SEND,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.sale.delivery import (
    SmtpReceiptSender,
    build_default_receipt_message,
    build_default_receipt_subject,
    build_default_whatsapp_message,
    build_whatsapp_url,
)
from app.modules.sale.exceptions import (
    SaleEmailConfigurationException,
    SaleEmailSendingException,
    SaleReceiptGenerationException,
    SaleReceiptRecipientRequiredException,
)
from app.modules.sale.model import (
    SaleItemType,
    SaleStatus,
)
from app.modules.sale.repository import SaleRepository
from app.modules.sale.receipt import (
    build_sale_receipt_filename,
    build_sale_receipt_pdf,
)
from app.modules.sale.schemas import (
    SaleCancelRequest,
    SaleCreate,
    SaleListResponse,
    SaleReceiptEmailRequest,
    SaleReceiptEmailResponse,
    SaleReceiptWhatsAppRequest,
    SaleReceiptWhatsAppResponse,
    SaleResponse,
)
from app.modules.sale.service import SaleService
from app.modules.user.model import User


router = APIRouter(
    prefix="/sales",
    tags=["Ventas"],
)


# ==========================================================
# Dependencies
# ==========================================================


def get_sale_service(
    db: Session = Depends(get_db),
) -> SaleService:
    """Build the transactional sale service."""

    repository = SaleRepository(db)

    return SaleService(
        repository=repository,
    )


def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:
    """Build the audit service."""

    return AuditService(
        AuditRepository(db),
    )


def get_receipt_sender() -> SmtpReceiptSender:
    """Build the SMTP receipt sender."""

    return SmtpReceiptSender(
        settings=settings,
    )


# ==========================================================
# Sales
# ==========================================================


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    data: SaleCreate,
    current_user: User = Depends(
        require_permission(SALES_CREATE)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
    audit_service: AuditService = Depends(
        get_audit_service
    ),
):
    """Complete a product, service or mixed sale."""

    sale = sale_service.create_sale(
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    product_count = sum(
        1
        for detail in sale.details
        if detail.item_type == SaleItemType.PRODUCT
    )

    service_count = sum(
        1
        for detail in sale.details
        if detail.item_type == SaleItemType.SERVICE
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="sales",
        action="create_sale",
        entity_type="Sale",
        entity_id=str(sale.id),
        description=(
            "Se completó una venta y se registraron "
            "sus movimientos automáticos."
        ),
        details={
            "sale_number": sale.sale_number,
            "status": sale.status.value,
            "customer_id": (
                str(sale.customer_id)
                if sale.customer_id is not None
                else None
            ),
            "cash_session_id": str(
                sale.cash_session_id
            ),
            "products_count": product_count,
            "services_count": service_count,
            "payments_count": len(sale.payments),
            "payment_methods": [
                payment.payment_method.value
                for payment in sale.payments
            ],
            "subtotal": str(sale.subtotal),
            "discount_amount": str(
                sale.discount_amount
            ),
            "tax_amount": str(sale.tax_amount),
            "total_amount": str(
                sale.total_amount
            ),
            "paid_amount": str(
                sale.paid_amount
            ),
            "change_amount": str(
                sale.change_amount
            ),
            "inventory_movement_id": (
                str(sale.inventory_movement_id)
                if sale.inventory_movement_id
                is not None
                else None
            ),
            "cash_transaction_id": (
                str(sale.cash_transaction_id)
                if sale.cash_transaction_id
                is not None
                else None
            ),
        },
    )

    return sale


@router.get(
    "",
    response_model=SaleListResponse,
)
def list_sales(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    sale_status: SaleStatus | None = Query(
        default=None,
        alias="status",
    ),
    customer_id: UUID | None = Query(
        default=None,
    ),
    cash_session_id: UUID | None = Query(
        default=None,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=150,
    ),
    sold_from: datetime | None = Query(
        default=None,
    ),
    sold_to: datetime | None = Query(
        default=None,
    ),
    current_user: User = Depends(
        require_permission(SALES_READ)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
):
    """List sales belonging to the authenticated company."""

    return sale_service.list_sales(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        status=sale_status,
        customer_id=customer_id,
        cash_session_id=cash_session_id,
        search=search,
        sold_from=sold_from,
        sold_to=sold_to,
    )


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
)
def get_sale(
    sale_id: UUID,
    current_user: User = Depends(
        require_permission(SALES_READ)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
):
    """Return one sale with details and payments."""

    return sale_service.get_sale(
        sale_id=sale_id,
        company_id=current_user.company_id,
    )


@router.get(
    "/{sale_id}/receipt.pdf",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/pdf": {},
            },
            "description": (
                "Comprobante interno de venta en PDF."
            ),
        },
    },
)
def download_sale_receipt(
    sale_id: UUID,
    current_user: User = Depends(
        require_permission(SALES_RECEIPT)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
    audit_service: AuditService = Depends(
        get_audit_service
    ),
) -> Response:
    """Generate and download the internal sale receipt."""

    sale = sale_service.get_sale(
        sale_id=sale_id,
        company_id=current_user.company_id,
    )

    pdf_content = build_sale_receipt_pdf(
        sale
    )

    filename = build_sale_receipt_filename(
        sale
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="sales",
        action="download_receipt",
        entity_type="Sale",
        entity_id=str(sale.id),
        description=(
            "Se generó y descargó el comprobante "
            "interno de una venta."
        ),
        details={
            "sale_number": sale.sale_number,
            "status": sale.status.value,
            "filename": filename,
            "content_type": "application/pdf",
            "size_bytes": len(pdf_content),
            "receipt_type": "internal",
            "is_electronic_invoice": False,
        },
    )

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Cache-Control": "private, no-store",
        },
    )



@router.post(
    "/{sale_id}/receipt/email",
    response_model=SaleReceiptEmailResponse,
)
def send_sale_receipt_email(
    sale_id: UUID,
    data: SaleReceiptEmailRequest,
    current_user: User = Depends(
        require_permission(SALES_SEND)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
    receipt_sender: SmtpReceiptSender = Depends(
        get_receipt_sender
    ),
    audit_service: AuditService = Depends(
        get_audit_service
    ),
) -> SaleReceiptEmailResponse:
    """Send the internal PDF receipt by email."""

    sale = sale_service.get_sale(
        sale_id=sale_id,
        company_id=current_user.company_id,
    )

    recipient_email = (
        str(data.recipient_email)
        if data.recipient_email is not None
        else sale.customer_email
    )

    if not recipient_email:
        raise SaleReceiptRecipientRequiredException()

    subject = (
        data.subject
        or build_default_receipt_subject(sale)
    )

    message = (
        data.message
        or build_default_receipt_message(sale)
    )

    filename = build_sale_receipt_filename(
        sale
    )

    try:
        pdf_content = build_sale_receipt_pdf(
            sale
        )

        receipt_sender.send(
            recipient_email=recipient_email,
            subject=subject,
            body=message,
            pdf_content=pdf_content,
            filename=filename,
        )

    except (
        SaleReceiptGenerationException,
        SaleEmailConfigurationException,
        SaleEmailSendingException,
    ) as exception:
        audit_service.log(
            company_id=current_user.company_id,
            user_id=current_user.id,
            module="sales",
            action="send_receipt_email",
            entity_type="Sale",
            entity_id=str(sale.id),
            description=(
                "No fue posible enviar el comprobante "
                "interno de una venta por correo."
            ),
            details={
                "sale_number": sale.sale_number,
                "recipient_email": recipient_email,
                "filename": filename,
                "delivery_channel": "email",
                "error_type": type(exception).__name__,
            },
            success=False,
        )

        raise

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="sales",
        action="send_receipt_email",
        entity_type="Sale",
        entity_id=str(sale.id),
        description=(
            "Se envió el comprobante interno "
            "de una venta por correo."
        ),
        details={
            "sale_number": sale.sale_number,
            "recipient_email": recipient_email,
            "filename": filename,
            "content_type": "application/pdf",
            "size_bytes": len(pdf_content),
            "delivery_channel": "email",
            "receipt_type": "internal",
            "is_electronic_invoice": False,
        },
        success=True,
    )

    return SaleReceiptEmailResponse(
        sale_id=sale.id,
        sale_number=sale.sale_number,
        recipient_email=recipient_email,
        filename=filename,
    )


@router.post(
    "/{sale_id}/receipt/whatsapp",
    response_model=SaleReceiptWhatsAppResponse,
)
def build_sale_receipt_whatsapp(
    sale_id: UUID,
    data: SaleReceiptWhatsAppRequest,
    current_user: User = Depends(
        require_permission(SALES_SEND)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
    audit_service: AuditService = Depends(
        get_audit_service
    ),
) -> SaleReceiptWhatsAppResponse:
    """Build a WhatsApp URL without calling the Meta API."""

    sale = sale_service.get_sale(
        sale_id=sale_id,
        company_id=current_user.company_id,
    )

    message = (
        data.message
        or build_default_whatsapp_message(sale)
    )

    url = build_whatsapp_url(
        phone_number=data.phone_number,
        message=message,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="sales",
        action="build_receipt_whatsapp",
        entity_type="Sale",
        entity_id=str(sale.id),
        description=(
            "Se generó un enlace para compartir "
            "el comprobante interno por WhatsApp."
        ),
        details={
            "sale_number": sale.sale_number,
            "phone_number": data.phone_number,
            "delivery_channel": "whatsapp",
            "attachment_included": False,
            "meta_api_used": False,
        },
        success=True,
    )

    return SaleReceiptWhatsAppResponse(
        sale_id=sale.id,
        sale_number=sale.sale_number,
        phone_number=data.phone_number,
        message=message,
        url=url,
    )


@router.post(
    "/{sale_id}/cancel",
    response_model=SaleResponse,
)
def cancel_sale(
    sale_id: UUID,
    data: SaleCancelRequest,
    current_user: User = Depends(
        require_permission(SALES_CANCEL)
    ),
    sale_service: SaleService = Depends(
        get_sale_service
    ),
    audit_service: AuditService = Depends(
        get_audit_service
    ),
):
    """Cancel a sale and reverse stock and cash."""

    sale = sale_service.cancel_sale(
        sale_id=sale_id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="sales",
        action="cancel_sale",
        entity_type="Sale",
        entity_id=str(sale.id),
        description=(
            "Se canceló una venta y se revirtieron "
            "sus movimientos automáticos."
        ),
        details={
            "sale_number": sale.sale_number,
            "status": sale.status.value,
            "reason": sale.cancellation_reason,
            "cancelled_by_user_id": (
                str(sale.cancelled_by_user_id)
                if sale.cancelled_by_user_id
                is not None
                else None
            ),
            "cancelled_at": (
                sale.cancelled_at.isoformat()
                if sale.cancelled_at is not None
                else None
            ),
            "cancellation_inventory_movement_id": (
                str(
                    sale.cancellation_inventory_movement_id
                )
                if (
                    sale.cancellation_inventory_movement_id
                    is not None
                )
                else None
            ),
            "cancellation_cash_transaction_id": (
                str(
                    sale.cancellation_cash_transaction_id
                )
                if (
                    sale.cancellation_cash_transaction_id
                    is not None
                )
                else None
            ),
            "refunded_cash_amount": str(
                sum(
                    (
                        payment.amount
                        for payment in sale.payments
                        if (
                            payment.payment_method.value
                            == "cash"
                        )
                    ),
                    start=0,
                )
            ),
        },
    )

    return sale
