import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.modules.cash_register.exceptions import (
    CashRegisterCodeAlreadyExistsException,
    CashRegisterHasOpenSessionException,
    CashRegisterInactiveException,
    CashRegisterNameAlreadyExistsException,
    CashRegisterNotFoundException,
    CashSessionAlreadyOpenException,
    CashSessionClosedException,
    CashSessionNotFoundException,
    CashSessionNotOpenException,
    CashSessionProcessingException,
    CashTransactionNotFoundException,
    CashTransactionProcessingException,
    InsufficientCashException,
)
from app.modules.cash_register.model import (
    CashRegister,
    CashSession,
    CashSessionStatus,
    CashTransaction,
    CashTransactionSource,
    CashTransactionType,
)
from app.modules.cash_register.repository import CashRegisterRepository
from app.modules.cash_register.schemas import (
    CashRegisterCreate,
    CashRegisterUpdate,
    CashSessionClose,
    CashSessionOpen,
    CashTransactionCreate,
)


class CashRegisterService:
    def __init__(
        self,
        repository: CashRegisterRepository,
    ):
        self.repository = repository

    # ======================================================
    # Cash Registers
    # ======================================================

    def create_register(
        self,
        company_id: uuid.UUID,
        data: CashRegisterCreate,
    ) -> CashRegister:
        code = data.code.strip()
        name = data.name.strip()

        existing_code = self.repository.get_register_by_code(
            company_id=company_id,
            code=code,
        )

        if existing_code is not None:
            raise CashRegisterCodeAlreadyExistsException()

        existing_name = self.repository.get_register_by_name(
            company_id=company_id,
            name=name,
        )

        if existing_name is not None:
            raise CashRegisterNameAlreadyExistsException()

        cash_register = CashRegister(
            company_id=company_id,
            code=code,
            name=name,
            description=data.description,
            is_active=data.is_active,
        )

        return self.repository.create_register(
            cash_register
        )

    def get_register(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashRegister:
        cash_register = self.repository.get_register_by_id(
            cash_register_id=cash_register_id,
            company_id=company_id,
        )

        if cash_register is None:
            raise CashRegisterNotFoundException()

        return cash_register

    def list_registers(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        cash_registers = self.repository.list_registers(
            company_id=company_id,
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active,
        )

        total = self.repository.count_registers(
            company_id=company_id,
            search=search,
            is_active=is_active,
        )

        return {
            "total": total,
            "items": cash_registers,
        }

    def update_register(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
        data: CashRegisterUpdate,
    ) -> CashRegister:
        cash_register = self.get_register(
            cash_register_id=cash_register_id,
            company_id=company_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return cash_register

        new_code = update_data.get("code")

        if new_code is not None:
            normalized_code = new_code.strip()

            existing_code = self.repository.get_register_by_code(
                company_id=company_id,
                code=normalized_code,
                exclude_register_id=cash_register.id,
            )

            if existing_code is not None:
                raise CashRegisterCodeAlreadyExistsException()

            update_data["code"] = normalized_code

        new_name = update_data.get("name")

        if new_name is not None:
            normalized_name = new_name.strip()

            existing_name = self.repository.get_register_by_name(
                company_id=company_id,
                name=normalized_name,
                exclude_register_id=cash_register.id,
            )

            if existing_name is not None:
                raise CashRegisterNameAlreadyExistsException()

            update_data["name"] = normalized_name

        if (
            update_data.get("is_active") is False
            and self.repository.register_has_open_session(
                cash_register_id=cash_register.id,
                company_id=company_id,
            )
        ):
            raise CashRegisterHasOpenSessionException()

        for field, value in update_data.items():
            setattr(
                cash_register,
                field,
                value,
            )

        return self.repository.update_register(
            cash_register
        )

    def deactivate_register(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashRegister:
        cash_register = self.get_register(
            cash_register_id=cash_register_id,
            company_id=company_id,
        )

        if self.repository.register_has_open_session(
            cash_register_id=cash_register.id,
            company_id=company_id,
        ):
            raise CashRegisterHasOpenSessionException()

        cash_register.is_active = False

        return self.repository.update_register(
            cash_register
        )

    # ======================================================
    # Cash Sessions
    # ======================================================

    def open_session(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CashSessionOpen,
    ) -> CashSession:
        cash_register = self.get_register(
            cash_register_id=data.cash_register_id,
            company_id=company_id,
        )

        if not cash_register.is_active:
            raise CashRegisterInactiveException()

        existing_session = (
            self.repository.get_open_session_by_register(
                cash_register_id=cash_register.id,
                company_id=company_id,
            )
        )

        if existing_session is not None:
            raise CashSessionAlreadyOpenException()

        cash_session = CashSession(
            company_id=company_id,
            cash_register_id=cash_register.id,
            opened_by_user_id=user_id,
            status=CashSessionStatus.OPEN,
            opening_amount=data.opening_amount,
            opening_notes=data.opening_notes,
        )

        try:
            self.repository.add_session(
                cash_session
            )
            self.repository.flush()
            self.repository.commit()

            return self.repository.refresh_session(
                cash_session
            )

        except IntegrityError as exception:
            self.repository.rollback()

            raise CashSessionAlreadyOpenException() from exception

        except Exception as exception:
            self.repository.rollback()

            raise CashSessionProcessingException() from exception

    def get_session(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashSession:
        cash_session = self.repository.get_session_by_id(
            cash_session_id=cash_session_id,
            company_id=company_id,
        )

        if cash_session is None:
            raise CashSessionNotFoundException()

        return cash_session

    def get_open_session(
        self,
        cash_register_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashSession:
        self.get_register(
            cash_register_id=cash_register_id,
            company_id=company_id,
        )

        cash_session = (
            self.repository.get_open_session_by_register(
                cash_register_id=cash_register_id,
                company_id=company_id,
            )
        )

        if cash_session is None:
            raise CashSessionNotOpenException()

        return cash_session

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
    ) -> dict:
        if cash_register_id is not None:
            self.get_register(
                cash_register_id=cash_register_id,
                company_id=company_id,
            )

        cash_sessions = self.repository.list_sessions(
            company_id=company_id,
            skip=skip,
            limit=limit,
            cash_register_id=cash_register_id,
            status=status,
            opened_by_user_id=opened_by_user_id,
            opened_from=opened_from,
            opened_to=opened_to,
        )

        total = self.repository.count_sessions(
            company_id=company_id,
            cash_register_id=cash_register_id,
            status=status,
            opened_by_user_id=opened_by_user_id,
            opened_from=opened_from,
            opened_to=opened_to,
        )

        return {
            "total": total,
            "items": cash_sessions,
        }

    def get_session_summary(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> dict:
        cash_session = self.get_session(
            cash_session_id=cash_session_id,
            company_id=company_id,
        )

        total_income, total_expense = (
            self.repository.get_session_totals(
                cash_session_id=cash_session.id,
                company_id=company_id,
            )
        )

        expected_amount = (
            Decimal(cash_session.opening_amount)
            + total_income
            - total_expense
        )

        return {
            "session": cash_session,
            "total_income": total_income,
            "total_expense": total_expense,
            "expected_amount": expected_amount,
        }

    def close_session(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CashSessionClose,
    ) -> CashSession:
        try:
            cash_session = (
                self.repository.get_session_for_update(
                    cash_session_id=cash_session_id,
                    company_id=company_id,
                )
            )

            if cash_session is None:
                raise CashSessionNotFoundException()

            if cash_session.status == CashSessionStatus.CLOSED:
                raise CashSessionClosedException()

            if cash_session.status != CashSessionStatus.OPEN:
                raise CashSessionNotOpenException()

            expected_amount = (
                self.repository.get_expected_amount(
                    cash_session
                )
            )

            counted_amount = Decimal(
                data.counted_amount
            )

            cash_session.status = CashSessionStatus.CLOSED
            cash_session.closed_by_user_id = user_id
            cash_session.expected_amount = expected_amount
            cash_session.counted_amount = counted_amount
            cash_session.difference_amount = (
                counted_amount - expected_amount
            )
            cash_session.closing_notes = (
                data.closing_notes
            )
            cash_session.closed_at = datetime.now(
                timezone.utc
            )

            self.repository.flush()
            self.repository.commit()

            return self.repository.refresh_session(
                cash_session
            )

        except (
            CashSessionNotFoundException,
            CashSessionClosedException,
            CashSessionNotOpenException,
        ):
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()

            raise CashSessionProcessingException() from exception

    # ======================================================
    # Cash Transactions
    # ======================================================

    def create_transaction(
        self,
        cash_session_id: uuid.UUID,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CashTransactionCreate,
    ) -> CashTransaction:
        try:
            cash_session = (
                self.repository.get_session_for_update(
                    cash_session_id=cash_session_id,
                    company_id=company_id,
                )
            )

            if cash_session is None:
                raise CashSessionNotFoundException()

            if cash_session.status == CashSessionStatus.CLOSED:
                raise CashSessionClosedException()

            if cash_session.status != CashSessionStatus.OPEN:
                raise CashSessionNotOpenException()

            if (
                data.transaction_type
                == CashTransactionType.EXPENSE
            ):
                expected_amount = (
                    self.repository.get_expected_amount(
                        cash_session
                    )
                )

                if data.amount > expected_amount:
                    raise InsufficientCashException()

            cash_transaction = CashTransaction(
                company_id=company_id,
                cash_session_id=cash_session.id,
                user_id=user_id,
                transaction_type=data.transaction_type,
                source=data.source,
                amount=data.amount,
                reference=data.reference,
                description=data.description,
                notes=data.notes,
            )

            self.repository.add_transaction(
                cash_transaction
            )
            self.repository.flush()
            self.repository.commit()

            return self.repository.refresh_transaction(
                cash_transaction
            )

        except (
            CashSessionNotFoundException,
            CashSessionClosedException,
            CashSessionNotOpenException,
            InsufficientCashException,
        ):
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()

            raise CashTransactionProcessingException() from exception

    def get_transaction(
        self,
        cash_transaction_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CashTransaction:
        cash_transaction = (
            self.repository.get_transaction_by_id(
                cash_transaction_id=cash_transaction_id,
                company_id=company_id,
            )
        )

        if cash_transaction is None:
            raise CashTransactionNotFoundException()

        return cash_transaction

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
    ) -> dict:
        if cash_session_id is not None:
            self.get_session(
                cash_session_id=cash_session_id,
                company_id=company_id,
            )

        cash_transactions = (
            self.repository.list_transactions(
                company_id=company_id,
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
        )

        total = self.repository.count_transactions(
            company_id=company_id,
            cash_session_id=cash_session_id,
            transaction_type=transaction_type,
            source=source,
            user_id=user_id,
            reference=reference,
            created_from=created_from,
            created_to=created_to,
        )

        return {
            "total": total,
            "items": cash_transactions,
        }