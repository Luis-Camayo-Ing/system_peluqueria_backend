from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    InventoryMovementType,
    Product,
)
from app.modules.purchase.exceptions import (
    PurchaseDomainException,
    PurchaseInvalidDiscountException,
    PurchaseOrderAlreadyExistsException,
    PurchaseOrderDetailNotFoundException,
    PurchaseOrderHasNoDetailsException,
    PurchaseOrderNotApprovableException,
    PurchaseOrderNotCancellableException,
    PurchaseOrderNotEditableException,
    PurchaseOrderNotFoundException,
    PurchaseOrderNotReceivableException,
    PurchaseOrderProcessingException,
    PurchaseProductInactiveException,
    PurchaseProductNotFoundException,
    PurchaseReceiptAlreadyExistsException,
    PurchaseReceiptNotFoundException,
    PurchaseReceiptProcessingException,
    PurchaseReceiptQuantityExceededException,
    PurchaseSupplierInactiveException,
    PurchaseSupplierNotFoundException,
)
from app.modules.purchase.model import (
    PurchaseOrder,
    PurchaseOrderDetail,
    PurchaseOrderStatus,
    PurchaseReceipt,
    PurchaseReceiptDetail,
)
from app.modules.purchase.repository import PurchaseRepository
from app.modules.purchase.schemas import (
    PurchaseOrderCancel,
    PurchaseOrderCreate,
    PurchaseOrderDetailCreate,
    PurchaseOrderUpdate,
    PurchaseReceiptCreate,
)
from app.modules.supplier.model import Supplier


MONEY_QUANTIZER = Decimal("0.01")


class PurchaseService:
    def __init__(
        self,
        repository: PurchaseRepository,
    ):
        self.repository = repository

    # ======================================================
    # Purchase orders
    # ======================================================

    def create_order(
        self,
        company_id: UUID,
        user_id: UUID,
        data: PurchaseOrderCreate,
    ) -> PurchaseOrder:
        try:
            supplier = self._get_active_supplier(
                supplier_id=data.supplier_id,
                company_id=company_id,
            )

            order_number = self._normalize_number(
                data.order_number
            )

            self._validate_order_number(
                company_id=company_id,
                order_number=order_number,
            )

            order = PurchaseOrder(
                company_id=company_id,
                supplier_id=supplier.id,
                created_by_user_id=user_id,
                order_number=order_number,
                status=PurchaseOrderStatus.DRAFT,
                expected_at=data.expected_at,
                tax_amount=data.tax_amount,
                discount_amount=data.discount_amount,
                notes=data.notes,
            )

            self.repository.add(order)
            self.repository.flush()

            subtotal = self._create_order_details(
                order=order,
                company_id=company_id,
                details_data=data.details,
            )

            order.subtotal = subtotal
            order.total_amount = self._calculate_total(
                subtotal=subtotal,
                tax_amount=order.tax_amount,
                discount_amount=order.discount_amount,
            )

            self.repository.commit()

            return self._get_order_or_raise(
                order_id=order.id,
                company_id=company_id,
            )

        except PurchaseDomainException:
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()
            raise PurchaseOrderProcessingException() from exception

    def get_order(
        self,
        order_id: UUID,
        company_id: UUID,
    ) -> PurchaseOrder:
        return self._get_order_or_raise(
            order_id=order_id,
            company_id=company_id,
        )

    def list_orders(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: PurchaseOrderStatus | None = None,
        supplier_id: UUID | None = None,
        search: str | None = None,
    ) -> dict:
        orders = self.repository.list_orders(
            company_id=company_id,
            skip=skip,
            limit=limit,
            status=status,
            supplier_id=supplier_id,
            search=search,
        )

        total = self.repository.count_orders(
            company_id=company_id,
            status=status,
            supplier_id=supplier_id,
            search=search,
        )

        return {
            "total": total,
            "items": orders,
        }

    def update_order(
        self,
        order_id: UUID,
        company_id: UUID,
        data: PurchaseOrderUpdate,
    ) -> PurchaseOrder:
        try:
            order = self._get_order_or_raise(
                order_id=order_id,
                company_id=company_id,
            )

            if order.status != PurchaseOrderStatus.DRAFT:
                raise PurchaseOrderNotEditableException()

            details_was_provided = (
                "details" in data.model_fields_set
            )

            details_data = (
                data.details
                if details_was_provided
                else None
            )

            update_data = data.model_dump(
                exclude_unset=True,
                exclude={"details"},
            )

            if not update_data and not details_was_provided:
                return order

            supplier_id = update_data.get(
                "supplier_id"
            )

            if supplier_id is not None:
                supplier = self._get_active_supplier(
                    supplier_id=supplier_id,
                    company_id=company_id,
                )
                update_data["supplier_id"] = supplier.id

            order_number = update_data.get(
                "order_number"
            )

            if order_number is not None:
                normalized_number = self._normalize_number(
                    order_number
                )

                self._validate_order_number(
                    company_id=company_id,
                    order_number=normalized_number,
                    exclude_order_id=order.id,
                )

                update_data["order_number"] = normalized_number

            for field, value in update_data.items():
                setattr(order, field, value)

            if details_data is not None:
                self.repository.delete_order_details(
                    order_id=order.id,
                )
                self.repository.flush()

                subtotal = self._create_order_details(
                    order=order,
                    company_id=company_id,
                    details_data=details_data,
                )
                order.subtotal = subtotal

            order.total_amount = self._calculate_total(
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                discount_amount=order.discount_amount,
            )

            self.repository.commit()

            return self._get_order_or_raise(
                order_id=order.id,
                company_id=company_id,
            )

        except PurchaseDomainException:
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()
            raise PurchaseOrderProcessingException() from exception

    def approve_order(
        self,
        order_id: UUID,
        company_id: UUID,
        user_id: UUID,
    ) -> PurchaseOrder:
        try:
            order, details = self.repository.get_order_for_update(
                order_id=order_id,
                company_id=company_id,
            )

            if order is None:
                raise PurchaseOrderNotFoundException()

            if order.status != PurchaseOrderStatus.DRAFT:
                raise PurchaseOrderNotApprovableException()

            if not details:
                raise PurchaseOrderHasNoDetailsException()

            order.status = PurchaseOrderStatus.APPROVED
            order.approved_by_user_id = user_id
            order.approved_at = datetime.now(timezone.utc)

            self.repository.commit()

            return self._get_order_or_raise(
                order_id=order.id,
                company_id=company_id,
            )

        except PurchaseDomainException:
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()
            raise PurchaseOrderProcessingException() from exception

    def cancel_order(
        self,
        order_id: UUID,
        company_id: UUID,
        user_id: UUID,
        data: PurchaseOrderCancel,
    ) -> PurchaseOrder:
        try:
            order, _ = self.repository.get_order_for_update(
                order_id=order_id,
                company_id=company_id,
            )

            if order is None:
                raise PurchaseOrderNotFoundException()

            cancellable_statuses = {
                PurchaseOrderStatus.DRAFT,
                PurchaseOrderStatus.APPROVED,
            }

            if order.status not in cancellable_statuses:
                raise PurchaseOrderNotCancellableException()

            order.status = PurchaseOrderStatus.CANCELLED
            order.cancelled_by_user_id = user_id
            order.cancelled_at = datetime.now(timezone.utc)
            order.cancellation_reason = data.reason

            self.repository.commit()

            return self._get_order_or_raise(
                order_id=order.id,
                company_id=company_id,
            )

        except PurchaseDomainException:
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()
            raise PurchaseOrderProcessingException() from exception

    # ======================================================
    # Purchase receipts
    # ======================================================

    def receive_order(
        self,
        order_id: UUID,
        company_id: UUID,
        user_id: UUID,
        data: PurchaseReceiptCreate,
    ) -> PurchaseReceipt:
        try:
            order, order_details = (
                self.repository.get_order_for_update(
                    order_id=order_id,
                    company_id=company_id,
                )
            )

            if order is None:
                raise PurchaseOrderNotFoundException()

            receivable_statuses = {
                PurchaseOrderStatus.APPROVED,
                PurchaseOrderStatus.PARTIALLY_RECEIVED,
            }

            if order.status not in receivable_statuses:
                raise PurchaseOrderNotReceivableException()

            receipt_number = self._normalize_number(
                data.receipt_number
            )

            existing_receipt = (
                self.repository.get_receipt_by_number(
                    receipt_number=receipt_number,
                    company_id=company_id,
                )
            )

            if existing_receipt is not None:
                raise PurchaseReceiptAlreadyExistsException()

            order_details_by_id = {
                detail.id: detail
                for detail in order_details
            }

            for detail_data in data.details:
                if (
                    detail_data.purchase_order_detail_id
                    not in order_details_by_id
                ):
                    raise PurchaseOrderDetailNotFoundException()

            movement = InventoryMovement(
                company_id=company_id,
                user_id=user_id,
                movement_type=InventoryMovementType.ENTRY,
                reference=receipt_number,
                reason=(
                    f"Recepción de la orden de compra "
                    f"{order.order_number}"
                ),
                notes=data.notes,
            )

            self.repository.add_inventory_movement(
                movement
            )
            self.repository.flush()

            receipt = PurchaseReceipt(
                company_id=company_id,
                purchase_order_id=order.id,
                received_by_user_id=user_id,
                inventory_movement_id=movement.id,
                receipt_number=receipt_number,
                supplier_invoice_number=(
                    self._normalize_optional_number(
                        data.supplier_invoice_number
                    )
                ),
                tax_amount=data.tax_amount,
                discount_amount=data.discount_amount,
                notes=data.notes,
            )

            self.repository.add(receipt)
            self.repository.flush()

            subtotal = Decimal("0.00")

            sorted_details = sorted(
                data.details,
                key=lambda item: str(
                    order_details_by_id[
                        item.purchase_order_detail_id
                    ].product_id
                ),
            )

            for detail_data in sorted_details:
                order_detail = order_details_by_id[
                    detail_data.purchase_order_detail_id
                ]

                product = self.repository.get_product_for_update(
                    product_id=order_detail.product_id,
                    company_id=company_id,
                )

                if product is None:
                    raise PurchaseProductNotFoundException()

                if not product.is_active:
                    raise PurchaseProductInactiveException(
                        product_name=product.name,
                    )

                pending_quantity = (
                    order_detail.ordered_quantity
                    - order_detail.received_quantity
                )

                if detail_data.quantity > pending_quantity:
                    raise PurchaseReceiptQuantityExceededException(
                        product_name=product.name,
                        pending_quantity=str(
                            pending_quantity
                        ),
                    )

                unit_cost = (
                    detail_data.unit_cost
                    if detail_data.unit_cost is not None
                    else order_detail.unit_cost
                )

                stock_before = product.current_stock
                stock_after = (
                    stock_before
                    + detail_data.quantity
                )

                product.purchase_price = (
                    self._calculate_weighted_average_cost(
                        stock_before=stock_before,
                        current_cost=product.purchase_price,
                        received_quantity=detail_data.quantity,
                        received_cost=unit_cost,
                    )
                )
                product.current_stock = stock_after

                order_detail.received_quantity = (
                    order_detail.received_quantity
                    + detail_data.quantity
                )

                line_total = self._calculate_line_total(
                    quantity=detail_data.quantity,
                    unit_cost=unit_cost,
                )
                subtotal += line_total

                movement_detail = InventoryMovementDetail(
                    movement_id=movement.id,
                    product_id=product.id,
                    quantity=detail_data.quantity,
                    stock_before=stock_before,
                    stock_after=stock_after,
                    unit_cost=unit_cost,
                )

                self.repository.add_inventory_movement_detail(
                    movement_detail
                )

                receipt_detail = PurchaseReceiptDetail(
                    purchase_receipt_id=receipt.id,
                    purchase_order_detail_id=order_detail.id,
                    product_id=product.id,
                    quantity=detail_data.quantity,
                    unit_cost=unit_cost,
                    line_total=line_total,
                    stock_before=stock_before,
                    stock_after=stock_after,
                )

                self.repository.add_receipt_detail(
                    receipt_detail
                )

            receipt.subtotal = self._money(subtotal)
            receipt.total_amount = self._calculate_total(
                subtotal=receipt.subtotal,
                tax_amount=receipt.tax_amount,
                discount_amount=receipt.discount_amount,
            )

            all_received = all(
                detail.received_quantity
                >= detail.ordered_quantity
                for detail in order_details
            )

            if all_received:
                order.status = PurchaseOrderStatus.RECEIVED
                order.completed_at = datetime.now(timezone.utc)
            else:
                order.status = (
                    PurchaseOrderStatus.PARTIALLY_RECEIVED
                )
                order.completed_at = None

            self.repository.flush()
            self.repository.commit()

            return self._get_receipt_or_raise(
                receipt_id=receipt.id,
                company_id=company_id,
            )

        except PurchaseDomainException:
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()
            raise PurchaseReceiptProcessingException() from exception

    def get_receipt(
        self,
        receipt_id: UUID,
        company_id: UUID,
    ) -> PurchaseReceipt:
        return self._get_receipt_or_raise(
            receipt_id=receipt_id,
            company_id=company_id,
        )

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
    ) -> dict:
        receipts = self.repository.list_receipts(
            company_id=company_id,
            skip=skip,
            limit=limit,
            order_id=order_id,
            supplier_id=supplier_id,
            search=search,
            received_from=received_from,
            received_to=received_to,
        )

        total = self.repository.count_receipts(
            company_id=company_id,
            order_id=order_id,
            supplier_id=supplier_id,
            search=search,
            received_from=received_from,
            received_to=received_to,
        )

        return {
            "total": total,
            "items": receipts,
        }

    # ======================================================
    # Internal helpers
    # ======================================================

    def _get_order_or_raise(
        self,
        order_id: UUID,
        company_id: UUID,
    ) -> PurchaseOrder:
        order = self.repository.get_order_by_id(
            order_id=order_id,
            company_id=company_id,
        )

        if order is None:
            raise PurchaseOrderNotFoundException()

        return order

    def _get_receipt_or_raise(
        self,
        receipt_id: UUID,
        company_id: UUID,
    ) -> PurchaseReceipt:
        receipt = self.repository.get_receipt_by_id(
            receipt_id=receipt_id,
            company_id=company_id,
        )

        if receipt is None:
            raise PurchaseReceiptNotFoundException()

        return receipt

    def _get_active_supplier(
        self,
        supplier_id: UUID,
        company_id: UUID,
    ) -> Supplier:
        supplier = self.repository.get_supplier_by_id(
            supplier_id=supplier_id,
            company_id=company_id,
        )

        if supplier is None:
            raise PurchaseSupplierNotFoundException()

        if not supplier.is_active:
            raise PurchaseSupplierInactiveException()

        return supplier

    def _get_active_product(
        self,
        product_id: UUID,
        company_id: UUID,
    ) -> Product:
        product = self.repository.get_product_by_id(
            product_id=product_id,
            company_id=company_id,
        )

        if product is None:
            raise PurchaseProductNotFoundException()

        if not product.is_active:
            raise PurchaseProductInactiveException(
                product_name=product.name,
            )

        return product

    def _create_order_details(
        self,
        order: PurchaseOrder,
        company_id: UUID,
        details_data: list[PurchaseOrderDetailCreate],
    ) -> Decimal:
        if not details_data:
            raise PurchaseOrderHasNoDetailsException()

        subtotal = Decimal("0.00")

        for detail_data in details_data:
            product = self._get_active_product(
                product_id=detail_data.product_id,
                company_id=company_id,
            )

            line_total = self._calculate_line_total(
                quantity=detail_data.ordered_quantity,
                unit_cost=detail_data.unit_cost,
            )

            detail = PurchaseOrderDetail(
                purchase_order_id=order.id,
                product_id=product.id,
                ordered_quantity=detail_data.ordered_quantity,
                received_quantity=Decimal("0.000"),
                unit_cost=detail_data.unit_cost,
                line_total=line_total,
            )

            self.repository.add(detail)
            subtotal += line_total

        self.repository.flush()

        return self._money(subtotal)

    def _validate_order_number(
        self,
        company_id: UUID,
        order_number: str,
        exclude_order_id: UUID | None = None,
    ) -> None:
        existing_order = self.repository.get_order_by_number(
            order_number=order_number,
            company_id=company_id,
            exclude_order_id=exclude_order_id,
        )

        if existing_order is not None:
            raise PurchaseOrderAlreadyExistsException()

    def _calculate_line_total(
        self,
        quantity: Decimal,
        unit_cost: Decimal,
    ) -> Decimal:
        return self._money(quantity * unit_cost)

    def _calculate_total(
        self,
        subtotal: Decimal,
        tax_amount: Decimal,
        discount_amount: Decimal,
    ) -> Decimal:
        total_before_discount = (
            subtotal + tax_amount
        )

        if discount_amount > total_before_discount:
            raise PurchaseInvalidDiscountException()

        return self._money(
            total_before_discount - discount_amount
        )

    def _calculate_weighted_average_cost(
        self,
        stock_before: Decimal,
        current_cost: Decimal,
        received_quantity: Decimal,
        received_cost: Decimal,
    ) -> Decimal:
        stock_after = stock_before + received_quantity

        if stock_after <= Decimal("0.000"):
            return self._money(received_cost)

        accumulated_cost = (
            stock_before * current_cost
        )
        received_total = (
            received_quantity * received_cost
        )

        return self._money(
            (accumulated_cost + received_total)
            / stock_after
        )

    def _money(
        self,
        value: Decimal,
    ) -> Decimal:
        return value.quantize(
            MONEY_QUANTIZER,
            rounding=ROUND_HALF_UP,
        )

    def _normalize_number(
        self,
        value: str,
    ) -> str:
        return value.strip().upper()

    def _normalize_optional_number(
        self,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip().upper()

        return normalized_value or None