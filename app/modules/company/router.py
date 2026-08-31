from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.modules.company.exceptions import CompanyNotFoundError
from app.modules.company.repository import CompanyRepository
from app.modules.company.schemas import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.modules.company.service import CompanyService
from app.modules.rbac.constants import ADMINISTRATOR_ROLE
from app.modules.rbac.dependencies import require_role
from app.modules.user.model import User

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
    current_user: User = Depends(
        require_role(ADMINISTRATOR_ROLE)
    ),
    service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    return service.create_company(company)


@router.get(
    "",
    response_model=CompanyListResponse,
    status_code=status.HTTP_200_OK,
)
def get_companies(
    current_user: User = Depends(
        require_role(ADMINISTRATOR_ROLE)
    ),
    service: CompanyService = Depends(get_company_service),
) -> CompanyListResponse:
    company = service.get_company(current_user.company_id)
    return CompanyListResponse(items=[company], total=1)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def get_company(
    company_id: UUID,
    current_user: User = Depends(
        require_role(ADMINISTRATOR_ROLE)
    ),
    service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    _ensure_company_scope(company_id, current_user.company_id)
    return service.get_company(company_id)

@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def update_company(
    company_id: UUID,
    company: CompanyUpdate,
    current_user: User = Depends(
        require_role(ADMINISTRATOR_ROLE)
    ),
    service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    _ensure_company_scope(company_id, current_user.company_id)
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
    current_user: User = Depends(
        require_role(ADMINISTRATOR_ROLE)
    ),
    service: CompanyService = Depends(get_company_service),
) -> None:
    _ensure_company_scope(company_id, current_user.company_id)
    service.delete_company(company_id)


def _ensure_company_scope(
    requested_company_id: UUID,
    authenticated_company_id: UUID,
) -> None:
    if requested_company_id != authenticated_company_id:
        raise CompanyNotFoundError(
            f"No existe una empresa con el id '{requested_company_id}'."
        )
