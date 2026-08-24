"""Aggregate SQLAlchemy queries for business reports."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.modules.cash_register.model import (
    CashRegister,
    CashSession,
    CashTransaction,
    CashTransactionType,
)
from app.modules.customer.model import Customer
from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    Product,
)
from app.modules.sale.model import (
    Sale,
    SaleDetail,
    SaleItemType,
    SalePayment,
    SaleStatus,
)
from app.modules.service.model import Service

ZERO_MONEY = Decimal("0.00")
ZERO_QUANTITY = Decimal("0.000")


class ReportRepository:
    """Read-only queries scoped to one company."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ======================================================
    # Sales
    # ======================================================

    def get_sales_totals(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        statement = select(
            func.count(Sale.id)
            .filter(Sale.status == SaleStatus.COMPLETED)
            .label("completed_sales_count"),
            func.count(Sale.id)
            .filter(Sale.status == SaleStatus.CANCELLED)
            .label("cancelled_sales_count"),
            func.coalesce(
                func.sum(Sale.total_amount).filter(
                    Sale.status == SaleStatus.CANCELLED
                ),
                ZERO_MONEY,
            ).label("cancelled_amount"),
            func.coalesce(
                func.sum(Sale.subtotal).filter(
                    Sale.status == SaleStatus.COMPLETED
                ),
                ZERO_MONEY,
            ).label("gross_subtotal"),
            func.coalesce(
                func.sum(Sale.discount_amount).filter(
                    Sale.status == SaleStatus.COMPLETED
                ),
                ZERO_MONEY,
            ).label("discount_amount"),
            func.coalesce(
                func.sum(Sale.tax_amount).filter(
                    Sale.status == SaleStatus.COMPLETED
                ),
                ZERO_MONEY,
            ).label("tax_amount"),
            func.coalesce(
                func.sum(Sale.total_amount).filter(
                    Sale.status == SaleStatus.COMPLETED
                ),
                ZERO_MONEY,
            ).label("net_sales"),
        ).where(
            Sale.company_id == company_id,
            Sale.sold_at >= start_at,
            Sale.sold_at < end_at,
        )

        return self.db.execute(statement).one()

    def get_sold_item_quantities(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        statement = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                SaleDetail.item_type
                                == SaleItemType.PRODUCT,
                                SaleDetail.quantity,
                            ),
                            else_=ZERO_QUANTITY,
                        )
                    ),
                    ZERO_QUANTITY,
                ).label("products_quantity"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                SaleDetail.item_type
                                == SaleItemType.SERVICE,
                                SaleDetail.quantity,
                            ),
                            else_=ZERO_QUANTITY,
                        )
                    ),
                    ZERO_QUANTITY,
                ).label("services_quantity"),
            )
            .select_from(SaleDetail)
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .where(
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
        )

        return self.db.execute(statement).one()

    def get_sales_by_payment_method(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list:
        statement = (
            select(
                SalePayment.payment_method,
                func.count(SalePayment.id).label(
                    "payments_count"
                ),
                func.coalesce(
                    func.sum(SalePayment.amount),
                    ZERO_MONEY,
                ).label("amount"),
            )
            .join(Sale, Sale.id == SalePayment.sale_id)
            .where(
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
            .group_by(SalePayment.payment_method)
            .order_by(SalePayment.payment_method.asc())
        )

        return list(self.db.execute(statement).all())

    def get_daily_sales(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
        timezone_name: str,
    ) -> list:
        local_date = func.date(
            func.timezone(timezone_name, Sale.sold_at)
        ).label("date")

        statement = (
            select(
                local_date,
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(Sale.total_amount),
                    ZERO_MONEY,
                ).label("net_sales"),
            )
            .where(
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
            .group_by(local_date)
            .order_by(local_date.asc())
        )

        return list(self.db.execute(statement).all())

    # ======================================================
    # Inventory
    # ======================================================

    def get_inventory_snapshot(self, *, company_id: UUID):
        statement = select(
            func.count(Product.id).label("total_products"),
            func.count(Product.id)
            .filter(Product.is_active.is_(True))
            .label("active_products"),
            func.count(Product.id)
            .filter(Product.is_active.is_(False))
            .label("inactive_products"),
            func.count(Product.id)
            .filter(
                Product.is_active.is_(True),
                Product.current_stock <= ZERO_QUANTITY,
            )
            .label("out_of_stock_products"),
            func.count(Product.id)
            .filter(
                Product.is_active.is_(True),
                Product.current_stock > ZERO_QUANTITY,
                Product.current_stock <= Product.minimum_stock,
            )
            .label("low_stock_products"),
            func.coalesce(
                func.sum(Product.current_stock),
                ZERO_QUANTITY,
            ).label("total_stock_units"),
            func.coalesce(
                func.sum(
                    Product.current_stock
                    * Product.purchase_price
                ),
                ZERO_MONEY,
            ).label("inventory_cost_value"),
            func.coalesce(
                func.sum(
                    Product.current_stock * Product.sale_price
                ),
                ZERO_MONEY,
            ).label("inventory_sale_value"),
        ).where(Product.company_id == company_id)

        return self.db.execute(statement).one()

    def get_inventory_movements(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list:
        statement = (
            select(
                InventoryMovement.movement_type,
                func.count(
                    func.distinct(InventoryMovement.id)
                ).label("movements_count"),
                func.coalesce(
                    func.sum(InventoryMovementDetail.quantity),
                    ZERO_QUANTITY,
                ).label("quantity"),
            )
            .join(
                InventoryMovementDetail,
                InventoryMovementDetail.movement_id
                == InventoryMovement.id,
            )
            .where(
                InventoryMovement.company_id == company_id,
                InventoryMovement.created_at >= start_at,
                InventoryMovement.created_at < end_at,
            )
            .group_by(InventoryMovement.movement_type)
            .order_by(InventoryMovement.movement_type.asc())
        )

        return list(self.db.execute(statement).all())

    def get_low_stock_products(
        self,
        *,
        company_id: UUID,
        limit: int,
    ) -> list:
        shortage_quantity = func.greatest(
            Product.minimum_stock - Product.current_stock,
            ZERO_QUANTITY,
        ).label("shortage_quantity")

        statement = (
            select(
                Product.id.label("product_id"),
                Product.code,
                Product.name,
                Product.current_stock,
                Product.minimum_stock,
                shortage_quantity,
            )
            .where(
                Product.company_id == company_id,
                Product.is_active.is_(True),
                Product.current_stock <= Product.minimum_stock,
            )
            .order_by(
                shortage_quantity.desc(),
                Product.current_stock.asc(),
                Product.name.asc(),
            )
            .limit(limit)
        )

        return list(self.db.execute(statement).all())

    # ======================================================
    # Cash
    # ======================================================

    def get_cash_totals(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        statement = select(
            func.count(CashTransaction.id).label(
                "transactions_count"
            ),
            func.coalesce(
                func.sum(CashTransaction.amount).filter(
                    CashTransaction.transaction_type
                    == CashTransactionType.INCOME
                ),
                ZERO_MONEY,
            ).label("total_income"),
            func.coalesce(
                func.sum(CashTransaction.amount).filter(
                    CashTransaction.transaction_type
                    == CashTransactionType.EXPENSE
                ),
                ZERO_MONEY,
            ).label("total_expense"),
        ).where(
            CashTransaction.company_id == company_id,
            CashTransaction.created_at >= start_at,
            CashTransaction.created_at < end_at,
        )

        return self.db.execute(statement).one()

    def get_cash_session_totals(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        opened_period = and_(
            CashSession.opened_at >= start_at,
            CashSession.opened_at < end_at,
        )
        closed_period = and_(
            CashSession.closed_at.is_not(None),
            CashSession.closed_at >= start_at,
            CashSession.closed_at < end_at,
        )

        statement = select(
            func.count(CashSession.id)
            .filter(opened_period)
            .label("sessions_opened"),
            func.count(CashSession.id)
            .filter(closed_period)
            .label("sessions_closed"),
            func.coalesce(
                func.sum(CashSession.opening_amount).filter(
                    opened_period
                ),
                ZERO_MONEY,
            ).label("opening_amount"),
            func.coalesce(
                func.sum(CashSession.difference_amount).filter(
                    closed_period
                ),
                ZERO_MONEY,
            ).label("closing_difference"),
        ).where(CashSession.company_id == company_id)

        return self.db.execute(statement).one()

    def get_cash_by_source(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list:
        statement = (
            select(
                CashTransaction.source,
                func.count(CashTransaction.id).label(
                    "transactions_count"
                ),
                func.coalesce(
                    func.sum(CashTransaction.amount).filter(
                        CashTransaction.transaction_type
                        == CashTransactionType.INCOME
                    ),
                    ZERO_MONEY,
                ).label("income"),
                func.coalesce(
                    func.sum(CashTransaction.amount).filter(
                        CashTransaction.transaction_type
                        == CashTransactionType.EXPENSE
                    ),
                    ZERO_MONEY,
                ).label("expense"),
            )
            .where(
                CashTransaction.company_id == company_id,
                CashTransaction.created_at >= start_at,
                CashTransaction.created_at < end_at,
            )
            .group_by(CashTransaction.source)
            .order_by(CashTransaction.source.asc())
        )

        return list(self.db.execute(statement).all())

    def get_cash_by_register(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list:
        statement = (
            select(
                CashRegister.id.label("cash_register_id"),
                CashRegister.code,
                CashRegister.name,
                func.count(CashTransaction.id).label(
                    "transactions_count"
                ),
                func.coalesce(
                    func.sum(CashTransaction.amount).filter(
                        CashTransaction.transaction_type
                        == CashTransactionType.INCOME
                    ),
                    ZERO_MONEY,
                ).label("income"),
                func.coalesce(
                    func.sum(CashTransaction.amount).filter(
                        CashTransaction.transaction_type
                        == CashTransactionType.EXPENSE
                    ),
                    ZERO_MONEY,
                ).label("expense"),
            )
            .join(
                CashSession,
                CashSession.cash_register_id == CashRegister.id,
            )
            .join(
                CashTransaction,
                CashTransaction.cash_session_id == CashSession.id,
            )
            .where(
                CashRegister.company_id == company_id,
                CashTransaction.company_id == company_id,
                CashTransaction.created_at >= start_at,
                CashTransaction.created_at < end_at,
            )
            .group_by(
                CashRegister.id,
                CashRegister.code,
                CashRegister.name,
            )
            .order_by(CashRegister.code.asc())
        )

        return list(self.db.execute(statement).all())

    # ======================================================
    # Customers
    # ======================================================

    def get_customer_totals(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        statement = select(
            func.count(Customer.id).label("total_customers"),
            func.count(Customer.id)
            .filter(Customer.is_active.is_(True))
            .label("active_customers"),
            func.count(Customer.id)
            .filter(Customer.is_active.is_(False))
            .label("inactive_customers"),
            func.count(Customer.id)
            .filter(
                Customer.created_at >= start_at,
                Customer.created_at < end_at,
            )
            .label("new_customers"),
        ).where(Customer.company_id == company_id)

        return self.db.execute(statement).one()

    def get_customer_sales_totals(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        statement = select(
            func.count(func.distinct(Sale.customer_id))
            .filter(Sale.customer_id.is_not(None))
            .label("customers_with_purchases"),
            func.count(Sale.id)
            .filter(Sale.customer_id.is_(None))
            .label("sales_without_customer"),
        ).where(
            Sale.company_id == company_id,
            Sale.status == SaleStatus.COMPLETED,
            Sale.sold_at >= start_at,
            Sale.sold_at < end_at,
        )

        return self.db.execute(statement).one()

    def get_returning_customers_count(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> int:
        returning_customers = (
            select(Sale.customer_id)
            .where(
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                Sale.customer_id.is_not(None),
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
            .group_by(Sale.customer_id)
            .having(func.count(Sale.id) >= 2)
            .subquery()
        )

        statement = select(func.count()).select_from(
            returning_customers
        )

        return int(self.db.scalar(statement) or 0)

    def get_top_customers(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list:
        total_spent = func.coalesce(
            func.sum(Sale.total_amount),
            ZERO_MONEY,
        ).label("total_spent")

        statement = (
            select(
                Customer.id.label("customer_id"),
                Customer.first_name,
                Customer.last_name,
                func.count(Sale.id).label("purchases_count"),
                total_spent,
            )
            .join(Sale, Sale.customer_id == Customer.id)
            .where(
                Customer.company_id == company_id,
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
            .group_by(
                Customer.id,
                Customer.first_name,
                Customer.last_name,
            )
            .order_by(total_spent.desc(), Customer.id.asc())
            .limit(limit)
        )

        return list(self.db.execute(statement).all())

    # ======================================================
    # Services
    # ======================================================

    def get_service_catalog_totals(self, *, company_id: UUID):
        statement = select(
            func.count(Service.id).label("total_services"),
            func.count(Service.id)
            .filter(Service.is_active.is_(True))
            .label("active_services"),
            func.count(Service.id)
            .filter(Service.is_active.is_(False))
            .label("inactive_services"),
        ).where(Service.company_id == company_id)

        return self.db.execute(statement).one()

    def get_service_sales_totals(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        statement = (
            select(
                func.count(
                    func.distinct(SaleDetail.service_id)
                ).label("services_sold"),
                func.count(
                    func.distinct(SaleDetail.service_id)
                )
                .filter(Service.is_active.is_(True))
                .label("active_services_sold"),
                func.count(
                    func.distinct(Sale.id)
                ).label("service_sales_count"),
                func.coalesce(
                    func.sum(SaleDetail.quantity),
                    ZERO_QUANTITY,
                ).label("service_quantity"),
                func.coalesce(
                    func.sum(SaleDetail.line_total),
                    ZERO_MONEY,
                ).label("service_revenue"),
            )
            .select_from(SaleDetail)
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .join(Service, Service.id == SaleDetail.service_id)
            .where(
                Sale.company_id == company_id,
                Service.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                SaleDetail.item_type == SaleItemType.SERVICE,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
        )

        return self.db.execute(statement).one()

    def get_top_services(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list:
        revenue = func.coalesce(
            func.sum(SaleDetail.line_total),
            ZERO_MONEY,
        ).label("revenue")

        statement = (
            select(
                Service.id.label("service_id"),
                Service.name.label("service_name"),
                func.count(func.distinct(Sale.id)).label(
                    "sales_count"
                ),
                func.coalesce(
                    func.sum(SaleDetail.quantity),
                    ZERO_QUANTITY,
                ).label("quantity"),
                revenue,
            )
            .join(
                SaleDetail,
                SaleDetail.service_id == Service.id,
            )
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .where(
                Service.company_id == company_id,
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                SaleDetail.item_type == SaleItemType.SERVICE,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
            .group_by(Service.id, Service.name)
            .order_by(revenue.desc(), Service.name.asc())
            .limit(limit)
        )

        return list(self.db.execute(statement).all())