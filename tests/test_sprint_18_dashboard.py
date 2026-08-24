"""Smoke and calculation tests for Sprint 18 dashboard."""

import unittest
from decimal import Decimal

from app.main import app
from app.modules.dashboard.schemas import DashboardResponse
from app.modules.dashboard.service import DashboardService
from app.modules.rbac.constants import (
    DASHBOARD_VIEW,
    SYSTEM_PERMISSIONS,
)


class Sprint18DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = app.openapi()["paths"]

    def test_dashboard_route_is_registered(self) -> None:
        path = "/api/v1/dashboard"

        self.assertIn(path, self.paths)
        self.assertIn("get", self.paths[path])

    def test_dashboard_permission_is_in_catalog(self) -> None:
        self.assertEqual(DASHBOARD_VIEW, "dashboard:view")
        self.assertIn(DASHBOARD_VIEW, SYSTEM_PERMISSIONS)

    def test_dashboard_response_exposes_required_sections(
        self,
    ) -> None:
        fields = DashboardResponse.model_fields

        self.assertIn("metadata", fields)
        self.assertIn("kpis", fields)
        self.assertIn("charts", fields)
        self.assertIn("highlights", fields)

    def test_percentage_is_zero_without_denominator(
        self,
    ) -> None:
        result = DashboardService._percentage(0, 0)

        self.assertEqual(result, Decimal("0.00"))

    def test_percentage_is_quantized(self) -> None:
        result = DashboardService._percentage(1, 3)

        self.assertEqual(result, Decimal("33.33"))

    def test_average_is_zero_without_divisor(self) -> None:
        result = DashboardService._average(
            Decimal("100.00"),
            0,
        )

        self.assertEqual(result, Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()