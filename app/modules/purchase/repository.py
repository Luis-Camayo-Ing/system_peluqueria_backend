from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    Product,
)
from app.modules.purchase.model import (
    PurchaseOrder,
    PurchaseOrderDetail,
    PurchaseOrderStatus,
    PurchaseReceipt,
    PurchaseReceiptDetail,
)
from app.modules.supplier.model import Supplier


class PurchaseRepository:
    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # Transaction helpers
    # ======================================================

    def add(self, instance: object) -> None:
        self.db.add(instance)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    # ======================================================
    # Suppliers and products
    # ======================================================

    def get_supplier_by_id(
        self,
        supplier_id: UUID,
        company_id: UUID,
    ) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_product_by_id(
        self,
        product_id: UUID,
        company_id: UUID,
    ) -> Product | None:
        statement = select(Product).where(
            Product.id == product_id,
            Product.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_product_for_update(
        self,
        product_id: UUID,
        company_id: UUID,
    ) -> Product | None:
        statement = (
            select(Product)
            .where(
                Product.id == product_id,
                Product.company_id == company_id,
            )
            .with_for_update()
        )

        return self.db.scalar(statement)

    # ======================================================
    # Purchase orders
    # ======================================================

    def get_order_by_number(
        self,
        order_number: str,
        company_id: UUID,
        exclude_order_id: UUID | None = None,
    ) -> PurchaseOrder | None:
        statement = select(PurchaseOrder).where(
            PurchaseOrder.company_id == company_id,
            func.upper(PurchaseOrder.order_number)
            == order_number.strip().upper(),
        )

        if exclude_order_id is not None:
            statement = statement.where(
                PurchaseOrder.id != exclude_order_id
            )

        return self.db.scalar(statement)

    def get_order_by_id(
        self,
        order_id: UUID,
        company_id: UUID,
    ) -> PurchaseOrder | None:
        statement = (
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.details),
            )
            .where(
                PurchaseOrder.id == order_id,
                PurchaseOrder.company_id == company_id,
            )
        )

        return self.db.scalar(statement)

    def get_order_for_update(
        self,
        order_id: UUID,
        company_id: UUID,
    ) -> tuple[
        PurchaseOrder | None,
        list[PurchaseOrderDetail],
    ]:
        order_statement = (
            select(PurchaseOrder)
            .where(
                PurchaseOrder.id == order_id,
                PurchaseOrder.company_id == company_id,
            )
            .with_for_update()
        )

        order = self.db.scalar(order_statement)

        if order is None:
            return None, []

        details_statement = (
            select(PurchaseOrderDetail)
            .where(
                PurchaseOrderDetail.purchase_order_id == order.id
            )
            .order_by(PurchaseOrderDetail.product_id.asc())
            .with_for_update()
        )

        details = list(
            self.db.scalars(details_statement).all()
        )

        return order, details

    def list_orders(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: PurchaseOrderStatus | None = None,
        supplier_id: UUID | None = None,
        search: str | None = None,
    ) -> list[PurchaseOrder]:
        statement = (
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.details),
            )
            .join(
                Supplier,
                Supplier.id == PurchaseOrder.supplier_id,
            )
            .where(
                PurchaseOrder.company_id == company_id
            )
        )

        if status is not None:
            statement = statement.where(
                PurchaseOrder.status == status
            )

        if supplier_id is not None:
            statement = statement.where(
                PurchaseOrder.supplier_id == supplier_id
            )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    PurchaseOrder.order_number.ilike(
                        search_value
                    ),
                    Supplier.business_name.ilike(
                        search_value
                    ),
                    Supplier.trade_name.ilike(
                        search_value
                    ),
                )
            )

        statement = (
            statement
            .order_by(PurchaseOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).unique().all()
        )

    def count_orders(
        self,
        company_id: UUID,
        status: PurchaseOrderStatus | None = None,
        supplier_id: UUID | None = None,
        search: str | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(PurchaseOrder)
            .join(
                Supplier,
                Supplier.id == PurchaseOrder.supplier_id,
            )
            .where(
                PurchaseOrder.company_id == company_id
            )
        )

        if status is not None:
            statement = statement.where(
                PurchaseOrder.status == status
            )

        if supplier_id is not None:
            statement = statement.where(
                PurchaseOrder.supplier_id == supplier_id
            )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    PurchaseOrder.order_number.ilike(
                        search_value
                    ),
                    Supplier.business_name.ilike(
                        search_value
                    ),
                    Supplier.trade_name.ilike(
                        search_value
                    ),
                )
            )

        return self.db.scalar(statement) or 0

    def delete_order_details(
        self,
        order_id: UUID,
    ) -> None:
        statement = delete(PurchaseOrderDetail).where(
            PurchaseOrderDetail.purchase_order_id == order_id
        )

        self.db.execute(statement)

    # ======================================================
    # Purchase receipts
    # ======================================================

    def get_receipt_by_number(
        self,
        receipt_number: str,
        company_id: UUID,
    ) -> PurchaseReceipt | None:
        statement = select(PurchaseReceipt).where(
            PurchaseReceipt.company_id == company_id,
            func.upper(PurchaseReceipt.receipt_number)
            == receipt_number.strip().upper(),
        )

        return self.db.scalar(statement)

    def get_receipt_by_id(
        self,
        receipt_id: UUID,
        company_id: UUID,
    ) -> PurchaseReceipt | None:
        statement = (
            select(PurchaseReceipt)
            .options(
                selectinload(PurchaseReceipt.details),
            )
            .where(
                PurchaseReceipt.id == receipt_id,
                PurchaseReceipt.company_id == company_id,
            )
        )

        return self.db.scalar(statement)

    def list_receipts(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        order_id: UUID | None = None,
        supplier_id: UUID | None = None,
        search: str | None = None,
        received_from: datetime | None = None,
        received_to: datetime | None = None,
    ) -> list[PurchaseReceipt]:
        statement = (
            select(PurchaseReceipt)
            .options(
                selectinload(PurchaseReceipt.details),
            )
            .join(
                PurchaseOrder,
                PurchaseOrder.id
                == PurchaseReceipt.purchase_order_id,
            )
            .where(
                PurchaseReceipt.company_id == company_id
            )
        )

        if order_id is not None:
            statement = statement.where(
                PurchaseReceipt.purchase_order_id == order_id
            )

        if supplier_id is not None:
            statement = statement.where(
                PurchaseOrder.supplier_id == supplier_id
            )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    PurchaseReceipt.receipt_number.ilike(
                        search_value
                    ),
                    PurchaseReceipt.supplier_invoice_number.ilike(
                        search_value
                    ),
                    PurchaseOrder.order_number.ilike(
                        search_value
                    ),
                )
            )

        if received_from is not None:
            statement = statement.where(
                PurchaseReceipt.received_at >= received_from
            )

        if received_to is not None:
            statement = statement.where(
                PurchaseReceipt.received_at <= received_to
            )

        statement = (
            statement
            .order_by(PurchaseReceipt.received_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).unique().all()
        )

    def count_receipts(
        self,
        company_id: UUID,
        order_id: UUID | None = None,
        supplier_id: UUID | None = None,
        search: str | None = None,
        received_from: datetime | None = None,
        received_to: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(PurchaseReceipt)
            .join(
                PurchaseOrder,
                PurchaseOrder.id
                == PurchaseReceipt.purchase_order_id,
            )
            .where(
                PurchaseReceipt.company_id == company_id
            )
        )

        if order_id is not None:
            statement = statement.where(
                PurchaseReceipt.purchase_order_id == order_id
            )

        if supplier_id is not None:
            statement = statement.where(
                PurchaseOrder.supplier_id == supplier_id
            )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    PurchaseReceipt.receipt_number.ilike(
                        search_value
                    ),
                    PurchaseReceipt.supplier_invoice_number.ilike(
                        search_value
                    ),
                    PurchaseOrder.order_number.ilike(
                        search_value
                    ),
                )
            )

        if received_from is not None:
            statement = statement.where(
                PurchaseReceipt.received_at >= received_from
            )

        if received_to is not None:
            statement = statement.where(
                PurchaseReceipt.received_at <= received_to
            )

        return self.db.scalar(statement) or 0

    # ======================================================
    # Inventory records created by a receipt
    # ======================================================

    def add_inventory_movement(
        self,
        movement: InventoryMovement,
    ) -> None:
        self.db.add(movement)

    def add_inventory_movement_detail(
        self,
        detail: InventoryMovementDetail,
    ) -> None:
        self.db.add(detail)

    def add_receipt_detail(
        self,
        detail: PurchaseReceiptDetail,
    ) -> None:
        self.db.add(detail)