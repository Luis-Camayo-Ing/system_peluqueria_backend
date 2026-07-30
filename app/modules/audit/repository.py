from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.audit.model import AuditLog
from app.modules.audit.schemas import AuditCreate, AuditFilter


class AuditRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ======================================================
    # Create
    # ======================================================

    def create(
        self,
        data: AuditCreate,
    ) -> AuditLog:
        audit = AuditLog(
            **data.model_dump()
        )

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        return audit

    # ======================================================
    # Get by ID
    # ======================================================

    def get_by_id(
        self,
        audit_id,
    ) -> AuditLog | None:
        return self.db.get(
            AuditLog,
            audit_id,
        )

    # ======================================================
    # List
    # ======================================================

    def list(
        self,
        filters: AuditFilter,
    ) -> list[AuditLog]:

        statement: Select = select(AuditLog)

        if filters.company_id:
            statement = statement.where(
                AuditLog.company_id == filters.company_id
            )

        if filters.user_id:
            statement = statement.where(
                AuditLog.user_id == filters.user_id
            )

        if filters.module:
            statement = statement.where(
                AuditLog.module == filters.module
            )

        if filters.action:
            statement = statement.where(
                AuditLog.action == filters.action
            )

        if filters.entity_type:
            statement = statement.where(
                AuditLog.entity_type == filters.entity_type
            )

        if filters.entity_id:
            statement = statement.where(
                AuditLog.entity_id == filters.entity_id
            )

        if filters.success is not None:
            statement = statement.where(
                AuditLog.success == filters.success
            )

        statement = (
            statement
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(filters.limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ======================================================
    # Recent
    # ======================================================

    def recent(
        self,
        limit: int = 20,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ======================================================
    # User Logs
    # ======================================================

    def by_user(
        self,
        user_id,
        limit: int = 100,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ======================================================
    # Module Logs
    # ======================================================

    def by_module(
        self,
        module: str,
        limit: int = 100,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.module == module
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ======================================================
    # Entity Logs
    # ======================================================

    def by_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(
                AuditLog.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )