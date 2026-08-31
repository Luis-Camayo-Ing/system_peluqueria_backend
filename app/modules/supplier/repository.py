from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.supplier.model import Supplier


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        supplier: Supplier,
    ) -> Supplier:
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def get_by_id(
        self,
        supplier_id: UUID,
        company_id: UUID,
    ) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_by_tax_id(
        self,
        tax_id: str,
        company_id: UUID,
        exclude_supplier_id: UUID | None = None,
    ) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.company_id == company_id,
            func.upper(Supplier.tax_id) == tax_id.strip().upper(),
        )

        if exclude_supplier_id is not None:
            statement = statement.where(
                Supplier.id != exclude_supplier_id
            )

        return self.db.scalar(statement)

    def list_suppliers(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Supplier]:
        statement = select(Supplier).where(
            Supplier.company_id == company_id
        )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Supplier.tax_id.ilike(search_value),
                    Supplier.business_name.ilike(search_value),
                    Supplier.trade_name.ilike(search_value),
                    Supplier.contact_name.ilike(search_value),
                    Supplier.phone.ilike(search_value),
                    Supplier.email.ilike(search_value),
                    Supplier.city.ilike(search_value),
                )
            )

        if is_active is not None:
            statement = statement.where(
                Supplier.is_active == is_active
            )

        statement = (
            statement
            .order_by(Supplier.business_name.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_suppliers(
        self,
        company_id: UUID,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Supplier)
            .where(Supplier.company_id == company_id)
        )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Supplier.tax_id.ilike(search_value),
                    Supplier.business_name.ilike(search_value),
                    Supplier.trade_name.ilike(search_value),
                    Supplier.contact_name.ilike(search_value),
                    Supplier.phone.ilike(search_value),
                    Supplier.email.ilike(search_value),
                    Supplier.city.ilike(search_value),
                )
            )

        if is_active is not None:
            statement = statement.where(
                Supplier.is_active == is_active
            )

        return self.db.scalar(statement) or 0

    def update(
        self,
        supplier: Supplier,
    ) -> Supplier:
        self.db.commit()
        self.db.refresh(supplier)

        return supplier