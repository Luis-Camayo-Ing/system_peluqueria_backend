import uuid
from decimal import Decimal

from app.modules.inventory.exceptions import (
    BarcodeAlreadyExistsException,
    InsufficientStockException,
    InvalidInventoryMovementTypeException,
    InvalidPriceException,
    InvalidStockException,
    InventoryMovementNotFoundException,
    InventoryMovementProcessingException,
    InventoryMovementProductInactiveException,
    ProductAlreadyExistsException,
    ProductCategoryAlreadyExistsException,
    ProductCategoryHasProductsException,
    ProductCategoryInactiveException,
    ProductCategoryNotFoundException,
    ProductNotFoundException,
)
from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    InventoryMovementType,
    Product,
    ProductCategory,
)
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    InventoryMovementCreate,
    InventoryMovementDetailCreate,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductUpdate,
)


class InventoryMovementService:
    def __init__(
        self,
        repository: InventoryRepository,
    ):
        self.repository = repository

    def create_movement(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        data: InventoryMovementCreate,
    ) -> InventoryMovement:
        try:
            movement = self._create_header(
                company_id=company_id,
                user_id=user_id,
                data=data,
            )

            for detail in data.details:
                self._process_detail(
                    movement=movement,
                    company_id=company_id,
                    movement_type=data.movement_type,
                    detail_data=detail,
                )

            self.repository.commit()

            return self.repository.refresh_movement(
                movement
            )

        except (
            ProductNotFoundException,
            InsufficientStockException,
            InventoryMovementProductInactiveException,
            InvalidInventoryMovementTypeException,
        ):
            self.repository.rollback()
            raise

        except Exception as exception:
            self.repository.rollback()
            raise InventoryMovementProcessingException() from exception

    def get_movement(
        self,
        movement_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> InventoryMovement:
        movement = self.repository.get_movement_by_id(
            movement_id=movement_id,
            company_id=company_id,
        )

        if movement is None:
            raise InventoryMovementNotFoundException()

        return movement

    def list_movements(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        movement_type: InventoryMovementType | None = None,
        product_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        reference: str | None = None,
    ) -> dict:
        movements = self.repository.list_movements(
            company_id=company_id,
            skip=skip,
            limit=limit,
            movement_type=movement_type,
            product_id=product_id,
            user_id=user_id,
            reference=reference,
        )

        total = self.repository.count_movements(
            company_id=company_id,
            movement_type=movement_type,
            product_id=product_id,
            user_id=user_id,
            reference=reference,
        )

        return {
            "total": total,
            "items": movements,
        }

    def _create_header(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        data: InventoryMovementCreate,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            company_id=company_id,
            user_id=user_id,
            movement_type=data.movement_type,
            reference=data.reference,
            reason=data.reason,
            notes=data.notes,
        )

        self.repository.db.add(movement)
        self.repository.flush()

        return movement

    def _process_detail(
        self,
        movement: InventoryMovement,
        company_id: uuid.UUID,
        movement_type: InventoryMovementType,
        detail_data: InventoryMovementDetailCreate,
    ) -> None:
        product = self.repository.get_product_for_update(
            product_id=detail_data.product_id,
            company_id=company_id,
        )

        if product is None:
            raise ProductNotFoundException()

        if not product.is_active:
            raise InventoryMovementProductInactiveException()

        stock_before = product.current_stock

        stock_after = self._calculate_stock_after(
            movement_type=movement_type,
            stock_before=stock_before,
            quantity=detail_data.quantity,
            product_name=product.name,
        )

        product.current_stock = stock_after

        movement_detail = InventoryMovementDetail(
            movement_id=movement.id,
            product_id=product.id,
            quantity=detail_data.quantity,
            stock_before=stock_before,
            stock_after=stock_after,
            unit_cost=detail_data.unit_cost,
        )

        self.repository.add_movement_detail(
            movement_detail
        )

    def _calculate_stock_after(
        self,
        movement_type: InventoryMovementType,
        stock_before: Decimal,
        quantity: Decimal,
        product_name: str,
    ) -> Decimal:
        increase_types = {
            InventoryMovementType.ENTRY,
            InventoryMovementType.ADJUSTMENT_IN,
            InventoryMovementType.RETURN_IN,
        }

        decrease_types = {
            InventoryMovementType.EXIT,
            InventoryMovementType.ADJUSTMENT_OUT,
            InventoryMovementType.CONSUMPTION,
            InventoryMovementType.RETURN_OUT,
        }

        if movement_type in increase_types:
            return stock_before + quantity

        if movement_type in decrease_types:
            stock_after = stock_before - quantity

            if stock_after < Decimal("0.000"):
                raise InsufficientStockException(
                    product_name=product_name,
                )

            return stock_after

        raise InvalidInventoryMovementTypeException()


class InventoryService:
    def __init__(
        self,
        repository: InventoryRepository,
    ):
        self.repository = repository

    def create_category(
        self,
        company_id: uuid.UUID,
        data: ProductCategoryCreate,
    ) -> ProductCategory:
        normalized_name = data.name.strip()

        existing_category = self.repository.get_category_by_name(
            company_id=company_id,
            name=normalized_name,
        )

        if existing_category is not None:
            raise ProductCategoryAlreadyExistsException()

        category = ProductCategory(
            company_id=company_id,
            name=normalized_name,
            description=data.description,
            is_active=data.is_active,
        )

        return self.repository.create_category(category)

    def get_category(
        self,
        category_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> ProductCategory:
        category = self.repository.get_category_by_id(
            category_id=category_id,
            company_id=company_id,
        )

        if category is None:
            raise ProductCategoryNotFoundException()

        return category

    def list_categories(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        categories = self.repository.list_categories(
            company_id=company_id,
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active,
        )

        total = self.repository.count_categories(
            company_id=company_id,
            search=search,
            is_active=is_active,
        )

        return {
            "total": total,
            "items": categories,
        }

    def update_category(
        self,
        category_id: uuid.UUID,
        company_id: uuid.UUID,
        data: ProductCategoryUpdate,
    ) -> ProductCategory:
        category = self.get_category(
            category_id=category_id,
            company_id=company_id,
        )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return category

        new_name = update_data.get("name")

        if new_name is not None:
            existing_category = self.repository.get_category_by_name(
                company_id=company_id,
                name=new_name,
                exclude_category_id=category.id,
            )

            if existing_category is not None:
                raise ProductCategoryAlreadyExistsException()

        for field, value in update_data.items():
            setattr(category, field, value)

        return self.repository.update_category(category)

    def delete_category(
        self,
        category_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> ProductCategory:
        category = self.get_category(
            category_id=category_id,
            company_id=company_id,
        )

        if self.repository.category_has_products(
            category_id=category.id,
            company_id=company_id,
        ):
            raise ProductCategoryHasProductsException()

        category.is_active = False

        return self.repository.update_category(category)

    def create_product(
        self,
        company_id: uuid.UUID,
        data: ProductCreate,
    ) -> Product:
        category = self._validate_category_for_product(
            category_id=data.category_id,
            company_id=company_id,
        )

        self._validate_product_code(
            company_id=company_id,
            code=data.code,
        )

        self._validate_product_barcode(
            company_id=company_id,
            barcode=data.barcode,
        )

        self._validate_prices(
            purchase_price=data.purchase_price,
            sale_price=data.sale_price,
        )

        self._validate_stock_values(
            current_stock=data.current_stock,
            minimum_stock=data.minimum_stock,
            maximum_stock=data.maximum_stock,
        )

        product = Product(
            company_id=company_id,
            category_id=category.id,
            code=data.code.strip(),
            barcode=(
                data.barcode.strip()
                if data.barcode is not None
                else None
            ),
            name=data.name.strip(),
            description=data.description,
            purchase_price=data.purchase_price,
            sale_price=data.sale_price,
            current_stock=data.current_stock,
            minimum_stock=data.minimum_stock,
            maximum_stock=data.maximum_stock,
            unit=data.unit.strip(),
            is_active=data.is_active,
        )

        return self.repository.create_product(product)

    def get_product(
        self,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Product:
        product = self.repository.get_product_by_id(
            product_id=product_id,
            company_id=company_id,
        )

        if product is None:
            raise ProductNotFoundException()

        return product

    def list_products(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        low_stock: bool | None = None,
    ) -> dict:
        if category_id is not None:
            self.get_category(
                category_id=category_id,
                company_id=company_id,
            )

        products = self.repository.list_products(
            company_id=company_id,
            skip=skip,
            limit=limit,
            search=search,
            category_id=category_id,
            is_active=is_active,
            low_stock=low_stock,
        )

        total = self.repository.count_products(
            company_id=company_id,
            search=search,
            category_id=category_id,
            is_active=is_active,
            low_stock=low_stock,
        )

        return {
            "total": total,
            "items": products,
        }

    def update_product(
        self,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
        data: ProductUpdate,
    ) -> Product:
        product = self.get_product(
            product_id=product_id,
            company_id=company_id,
        )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return product

        category_id = update_data.get(
            "category_id",
            product.category_id,
        )

        self._validate_category_for_product(
            category_id=category_id,
            company_id=company_id,
        )

        code = update_data.get(
            "code",
            product.code,
        )

        barcode = update_data.get(
            "barcode",
            product.barcode,
        )

        purchase_price = update_data.get(
            "purchase_price",
            product.purchase_price,
        )

        sale_price = update_data.get(
            "sale_price",
            product.sale_price,
        )

        current_stock = update_data.get(
            "current_stock",
            product.current_stock,
        )

        minimum_stock = update_data.get(
            "minimum_stock",
            product.minimum_stock,
        )

        maximum_stock = update_data.get(
            "maximum_stock",
            product.maximum_stock,
        )

        self._validate_product_code(
            company_id=company_id,
            code=code,
            exclude_product_id=product.id,
        )

        self._validate_product_barcode(
            company_id=company_id,
            barcode=barcode,
            exclude_product_id=product.id,
        )

        self._validate_prices(
            purchase_price=purchase_price,
            sale_price=sale_price,
        )

        self._validate_stock_values(
            current_stock=current_stock,
            minimum_stock=minimum_stock,
            maximum_stock=maximum_stock,
        )

        for field, value in update_data.items():
            setattr(product, field, value)

        return self.repository.update_product(product)

    def delete_product(
        self,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Product:
        product = self.get_product(
            product_id=product_id,
            company_id=company_id,
        )

        product.is_active = False

        return self.repository.update_product(product)

    def _validate_category_for_product(
        self,
        category_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> ProductCategory:
        category = self.repository.get_category_by_id(
            category_id=category_id,
            company_id=company_id,
        )

        if category is None:
            raise ProductCategoryNotFoundException()

        if not category.is_active:
            raise ProductCategoryInactiveException()

        return category

    def _validate_product_code(
        self,
        company_id: uuid.UUID,
        code: str,
        exclude_product_id: uuid.UUID | None = None,
    ) -> None:
        existing_product = self.repository.get_product_by_code(
            company_id=company_id,
            code=code,
            exclude_product_id=exclude_product_id,
        )

        if existing_product is not None:
            raise ProductAlreadyExistsException()

    def _validate_product_barcode(
        self,
        company_id: uuid.UUID,
        barcode: str | None,
        exclude_product_id: uuid.UUID | None = None,
    ) -> None:
        if barcode is None:
            return

        normalized_barcode = barcode.strip()

        if not normalized_barcode:
            return

        existing_product = self.repository.get_product_by_barcode(
            company_id=company_id,
            barcode=normalized_barcode,
            exclude_product_id=exclude_product_id,
        )

        if existing_product is not None:
            raise BarcodeAlreadyExistsException()

    def _validate_prices(
        self,
        purchase_price: Decimal,
        sale_price: Decimal,
    ) -> None:
        if (
            purchase_price < Decimal("0.00")
            or sale_price < Decimal("0.00")
        ):
            raise InvalidPriceException()

    def _validate_stock_values(
        self,
        current_stock: Decimal,
        minimum_stock: Decimal,
        maximum_stock: Decimal | None,
    ) -> None:
        if (
            current_stock < Decimal("0.000")
            or minimum_stock < Decimal("0.000")
        ):
            raise InvalidStockException()

        if (
            maximum_stock is not None
            and maximum_stock < minimum_stock
        ):
            raise InvalidStockException()