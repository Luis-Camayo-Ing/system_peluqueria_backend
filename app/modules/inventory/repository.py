import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.inventory.model import (
    InventoryMovement,
    InventoryMovementDetail,
    InventoryMovementType,
    Product,
    ProductCategory,
)


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # Product Categories
    # ======================================================

    def create_category(
        self,
        category: ProductCategory,
    ) -> ProductCategory:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category

    def get_category_by_id(
        self,
        category_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> ProductCategory | None:
        statement = select(ProductCategory).where(
            ProductCategory.id == category_id,
            ProductCategory.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_category_by_name(
        self,
        company_id: uuid.UUID,
        name: str,
        exclude_category_id: uuid.UUID | None = None,
    ) -> ProductCategory | None:
        statement = select(ProductCategory).where(
            ProductCategory.company_id == company_id,
            func.lower(ProductCategory.name) == name.strip().lower(),
        )

        if exclude_category_id is not None:
            statement = statement.where(
                ProductCategory.id != exclude_category_id
            )

        return self.db.scalar(statement)

    def list_categories(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[ProductCategory]:
        statement = select(ProductCategory).where(
            ProductCategory.company_id == company_id
        )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    ProductCategory.name.ilike(search_pattern),
                    ProductCategory.description.ilike(search_pattern),
                )
            )

        if is_active is not None:
            statement = statement.where(
                ProductCategory.is_active == is_active
            )

        statement = (
            statement
            .order_by(ProductCategory.name.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_categories(
        self,
        company_id: uuid.UUID,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(ProductCategory)
            .where(ProductCategory.company_id == company_id)
        )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    ProductCategory.name.ilike(search_pattern),
                    ProductCategory.description.ilike(search_pattern),
                )
            )

        if is_active is not None:
            statement = statement.where(
                ProductCategory.is_active == is_active
            )

        return self.db.scalar(statement) or 0

    def update_category(
        self,
        category: ProductCategory,
    ) -> ProductCategory:
        self.db.commit()
        self.db.refresh(category)

        return category

    def delete_category(
        self,
        category: ProductCategory,
    ) -> None:
        self.db.delete(category)
        self.db.commit()

    def category_has_products(
        self,
        category_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> bool:
        statement = (
            select(func.count())
            .select_from(Product)
            .where(
                Product.category_id == category_id,
                Product.company_id == company_id,
            )
        )

        return (self.db.scalar(statement) or 0) > 0

    # ======================================================
    # Products
    # ======================================================

    def create_product(
        self,
        product: Product,
    ) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        return product

    def get_product_by_id(
        self,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Product | None:
        statement = select(Product).where(
            Product.id == product_id,
            Product.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_product_by_code(
        self,
        company_id: uuid.UUID,
        code: str,
        exclude_product_id: uuid.UUID | None = None,
    ) -> Product | None:
        statement = select(Product).where(
            Product.company_id == company_id,
            func.lower(Product.code) == code.strip().lower(),
        )

        if exclude_product_id is not None:
            statement = statement.where(
                Product.id != exclude_product_id
            )

        return self.db.scalar(statement)

    def get_product_by_barcode(
        self,
        company_id: uuid.UUID,
        barcode: str,
        exclude_product_id: uuid.UUID | None = None,
    ) -> Product | None:
        statement = select(Product).where(
            Product.company_id == company_id,
            Product.barcode == barcode.strip(),
        )

        if exclude_product_id is not None:
            statement = statement.where(
                Product.id != exclude_product_id
            )

        return self.db.scalar(statement)

    def list_products(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        low_stock: bool | None = None,
    ) -> list[Product]:
        statement = select(Product).where(
            Product.company_id == company_id
        )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.code.ilike(search_pattern),
                    Product.barcode.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                )
            )

        if category_id is not None:
            statement = statement.where(
                Product.category_id == category_id
            )

        if is_active is not None:
            statement = statement.where(
                Product.is_active == is_active
            )

        if low_stock is True:
            statement = statement.where(
                Product.current_stock <= Product.minimum_stock
            )

        statement = (
            statement
            .order_by(Product.name.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_products(
        self,
        company_id: uuid.UUID,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        low_stock: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Product)
            .where(Product.company_id == company_id)
        )

        if search:
            search_pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.code.ilike(search_pattern),
                    Product.barcode.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                )
            )

        if category_id is not None:
            statement = statement.where(
                Product.category_id == category_id
            )

        if is_active is not None:
            statement = statement.where(
                Product.is_active == is_active
            )

        if low_stock is True:
            statement = statement.where(
                Product.current_stock <= Product.minimum_stock
            )

        return self.db.scalar(statement) or 0

    def update_product(
        self,
        product: Product,
    ) -> Product:
        self.db.commit()
        self.db.refresh(product)

        return product

    def delete_product(
        self,
        product: Product,
    ) -> None:
        self.db.delete(product)
        self.db.commit()

    # ======================================================
    # Inventory Movements
    # ======================================================

    def create_movement(
        self,
        movement: InventoryMovement,
    ) -> InventoryMovement:
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)

        return movement

    def get_movement_by_id(
        self,
        movement_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> InventoryMovement | None:
        statement = select(InventoryMovement).where(
            InventoryMovement.id == movement_id,
            InventoryMovement.company_id == company_id,
        )

        return self.db.scalar(statement)

    def list_movements(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        movement_type: InventoryMovementType | None = None,
        product_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        reference: str | None = None,
    ) -> list[InventoryMovement]:
        statement = select(InventoryMovement).where(
            InventoryMovement.company_id == company_id
        )

        if movement_type is not None:
            statement = statement.where(
                InventoryMovement.movement_type == movement_type
            )

        if user_id is not None:
            statement = statement.where(
                InventoryMovement.user_id == user_id
            )

        if reference:
            statement = statement.where(
                InventoryMovement.reference.ilike(
                    f"%{reference.strip()}%"
                )
            )

        if product_id is not None:
            statement = (
                statement
                .join(InventoryMovement.details)
                .where(
                    InventoryMovementDetail.product_id == product_id
                )
                .distinct()
            )

        statement = (
            statement
            .order_by(InventoryMovement.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).unique().all())

    def count_movements(
        self,
        company_id: uuid.UUID,
        movement_type: InventoryMovementType | None = None,
        product_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        reference: str | None = None,
    ) -> int:
        statement = (
            select(func.count(func.distinct(InventoryMovement.id)))
            .select_from(InventoryMovement)
            .where(InventoryMovement.company_id == company_id)
        )

        if movement_type is not None:
            statement = statement.where(
                InventoryMovement.movement_type == movement_type
            )

        if user_id is not None:
            statement = statement.where(
                InventoryMovement.user_id == user_id
            )

        if reference:
            statement = statement.where(
                InventoryMovement.reference.ilike(
                    f"%{reference.strip()}%"
                )
            )

        if product_id is not None:
            statement = (
                statement
                .join(InventoryMovement.details)
                .where(
                    InventoryMovementDetail.product_id == product_id
                )
            )

        return self.db.scalar(statement) or 0

    def get_product_for_update(
        self,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
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

    def add_movement_detail(
        self,
        detail: InventoryMovementDetail,
    ) -> None:
        self.db.add(detail)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh_movement(
        self,
        movement: InventoryMovement,
    ) -> InventoryMovement:
        self.db.refresh(movement)

        return movement