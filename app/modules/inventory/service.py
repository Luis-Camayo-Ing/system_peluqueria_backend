import uuid
from decimal import Decimal

from app.modules.inventory.exceptions import (
    BarcodeAlreadyExistsException,
    InvalidPriceException,
    InvalidStockException,
    ProductAlreadyExistsException,
    ProductCategoryAlreadyExistsException,
    ProductCategoryHasProductsException,
    ProductCategoryInactiveException,
    ProductCategoryNotFoundException,
    ProductNotFoundException,
)
from app.modules.inventory.model import (
    Product,
    ProductCategory,
)
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductUpdate,
)


class InventoryService:
    def __init__(
        self,
        repository: InventoryRepository,
    ):
        self.repository = repository

    # ======================================================
    # Product Categories
    # ======================================================

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

    # ======================================================
    # Products
    # ======================================================

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

    # ======================================================
    # Private validations
    # ======================================================

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