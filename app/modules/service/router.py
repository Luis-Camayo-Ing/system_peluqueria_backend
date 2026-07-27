import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.company.repository import CompanyRepository
from app.modules.service.repository import ServiceRepository
from app.modules.service.schemas import (
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.modules.service.service import ServiceService


router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


def get_service(
    db: Session = Depends(get_db),
) -> ServiceService:
    repository = ServiceRepository(db)
    company_repository = CompanyRepository(db)

    return ServiceService(
        repository=repository,
        company_repository=company_repository,
    )


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    data: ServiceCreate,
    service: ServiceService = Depends(get_service),
):
    return service.create(data)


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
)
def get_service_by_id(
    service_id: uuid.UUID,
    service: ServiceService = Depends(get_service),
):
    return service.get_by_id(service_id)


@router.get(
    "/company/{company_id}",
    response_model=list[ServiceResponse],
)
def get_services(
    company_id: uuid.UUID,
    service: ServiceService = Depends(get_service),
):
    return service.get_all(company_id)


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
)
def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    service: ServiceService = Depends(get_service),
):
    return service.update(
        service_id,
        data,
    )


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_service(
    service_id: uuid.UUID,
    service: ServiceService = Depends(get_service),
) -> None:
    service.delete(service_id)