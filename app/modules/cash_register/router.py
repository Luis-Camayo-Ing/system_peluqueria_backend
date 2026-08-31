import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.cash_register.model import (
    CashSessionStatus,
    CashTransactionSource,
    CashTransactionType,
)
from app.modules.cash_register.repository import CashRegisterRepository
from app.modules.cash_register.schemas import (
    CashRegisterCreate,
    CashRegisterListResponse,
    CashRegisterResponse,
    CashRegisterUpdate,
    CashSessionClose,
    CashSessionListResponse,
    CashSessionOpen,
    CashSessionResponse,
    CashSessionSummaryResponse,
    CashTransactionCreate,
    CashTransactionListResponse,
    CashTransactionResponse,
)
from app.modules.cash_register.service import CashRegisterService
from app.modules.rbac.constants import (
    CASH_REGISTERS_CREATE,
    CASH_REGISTERS_DELETE,
    CASH_REGISTERS_READ,
    CASH_REGISTERS_UPDATE,
    CASH_SESSIONS_CLOSE,
    CASH_SESSIONS_OPEN,
    CASH_SESSIONS_READ,
    CASH_TRANSACTIONS_CREATE,
    CASH_TRANSACTIONS_READ,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.user.model import User


router = APIRouter(
    prefix="/cash-register",
    tags=["Cash Register"],
)


# ==========================================================
# Dependencies
# ==========================================================


def get_cash_register_service(
    db: Session = Depends(get_db),
) -> CashRegisterService:
    repository = CashRegisterRepository(db)

    return CashRegisterService(
        repository=repository,
    )


def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:
    return AuditService(
        AuditRepository(db),
    )


# ==========================================================
# Cash Registers
# ==========================================================


@router.post(
    "/registers",
    response_model=CashRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cash_register(
    data: CashRegisterCreate,
    current_user: User = Depends(
        require_permission(CASH_REGISTERS_CREATE)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    cash_register = cash_service.create_register(
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="cash_register",
        action="create_register",
        entity_type="CashRegister",
        entity_id=str(cash_register.id),
        description="Se creó una caja.",
        details={
            "code": cash_register.code,
            "name": cash_register.name,
            "is_active": cash_register.is_active,
        },
    )

    return cash_register


@router.get(
    "/registers",
    response_model=CashRegisterListResponse,
)
def list_cash_registers(
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
        require_permission(CASH_REGISTERS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.list_registers(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )


@router.get(
    "/registers/{cash_register_id}/open-session",
    response_model=CashSessionResponse,
)
def get_open_cash_session(
    cash_register_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(CASH_SESSIONS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.get_open_session(
        cash_register_id=cash_register_id,
        company_id=current_user.company_id,
    )


@router.get(
    "/registers/{cash_register_id}",
    response_model=CashRegisterResponse,
)
def get_cash_register(
    cash_register_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(CASH_REGISTERS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.get_register(
        cash_register_id=cash_register_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/registers/{cash_register_id}",
    response_model=CashRegisterResponse,
)
def update_cash_register(
    cash_register_id: uuid.UUID,
    data: CashRegisterUpdate,
    current_user: User = Depends(
        require_permission(CASH_REGISTERS_UPDATE)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    cash_register = cash_service.update_register(
        cash_register_id=cash_register_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="cash_register",
        action="update_register",
        entity_type="CashRegister",
        entity_id=str(cash_register.id),
        description="Se actualizó una caja.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
        },
    )

    return cash_register


@router.delete(
    "/registers/{cash_register_id}",
    response_model=CashRegisterResponse,
)
def deactivate_cash_register(
    cash_register_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(CASH_REGISTERS_DELETE)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    cash_register = cash_service.deactivate_register(
        cash_register_id=cash_register_id,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="cash_register",
        action="deactivate_register",
        entity_type="CashRegister",
        entity_id=str(cash_register.id),
        description="Se desactivó una caja.",
        details={
            "code": cash_register.code,
            "name": cash_register.name,
            "is_active": cash_register.is_active,
        },
    )

    return cash_register


# ==========================================================
# Cash Sessions
# ==========================================================


@router.post(
    "/sessions/open",
    response_model=CashSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def open_cash_session(
    data: CashSessionOpen,
    current_user: User = Depends(
        require_permission(CASH_SESSIONS_OPEN)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    cash_session = cash_service.open_session(
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="cash_register",
        action="open_session",
        entity_type="CashSession",
        entity_id=str(cash_session.id),
        description="Se abrió una sesión de caja.",
        details={
            "cash_register_id": str(cash_session.cash_register_id),
            "opening_amount": str(cash_session.opening_amount),
            "status": cash_session.status.value,
        },
    )

    return cash_session


@router.get(
    "/sessions",
    response_model=CashSessionListResponse,
)
def list_cash_sessions(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    cash_register_id: uuid.UUID | None = Query(default=None),
    session_status: CashSessionStatus | None = Query(
        default=None,
        alias="status",
    ),
    opened_by_user_id: uuid.UUID | None = Query(default=None),
    opened_from: datetime | None = Query(default=None),
    opened_to: datetime | None = Query(default=None),
    current_user: User = Depends(
        require_permission(CASH_SESSIONS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.list_sessions(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        cash_register_id=cash_register_id,
        status=session_status,
        opened_by_user_id=opened_by_user_id,
        opened_from=opened_from,
        opened_to=opened_to,
    )


@router.get(
    "/sessions/{cash_session_id}/summary",
    response_model=CashSessionSummaryResponse,
)
def get_cash_session_summary(
    cash_session_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(CASH_SESSIONS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.get_session_summary(
        cash_session_id=cash_session_id,
        company_id=current_user.company_id,
    )


@router.post(
    "/sessions/{cash_session_id}/close",
    response_model=CashSessionResponse,
)
def close_cash_session(
    cash_session_id: uuid.UUID,
    data: CashSessionClose,
    current_user: User = Depends(
        require_permission(CASH_SESSIONS_CLOSE)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    cash_session = cash_service.close_session(
        cash_session_id=cash_session_id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="cash_register",
        action="close_session",
        entity_type="CashSession",
        entity_id=str(cash_session.id),
        description="Se cerró una sesión de caja.",
        details={
            "cash_register_id": str(cash_session.cash_register_id),
            "expected_amount": str(cash_session.expected_amount),
            "counted_amount": str(cash_session.counted_amount),
            "difference_amount": str(cash_session.difference_amount),
            "status": cash_session.status.value,
        },
    )

    return cash_session


@router.get(
    "/sessions/{cash_session_id}",
    response_model=CashSessionResponse,
)
def get_cash_session(
    cash_session_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(CASH_SESSIONS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.get_session(
        cash_session_id=cash_session_id,
        company_id=current_user.company_id,
    )


# ==========================================================
# Cash Transactions
# ==========================================================


@router.post(
    "/sessions/{cash_session_id}/transactions",
    response_model=CashTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cash_transaction(
    cash_session_id: uuid.UUID,
    data: CashTransactionCreate,
    current_user: User = Depends(
        require_permission(CASH_TRANSACTIONS_CREATE)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    cash_transaction = cash_service.create_transaction(
        cash_session_id=cash_session_id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="cash_register",
        action="create_transaction",
        entity_type="CashTransaction",
        entity_id=str(cash_transaction.id),
        description="Se registró un movimiento de caja.",
        details={
            "cash_session_id": str(cash_transaction.cash_session_id),
            "transaction_type": cash_transaction.transaction_type.value,
            "source": cash_transaction.source.value,
            "amount": str(cash_transaction.amount),
            "reference": cash_transaction.reference,
        },
    )

    return cash_transaction


@router.get(
    "/transactions",
    response_model=CashTransactionListResponse,
)
def list_cash_transactions(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    cash_session_id: uuid.UUID | None = Query(default=None),
    transaction_type: CashTransactionType | None = Query(default=None),
    source: CashTransactionSource | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    reference: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    current_user: User = Depends(
        require_permission(CASH_TRANSACTIONS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.list_transactions(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        cash_session_id=cash_session_id,
        transaction_type=transaction_type,
        source=source,
        user_id=user_id,
        reference=reference,
        created_from=created_from,
        created_to=created_to,
    )


@router.get(
    "/transactions/{cash_transaction_id}",
    response_model=CashTransactionResponse,
)
def get_cash_transaction(
    cash_transaction_id: uuid.UUID,
    current_user: User = Depends(
        require_permission(CASH_TRANSACTIONS_READ)
    ),
    cash_service: CashRegisterService = Depends(
        get_cash_register_service
    ),
):
    return cash_service.get_transaction(
        cash_transaction_id=cash_transaction_id,
        company_id=current_user.company_id,
    )