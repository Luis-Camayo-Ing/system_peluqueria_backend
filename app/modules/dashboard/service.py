"""Business rules and response assembly for the dashboard."""

from decimal import Decimal
from uuid import UUID

from app.modules.appointment.model import AppointmentStatus
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import (
    DashboardAppointmentStatusMetric,
    DashboardCashDailyMetric,
    DashboardCharts,
    DashboardHighlights,
    DashboardKpis,
    DashboardResponse,
    DashboardTopProductMetric,
)
from app.modules.report.repository import ReportRepository
from app.modules.report.schemas import (
    InventoryMovementMetric,
    ReportPeriodRequest,
    SalesDailyMetric,
    TopCustomerMetric,
    TopServiceMetric,
)
from app.modules.report.service import ReportService

ZERO_MONEY = Decimal("0.00")
ZERO_QUANTITY = Decimal("0.000")
PERCENT_QUANTUM = Decimal("0.01")


class DashboardService:
    """Build a complete operational dashboard for one company."""

    def __init__(
        self,
        *,
        repository: DashboardRepository,
        report_repository: ReportRepository,
    ) -> None:
        self.repository = repository
        self.report_repository = report_repository
        self.report_service = ReportService(report_repository)

    def get_dashboard(
        self,
        *,
        company_id: UUID,
        period: ReportPeriodRequest,
        top_limit: int,
    ) -> DashboardResponse:
        bounds = self.report_service.resolve_period(
            company_id=company_id,
            period=period,
        )

        sales = self.report_repository.get_sales_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        inventory = self.report_repository.get_inventory_snapshot(company_id=company_id)
        cash = self.report_repository.get_cash_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        customers = self.report_repository.get_customer_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        services = self.report_repository.get_service_sales_totals(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )

        daily_sales_rows = self.report_repository.get_daily_sales(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            timezone_name=period.timezone,
        )
        movement_rows = self.report_repository.get_inventory_movements(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        appointment_rows = self.repository.get_appointment_status_counts(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
        )
        daily_cash_rows = self.repository.get_daily_cash_flow(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            timezone_name=period.timezone,
        )

        product_rows = self.repository.get_top_products(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            limit=top_limit,
        )
        service_rows = self.report_repository.get_top_services(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            limit=top_limit,
        )
        customer_rows = self.report_repository.get_top_customers(
            company_id=company_id,
            start_at=bounds.start_at,
            end_at=bounds.end_at,
            limit=top_limit,
        )

        completed_sales = int(sales.completed_sales_count or 0)
        cancelled_sales = int(sales.cancelled_sales_count or 0)
        net_sales = self._decimal(sales.net_sales, ZERO_MONEY)
        total_income = self._decimal(cash.total_income, ZERO_MONEY)
        total_expense = self._decimal(cash.total_expense, ZERO_MONEY)

        appointment_counts = {
            row.status: int(row.appointments_count or 0) for row in appointment_rows
        }
        appointment_chart = [
            DashboardAppointmentStatusMetric(
                status=status,
                appointments_count=appointment_counts.get(status, 0),
            )
            for status in AppointmentStatus
        ]

        completed_appointments = appointment_counts.get(
            AppointmentStatus.COMPLETED,
            0,
        )
        cancelled_appointments = appointment_counts.get(
            AppointmentStatus.CANCELLED,
            0,
        )
        no_show_appointments = appointment_counts.get(
            AppointmentStatus.NO_SHOW,
            0,
        )
        terminal_appointments = (
            completed_appointments + cancelled_appointments + no_show_appointments
        )

        return DashboardResponse(
            metadata=bounds.metadata,
            top_limit=top_limit,
            kpis=DashboardKpis(
                completed_sales_count=completed_sales,
                cancelled_sales_count=cancelled_sales,
                sales_cancellation_rate=self._percentage(
                    cancelled_sales,
                    completed_sales + cancelled_sales,
                ),
                net_sales=net_sales,
                average_ticket=self._average(
                    net_sales,
                    completed_sales,
                ),
                total_income=total_income,
                total_expense=total_expense,
                net_cash_flow=total_income - total_expense,
                total_stock_units=self._decimal(
                    inventory.total_stock_units,
                    ZERO_QUANTITY,
                ),
                low_stock_products=int(inventory.low_stock_products or 0),
                out_of_stock_products=int(inventory.out_of_stock_products or 0),
                active_customers=int(customers.active_customers or 0),
                new_customers=int(customers.new_customers or 0),
                services_sold=int(services.services_sold or 0),
                service_revenue=self._decimal(
                    services.service_revenue,
                    ZERO_MONEY,
                ),
                appointments_count=sum(appointment_counts.values()),
                completed_appointments=completed_appointments,
                cancelled_appointments=cancelled_appointments,
                no_show_appointments=no_show_appointments,
                appointment_completion_rate=self._percentage(
                    completed_appointments,
                    terminal_appointments,
                ),
            ),
            charts=DashboardCharts(
                daily_sales=[
                    SalesDailyMetric(
                        date=row.date,
                        sales_count=int(row.sales_count or 0),
                        net_sales=self._decimal(
                            row.net_sales,
                            ZERO_MONEY,
                        ),
                    )
                    for row in daily_sales_rows
                ],
                daily_cash_flow=[
                    self._build_cash_metric(row) for row in daily_cash_rows
                ],
                appointments_by_status=appointment_chart,
                inventory_movements=[
                    InventoryMovementMetric(
                        movement_type=row.movement_type,
                        movements_count=int(row.movements_count or 0),
                        quantity=self._decimal(
                            row.quantity,
                            ZERO_QUANTITY,
                        ),
                    )
                    for row in movement_rows
                ],
            ),
            highlights=DashboardHighlights(
                products=[
                    DashboardTopProductMetric(
                        product_id=row.product_id,
                        code=row.code,
                        name=row.name,
                        sales_count=int(row.sales_count or 0),
                        quantity=self._decimal(
                            row.quantity,
                            ZERO_QUANTITY,
                        ),
                        revenue=self._decimal(
                            row.revenue,
                            ZERO_MONEY,
                        ),
                        current_stock=self._decimal(
                            row.current_stock,
                            ZERO_QUANTITY,
                        ),
                    )
                    for row in product_rows
                ],
                services=[self._build_top_service(row) for row in service_rows],
                customers=[self._build_top_customer(row) for row in customer_rows],
            ),
        )

    def _build_cash_metric(self, row) -> DashboardCashDailyMetric:
        income = self._decimal(row.income, ZERO_MONEY)
        expense = self._decimal(row.expense, ZERO_MONEY)

        return DashboardCashDailyMetric(
            date=row.date,
            income=income,
            expense=expense,
            net_amount=income - expense,
        )

    def _build_top_service(self, row) -> TopServiceMetric:
        quantity = self._decimal(row.quantity, ZERO_QUANTITY)
        revenue = self._decimal(row.revenue, ZERO_MONEY)

        return TopServiceMetric(
            service_id=row.service_id,
            service_name=row.service_name,
            sales_count=int(row.sales_count or 0),
            quantity=quantity,
            revenue=revenue,
            average_unit_price=self._average(revenue, quantity),
        )

    def _build_top_customer(self, row) -> TopCustomerMetric:
        purchases_count = int(row.purchases_count or 0)
        total_spent = self._decimal(row.total_spent, ZERO_MONEY)

        return TopCustomerMetric(
            customer_id=row.customer_id,
            customer_name=(f"{row.first_name} {row.last_name}").strip(),
            purchases_count=purchases_count,
            total_spent=total_spent,
            average_ticket=self._average(
                total_spent,
                purchases_count,
            ),
        )

    @staticmethod
    def _percentage(numerator: int, denominator: int) -> Decimal:
        if denominator <= 0:
            return ZERO_MONEY

        return (Decimal(numerator) * Decimal(100) / Decimal(denominator)).quantize(
            PERCENT_QUANTUM
        )

    @staticmethod
    def _average(value: Decimal, divisor) -> Decimal:
        decimal_divisor = Decimal(str(divisor))
        if decimal_divisor <= 0:
            return ZERO_MONEY

        return (value / decimal_divisor).quantize(PERCENT_QUANTUM)

    @staticmethod
    def _decimal(value, default: Decimal) -> Decimal:
        if value is None:
            return default

        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))