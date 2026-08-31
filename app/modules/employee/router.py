from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.company.repository import CompanyRepository
from app.modules.employee.exceptions import (
    EmployeeAttendanceCodeAlreadyExistsException,
    EmployeeBiometricIdAlreadyExistsException,
    EmployeeEmailAlreadyExistsException,
    EmployeeNotFoundException,
    InvalidEmployeeServicesException,
)
from app.modules.employee.repository import EmployeeRepository
from app.modules.employee.schemas import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.modules.employee.service import EmployeeService
from app.modules.rbac.constants import (
    EMPLOYEES_CREATE,
    EMPLOYEES_DELETE,
    EMPLOYEES_READ,
    EMPLOYEES_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.user.model import User


router = APIRouter()


def get_employee_service(
    db: Session = Depends(get_db),
) -> EmployeeService:
    employee_repository = EmployeeRepository(db)
    company_repository = CompanyRepository(db)

    return EmployeeService(
        employee_repository=employee_repository,
        company_repository=company_repository,
    )


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(
        require_permission(EMPLOYEES_CREATE)
    ),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        return employee_service.create(
            data,
            company_id=current_user.company_id,
        )

    except EmployeeEmailAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con ese correo en la empresa.",
        )

    except EmployeeAttendanceCodeAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con ese código de asistencia.",
        )

    except EmployeeBiometricIdAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con ese identificador biométrico.",
        )

    except InvalidEmployeeServicesException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Uno o varios servicios no existen "
                "o no pertenecen a la empresa."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[EmployeeResponse],
)
def get_employees(
    company_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(
        require_permission(EMPLOYEES_READ)
    ),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    if company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada.",
        )

    return employee_service.get_all_by_company(
        company_id=company_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def get_employee(
    employee_id: UUID,
    current_user: User = Depends(
        require_permission(EMPLOYEES_READ)
    ),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        return employee_service.get_by_id(
            employee_id,
            company_id=current_user.company_id,
        )

    except EmployeeNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado.",
        )


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    current_user: User = Depends(
        require_permission(EMPLOYEES_UPDATE)
    ),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        return employee_service.update(
            employee_id=employee_id,
            data=data,
            company_id=current_user.company_id,
        )

    except EmployeeNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado.",
        )

    except EmployeeEmailAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con ese correo en la empresa.",
        )

    except EmployeeAttendanceCodeAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con ese código de asistencia.",
        )

    except EmployeeBiometricIdAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un empleado con ese identificador biométrico.",
        )

    except InvalidEmployeeServicesException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Uno o varios servicios no existen "
                "o no pertenecen a la empresa."
            ),
        )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_employee(
    employee_id: UUID,
    current_user: User = Depends(
        require_permission(EMPLOYEES_DELETE)
    ),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        employee_service.delete(
            employee_id,
            company_id=current_user.company_id,
        )

    except EmployeeNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado."
        )

    return None
