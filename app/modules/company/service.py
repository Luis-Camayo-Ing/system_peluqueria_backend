import uuid

from app.modules.company.exceptions import (
    CompanyAlreadyExistsError,
    CompanyNotFoundError,
)
from app.modules.company.model import Company
from app.modules.company.repository import CompanyRepository
from app.modules.company.schemas import (
    CompanyCreate,
    CompanyListResponse,
    CompanyUpdate,
)


class CompanyService:
    def __init__(self, repository: CompanyRepository):
        self.repository = repository

    def create_company(self, company_data: CompanyCreate) -> Company:
        existing_company = self.repository.get_by_tax_id(
            company_data.tax_id
        )

        if existing_company is not None:
            raise CompanyAlreadyExistsError(
                f"Ya existe una empresa con el identificador fiscal "
                f"'{company_data.tax_id}'."
            )

        return self.repository.create(company_data)

    def get_company(self, company_id: uuid.UUID) -> Company:
        company = self.repository.get_by_id(company_id)

        if company is None:
            raise CompanyNotFoundError(
                f"No existe una empresa con el id '{company_id}'."
            )

        return company

    def get_companies(self) -> CompanyListResponse:
        companies, total = self.repository.get_all()

        return CompanyListResponse(
            items=companies,
            total=total,
        )

    def update_company(
        self,
        company_id: uuid.UUID,
        company_data: CompanyUpdate,
    ) -> Company:
        company = self.get_company(company_id)

        if (
            company_data.tax_id is not None
            and company_data.tax_id != company.tax_id
        ):
            existing_company = self.repository.get_by_tax_id(
                company_data.tax_id
            )

            if existing_company is not None:
                raise CompanyAlreadyExistsError(
                    f"Ya existe una empresa con el identificador fiscal "
                    f"'{company_data.tax_id}'."
                )

        return self.repository.update(company, company_data)

    def delete_company(self, company_id: uuid.UUID) -> None:
        company = self.get_company(company_id)

        self.repository.delete(company)