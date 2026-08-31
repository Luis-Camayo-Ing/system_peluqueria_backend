"""Database repository for sales and point-of-sale operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.cash_register.model import (
    CashSession,
    CashTransaction,
    CashTransactionType,
)
from app.modules.company.model import Company
from app.modules.customer.model import Customer
from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    Product,
)
from app.modules.sale.model import (
    Sale,
    SaleDetail,
    SalePayment,
    SaleStatus,
)
from app.modules.service.model import Service


class SaleRepository:
    """Persistence and locking operations for sales."""

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    # ======================================================
    # Company and customer
    # ======================================================

    def get_company_by_id(
        self,
        company_id: UUID,
    ) -> Company | None:
        statement = select(Company).where(
            Company.id == company_id,
        )

        return self.db.scalar(statement)

    def get_customer_by_id(
        self,
        customer_id: UUID,
        company_id: UUID,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.id == customer_id,
            Customer.company_id == company_id,
        )

        return self.db.scalar(statement)

    # ======================================================
    # Catalog items
    # ======================================================

    def get_product_for_update(
        self,
        product_id: UUID,
        company_id: UUID,
    ) -> Product | None:
        statement = (
            select(Product)
            .where(
                Product.id == product_id,
                Product.company_id == company_id,
            )
            .with_for_update()
        )

        return self.db.scalar(statement)

    def get_service_by_id(
        self,
        service_id: UUID,
        company_id: UUID,
    ) -> Service | None:
        statement = select(Service).where(
            Service.id == service_id,
            Service.company_id == company_id,
        )

        return self.db.scalar(statement)

    # ======================================================
    # Cash session
    # ======================================================

    def get_cash_session_for_update(
        self,
        cash_session_id: UUID,
        company_id: UUID,
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

    def get_cash_session_totals(
        self,
        cash_session_id: UUID,
        company_id: UUID,
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
            CashTransaction.cash_session_id
            == cash_session_id,
            CashTransaction.company_id == company_id,
        )

        row = self.db.execute(statement).one()

        return (
            Decimal(row.total_income),
            Decimal(row.total_expense),
        )

    def get_expected_cash_amount(
        self,
        cash_session: CashSession,
    ) -> Decimal:
        total_income, total_expense = (
            self.get_cash_session_totals(
                cash_session_id=cash_session.id,
                company_id=cash_session.company_id,
            )
        )

        return (
            Decimal(cash_session.opening_amount)
            + total_income
            - total_expense
        )

    # ======================================================
    # Sales
    # ======================================================

    def get_sale_by_number(
        self,
        sale_number: str,
        company_id: UUID,
    ) -> Sale | None:
        statement = select(Sale).where(
            Sale.company_id == company_id,
            func.lower(Sale.sale_number)
            == sale_number.strip().lower(),
        )

        return self.db.scalar(statement)

    def get_sale_by_id(
        self,
        sale_id: UUID,
        company_id: UUID,
    ) -> Sale | None:
        statement = (
            select(Sale)
            .options(
                selectinload(Sale.details),
                selectinload(Sale.payments),
            )
            .where(
                Sale.id == sale_id,
                Sale.company_id == company_id,
            )
        )

        return self.db.scalar(statement)

    def get_sale_for_update(
        self,
        sale_id: UUID,
        company_id: UUID,
    ) -> Sale | None:
        statement = (
            select(Sale)
            .where(
                Sale.id == sale_id,
                Sale.company_id == company_id,
            )
            .with_for_update()
        )

        sale = self.db.scalar(statement)

        if sale is not None:
            # Carga las colecciones dentro de la misma sesión.
            list(sale.details)
            list(sale.payments)

        return sale

    def list_sales(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: SaleStatus | None = None,
        customer_id: UUID | None = None,
        cash_session_id: UUID | None = None,
        search: str | None = None,
        sold_from: datetime | None = None,
        sold_to: datetime | None = None,
    ) -> list[Sale]:
        statement = (
            select(Sale)
            .options(
                selectinload(Sale.details),
                selectinload(Sale.payments),
            )
            .where(
                Sale.company_id == company_id,
            )
        )

        if status is not None:
            statement = statement.where(
                Sale.status == status,
            )

        if customer_id is not None:
            statement = statement.where(
                Sale.customer_id == customer_id,
            )

        if cash_session_id is not None:
            statement = statement.where(
                Sale.cash_session_id == cash_session_id,
            )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Sale.sale_number.ilike(search_pattern),
                    Sale.customer_name.ilike(search_pattern),
                    Sale.customer_document.ilike(
                        search_pattern
                    ),
                )
            )

        if sold_from is not None:
            statement = statement.where(
                Sale.sold_at >= sold_from,
            )

        if sold_to is not None:
            statement = statement.where(
                Sale.sold_at <= sold_to,
            )

        statement = (
            statement
            .order_by(
                Sale.sold_at.desc(),
                Sale.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).unique().all()
        )

    def count_sales(
        self,
        company_id: UUID,
        status: SaleStatus | None = None,
        customer_id: UUID | None = None,
        cash_session_id: UUID | None = None,
        search: str | None = None,
        sold_from: datetime | None = None,
        sold_to: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count(Sale.id))
            .select_from(Sale)
            .where(
                Sale.company_id == company_id,
            )
        )

        if status is not None:
            statement = statement.where(
                Sale.status == status,
            )

        if customer_id is not None:
            statement = statement.where(
                Sale.customer_id == customer_id,
            )

        if cash_session_id is not None:
            statement = statement.where(
                Sale.cash_session_id == cash_session_id,
            )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Sale.sale_number.ilike(search_pattern),
                    Sale.customer_name.ilike(search_pattern),
                    Sale.customer_document.ilike(
                        search_pattern
                    ),
                )
            )

        if sold_from is not None:
            statement = statement.where(
                Sale.sold_at >= sold_from,
            )

        if sold_to is not None:
            statement = statement.where(
                Sale.sold_at <= sold_to,
            )

        return self.db.scalar(statement) or 0

    # ======================================================
    # Entity persistence
    # ======================================================

    def add_sale(
        self,
        sale: Sale,
    ) -> None:
        self.db.add(sale)

    def add_sale_detail(
        self,
        detail: SaleDetail,
    ) -> None:
        self.db.add(detail)

    def add_sale_payment(
        self,
        payment: SalePayment,
    ) -> None:
        self.db.add(payment)

    def add_inventory_movement(
        self,
        movement: InventoryMovement,
    ) -> None:
        self.db.add(movement)

    def add_inventory_movement_detail(
        self,
        detail: InventoryMovementDetail,
    ) -> None:
        self.db.add(detail)

    def add_cash_transaction(
        self,
        transaction: CashTransaction,
    ) -> None:
        self.db.add(transaction)

    # ======================================================
    # Transaction helpers
    # ======================================================

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh_sale(
        self,
        sale: Sale,
    ) -> Sale:
        self.db.refresh(sale)

        refreshed_sale = self.get_sale_by_id(
            sale_id=sale.id,
            company_id=sale.company_id,
        )

        return refreshed_sale or sale
