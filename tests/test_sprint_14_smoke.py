import unittest

from app.main import app
from app.modules.purchase.model import (
    PurchaseOrder,
    PurchaseOrderDetail,
    PurchaseReceipt,
    PurchaseReceiptDetail,
)
from app.modules.supplier.model import Supplier
import app.modules.rbac.constants as rbac_constants


def collect_string_constants(module) -> set[str]:
    values: set[str] = set()

    for value in vars(module).values():
        if isinstance(value, str):
            values.add(value)

        elif isinstance(value, type):
            for nested_value in vars(value).values():
                if isinstance(nested_value, str):
                    values.add(nested_value)

        elif isinstance(value, (list, tuple, set, frozenset)):
            values.update(
                item
                for item in value
                if isinstance(item, str)
            )

        elif isinstance(value, dict):
            values.update(
                item
                for item in value.values()
                if isinstance(item, str)
            )

    return values


class Sprint14SmokeTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.openapi = app.openapi()
        cls.paths = cls.openapi["paths"]

    def test_supplier_routes_are_registered(self) -> None:
        self.assertIn("/api/v1/suppliers", self.paths)
        self.assertIn("/api/v1/suppliers/{supplier_id}", self.paths)

        self.assertIn("post", self.paths["/api/v1/suppliers"])
        self.assertIn("get", self.paths["/api/v1/suppliers"])
        self.assertIn("get", self.paths["/api/v1/suppliers/{supplier_id}"])
        self.assertIn("patch", self.paths["/api/v1/suppliers/{supplier_id}"])

    def test_purchase_routes_are_registered(self) -> None:
        expected_operations = {
            "/api/v1/purchases/orders": {"get", "post"},
            "/api/v1/purchases/orders/{order_id}": {"get", "patch"},
            "/api/v1/purchases/orders/{order_id}/approve": {"post"},
            "/api/v1/purchases/orders/{order_id}/cancel": {"post"},
            "/api/v1/purchases/orders/{order_id}/receipts": {"post"},
            "/api/v1/purchases/receipts": {"get"},
            "/api/v1/purchases/receipts/{receipt_id}": {"get"},
        }

        for path, methods in expected_operations.items():
            with self.subTest(path=path):
                self.assertIn(path, self.paths)

                for method in methods:
                    self.assertIn(method, self.paths[path])

    def test_supplier_model_table_name(self) -> None:
        self.assertEqual(Supplier.__tablename__, "suppliers")

    def test_purchase_model_table_names(self) -> None:
        self.assertEqual(PurchaseOrder.__tablename__, "purchase_orders")
        self.assertEqual(
            PurchaseOrderDetail.__tablename__,
            "purchase_order_details",
        )
        self.assertEqual(PurchaseReceipt.__tablename__, "purchase_receipts")
        self.assertEqual(
            PurchaseReceiptDetail.__tablename__,
            "purchase_receipt_details",
        )

    def test_purchase_permissions_are_declared(self) -> None:
        declared_permissions = collect_string_constants(rbac_constants)

        expected_permissions = {
            "purchases:create",
            "purchases:read",
            "purchases:update",
            "purchases:approve",
            "purchases:cancel",
            "purchases:receive",
        }

        missing_permissions = expected_permissions - declared_permissions

        self.assertFalse(
            missing_permissions,
            f"Permisos no encontrados: {sorted(missing_permissions)}",
        )


if __name__ == "__main__":
    unittest.main()
