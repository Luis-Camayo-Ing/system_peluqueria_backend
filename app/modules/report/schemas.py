"""Pydantic contracts for business reports."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.cash_register.model import (
    CashTransactionSource,
)
from app.modules.inventory.model import InventoryMovementType
from app.modules.sale.model import SalePaymentMethod


class ReportPeriodRequest(BaseModel):
    """Date range and timezone received from query parameters."""

    start_date: date
    end_date: date
    timezone: str = Field(
        default="America/Bogota",
        min_length=1,
        max_length=100,
    )


class ReportMetadata(BaseModel):
    """Shared metadata returned by every report."""

    company_id: UUID
    start_date: date
    end_date: date
    timezone: str
    generated_at: datetime


class SalesDailyMetric(BaseModel):
    """Completed sales grouped by local calendar date."""

    date: date
    sales_count: int = Field(ge=0)
    net_sales: Decimal = Field(ge=0)


class SalesPaymentMethodMetric(BaseModel):
    """Amounts collected through one payment method."""

    payment_method: SalePaymentMethod
    payments_count: int = Field(ge=0)
    amount: Decimal = Field(ge=0)


class SalesReportResponse(BaseModel):
    """Commercial performance for one period."""

    metadata: ReportMetadata
    completed_sales_count: int = Field(ge=0)
    cancelled_sales_count: int = Field(ge=0)
    cancelled_amount: Decimal = Field(ge=0)
    gross_subtotal: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    net_sales: Decimal = Field(ge=0)
    average_ticket: Decimal = Field(ge=0)
    products_quantity: Decimal = Field(ge=0)
    services_quantity: Decimal = Field(ge=0)
    payment_methods: list[SalesPaymentMethodMetric]
    daily: list[SalesDailyMetric]


class InventoryMovementMetric(BaseModel):
    """Inventory quantities grouped by movement type."""

    movement_type: InventoryMovementType
    movements_count: int = Field(ge=0)
    quantity: Decimal = Field(ge=0)


class LowStockProductMetric(BaseModel):
    """Product requiring inventory attention."""

    product_id: UUID
    code: str
    name: str
    current_stock: Decimal = Field(ge=0)
    minimum_stock: Decimal = Field(ge=0)
    shortage_quantity: Decimal = Field(ge=0)


class InventoryReportResponse(BaseModel):
    """Current inventory snapshot plus period movements."""

    metadata: ReportMetadata
    total_products: int = Field(ge=0)
    active_products: int = Field(ge=0)
    inactive_products: int = Field(ge=0)
    out_of_stock_products: int = Field(ge=0)
    low_stock_products: int = Field(ge=0)
    total_stock_units: Decimal = Field(ge=0)
    inventory_cost_value: Decimal = Field(ge=0)
    inventory_sale_value: Decimal = Field(ge=0)
    movements_count: int = Field(ge=0)
    movements: list[InventoryMovementMetric]
    low_stock_items: list[LowStockProductMetric]


class CashSourceMetric(BaseModel):
    """Cash movement totals grouped by origin."""

    source: CashTransactionSource
    transactions_count: int = Field(ge=0)
    income: Decimal = Field(ge=0)
    expense: Decimal = Field(ge=0)
    net_amount: Decimal


class CashRegisterMetric(BaseModel):
    """Cash totals for one register."""

    cash_register_id: UUID
    code: str
    name: str
    transactions_count: int = Field(ge=0)
    income: Decimal = Field(ge=0)
    expense: Decimal = Field(ge=0)
    net_amount: Decimal


class CashReportResponse(BaseModel):
    """Cash flow and session indicators for one period."""

    metadata: ReportMetadata
    transactions_count: int = Field(ge=0)
    total_income: Decimal = Field(ge=0)
    total_expense: Decimal = Field(ge=0)
    net_cash_flow: Decimal
    sessions_opened: int = Field(ge=0)
    sessions_closed: int = Field(ge=0)
    opening_amount: Decimal = Field(ge=0)
    closing_difference: Decimal
    sources: list[CashSourceMetric]
    registers: list[CashRegisterMetric]


class TopCustomerMetric(BaseModel):
    """Customer ranked by completed sales."""

    customer_id: UUID
    customer_name: str
    purchases_count: int = Field(ge=0)
    total_spent: Decimal = Field(ge=0)
    average_ticket: Decimal = Field(ge=0)


class CustomerReportResponse(BaseModel):
    """Customer base and purchasing activity."""

    metadata: ReportMetadata
    total_customers: int = Field(ge=0)
    active_customers: int = Field(ge=0)
    inactive_customers: int = Field(ge=0)
    new_customers: int = Field(ge=0)
    customers_with_purchases: int = Field(ge=0)
    returning_customers: int = Field(ge=0)
    sales_without_customer: int = Field(ge=0)
    top_customers: list[TopCustomerMetric]


class TopServiceMetric(BaseModel):
    """Service ranked by completed sale revenue."""

    service_id: UUID
    service_name: str
    sales_count: int = Field(ge=0)
    quantity: Decimal = Field(ge=0)
    revenue: Decimal = Field(ge=0)
    average_unit_price: Decimal = Field(ge=0)


class ServiceReportResponse(BaseModel):
    """Service catalog and sales performance."""

    metadata: ReportMetadata
    total_services: int = Field(ge=0)
    active_services: int = Field(ge=0)
    inactive_services: int = Field(ge=0)
    services_sold: int = Field(ge=0)
    services_without_sales: int = Field(ge=0)
    service_sales_count: int = Field(ge=0)
    service_quantity: Decimal = Field(ge=0)
    service_revenue: Decimal = Field(ge=0)
    top_services: list[TopServiceMetric]