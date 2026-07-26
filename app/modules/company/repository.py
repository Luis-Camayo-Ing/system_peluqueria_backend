import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.company.schemas import CompanyCreate, CompanyUpdate


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, company_data: CompanyCreate) -> Company:
        company = Company(**company_data.model_dump())

        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)

        return company

    def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        statement = select(Company).where(Company.id == company_id)

        return self.db.scalar(statement)

    def get_by_tax_id(self, tax_id: str) -> Company | None:
        statement = select(Company).where(Company.tax_id == tax_id)

        return self.db.scalar(statement)

    def get_all(self) -> tuple[list[Company], int]:
        companies_statement = select(Company).order_by(
            Company.created_at.desc()
        )

        total_statement = select(func.count()).select_from(Company)

        companies = list(
            self.db.scalars(companies_statement).all()
        )

        total = self.db.scalar(total_statement) or 0

        return companies, total

    def update(
        self,
        company: Company,
        company_data: CompanyUpdate,
    ) -> Company:
        update_data = company_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(company, field, value)

        self.db.commit()
        self.db.refresh(company)

        return company

    def delete(self, company: Company) -> None:
        self.db.delete(company)
        self.db.commit()