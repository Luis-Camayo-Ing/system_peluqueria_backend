"""Business logic for company configuration."""

from __future__ import annotations

import uuid

from app.modules.configuration.model import CompanySetting
from app.modules.configuration.repository import (
    CompanySettingRepository,
)
from app.modules.configuration.schemas import (
    CompanySettingUpdate,
)


class CompanySettingService:
    """Manage the authenticated company's configuration."""

    def __init__(
        self,
        repository: CompanySettingRepository,
    ) -> None:
        self.repository = repository

    def get_setting(
        self,
        company_id: uuid.UUID,
    ) -> CompanySetting:
        """Return company settings, creating defaults when absent."""

        return self.repository.get_or_create(
            company_id=company_id,
        )

    def update_setting(
        self,
        company_id: uuid.UUID,
        current_user_id: uuid.UUID,
        setting_data: CompanySettingUpdate,
    ) -> CompanySetting:
        """Update the authenticated company's configuration."""

        setting = self.repository.get_or_create(
            company_id=company_id,
            updated_by_user_id=current_user_id,
        )

        return self.repository.update(
            setting=setting,
            setting_data=setting_data,
            updated_by_user_id=current_user_id,
        )

    @staticmethod
    def build_sale_number_preview(
        setting: CompanySetting,
    ) -> str:
        """Build an example using the configured sale numbering."""

        padded_number = str(
            setting.next_sale_number
        ).zfill(
            setting.sale_number_padding
        )

        return (
            f"{setting.sale_prefix}-"
            f"{padded_number}"
        )