from __future__ import annotations

from uuid import UUID

from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import (
    AuditCreate,
    AuditFilter,
)


class AuditService:

    def __init__(
        self,
        repository: AuditRepository,
    ):
        self.repository = repository

    # ======================================================
    # Registrar evento
    # ======================================================

    def log(
        self,
        *,
        company_id: UUID,
        user_id: UUID | None,
        module: str,
        action: str,
        entity_type: str,
        entity_id: str | None,
        description: str,
        details: dict | None = None,
        success: bool = True,
    ):
        audit = AuditCreate(
            company_id=company_id,
            user_id=user_id,
            module=module,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            details=details,
            success=success,
        )

        return self.repository.create(audit)

    # ======================================================
    # Consultas
    # ======================================================

    def get_by_id(
        self,
        audit_id,
    ):
        return self.repository.get_by_id(audit_id)

    def list(
        self,
        filters: AuditFilter,
    ):
        return self.repository.list(filters)

    def recent(
        self,
        limit: int = 20,
    ):
        return self.repository.recent(limit)

    def by_user(
        self,
        user_id,
        limit: int = 100,
    ):
        return self.repository.by_user(
            user_id=user_id,
            limit=limit,
        )

    def by_module(
        self,
        module: str,
        limit: int = 100,
    ):
        return self.repository.by_module(
            module=module,
            limit=limit,
        )

    def by_entity(
        self,
        entity_type: str,
        entity_id: str,
    ):
        return self.repository.by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
        )