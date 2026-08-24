"""Dashboard-specific aggregate SQLAlchemy queries."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.appointment.model import Appointment
from app.modules.cash_register.model import (
    CashTransaction,
    CashTransactionType,
)
from app.modules.inventory.model import Product
from app.modules.sale.model import (
    Sale,
    SaleDetail,
    SaleItemType,
    SaleStatus,
)

ZERO_MONEY = Decimal("0.00")
ZERO_QUANTITY = Decimal("0.000")


class DashboardRepository:
    """Read-only queries exclusive to dashboard visualizations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_appointment_status_counts(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list:
        statement = (
            select(
                Appointment.status,
                func.count(Appointment.id).label("appointments_count"),
            )
            .where(
                Appointment.company_id == company_id,
                Appointment.start_at >= start_at,
                Appointment.start_at < end_at,
            )
            .group_by(Appointment.status)
            .order_by(Appointment.status.asc())
        )

        return list(self.db.execute(statement).all())

    def get_daily_cash_flow(
        self,
        *,
        company_id: UUID,
        start_at: datetime,
        end_at: datetime,
        timezone_name: str,
    ) -> list:
        local_date = func.date(
            func.timezone(
                timezone_name,
                CashTransaction.created_at,
            )
        ).label("date")

        statement = (
            select(
                local_date,
                func.coalesce(
                    func.sum(CashTransaction.amount).filter(
                        CashTransaction.transaction_type == CashTransactionType.INCOME
                    ),
                    ZERO_MONEY,
                ).label("income"),
                func.coalesce(
                    func.sum(CashTransaction.amount).filter(
                        CashTransaction.transaction_type == CashTransactionType.EXPENSE
                    ),
                    ZERO_MONEY,
                ).label("expense"),
            )
            .where(
                CashTransaction.company_id == company_id,
                CashTransaction.created_at >= start_at,
                CashTransaction.created_at < end_at,
            )
            .group_by(local_date)
            .order_by(local_date.asc())
        )

        return list(self.db.execute(statement).all())

    def get_top_products(
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
                Product.id.label("product_id"),
                Product.code,
                Product.name,
                Product.current_stock,
                func.count(func.distinct(Sale.id)).label("sales_count"),
                func.coalesce(
                    func.sum(SaleDetail.quantity),
                    ZERO_QUANTITY,
                ).label("quantity"),
                revenue,
            )
            .join(
                SaleDetail,
                SaleDetail.product_id == Product.id,
            )
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .where(
                Product.company_id == company_id,
                Sale.company_id == company_id,
                Sale.status == SaleStatus.COMPLETED,
                SaleDetail.item_type == SaleItemType.PRODUCT,
                Sale.sold_at >= start_at,
                Sale.sold_at < end_at,
            )
            .group_by(
                Product.id,
                Product.code,
                Product.name,
                Product.current_stock,
            )
            .order_by(revenue.desc(), Product.name.asc())
            .limit(limit)
        )

        return list(self.db.execute(statement).all())