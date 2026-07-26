from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.customer.repository import CustomerRepository
from app.modules.customer.schemas import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.modules.customer.service import CustomerService
from app.modules.user.model import User


router = APIRouter(
    prefix="/customers",
    tags=["Clientes"],
)


def get_customer_service(
    db: Session = Depends(get_db),
) -> CustomerService:
    repository = CustomerRepository(db)

    return CustomerService(repository)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):
    return service.create_customer(
        data=data,
        company_id=current_user.company_id,
    )


@router.get(
    "",
    response_model=CustomerListResponse,
)
def list_customers(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):
    return service.list_customers(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):
    return service.get_customer(
        customer_id=customer_id,
        company_id=current_user.company_id,
    )


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):
    return service.update_customer(
        customer_id=customer_id,
        company_id=current_user.company_id,
        data=data,
    )