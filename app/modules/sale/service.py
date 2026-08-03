"""Transactional business logic for sales and POS operations."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.modules.cash_register.model import (
    CashSessionStatus,
    CashTransaction,
    CashTransactionSource,
    CashTransactionType,
)
from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    InventoryMovementType,
    Product,
)
from app.modules.sale.exceptions import (
    SaleAlreadyCancelledException,
    SaleAlreadyExistsException,
    SaleCancellationCashSessionClosedException,
    SaleCancellationProcessingException,
    SaleCashSessionClosedException,
    SaleCashSessionNotFoundException,
    SaleCashSessionNotOpenException,
    SaleCompanyInactiveException,
    SaleCompanyNotFoundException,
    SaleCustomerInactiveException,
    SaleCustomerNotFoundException,
    SaleDiscountExceededException,
    SaleDomainException,
    SaleInsufficientCashForRefundException,
    SaleInsufficientStockException,
    SaleInvalidCashPaymentException,
    SaleInvalidTotalException,
    SaleNotFoundException,
    SalePaymentTotalMismatchException,
    SaleProcessingException,
    SaleProductInactiveException,
    SaleProductNotFoundException,
    SaleServiceInactiveException,
    SaleServiceNotFoundException,
)
from app.modules.sale.model import (
    Sale,
    SaleDetail,
    SaleItemType,
    SalePayment,
    SalePaymentMethod,
    SaleStatus,
)
from app.modules.sale.repository import SaleRepository
from app.modules.sale.schemas import (
    SaleCancelRequest,
    SaleCreate,
    SaleDetailCreate,
    SalePaymentCreate,
)
from app.modules.service.model import Service


MONEY_UNIT = Decimal("0.01")
QUANTITY_UNIT = Decimal("0.001")
PERCENT_DIVISOR = Decimal("100.00")


@dataclass(slots=True)
class PreparedSaleDetail:
    """Validated catalog item ready to be persisted."""

    source: SaleDetailCreate

    product: Product | None
    service: Service | None

    item_code: str | None
    item_name: str
    item_description: str | None
    unit: str

    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal

    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal

    line_subtotal: Decimal
    line_total: Decimal


class SaleService:
    """Coordinates atomic sale and cancellation transactions."""

    def __init__(
        self,
        repository: SaleRepository,
    ) -> None:
        self.repository = repository

    # ======================================================
    # Public sale operations
    # ======================================================

    def create_sale(
        self,
        company_id: UUID,
        user_id: UUID,
        data: SaleCreate,
    ) -> Sale:
        """Complete a sale using one database transaction."""

        sale_id: UUID

        try:
            sale_number = data.sale_number.strip().upper()

            existing_sale = self.repository.get_sale_by_number(
                sale_number=sale_number,
                company_id=company_id,
            )

            if existing_sale is not None:
                raise SaleAlreadyExistsException()

            company = self.repository.get_company_by_id(
                company_id=company_id,
            )

            if company is None:
                raise SaleCompanyNotFoundException()

            if not company.is_active:
                raise SaleCompanyInactiveException()

            customer = None

            if data.customer_id is not None:
                customer = self.repository.get_customer_by_id(
                    customer_id=data.customer_id,
                    company_id=company_id,
                )

                if customer is None:
                    raise SaleCustomerNotFoundException()

                if not customer.is_active:
                    raise SaleCustomerInactiveException()

            cash_session = (
                self.repository.get_cash_session_for_update(
                    cash_session_id=data.cash_session_id,
                    company_id=company_id,
                )
            )

            self._validate_open_cash_session(
                cash_session=cash_session,
            )

            prepared_details = self._prepare_details(
                company_id=company_id,
                details=data.details,
            )

            subtotal = self._money(
                sum(
                    (
                        detail.line_subtotal
                        for detail in prepared_details
                    ),
                    Decimal("0.00"),
                )
            )

            discount_amount = self._money(
                sum(
                    (
                        detail.discount_amount
                        for detail in prepared_details
                    ),
                    Decimal("0.00"),
                )
            )

            tax_amount = self._money(
                sum(
                    (
                        detail.tax_amount
                        for detail in prepared_details
                    ),
                    Decimal("0.00"),
                )
            )

            total_amount = self._money(
                sum(
                    (
                        detail.line_total
                        for detail in prepared_details
                    ),
                    Decimal("0.00"),
                )
            )

            if (
                subtotal <= Decimal("0.00")
                or total_amount <= Decimal("0.00")
            ):
                raise SaleInvalidTotalException()

            (
                paid_amount,
                change_amount,
                cash_amount,
            ) = self._calculate_payment_summary(
                payments=data.payments,
                total_amount=total_amount,
            )

            inventory_movement = (
                self._create_sale_inventory_movement(
                    company_id=company_id,
                    user_id=user_id,
                    sale_number=sale_number,
                    notes=data.notes,
                    prepared_details=prepared_details,
                )
            )

            cash_transaction = (
                self._create_sale_cash_transaction(
                    company_id=company_id,
                    cash_session_id=data.cash_session_id,
                    user_id=user_id,
                    sale_number=sale_number,
                    cash_amount=cash_amount,
                    notes=data.notes,
                )
            )

            customer_name = None

            if customer is not None:
                customer_name = (
                    f"{customer.first_name} "
                    f"{customer.last_name}"
                ).strip()

            sale = Sale(
                company_id=company_id,
                customer_id=(
                    customer.id
                    if customer is not None
                    else None
                ),
                cash_session_id=data.cash_session_id,
                created_by_user_id=user_id,
                inventory_movement_id=(
                    inventory_movement.id
                    if inventory_movement is not None
                    else None
                ),
                cash_transaction_id=(
                    cash_transaction.id
                    if cash_transaction is not None
                    else None
                ),
                sale_number=sale_number,
                status=SaleStatus.COMPLETED,
                company_name=company.name,
                company_tax_id=company.tax_id,
                company_email=company.email,
                company_phone=company.phone,
                customer_name=customer_name,
                customer_document=(
                    customer.document_number
                    if customer is not None
                    else None
                ),
                customer_email=(
                    customer.email
                    if customer is not None
                    else None
                ),
                customer_phone=(
                    customer.phone
                    if customer is not None
                    else None
                ),
                subtotal=subtotal,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                paid_amount=paid_amount,
                change_amount=change_amount,
                notes=data.notes,
            )

            self.repository.add_sale(sale)
            self.repository.flush()

            self._persist_sale_details(
                sale=sale,
                inventory_movement=inventory_movement,
                prepared_details=prepared_details,
            )

            self._persist_sale_payments(
                sale=sale,
                payments=data.payments,
            )

            self.repository.flush()

            sale_id = sale.id

            self.repository.commit()

        except SaleDomainException:
            self.repository.rollback()
            raise

        except IntegrityError as exception:
            self.repository.rollback()

            if (
                "uq_sales_company_number"
                in str(exception.orig)
            ):
                raise SaleAlreadyExistsException() from exception

            raise SaleProcessingException() from exception

        except Exception as exception:
            self.repository.rollback()

            raise SaleProcessingException() from exception

        return self._get_sale_or_raise(
            sale_id=sale_id,
            company_id=company_id,
        )

    def get_sale(
        self,
        sale_id: UUID,
        company_id: UUID,
    ) -> Sale:
        """Return a sale with its details and payments."""

        return self._get_sale_or_raise(
            sale_id=sale_id,
            company_id=company_id,
        )

    def list_sales(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: SaleStatus | None = None,
        customer_id: UUID | None = None,
        cash_session_id: UUID | None = None,
        search: str | None = None,
        sold_from: datetime | None = None,
        sold_to: datetime | None = None,
    ) -> dict:
        """Return a filtered and paginated sale collection."""

        sales = self.repository.list_sales(
            company_id=company_id,
            skip=skip,
            limit=limit,
            status=status,
            customer_id=customer_id,
            cash_session_id=cash_session_id,
            search=search,
            sold_from=sold_from,
            sold_to=sold_to,
        )

        total = self.repository.count_sales(
            company_id=company_id,
            status=status,
            customer_id=customer_id,
            cash_session_id=cash_session_id,
            search=search,
            sold_from=sold_from,
            sold_to=sold_to,
        )

        return {
            "total": total,
            "items": sales,
        }

    def cancel_sale(
        self,
        sale_id: UUID,
        company_id: UUID,
        user_id: UUID,
        data: SaleCancelRequest,
    ) -> Sale:
        """Cancel a sale and reverse stock and physical cash."""

        try:
            sale = self.repository.get_sale_for_update(
                sale_id=sale_id,
                company_id=company_id,
            )

            if sale is None:
                raise SaleNotFoundException()

            if sale.status == SaleStatus.CANCELLED:
                raise SaleAlreadyCancelledException()

            cash_session = (
                self.repository.get_cash_session_for_update(
                    cash_session_id=sale.cash_session_id,
                    company_id=company_id,
                )
            )

            if cash_session is None:
                raise SaleCashSessionNotFoundException()

            if cash_session.status != CashSessionStatus.OPEN:
                raise (
                    SaleCancellationCashSessionClosedException()
                )

            product_details = sorted(
                (
                    detail
                    for detail in sale.details
                    if detail.item_type
                    == SaleItemType.PRODUCT
                ),
                key=lambda detail: str(detail.product_id),
            )

            locked_products: dict[UUID, Product] = {}

            for detail in product_details:
                if detail.product_id is None:
                    raise SaleProductNotFoundException()

                product = (
                    self.repository.get_product_for_update(
                        product_id=detail.product_id,
                        company_id=company_id,
                    )
                )

                if product is None:
                    raise SaleProductNotFoundException()

                locked_products[product.id] = product

            cancellation_movement = None

            if product_details:
                cancellation_movement = InventoryMovement(
                    company_id=company_id,
                    user_id=user_id,
                    movement_type=(
                        InventoryMovementType.RETURN_IN
                    ),
                    reference=sale.sale_number,
                    reason=(
                        "Cancelación y devolución de inventario "
                        f"de la venta {sale.sale_number}"
                    ),
                    notes=data.reason,
                )

                self.repository.add_inventory_movement(
                    cancellation_movement
                )
                self.repository.flush()

                for detail in product_details:
                    product = locked_products[
                        detail.product_id
                    ]

                    stock_before = Decimal(
                        product.current_stock
                    )
                    stock_after = (
                        stock_before
                        + Decimal(detail.quantity)
                    )

                    product.current_stock = stock_after

                    movement_detail = (
                        InventoryMovementDetail(
                            movement_id=(
                                cancellation_movement.id
                            ),
                            product_id=product.id,
                            quantity=detail.quantity,
                            stock_before=stock_before,
                            stock_after=stock_after,
                            unit_cost=detail.unit_cost,
                        )
                    )

                    self.repository.add_inventory_movement_detail(
                        movement_detail
                    )

            refund_amount = self._money(
                sum(
                    (
                        Decimal(payment.amount)
                        for payment in sale.payments
                        if payment.payment_method
                        == SalePaymentMethod.CASH
                    ),
                    Decimal("0.00"),
                )
            )

            cancellation_cash_transaction = None

            if refund_amount > Decimal("0.00"):
                expected_cash = self._money(
                    self.repository.get_expected_cash_amount(
                        cash_session
                    )
                )

                if refund_amount > expected_cash:
                    raise (
                        SaleInsufficientCashForRefundException(
                            available_amount=str(
                                expected_cash
                            ),
                            refund_amount=str(
                                refund_amount
                            ),
                        )
                    )

                cancellation_cash_transaction = (
                    CashTransaction(
                        company_id=company_id,
                        cash_session_id=cash_session.id,
                        user_id=user_id,
                        transaction_type=(
                            CashTransactionType.EXPENSE
                        ),
                        source=CashTransactionSource.REFUND,
                        amount=refund_amount,
                        reference=sale.sale_number,
                        description=(
                            "Reembolso en efectivo por "
                            f"cancelación de la venta "
                            f"{sale.sale_number}"
                        ),
                        notes=data.reason,
                    )
                )

                self.repository.add_cash_transaction(
                    cancellation_cash_transaction
                )
                self.repository.flush()

            sale.status = SaleStatus.CANCELLED
            sale.cancelled_by_user_id = user_id
            sale.cancelled_at = datetime.now(timezone.utc)
            sale.cancellation_reason = data.reason
            sale.cancellation_inventory_movement_id = (
                cancellation_movement.id
                if cancellation_movement is not None
                else None
            )
            sale.cancellation_cash_transaction_id = (
                cancellation_cash_transaction.id
                if cancellation_cash_transaction is not None
                else None
            )

            self.repository.flush()
            self.repository.commit()

        except SaleDomainException:
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()

            raise (
                SaleCancellationProcessingException()
            ) from exception

        return self._get_sale_or_raise(
            sale_id=sale_id,
            company_id=company_id,
        )

    # ======================================================
    # Validation and calculation helpers
    # ======================================================

    def _validate_open_cash_session(
        self,
        cash_session: object,
    ) -> None:
        if cash_session is None:
            raise SaleCashSessionNotFoundException()

        if cash_session.status == CashSessionStatus.CLOSED:
            raise SaleCashSessionClosedException()

        if cash_session.status != CashSessionStatus.OPEN:
            raise SaleCashSessionNotOpenException()

    def _prepare_details(
        self,
        company_id: UUID,
        details: list[SaleDetailCreate],
    ) -> list[PreparedSaleDetail]:
        products: dict[UUID, Product] = {}
        services: dict[UUID, Service] = {}

        product_ids = sorted(
            {
                detail.product_id
                for detail in details
                if (
                    detail.item_type
                    == SaleItemType.PRODUCT
                    and detail.product_id is not None
                )
            },
            key=str,
        )

        for product_id in product_ids:
            product = (
                self.repository.get_product_for_update(
                    product_id=product_id,
                    company_id=company_id,
                )
            )

            if product is None:
                raise SaleProductNotFoundException()

            if not product.is_active:
                raise SaleProductInactiveException(
                    product_name=product.name,
                )

            products[product.id] = product

        service_ids = sorted(
            {
                detail.service_id
                for detail in details
                if (
                    detail.item_type
                    == SaleItemType.SERVICE
                    and detail.service_id is not None
                )
            },
            key=str,
        )

        for service_id in service_ids:
            service = self.repository.get_service_by_id(
                service_id=service_id,
                company_id=company_id,
            )

            if service is None:
                raise SaleServiceNotFoundException()

            if not service.is_active:
                raise SaleServiceInactiveException(
                    service_name=service.name,
                )

            services[service.id] = service

        prepared_details: list[PreparedSaleDetail] = []

        for detail in details:
            prepared_details.append(
                self._prepare_detail(
                    detail=detail,
                    products=products,
                    services=services,
                )
            )

        return prepared_details

    def _prepare_detail(
        self,
        detail: SaleDetailCreate,
        products: dict[UUID, Product],
        services: dict[UUID, Service],
    ) -> PreparedSaleDetail:
        product = None
        service = None

        if detail.item_type == SaleItemType.PRODUCT:
            if detail.product_id is None:
                raise SaleProductNotFoundException()

            product = products.get(detail.product_id)

            if product is None:
                raise SaleProductNotFoundException()

            item_code = product.code
            item_name = product.name
            item_description = product.description
            unit = product.unit

            quantity = self._quantity(detail.quantity)

            if quantity > Decimal(product.current_stock):
                raise SaleInsufficientStockException(
                    product_name=product.name,
                    requested_quantity=str(quantity),
                    available_quantity=str(
                        product.current_stock
                    ),
                )

            catalog_price = Decimal(product.sale_price)
            unit_cost = self._money(
                Decimal(product.purchase_price)
            )

        else:
            if detail.service_id is None:
                raise SaleServiceNotFoundException()

            service = services.get(detail.service_id)

            if service is None:
                raise SaleServiceNotFoundException()

            item_code = None
            item_name = service.name
            item_description = service.description
            unit = "servicio"

            quantity = self._quantity(detail.quantity)
            catalog_price = Decimal(service.price)
            unit_cost = Decimal("0.00")

        unit_price = self._money(
            Decimal(
                detail.unit_price
                if detail.unit_price is not None
                else catalog_price
            )
        )

        line_subtotal = self._money(
            quantity * unit_price
        )

        discount_amount = self._money(
            Decimal(detail.discount_amount)
        )

        if discount_amount > line_subtotal:
            raise SaleDiscountExceededException(
                item_name=item_name,
            )

        taxable_amount = self._money(
            line_subtotal - discount_amount
        )

        tax_rate = self._money(
            Decimal(detail.tax_rate)
        )

        tax_amount = self._money(
            taxable_amount
            * tax_rate
            / PERCENT_DIVISOR
        )

        line_total = self._money(
            taxable_amount + tax_amount
        )

        return PreparedSaleDetail(
            source=detail,
            product=product,
            service=service,
            item_code=item_code,
            item_name=item_name,
            item_description=item_description,
            unit=unit,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=unit_cost,
            discount_amount=discount_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            line_subtotal=line_subtotal,
            line_total=line_total,
        )

    def _calculate_payment_summary(
        self,
        payments: list[SalePaymentCreate],
        total_amount: Decimal,
    ) -> tuple[Decimal, Decimal, Decimal]:
        paid_amount = self._money(
            sum(
                (
                    Decimal(payment.amount)
                    for payment in payments
                ),
                Decimal("0.00"),
            )
        )

        if paid_amount != total_amount:
            raise SalePaymentTotalMismatchException(
                sale_total=str(total_amount),
                payment_total=str(paid_amount),
            )

        change_amount = Decimal("0.00")
        cash_amount = Decimal("0.00")

        for payment in payments:
            if (
                payment.payment_method
                != SalePaymentMethod.CASH
            ):
                continue

            if payment.tendered_amount is None:
                raise SaleInvalidCashPaymentException()

            cash_amount = self._money(
                Decimal(payment.amount)
            )

            change_amount = self._money(
                Decimal(payment.tendered_amount)
                - cash_amount
            )

            if change_amount < Decimal("0.00"):
                raise SaleInvalidCashPaymentException()

        return (
            paid_amount,
            change_amount,
            cash_amount,
        )

    # ======================================================
    # Persistence helpers
    # ======================================================

    def _create_sale_inventory_movement(
        self,
        company_id: UUID,
        user_id: UUID,
        sale_number: str,
        notes: str | None,
        prepared_details: list[PreparedSaleDetail],
    ) -> InventoryMovement | None:
        has_products = any(
            detail.product is not None
            for detail in prepared_details
        )

        if not has_products:
            return None

        movement = InventoryMovement(
            company_id=company_id,
            user_id=user_id,
            movement_type=InventoryMovementType.EXIT,
            reference=sale_number,
            reason=f"Salida por venta {sale_number}",
            notes=notes,
        )

        self.repository.add_inventory_movement(
            movement
        )
        self.repository.flush()

        return movement

    def _create_sale_cash_transaction(
        self,
        company_id: UUID,
        cash_session_id: UUID,
        user_id: UUID,
        sale_number: str,
        cash_amount: Decimal,
        notes: str | None,
    ) -> CashTransaction | None:
        if cash_amount <= Decimal("0.00"):
            return None

        transaction = CashTransaction(
            company_id=company_id,
            cash_session_id=cash_session_id,
            user_id=user_id,
            transaction_type=CashTransactionType.INCOME,
            source=CashTransactionSource.SALE,
            amount=cash_amount,
            reference=sale_number,
            description=(
                f"Ingreso en efectivo por venta {sale_number}"
            ),
            notes=notes,
        )

        self.repository.add_cash_transaction(
            transaction
        )
        self.repository.flush()

        return transaction

    def _persist_sale_details(
        self,
        sale: Sale,
        inventory_movement: InventoryMovement | None,
        prepared_details: list[PreparedSaleDetail],
    ) -> None:
        for prepared in prepared_details:
            if prepared.product is not None:
                product = prepared.product

                stock_before = Decimal(
                    product.current_stock
                )
                stock_after = (
                    stock_before
                    - prepared.quantity
                )

                product.current_stock = stock_after

                if inventory_movement is None:
                    raise SaleProcessingException()

                movement_detail = InventoryMovementDetail(
                    movement_id=inventory_movement.id,
                    product_id=product.id,
                    quantity=prepared.quantity,
                    stock_before=stock_before,
                    stock_after=stock_after,
                    unit_cost=prepared.unit_cost,
                )

                self.repository.add_inventory_movement_detail(
                    movement_detail
                )

            sale_detail = SaleDetail(
                sale_id=sale.id,
                item_type=prepared.source.item_type,
                product_id=(
                    prepared.product.id
                    if prepared.product is not None
                    else None
                ),
                service_id=(
                    prepared.service.id
                    if prepared.service is not None
                    else None
                ),
                item_code=prepared.item_code,
                item_name=prepared.item_name,
                item_description=prepared.item_description,
                unit=prepared.unit,
                quantity=prepared.quantity,
                unit_price=prepared.unit_price,
                unit_cost=prepared.unit_cost,
                discount_amount=prepared.discount_amount,
                tax_rate=prepared.tax_rate,
                tax_amount=prepared.tax_amount,
                line_subtotal=prepared.line_subtotal,
                line_total=prepared.line_total,
            )

            self.repository.add_sale_detail(
                sale_detail
            )

    def _persist_sale_payments(
        self,
        sale: Sale,
        payments: list[SalePaymentCreate],
    ) -> None:
        for payment_data in payments:
            payment = SalePayment(
                sale_id=sale.id,
                payment_method=(
                    payment_data.payment_method
                ),
                amount=self._money(
                    Decimal(payment_data.amount)
                ),
                tendered_amount=(
                    self._money(
                        Decimal(
                            payment_data.tendered_amount
                        )
                    )
                    if (
                        payment_data.tendered_amount
                        is not None
                    )
                    else None
                ),
                reference=payment_data.reference,
                notes=payment_data.notes,
            )

            self.repository.add_sale_payment(
                payment
            )

    # ======================================================
    # General helpers
    # ======================================================

    def _get_sale_or_raise(
        self,
        sale_id: UUID,
        company_id: UUID,
    ) -> Sale:
        sale = self.repository.get_sale_by_id(
            sale_id=sale_id,
            company_id=company_id,
        )

        if sale is None:
            raise SaleNotFoundException()

        return sale

    @staticmethod
    def _money(
        value: Decimal,
    ) -> Decimal:
        return Decimal(value).quantize(
            MONEY_UNIT,
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _quantity(
        value: Decimal,
    ) -> Decimal:
        return Decimal(value).quantize(
            QUANTITY_UNIT,
            rounding=ROUND_HALF_UP,
        )
