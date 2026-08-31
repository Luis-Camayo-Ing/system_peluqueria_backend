"""Smoke and rule tests for Sprint 17 reports."""

import unittest
import uuid
from datetime import date
from unittest.mock import Mock

from app.main import app
from app.modules.rbac.constants import (
    REPORTS_VIEW,
    SYSTEM_PERMISSIONS,
)
from app.modules.report.exceptions import (
    InvalidReportPeriodException,
    InvalidReportTimezoneException,
    ReportPeriodTooLargeException,
)
from app.modules.report.schemas import ReportPeriodRequest
from app.modules.report.service import ReportService


class Sprint17ReportTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = app.openapi()["paths"]
        cls.service = ReportService(repository=Mock())
        cls.company_id = uuid.uuid4()

    def test_report_routes_are_registered(self) -> None:
        expected_paths = {
            "/api/v1/reports/sales",
            "/api/v1/reports/inventory",
            "/api/v1/reports/cash",
            "/api/v1/reports/customers",
            "/api/v1/reports/services",
        }

        for path in expected_paths:
            with self.subTest(path=path):
                self.assertIn(path, self.paths)
                self.assertIn("get", self.paths[path])

    def test_report_permission_is_in_catalog(self) -> None:
        self.assertEqual(REPORTS_VIEW, "reports:view")
        self.assertIn(REPORTS_VIEW, SYSTEM_PERMISSIONS)

    def test_period_is_inclusive_and_converted_to_utc(
        self,
    ) -> None:
        period = ReportPeriodRequest(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 2),
            timezone="America/Bogota",
        )

        bounds = self.service.resolve_period(
            company_id=self.company_id,
            period=period,
        )

        self.assertEqual(
            bounds.start_at.isoformat(),
            "2026-08-01T05:00:00+00:00",
        )
        self.assertEqual(
            bounds.end_at.isoformat(),
            "2026-08-03T05:00:00+00:00",
        )

    def test_invalid_period_is_rejected(self) -> None:
        period = ReportPeriodRequest(
            start_date=date(2026, 8, 2),
            end_date=date(2026, 8, 1),
        )

        with self.assertRaises(InvalidReportPeriodException):
            self.service.resolve_period(
                company_id=self.company_id,
                period=period,
            )

    def test_period_longer_than_366_days_is_rejected(
        self,
    ) -> None:
        period = ReportPeriodRequest(
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 2),
        )

        with self.assertRaises(ReportPeriodTooLargeException):
            self.service.resolve_period(
                company_id=self.company_id,
                period=period,
            )

    def test_unknown_timezone_is_rejected(self) -> None:
        period = ReportPeriodRequest(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 2),
            timezone="Zona/Inexistente",
        )

        with self.assertRaises(InvalidReportTimezoneException):
            self.service.resolve_period(
                company_id=self.company_id,
                period=period,
            )


if __name__ == "__main__":
    unittest.main()