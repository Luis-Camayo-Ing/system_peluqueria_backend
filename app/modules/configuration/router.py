"""REST endpoints for company configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.configuration.repository import (
    CompanySettingRepository,
)
from app.modules.configuration.schemas import (
    CompanySettingResponse,
    CompanySettingUpdate,
)
from app.modules.configuration.service import (
    CompanySettingService,
)
from app.modules.rbac.constants import (
    CONFIGURATION_READ,
    CONFIGURATION_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.user.model import User


router = APIRouter(
    prefix="/configuration",
    tags=["Configuración"],
)


def get_company_setting_service(
    db: Session = Depends(get_db),
) -> CompanySettingService:
    """Build the configuration service."""

    return CompanySettingService(
        repository=CompanySettingRepository(db),
    )


@router.get(
    "",
    response_model=CompanySettingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company Configuration",
)
def get_company_configuration(
    current_user: User = Depends(
        require_permission(CONFIGURATION_READ)
    ),
    setting_service: CompanySettingService = Depends(
        get_company_setting_service
    ),
) -> CompanySettingResponse:
    """Return settings for the authenticated user's company."""

    return setting_service.get_setting(
        company_id=current_user.company_id,
    )


@router.patch(
    "",
    response_model=CompanySettingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Company Configuration",
)
def update_company_configuration(
    setting_data: CompanySettingUpdate,
    current_user: User = Depends(
        require_permission(CONFIGURATION_UPDATE)
    ),
    setting_service: CompanySettingService = Depends(
        get_company_setting_service
    ),
) -> CompanySettingResponse:
    """Partially update settings for the authenticated company."""

    return setting_service.update_setting(
        company_id=current_user.company_id,
        current_user_id=current_user.id,
        setting_data=setting_data,
    )