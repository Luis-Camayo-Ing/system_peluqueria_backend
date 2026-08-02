from uuid import UUID

from app.modules.supplier.exceptions import (
    SupplierAlreadyExistsException,
    SupplierNotFoundException,
)
from app.modules.supplier.model import Supplier
from app.modules.supplier.repository import SupplierRepository
from app.modules.supplier.schemas import (
    SupplierCreate,
    SupplierUpdate,
)


class SupplierService:
    def __init__(
        self,
        repository: SupplierRepository,
    ):
        self.repository = repository

    def create_supplier(
        self,
        data: SupplierCreate,
        company_id: UUID,
    ) -> Supplier:
        normalized_tax_id = data.tax_id.strip().upper()

        existing_supplier = self.repository.get_by_tax_id(
            tax_id=normalized_tax_id,
            company_id=company_id,
        )

        if existing_supplier:
            raise SupplierAlreadyExistsException()

        supplier_data = data.model_dump()
        supplier_data["tax_id"] = normalized_tax_id

        if supplier_data.get("email") is not None:
            supplier_data["email"] = str(
                supplier_data["email"]
            )

        supplier = Supplier(
            company_id=company_id,
            **supplier_data,
        )

        return self.repository.create(supplier)

    def get_supplier(
        self,
        supplier_id: UUID,
        company_id: UUID,
    ) -> Supplier:
        supplier = self.repository.get_by_id(
            supplier_id=supplier_id,
            company_id=company_id,
        )

        if not supplier:
            raise SupplierNotFoundException()

        return supplier

    def list_suppliers(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        suppliers = self.repository.list_suppliers(
            company_id=company_id,
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active,
        )

        total = self.repository.count_suppliers(
            company_id=company_id,
            search=search,
            is_active=is_active,
        )

        return {
            "total": total,
            "items": suppliers,
        }

    def update_supplier(
        self,
        supplier_id: UUID,
        company_id: UUID,
        data: SupplierUpdate,
    ) -> Supplier:
        supplier = self.get_supplier(
            supplier_id=supplier_id,
            company_id=company_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        new_tax_id = update_data.get("tax_id")

        if new_tax_id is not None:
            normalized_tax_id = new_tax_id.strip().upper()

            existing_supplier = self.repository.get_by_tax_id(
                tax_id=normalized_tax_id,
                company_id=company_id,
                exclude_supplier_id=supplier.id,
            )

            if existing_supplier:
                raise SupplierAlreadyExistsException()

            update_data["tax_id"] = normalized_tax_id

        if update_data.get("email") is not None:
            update_data["email"] = str(
                update_data["email"]
            )

        for field, value in update_data.items():
            setattr(
                supplier,
                field,
                value,
            )

        return self.repository.update(supplier)

    def deactivate_supplier(
        self,
        supplier_id: UUID,
        company_id: UUID,
    ) -> Supplier:
        supplier = self.get_supplier(
            supplier_id=supplier_id,
            company_id=company_id,
        )

        supplier.is_active = False

        return self.repository.update(supplier)