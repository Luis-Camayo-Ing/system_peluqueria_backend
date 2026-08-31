"""Security and release regression tests for Sprint 30."""

import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app
from app.modules.rbac.constants import SYSTEM_PERMISSIONS
from app.modules.rbac.exceptions import (
    RBACCompanyScopeException,
    SystemPermissionModificationException,
    SystemRoleModificationException,
)
from app.modules.rbac.schemas import PermissionUpdate, RoleCreate
from app.modules.rbac.service import RBACService


def dependency_modules(route: APIRoute) -> set[str]:
    modules: set[str] = set()

    def visit(dependant) -> None:
        for dependency in dependant.dependencies:
            call = dependency.call
            modules.add(getattr(call, "__module__", ""))
            visit(dependency)

    visit(route.dependant)
    return modules


class Sprint30SecurityTests(unittest.TestCase):
    def test_production_rejects_debug_and_short_secret(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                environment="production",
                debug=True,
                database_url="postgresql+psycopg://db/app",
                secret_key="short",
                allowed_hosts=["erp.example.com"],
            )

    def test_api_responses_include_security_headers(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/v1/salud")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["x-content-type-options"],
            "nosniff",
        )
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_private_api_routes_declare_authentication(self) -> None:
        public_paths = {
            "/api/v1/salud",
            "/api/v1/salud/base-datos",
            "/api/v1/auth/login",
        }
        security_modules = {
            "app.modules.auth.dependencies",
            "app.modules.rbac.dependencies",
        }

        unprotected: list[str] = []
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            if not route.path.startswith("/api/v1"):
                continue
            if route.path in public_paths:
                continue
            if dependency_modules(route).isdisjoint(security_modules):
                unprotected.append(route.path)

        self.assertEqual(unprotected, [])

    def test_role_schema_rejects_system_role_escalation(self) -> None:
        with self.assertRaises(ValidationError):
            RoleCreate(
                company_id=uuid.uuid4(),
                name="Custom role",
                is_system_role=True,
            )

    def test_role_creation_is_scoped_and_never_system(self) -> None:
        company_id = uuid.uuid4()
        repository = Mock()
        repository.get_role_by_name.return_value = None
        repository.create_role.side_effect = lambda role: role
        service = RBACService.__new__(RBACService)
        service.repository = repository

        role = service.create_role(
            RoleCreate(
                company_id=company_id,
                name="Custom role",
            ),
            company_id=company_id,
        )

        self.assertFalse(role.is_system_role)

        with self.assertRaises(RBACCompanyScopeException):
            service.create_role(
                RoleCreate(
                    company_id=uuid.uuid4(),
                    name="Other company role",
                ),
                company_id=company_id,
            )

    def test_system_rbac_catalog_is_protected(self) -> None:
        repository = Mock()
        service = RBACService.__new__(RBACService)
        service.repository = repository
        repository.get_permission_by_id.return_value = SimpleNamespace(
            name=SYSTEM_PERMISSIONS[0]
        )

        with self.assertRaises(SystemPermissionModificationException):
            service.update_permission(
                uuid.uuid4(),
                PermissionUpdate(description="No permitido"),
            )

        repository.get_role_by_id.return_value = SimpleNamespace(
            is_system_role=True
        )
        with self.assertRaises(SystemRoleModificationException):
            service.assign_permission_to_role(
                role_id=uuid.uuid4(),
                permission_id=uuid.uuid4(),
                company_id=uuid.uuid4(),
            )


if __name__ == "__main__":
    unittest.main()
