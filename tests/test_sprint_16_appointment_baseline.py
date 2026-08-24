import unittest
import uuid
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.main import app
from app.modules.appointment.model import (
    Appointment,
    AppointmentStatus,
)
from app.modules.appointment.schemas import AppointmentCreate
from app.modules.appointment.service import AppointmentService
import app.modules.rbac.constants as rbac_constants


class Sprint16AppointmentBaselineTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.openapi = app.openapi()
        cls.paths = cls.openapi["paths"]

    def test_appointment_routes_are_registered(self) -> None:
        expected_operations = {
            "/api/v1/appointments": {"get", "post"},
            "/api/v1/appointments/{appointment_id}": {
                "get",
                "patch",
            },
            "/api/v1/appointments/{appointment_id}/cancel": {
                "post",
            },
        }

        for path, methods in expected_operations.items():
            with self.subTest(path=path):
                self.assertIn(path, self.paths)

                for method in methods:
                    self.assertIn(method, self.paths[path])

    def test_appointment_table_name(self) -> None:
        self.assertEqual(
            Appointment.__tablename__,
            "appointments",
        )

    def test_appointment_status_catalog(self) -> None:
        self.assertEqual(
            {status.value for status in AppointmentStatus},
            {
                "scheduled",
                "confirmed",
                "in_progress",
                "completed",
                "cancelled",
                "no_show",
            },
        )

    def test_terminal_statuses_have_no_transitions(self) -> None:
        terminal_statuses = {
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        }

        for status in terminal_statuses:
            with self.subTest(status=status.value):
                self.assertEqual(
                    AppointmentService.ALLOWED_STATUS_TRANSITIONS[
                        status
                    ],
                    set(),
                )

    def test_create_schema_rejects_invalid_time_range(self) -> None:
        start_at = datetime.now(timezone.utc)
        end_at = start_at - timedelta(minutes=30)

        with self.assertRaises(ValidationError):
            AppointmentCreate(
                customer_id=uuid.uuid4(),
                employee_id=uuid.uuid4(),
                service_id=uuid.uuid4(),
                start_at=start_at,
                end_at=end_at,
            )

    def test_current_appointment_permissions_are_declared(self) -> None:
        expected_permissions = {
            "appointments:create",
            "appointments:read",
            "appointments:update",
            "appointments:delete",
        }

        declared_permissions = {
            value
            for value in vars(rbac_constants).values()
            if isinstance(value, str)
        }

        self.assertTrue(
            expected_permissions.issubset(declared_permissions),
        )


if __name__ == "__main__":
    unittest.main()
