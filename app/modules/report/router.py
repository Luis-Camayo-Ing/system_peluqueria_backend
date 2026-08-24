"""REST endpoints for period-based business reports."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.rbac.constants import REPORTS_VIEW
from app.modules.rbac.dependencies import require_permission
from app.modules.report.repository import ReportRepository
from app.modules.report.schemas import (
    CashReportResponse,
    CustomerReportResponse,
    InventoryReportResponse,
    ReportPeriodRequest,
    SalesReportResponse,
    ServiceReportResponse,
)
from app.modules.report.service import ReportService
from app.modules.user.model import User

router = APIRouter(
    prefix="/reports",
    tags=["Reportes"],
)


def get_report_service(
    db: Session = Depends(get_db),
) -> ReportService:
    """Build the read-only report service."""

    return ReportService(
        repository=ReportRepository(db),
    )


def get_report_period(
    start_date: date = Query(
        ...,
        description="Fecha inicial inclusiva del reporte.",
    ),
    end_date: date = Query(
        ...,
        description="Fecha final inclusiva del reporte.",
    ),
    timezone_name: str = Query(
        default="America/Bogota",
        alias="timezone",
        min_length=1,
        max_length=100,
        description="Zona horaria IANA usada para el período.",
    ),
) -> ReportPeriodRequest:
    """Collect the common period query parameters."""

    return ReportPeriodRequest(
        start_date=start_date,
        end_date=end_date,
        timezone=timezone_name,
    )


@router.get(
    "/sales",
    response_model=SalesReportResponse,
)
def get_sales_report(
    period: ReportPeriodRequest = Depends(get_report_period),
    current_user: User = Depends(
        require_permission(REPORTS_VIEW)
    ),
    report_service: ReportService = Depends(
        get_report_service
    ),
) -> SalesReportResponse:
    """Return sales totals, payment methods and daily values."""

    return report_service.get_sales_report(
        company_id=current_user.company_id,
        period=period,
    )


@router.get(
    "/inventory",
    response_model=InventoryReportResponse,
)
def get_inventory_report(
    top_limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Cantidad máxima de productos con alerta.",
    ),
    period: ReportPeriodRequest = Depends(get_report_period),
    current_user: User = Depends(
        require_permission(REPORTS_VIEW)
    ),
    report_service: ReportService = Depends(
        get_report_service
    ),
) -> InventoryReportResponse:
    """Return inventory valuation, alerts and movements."""

    return report_service.get_inventory_report(
        company_id=current_user.company_id,
        period=period,
        top_limit=top_limit,
    )


@router.get(
    "/cash",
    response_model=CashReportResponse,
)
def get_cash_report(
    period: ReportPeriodRequest = Depends(get_report_period),
    current_user: User = Depends(
        require_permission(REPORTS_VIEW)
    ),
    report_service: ReportService = Depends(
        get_report_service
    ),
) -> CashReportResponse:
    """Return cash flow, session and register totals."""

    return report_service.get_cash_report(
        company_id=current_user.company_id,
        period=period,
    )


@router.get(
    "/customers",
    response_model=CustomerReportResponse,
)
def get_customer_report(
    top_limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Cantidad máxima de clientes destacados.",
    ),
    period: ReportPeriodRequest = Depends(get_report_period),
    current_user: User = Depends(
        require_permission(REPORTS_VIEW)
    ),
    report_service: ReportService = Depends(
        get_report_service
    ),
) -> CustomerReportResponse:
    """Return customer base and purchasing activity."""

    return report_service.get_customer_report(
        company_id=current_user.company_id,
        period=period,
        top_limit=top_limit,
    )


@router.get(
    "/services",
    response_model=ServiceReportResponse,
)
def get_service_report(
    top_limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Cantidad máxima de servicios destacados.",
    ),
    period: ReportPeriodRequest = Depends(get_report_period),
    current_user: User = Depends(
        require_permission(REPORTS_VIEW)
    ),
    report_service: ReportService = Depends(
        get_report_service
    ),
) -> ServiceReportResponse:
    """Return service catalog and commercial performance."""

    return report_service.get_service_report(
        company_id=current_user.company_id,
        period=period,
        top_limit=top_limit,
    )