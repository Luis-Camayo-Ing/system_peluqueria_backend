"""REST endpoint for the operational dashboard."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import DashboardResponse
from app.modules.dashboard.service import DashboardService
from app.modules.rbac.constants import DASHBOARD_VIEW
from app.modules.rbac.dependencies import require_permission
from app.modules.report.repository import ReportRepository
from app.modules.report.schemas import ReportPeriodRequest
from app.modules.user.model import User

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def get_dashboard_service(
    db: Session = Depends(get_db),
) -> DashboardService:
    """Build dashboard services with one database session."""

    return DashboardService(
        repository=DashboardRepository(db),
        report_repository=ReportRepository(db),
    )


def get_dashboard_period(
    start_date: date = Query(
        ...,
        description="Fecha inicial inclusiva del dashboard.",
    ),
    end_date: date = Query(
        ...,
        description="Fecha final inclusiva del dashboard.",
    ),
    timezone_name: str = Query(
        default="America/Bogota",
        alias="timezone",
        min_length=1,
        max_length=100,
        description="Zona horaria IANA usada para el período.",
    ),
) -> ReportPeriodRequest:
    """Collect the dashboard date range and timezone."""

    return ReportPeriodRequest(
        start_date=start_date,
        end_date=end_date,
        timezone=timezone_name,
    )


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    top_limit: int = Query(
        default=5,
        ge=1,
        le=50,
        description="Cantidad máxima de destacados por categoría.",
    ),
    period: ReportPeriodRequest = Depends(get_dashboard_period),
    current_user: User = Depends(require_permission(DASHBOARD_VIEW)),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    """Return KPIs, chart series and highlighted entities."""

    return dashboard_service.get_dashboard(
        company_id=current_user.company_id,
        period=period,
        top_limit=top_limit,
    )