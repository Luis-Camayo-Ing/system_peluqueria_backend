"""Business rules and response assembly for reports."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.report.exceptions import (
    InvalidReportPeriodException,
    InvalidReportTimezoneException,
    ReportPeriodTooLargeException,
)
from app.modules.report.repository import ReportRepository
from app.modules.report.schemas import (
    CashRegisterMetric,
    CashReportResponse,
    CashSourceMetric,
    CustomerReportResponse,
    InventoryMovementMetric,
    InventoryReportResponse,
    LowStockProductMetric,
    ReportMetadata,
    ReportPeriodRequest,
    SalesDailyMetric,
    SalesPaymentMethodMetric,
    SalesReportResponse,
    ServiceReportResponse,
    TopCustomerMetric,
    TopServiceMetric,
)

ZERO_MONEY = Decimal("0.00")
ZERO_QUANTITY = Decimal("0.000")
MONEY_QUANTUM = Decimal("0.01")


@dataclass(frozen=True)
class ReportPeriodBounds:
    """UTC boundaries and metadata for one local date period."""

    start_at: datetime
    end_at: datetime
    metadata: ReportMetadata


class ReportService:
    """Generate multi-company reports from aggregate queries."""

    MAXIMUM_PERIOD_DAYS = 366

    def __init__(self, repository: ReportRepository) -> None:
        self.repository = repository

    # ======================================================
    # Sales
    # ======================================================

    def get_sales_report(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
    ) -> SalesReportResponse:
        bounds = self.resolve_period(
            company_id=company_id,
            period=period,
        )

        totals = self.repository.get_sales_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        quantities = self.repository.get_sold_item_quantities(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        payment_rows = (
            self.repository.get_sales_by_payment_method(
                company_id=company_id,
                start_at=bounds.start_at,
                end_at=bounds.end_at,
            )
        )
        daily_rows = self.repository.get_daily_sales(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            timezone_name=period.timezone,
        )

        completed_count = int(
            totals.completed_sales_count or 0
        )
        net_sales = self._decimal(
            totals.net_sales,
            ZERO_MONEY,
        )

        average_ticket = ZERO_MONEY
        if completed_count > 0:
            average_ticket = (
                net_sales / Decimal(completed_count)
            ).quantize(MONEY_QUANTUM)

        return SalesReportResponse(
            metadata=bounds.metadata,
            completed_sales_count=completed_count,
            cancelled_sales_count=int(
                totals.cancelled_sales_count or 0
            ),
            cancelled_amount=self._decimal(
                totals.cancelled_amount,
                ZERO_MONEY,
            ),
            gross_subtotal=self._decimal(
                totals.gross_subtotal,
                ZERO_MONEY,
            ),
            discount_amount=self._decimal(
                totals.discount_amount,
                ZERO_MONEY,
            ),
            tax_amount=self._decimal(
                totals.tax_amount,
                ZERO_MONEY,
            ),
            net_sales=net_sales,
            average_ticket=average_ticket,
            products_quantity=self._decimal(
                quantities.products_quantity,
                ZERO_QUANTITY,
            ),
            services_quantity=self._decimal(
                quantities.services_quantity,
                ZERO_QUANTITY,
            ),
            payment_methods=[
                SalesPaymentMethodMetric(
                    payment_method=row.payment_method,
                    payments_count=int(
                        row.payments_count or 0
                    ),
                    amount=self._decimal(
                        row.amount,
                        ZERO_MONEY,
                    ),
                )
                for row in payment_rows
            ],
            daily=[
                SalesDailyMetric(
                    date=row.date,
                    sales_count=int(row.sales_count or 0),
                    net_sales=self._decimal(
                        row.net_sales,
                        ZERO_MONEY,
                    ),
                )
                for row in daily_rows
            ],
        )

    # ======================================================
    # Inventory
    # ======================================================

    def get_inventory_report(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
        top_limit: int,
    ) -> InventoryReportResponse:
        bounds = self.resolve_period(
            company_id=company_id,
            period=period,
        )

        snapshot = self.repository.get_inventory_snapshot(
            company_id=company_id
        )
        movement_rows = self.repository.get_inventory_movements(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        low_stock_rows = (
            self.repository.get_low_stock_products(
                company_id=company_id,
                limit=top_limit,
            )
        )

        movements = [
            InventoryMovementMetric(
                movement_type=row.movement_type,
                movements_count=int(
                    row.movements_count or 0
                ),
                quantity=self._decimal(
                    row.quantity,
                    ZERO_QUANTITY,
                ),
            )
            for row in movement_rows
        ]

        return InventoryReportResponse(
            metadata=bounds.metadata,
            total_products=int(snapshot.total_products or 0),
            active_products=int(
                snapshot.active_products or 0
            ),
            inactive_products=int(
                snapshot.inactive_products or 0
            ),
            out_of_stock_products=int(
                snapshot.out_of_stock_products or 0
            ),
            low_stock_products=int(
                snapshot.low_stock_products or 0
            ),
            total_stock_units=self._decimal(
                snapshot.total_stock_units,
                ZERO_QUANTITY,
            ),
            inventory_cost_value=self._decimal(
                snapshot.inventory_cost_value,
                ZERO_MONEY,
            ),
            inventory_sale_value=self._decimal(
                snapshot.inventory_sale_value,
                ZERO_MONEY,
            ),
            movements_count=sum(
                item.movements_count for item in movements
            ),
            movements=movements,
            low_stock_items=[
                LowStockProductMetric(
                    product_id=row.product_id,
                    code=row.code,
                    name=row.name,
                    current_stock=self._decimal(
                        row.current_stock,
                        ZERO_QUANTITY,
                    ),
                    minimum_stock=self._decimal(
                        row.minimum_stock,
                        ZERO_QUANTITY,
                    ),
                    shortage_quantity=self._decimal(
                        row.shortage_quantity,
                        ZERO_QUANTITY,
                    ),
                )
                for row in low_stock_rows
            ],
        )

    # ======================================================
    # Cash
    # ======================================================

    def get_cash_report(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
    ) -> CashReportResponse:
        bounds = self.resolve_period(
            company_id=company_id,
            period=period,
        )

        totals = self.repository.get_cash_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        session_totals = (
            self.repository.get_cash_session_totals(
                company_id=company_id,
                start_at=bounds.start_at,
                end_at=bounds.end_at,
            )
        )
        source_rows = self.repository.get_cash_by_source(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        register_rows = self.repository.get_cash_by_register(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )

        total_income = self._decimal(
            totals.total_income,
            ZERO_MONEY,
        )
        total_expense = self._decimal(
            totals.total_expense,
            ZERO_MONEY,
        )

        sources = []
        for row in source_rows:
            income = self._decimal(row.income, ZERO_MONEY)
            expense = self._decimal(row.expense, ZERO_MONEY)
            sources.append(
                CashSourceMetric(
                    source=row.source,
                    transactions_count=int(
                        row.transactions_count or 0
                    ),
                    income=income,
                    expense=expense,
                    net_amount=income - expense,
                )
            )

        registers = []
        for row in register_rows:
            income = self._decimal(row.income, ZERO_MONEY)
            expense = self._decimal(row.expense, ZERO_MONEY)
            registers.append(
                CashRegisterMetric(
                    cash_register_id=row.cash_register_id,
                    code=row.code,
                    name=row.name,
                    transactions_count=int(
                        row.transactions_count or 0
                    ),
                    income=income,
                    expense=expense,
                    net_amount=income - expense,
                )
            )

        return CashReportResponse(
            metadata=bounds.metadata,
            transactions_count=int(
                totals.transactions_count or 0
            ),
            total_income=total_income,
            total_expense=total_expense,
            net_cash_flow=total_income - total_expense,
            sessions_opened=int(
                session_totals.sessions_opened or 0
            ),
            sessions_closed=int(
                session_totals.sessions_closed or 0
            ),
            opening_amount=self._decimal(
                session_totals.opening_amount,
                ZERO_MONEY,
            ),
            closing_difference=self._decimal(
                session_totals.closing_difference,
                ZERO_MONEY,
            ),
            sources=sources,
            registers=registers,
        )

    # ======================================================
    # Customers
    # ======================================================

    def get_customer_report(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
        top_limit: int,
    ) -> CustomerReportResponse:
        bounds = self.resolve_period(
            company_id=company_id,
            period=period,
        )

        totals = self.repository.get_customer_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        sales_totals = (
            self.repository.get_customer_sales_totals(
                company_id=company_id,
                start_at=bounds.start_at,
                end_at=bounds.end_at,
            )
        )
        returning_customers = (
            self.repository.get_returning_customers_count(
                company_id=company_id,
                start_at=bounds.start_at,
                end_at=bounds.end_at,
            )
        )
        top_rows = self.repository.get_top_customers(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            limit=top_limit,
        )

        top_customers = []
        for row in top_rows:
            total_spent = self._decimal(
                row.total_spent,
                ZERO_MONEY,
            )
            purchases_count = int(row.purchases_count or 0)
            average_ticket = ZERO_MONEY
            if purchases_count > 0:
                average_ticket = (
                    total_spent / Decimal(purchases_count)
                ).quantize(MONEY_QUANTUM)

            top_customers.append(
                TopCustomerMetric(
                    customer_id=row.customer_id,
                    customer_name=(
                        f"{row.first_name} {row.last_name}"
                    ).strip(),
                    purchases_count=purchases_count,
                    total_spent=total_spent,
                    average_ticket=average_ticket,
                )
            )

        return CustomerReportResponse(
            metadata=bounds.metadata,
            total_customers=int(totals.total_customers or 0),
            active_customers=int(
                totals.active_customers or 0
            ),
            inactive_customers=int(
                totals.inactive_customers or 0
            ),
            new_customers=int(totals.new_customers or 0),
            customers_with_purchases=int(
                sales_totals.customers_with_purchases or 0
            ),
            returning_customers=returning_customers,
            sales_without_customer=int(
                sales_totals.sales_without_customer or 0
            ),
            top_customers=top_customers,
        )

    # ======================================================
    # Services
    # ======================================================

    def get_service_report(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
        top_limit: int,
    ) -> ServiceReportResponse:
        bounds = self.resolve_period(
            company_id=company_id,
            period=period,
        )

        catalog = self.repository.get_service_catalog_totals(
            company_id=company_id
        )
        totals = self.repository.get_service_sales_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        top_rows = self.repository.get_top_services(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            limit=top_limit,
        )

        top_services = []
        for row in top_rows:
            quantity = self._decimal(
                row.quantity,
                ZERO_QUANTITY,
            )
            revenue = self._decimal(
                row.revenue,
                ZERO_MONEY,
            )
            average_unit_price = ZERO_MONEY
            if quantity > ZERO_QUANTITY:
                average_unit_price = (
                    revenue / quantity
                ).quantize(MONEY_QUANTUM)

            top_services.append(
                TopServiceMetric(
                    service_id=row.service_id,
                    service_name=row.service_name,
                    sales_count=int(row.sales_count or 0),
                    quantity=quantity,
                    revenue=revenue,
                    average_unit_price=average_unit_price,
                )
            )

        active_services = int(catalog.active_services or 0)
        active_services_sold = int(
            totals.active_services_sold or 0
        )

        return ServiceReportResponse(
            metadata=bounds.metadata,
            total_services=int(catalog.total_services or 0),
            active_services=active_services,
            inactive_services=int(
                catalog.inactive_services or 0
            ),
            services_sold=int(totals.services_sold or 0),
            services_without_sales=max(
                active_services - active_services_sold,
                0,
            ),
            service_sales_count=int(
                totals.service_sales_count or 0
            ),
            service_quantity=self._decimal(
                totals.service_quantity,
                ZERO_QUANTITY,
            ),
            service_revenue=self._decimal(
                totals.service_revenue,
                ZERO_MONEY,
            ),
            top_services=top_services,
        )

    # ======================================================
    # Shared period rules
    # ======================================================

    def resolve_period(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
    ) -> ReportPeriodBounds:
        if period.end_date < period.start_date:
            raise InvalidReportPeriodException()

        inclusive_days = (
            period.end_date - period.start_date
        ).days + 1

        if inclusive_days > self.MAXIMUM_PERIOD_DAYS:
            raise ReportPeriodTooLargeException(
                maximum_days=self.MAXIMUM_PERIOD_DAYS
            )

        try:
            timezone_info = ZoneInfo(period.timezone)
        except ZoneInfoNotFoundError as error:
            raise InvalidReportTimezoneException(
                period.timezone
            ) from error

        start_local = datetime.combine(
            period.start_date,
            time.min,
            tzinfo=timezone_info,
        )
        end_local = datetime.combine(
            period.end_date + timedelta(days=1),
            time.min,
            tzinfo=timezone_info,
        )

        return ReportPeriodBounds(
            start_at=start_local.astimezone(timezone.utc),
            end_at=end_local.astimezone(timezone.utc),
            metadata=ReportMetadata(
                company_id=company_id,
                start_date=period.start_date,
                end_date=period.end_date,
                timezone=period.timezone,
                generated_at=datetime.now(timezone.utc),
            ),
        )

    @staticmethod
    def _decimal(
        value,
        default: Decimal,
    ) -> Decimal:
        if value is None:
            return default

        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))