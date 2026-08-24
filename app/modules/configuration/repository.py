"""Persistence operations for company configuration."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.configuration.model import CompanySetting
from app.modules.configuration.schemas import CompanySettingUpdate


class CompanySettingRepository:
    """Store and retrieve one configuration per company."""

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get_by_company_id(
        self,
        company_id: uuid.UUID,
    ) -> CompanySetting | None:
        """Return the configuration owned by a company."""

        statement = select(CompanySetting).where(
            CompanySetting.company_id == company_id
        )

        return self.db.scalar(statement)

    def create_default(
        self,
        company_id: uuid.UUID,
        updated_by_user_id: uuid.UUID | None = None,
    ) -> CompanySetting:
        """Create a configuration using the model defaults."""

        setting = CompanySetting(
            company_id=company_id,
            updated_by_user_id=updated_by_user_id,
        )

        self.db.add(setting)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

            existing_setting = self.get_by_company_id(
                company_id
            )

            if existing_setting is None:
                raise

            return existing_setting

        self.db.refresh(setting)

        return setting

    def get_or_create(
        self,
        company_id: uuid.UUID,
        updated_by_user_id: uuid.UUID | None = None,
    ) -> CompanySetting:
        """Return the existing configuration or create defaults."""

        setting = self.get_by_company_id(company_id)

        if setting is not None:
            return setting

        return self.create_default(
            company_id=company_id,
            updated_by_user_id=updated_by_user_id,
        )

    def update(
        self,
        setting: CompanySetting,
        setting_data: CompanySettingUpdate,
        updated_by_user_id: uuid.UUID,
    ) -> CompanySetting:
        """Apply only the explicitly provided configuration fields."""

        update_data = setting_data.model_dump(
            exclude_unset=True,
        )

        for field_name, value in update_data.items():
            setattr(
                setting,
                field_name,
                value,
            )

        setting.updated_by_user_id = updated_by_user_id

        self.db.commit()
        self.db.refresh(setting)

        return setting