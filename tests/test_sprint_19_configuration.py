"""Smoke and validation tests for Sprint 19 configuration."""

import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from app.main import app
from app.modules.configuration.model import CompanySetting
from app.modules.configuration.schemas import (
    CompanySettingUpdate,
    CompanySettingValues,
)
from app.modules.configuration.service import (
    CompanySettingService,
)
from app.modules.rbac.constants import (
    CONFIGURATION_READ,
    CONFIGURATION_UPDATE,
    SYSTEM_PERMISSIONS,
)


class Sprint19ConfigurationTests(unittest.TestCase):
    """Validate the general configuration module."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = app.openapi()["paths"]

    def test_configuration_routes_are_registered(
        self,
    ) -> None:
        path = "/api/v1/configuration"

        self.assertIn(path, self.paths)
        self.assertIn("get", self.paths[path])
        self.assertIn("patch", self.paths[path])

    def test_configuration_permissions_are_declared(
        self,
    ) -> None:
        self.assertEqual(
            CONFIGURATION_READ,
            "configuration:read",
        )
        self.assertEqual(
            CONFIGURATION_UPDATE,
            "configuration:update",
        )
        self.assertIn(
            CONFIGURATION_READ,
            SYSTEM_PERMISSIONS,
        )
        self.assertIn(
            CONFIGURATION_UPDATE,
            SYSTEM_PERMISSIONS,
        )

    def test_configuration_model_table_name(
        self,
    ) -> None:
        self.assertEqual(
            CompanySetting.__tablename__,
            "company_settings",
        )

    def test_default_configuration_values(
        self,
    ) -> None:
        values = CompanySettingValues()

        self.assertEqual(values.country_code, "CO")
        self.assertEqual(values.currency_code, "COP")
        self.assertEqual(values.tax_name, "IVA")
        self.assertEqual(values.sale_prefix, "VTA")
        self.assertEqual(values.next_sale_number, 1)
        self.assertEqual(values.sale_number_padding, 6)
        self.assertEqual(
            values.timezone,
            "America/Bogota",
        )

    def test_codes_locale_and_colors_are_normalized(
        self,
    ) -> None:
        values = CompanySettingValues(
            country_code="co",
            currency_code="cop",
            locale="es-co",
            primary_color="#abcdef",
            secondary_color="#123abc",
        )

        self.assertEqual(values.country_code, "CO")
        self.assertEqual(values.currency_code, "COP")
        self.assertEqual(values.locale, "es_CO")
        self.assertEqual(
            values.primary_color,
            "#ABCDEF",
        )
        self.assertEqual(
            values.secondary_color,
            "#123ABC",
        )

    def test_unknown_timezone_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            CompanySettingUpdate(
                timezone="America/Timezone-Inexistente",
            )

    def test_empty_update_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            CompanySettingUpdate()

    def test_required_setting_cannot_be_null(
        self,
    ) -> None:
        with self.assertRaises(ValidationError):
            CompanySettingUpdate(
                currency_code=None,
            )

    def test_nullable_setting_can_be_cleared(
        self,
    ) -> None:
        update = CompanySettingUpdate(
            logo_url=None,
        )

        self.assertIn(
            "logo_url",
            update.model_fields_set,
        )
        self.assertIsNone(update.logo_url)

    def test_sale_number_preview_uses_padding(
        self,
    ) -> None:
        setting = SimpleNamespace(
            sale_prefix="VTA",
            next_sale_number=27,
            sale_number_padding=6,
        )

        preview = (
            CompanySettingService
            .build_sale_number_preview(setting)
        )

        self.assertEqual(
            preview,
            "VTA-000027",
        )


if __name__ == "__main__":
    unittest.main()