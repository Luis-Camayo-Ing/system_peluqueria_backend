import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.modules.cash_register.model import (
    CashRegister,
    CashSession,
    CashSessionStatus,
    CashTransaction,
    CashTransactionSource,
    CashTransactionType,
)


class CashRegisterRepository:
    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # Cash Registers
    # ======================================================

    def create_register(
        self,
        cash_register: CashRegister,
    ) -> CashRegister:
        self.db.add(cash_register)
        self.db.commit()
        self.db.refresh(cash_register)

        return cash_register

    def get_register_by_id(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashRegister | None:
        statement = select(CashRegister).where(
            CashRegister.id == cash_register_id,
            CashRegister.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_register_by_code(
        self,
        company_id: uuid.UUID,
        code: str,
        exclude_register_id: uuid.UUID | None = None,
    ) -> CashRegister | None:
        statement = select(CashRegister).where(
            CashRegister.company_id == company_id,
            func.lower(CashRegister.code) == code.strip().lower(),
        )

        if exclude_register_id is not None:
            statement = statement.where(
                CashRegister.id != exclude_register_id
            )

        return self.db.scalar(statement)

    def get_register_by_name(
        self,
        company_id: uuid.UUID,
        name: str,
        exclude_register_id: uuid.UUID | None = None,
    ) -> CashRegister | None:
        statement = select(CashRegister).where(
            CashRegister.company_id == company_id,
            func.lower(CashRegister.name) == name.strip().lower(),
        )

        if exclude_register_id is not None:
            statement = statement.where(
                CashRegister.id != exclude_register_id
            )

        return self.db.scalar(statement)

    def list_registers(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[CashRegister]:
        statement = select(CashRegister).where(
            CashRegister.company_id == company_id
        )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    CashRegister.code.ilike(search_pattern),
                    CashRegister.name.ilike(search_pattern),
                    CashRegister.description.ilike(search_pattern),
                )
            )

        if is_active is not None:
            statement = statement.where(
                CashRegister.is_active == is_active
            )

        statement = (
            statement
            .order_by(CashRegister.name.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_registers(
        self,
        company_id: uuid.UUID,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(CashRegister)
            .where(CashRegister.company_id == company_id)
        )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    CashRegister.code.ilike(search_pattern),
                    CashRegister.name.ilike(search_pattern),
                    CashRegister.description.ilike(search_pattern),
                )
            )

        if is_active is not None:
            statement = statement.where(
                CashRegister.is_active == is_active
            )

        return self.db.scalar(statement) or 0

    def update_register(
        self,
        cash_register: CashRegister,
    ) -> CashRegister:
        self.db.commit()
        self.db.refresh(cash_register)

        return cash_register

    def register_has_open_session(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> bool:
        statement = (
            select(func.count())
            .select_from(CashSession)
            .where(
                CashSession.cash_register_id == cash_register_id,
                CashSession.company_id == company_id,
                CashSession.status == CashSessionStatus.OPEN,
            )
        )

        return (self.db.scalar(statement) or 0) > 0

    # ======================================================
    # Cash Sessions
    # ======================================================

    def add_session(
        self,
        cash_session: CashSession,
    ) -> None:
        self.db.add(cash_session)

    def create_session(
        self,
        cash_session: CashSession,
    ) -> CashSession:
        self.db.add(cash_session)
        self.db.commit()
        self.db.refresh(cash_session)

        return cash_session

    def get_session_by_id(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashSession | None:
        statement = select(CashSession).where(
            CashSession.id == cash_session_id,
            CashSession.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_session_for_update(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashSession | None:
        statement = (
            select(CashSession)
            .where(
                CashSession.id == cash_session_id,
                CashSession.company_id == company_id,
            )
            .with_for_update()
        )

        return self.db.scalar(statement)

    def get_open_session_by_register(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
        for_update: bool = False,
    ) -> CashSession | None:
        statement = select(CashSession).where(
            CashSession.cash_register_id == cash_register_id,
            CashSession.company_id == company_id,
            CashSession.status == CashSessionStatus.OPEN,
        )

        if for_update:
            statement = statement.with_for_update()

        return self.db.scalar(statement)

    def list_sessions(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        cash_register_id: uuid.UUID | None = None,
        status: CashSessionStatus | None = None,
        opened_by_user_id: uuid.UUID | None = None,
        opened_from: datetime | None = None,
        opened_to: datetime | None = None,
    ) -> list[CashSession]:
        statement = select(CashSession).where(
            CashSession.company_id == company_id
        )

        if cash_register_id is not None:
            statement = statement.where(
                CashSession.cash_register_id == cash_register_id
            )

        if status is not None:
            statement = statement.where(
                CashSession.status == status
            )

        if opened_by_user_id is not None:
            statement = statement.where(
                CashSession.opened_by_user_id == opened_by_user_id
            )

        if opened_from is not None:
            statement = statement.where(
                CashSession.opened_at >= opened_from
            )

        if opened_to is not None:
            statement = statement.where(
                CashSession.opened_at <= opened_to
            )

        statement = (
            statement
            .order_by(CashSession.opened_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_sessions(
        self,
        company_id: uuid.UUID,
        cash_register_id: uuid.UUID | None = None,
        status: CashSessionStatus | None = None,
        opened_by_user_id: uuid.UUID | None = None,
        opened_from: datetime | None = None,
        opened_to: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(CashSession)
            .where(CashSession.company_id == company_id)
        )

        if cash_register_id is not None:
            statement = statement.where(
                CashSession.cash_register_id == cash_register_id
            )

        if status is not None:
            statement = statement.where(
                CashSession.status == status
            )

        if opened_by_user_id is not None:
            statement = statement.where(
                CashSession.opened_by_user_id == opened_by_user_id
            )

        if opened_from is not None:
            statement = statement.where(
                CashSession.opened_at >= opened_from
            )

        if opened_to is not None:
            statement = statement.where(
                CashSession.opened_at <= opened_to
            )

        return self.db.scalar(statement) or 0

    # ======================================================
    # Cash Transactions
    # ======================================================

    def add_transaction(
        self,
        cash_transaction: CashTransaction,
    ) -> None:
        self.db.add(cash_transaction)

    def create_transaction(
        self,
        cash_transaction: CashTransaction,
    ) -> CashTransaction:
        self.db.add(cash_transaction)
        self.db.commit()
        self.db.refresh(cash_transaction)

        return cash_transaction

    def get_transaction_by_id(
        self,
        cash_transaction_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashTransaction | None:
        statement = select(CashTransaction).where(
            CashTransaction.id == cash_transaction_id,
            CashTransaction.company_id == company_id,
        )

        return self.db.scalar(statement)

    def list_transactions(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        cash_session_id: uuid.UUID | None = None,
        transaction_type: CashTransactionType | None = None,
        source: CashTransactionSource | None = None,
        user_id: uuid.UUID | None = None,
        reference: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[CashTransaction]:
        statement = select(CashTransaction).where(
            CashTransaction.company_id == company_id
        )

        if cash_session_id is not None:
            statement = statement.where(
                CashTransaction.cash_session_id == cash_session_id
            )

        if transaction_type is not None:
            statement = statement.where(
                CashTransaction.transaction_type == transaction_type
            )

        if source is not None:
            statement = statement.where(
                CashTransaction.source == source
            )

        if user_id is not None:
            statement = statement.where(
                CashTransaction.user_id == user_id
            )

        if reference:
            statement = statement.where(
                CashTransaction.reference.ilike(
                    f"%{reference.strip()}%"
                )
            )

        if created_from is not None:
            statement = statement.where(
                CashTransaction.created_at >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                CashTransaction.created_at <= created_to
            )

        statement = (
            statement
            .order_by(CashTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_transactions(
        self,
        company_id: uuid.UUID,
        cash_session_id: uuid.UUID | None = None,
        transaction_type: CashTransactionType | None = None,
        source: CashTransactionSource | None = None,
        user_id: uuid.UUID | None = None,
        reference: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(CashTransaction)
            .where(CashTransaction.company_id == company_id)
        )

        if cash_session_id is not None:
            statement = statement.where(
                CashTransaction.cash_session_id == cash_session_id
            )

        if transaction_type is not None:
            statement = statement.where(
                CashTransaction.transaction_type == transaction_type
            )

        if source is not None:
            statement = statement.where(
                CashTransaction.source == source
            )

        if user_id is not None:
            statement = statement.where(
                CashTransaction.user_id == user_id
            )

        if reference:
            statement = statement.where(
                CashTransaction.reference.ilike(
                    f"%{reference.strip()}%"
                )
            )

        if created_from is not None:
            statement = statement.where(
                CashTransaction.created_at >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                CashTransaction.created_at <= created_to
            )

        return self.db.scalar(statement) or 0

    def get_session_totals(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> tuple[Decimal, Decimal]:
        statement = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            CashTransaction.transaction_type
                            == CashTransactionType.INCOME,
                            CashTransaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            CashTransaction.transaction_type
                            == CashTransactionType.EXPENSE,
                            CashTransaction.amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_expense"),
        ).where(
            CashTransaction.cash_session_id == cash_session_id,
            CashTransaction.company_id == company_id,
        )

        row = self.db.execute(statement).one()

        return (
            Decimal(row.total_income),
            Decimal(row.total_expense),
        )

    def get_expected_amount(
        self,
        cash_session: CashSession,
    ) -> Decimal:
        total_income, total_expense = self.get_session_totals(
            cash_session_id=cash_session.id,
            company_id=cash_session.company_id,
        )

        return (
            Decimal(cash_session.opening_amount)
            + total_income
            - total_expense
        )

    # ======================================================
    # Transaction helpers
    # ======================================================

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh_register(
        self,
        cash_register: CashRegister,
    ) -> CashRegister:
        self.db.refresh(cash_register)

        return cash_register

    def refresh_session(
        self,
        cash_session: CashSession,
    ) -> CashSession:
        self.db.refresh(cash_session)

        return cash_session

    def refresh_transaction(
        self,
        cash_transaction: CashTransaction,
    ) -> CashTransaction:
        self.db.refresh(cash_transaction)

        return cash_transaction