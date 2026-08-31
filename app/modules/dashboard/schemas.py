"""Pydantic contracts for the operational dashboard."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.appointment.model import AppointmentStatus
from app.modules.report.schemas import (
    InventoryMovementMetric,
    ReportMetadata,
    SalesDailyMetric,
    TopCustomerMetric,
    TopServiceMetric,
)


class DashboardKpis(BaseModel):
    """Main operational indicators for the selected period."""

    completed_sales_count: int = Field(ge=0)
    cancelled_sales_count: int = Field(ge=0)
    sales_cancellation_rate: Decimal = Field(ge=0, le=100)
    net_sales: Decimal = Field(ge=0)
    average_ticket: Decimal = Field(ge=0)
    total_income: Decimal = Field(ge=0)
    total_expense: Decimal = Field(ge=0)
    net_cash_flow: Decimal
    total_stock_units: Decimal = Field(ge=0)
    low_stock_products: int = Field(ge=0)
    out_of_stock_products: int = Field(ge=0)
    active_customers: int = Field(ge=0)
    new_customers: int = Field(ge=0)
    services_sold: int = Field(ge=0)
    service_revenue: Decimal = Field(ge=0)
    appointments_count: int = Field(ge=0)
    completed_appointments: int = Field(ge=0)
    cancelled_appointments: int = Field(ge=0)
    no_show_appointments: int = Field(ge=0)
    appointment_completion_rate: Decimal = Field(ge=0, le=100)


class DashboardCashDailyMetric(BaseModel):
    """Cash flow grouped by local calendar date."""

    date: date
    income: Decimal = Field(ge=0)
    expense: Decimal = Field(ge=0)
    net_amount: Decimal


class DashboardAppointmentStatusMetric(BaseModel):
    """Appointments grouped by lifecycle status."""

    status: AppointmentStatus
    appointments_count: int = Field(ge=0)


class DashboardCharts(BaseModel):
    """Series ready to be rendered by the frontend."""

    daily_sales: list[SalesDailyMetric]
    daily_cash_flow: list[DashboardCashDailyMetric]
    appointments_by_status: list[DashboardAppointmentStatusMetric]
    inventory_movements: list[InventoryMovementMetric]


class DashboardTopProductMetric(BaseModel):
    """Product ranked by completed sale revenue."""

    product_id: UUID
    code: str
    name: str
    sales_count: int = Field(ge=0)
    quantity: Decimal = Field(ge=0)
    revenue: Decimal = Field(ge=0)
    current_stock: Decimal = Field(ge=0)


class DashboardHighlights(BaseModel):
    """Top commercial entities for the selected period."""

    products: list[DashboardTopProductMetric]
    services: list[TopServiceMetric]
    customers: list[TopCustomerMetric]


class DashboardResponse(BaseModel):
    """Complete payload consumed by the dashboard screen."""

    metadata: ReportMetadata
    top_limit: int = Field(ge=1, le=50)
    kpis: DashboardKpis
    charts: DashboardCharts
    highlights: DashboardHighlights