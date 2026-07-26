from uuid import UUID

from app.modules.customer.exceptions import (
    CustomerAlreadyExistsException,
    CustomerNotFoundException,
)
from app.modules.customer.model import Customer
from app.modules.customer.repository import CustomerRepository
from app.modules.customer.schemas import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository

    def create_customer(
        self,
        data: CustomerCreate,
        company_id: UUID,
    ) -> Customer:
        if data.document_number:
            existing_customer = self.repository.get_by_document(
                document_number=data.document_number,
                company_id=company_id,
            )

            if existing_customer:
                raise CustomerAlreadyExistsException()

        if data.email:
            existing_customer = self.repository.get_by_email(
                email=str(data.email),
                company_id=company_id,
            )

            if existing_customer:
                raise CustomerAlreadyExistsException()

        customer = Customer(
            company_id=company_id,
            **data.model_dump(),
        )

        return self.repository.create(customer)

    def get_customer(
        self,
        customer_id: UUID,
        company_id: UUID,
    ) -> Customer:
        customer = self.repository.get_by_id(
            customer_id=customer_id,
            company_id=company_id,
        )

        if not customer:
            raise CustomerNotFoundException()

        return customer

    def list_customers(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        customers = self.repository.list_customers(
            company_id=company_id,
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active,
        )

        total = self.repository.count_customers(
            company_id=company_id,
            search=search,
            is_active=is_active,
        )

        return {
            "total": total,
            "items": customers,
        }

    def update_customer(
        self,
        customer_id: UUID,
        company_id: UUID,
        data: CustomerUpdate,
    ) -> Customer:
        customer = self.get_customer(
            customer_id=customer_id,
            company_id=company_id,
        )

        update_data = data.model_dump(exclude_unset=True)

        new_document = update_data.get("document_number")

        if new_document:
            existing_customer = self.repository.get_by_document(
                document_number=new_document,
                company_id=company_id,
            )

            if (
                existing_customer
                and existing_customer.id != customer.id
            ):
                raise CustomerAlreadyExistsException()

        new_email = update_data.get("email")

        if new_email:
            existing_customer = self.repository.get_by_email(
                email=str(new_email),
                company_id=company_id,
            )

            if (
                existing_customer
                and existing_customer.id != customer.id
            ):
                raise CustomerAlreadyExistsException()

        for field, value in update_data.items():
            setattr(customer, field, value)

        return self.repository.update(customer)