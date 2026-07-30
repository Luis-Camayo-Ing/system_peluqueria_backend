from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db

from app.modules.auth.dependencies import get_current_user

from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import (
    AuditFilter,
    AuditResponse,
)
from app.modules.audit.service import AuditService

from app.modules.rbac.dependencies import require_permission
from app.modules.rbac.constants import AUDIT_READ


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


def get_service(db: Session) -> AuditService:
    repository = AuditRepository(db)
    return AuditService(repository)


@router.get(
    "/",
    response_model=list[AuditResponse],
)
def list_logs(
    company_id: UUID | None = None,
    user_id: UUID | None = None,
    module: str | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    success: bool | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission(AUDIT_READ)),
):

    service = get_service(db)

    filters = AuditFilter(
        company_id=company_id,
        user_id=user_id,
        module=module,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        success=success,
        limit=limit,
    )

    return service.list(filters)


@router.get(
    "/recent",
    response_model=list[AuditResponse],
)
def recent_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission(AUDIT_READ)),
):

    service = get_service(db)

    return service.recent(limit)


@router.get(
    "/{audit_id}",
    response_model=AuditResponse,
)
def get_log(
    audit_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission(AUDIT_READ)),
):

    service = get_service(db)

    return service.get_by_id(audit_id)
