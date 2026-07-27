import uuid

from app.modules.company.repository import CompanyRepository
from app.modules.service.exceptions import (
    CompanyNotFoundForServiceError,
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
)
from app.modules.service.model import Service
from app.modules.service.repository import ServiceRepository
from app.modules.service.schemas import (
    ServiceCreate,
    ServiceUpdate,
)


class ServiceService:
    def __init__(
        self,
        repository: ServiceRepository,
        company_repository: CompanyRepository,
    ):
        self.repository = repository
        self.company_repository = company_repository

    def create(
        self,
        data: ServiceCreate,
    ) -> Service:
        company = self.company_repository.get_by_id(
            data.company_id
        )

        if company is None:
            raise CompanyNotFoundForServiceError()

        existing_service = self.repository.get_by_name(
            company_id=data.company_id,
            name=data.name,
        )

        if existing_service is not None:
            raise ServiceAlreadyExistsError()

        service = Service(
            **data.model_dump()
        )

        return self.repository.create(service)

    def get_by_id(
        self,
        service_id: uuid.UUID,
    ) -> Service:
        service = self.repository.get_by_id(service_id)

        if service is None:
            raise ServiceNotFoundError()

        return service

    def get_all(
        self,
        company_id: uuid.UUID,
    ) -> list[Service]:
        company = self.company_repository.get_by_id(
            company_id
        )

        if company is None:
            raise CompanyNotFoundForServiceError()

        return self.repository.get_all(company_id)

    def update(
        self,
        service_id: uuid.UUID,
        data: ServiceUpdate,
    ) -> Service:
        service = self.get_by_id(service_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "name" in update_data:
            existing_service = self.repository.get_by_name(
                company_id=service.company_id,
                name=update_data["name"],
            )

            if (
                existing_service is not None
                and existing_service.id != service.id
            ):
                raise ServiceAlreadyExistsError()

        for field, value in update_data.items():
            setattr(service, field, value)

        return self.repository.update(service)

    def delete(
        self,
        service_id: uuid.UUID,
    ) -> None:
        service = self.get_by_id(service_id)
        self.repository.delete(service)