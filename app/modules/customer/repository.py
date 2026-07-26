from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.customer.model import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def get_by_id(
        self,
        customer_id: UUID,
        company_id: UUID,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.id == customer_id,
            Customer.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_by_document(
        self,
        document_number: str,
        company_id: UUID,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.document_number == document_number,
            Customer.company_id == company_id,
        )

        return self.db.scalar(statement)

    def get_by_email(
        self,
        email: str,
        company_id: UUID,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.email == email,
            Customer.company_id == company_id,
        )

        return self.db.scalar(statement)

    def list_customers(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Customer]:
        statement = select(Customer).where(
            Customer.company_id == company_id
        )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Customer.first_name.ilike(search_value),
                    Customer.last_name.ilike(search_value),
                    Customer.document_number.ilike(search_value),
                    Customer.phone.ilike(search_value),
                    Customer.email.ilike(search_value),
                )
            )

        if is_active is not None:
            statement = statement.where(
                Customer.is_active == is_active
            )

        statement = (
            statement
            .order_by(Customer.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_customers(
        self,
        company_id: UUID,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Customer)
            .where(Customer.company_id == company_id)
        )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    Customer.first_name.ilike(search_value),
                    Customer.last_name.ilike(search_value),
                    Customer.document_number.ilike(search_value),
                    Customer.phone.ilike(search_value),
                    Customer.email.ilike(search_value),
                )
            )

        if is_active is not None:
            statement = statement.where(
                Customer.is_active == is_active
            )

        return self.db.scalar(statement) or 0

    def update(self, customer: Customer) -> Customer:
        self.db.commit()
        self.db.refresh(customer)

        return customer