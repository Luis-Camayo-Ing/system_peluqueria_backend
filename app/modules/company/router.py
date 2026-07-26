from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.modules.company.repository import CompanyRepository
from app.modules.company.schemas import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.modules.company.service import CompanyService

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)

def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    repository = CompanyRepository(db)
    return CompanyService(repository)


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    company: CompanyCreate,
    service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    return service.create_company(company)


@router.get(
    "",
    response_model=CompanyListResponse,
    status_code=status.HTTP_200_OK,
)
def get_companies(
    service: CompanyService = Depends(get_company_service),
) -> CompanyListResponse:
    return service.get_companies()


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def get_company(
    company_id: UUID,
    service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    return service.get_company(company_id)

@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def update_company(
    company_id: UUID,
    company: CompanyUpdate,
    service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    return service.update_company(
        company_id,
        company,
    )

@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_company(
    company_id: UUID,
    service: CompanyService = Depends(get_company_service),
) -> None:
    service.delete_company(company_id)