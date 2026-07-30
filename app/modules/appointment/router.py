from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.appointment.model import AppointmentStatus
from app.modules.appointment.repository import AppointmentRepository
from app.modules.appointment.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.modules.appointment.service import AppointmentService
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.customer.repository import CustomerRepository
from app.modules.employee.repository import EmployeeRepository
from app.modules.rbac.constants import (
    APPOINTMENTS_CREATE,
    APPOINTMENTS_DELETE,
    APPOINTMENTS_READ,
    APPOINTMENTS_UPDATE,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.service.repository import ServiceRepository
from app.modules.user.model import User


router = APIRouter(
    prefix="/appointments",
    tags=["Citas"],
)


def get_appointment_service(
    db: Session = Depends(get_db),
) -> AppointmentService:
    return AppointmentService(
        appointment_repository=AppointmentRepository(db),
        customer_repository=CustomerRepository(db),
        employee_repository=EmployeeRepository(db),
        service_repository=ServiceRepository(db),
    )


def get_audit_service(
    db: Session = Depends(get_db),
) -> AuditService:
    return AuditService(
        AuditRepository(db),
    )


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_CREATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    appointment = appointment_service.create_appointment(
        data=data,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="create",
        entity_type="Appointment",
        entity_id=str(appointment.id),
        description="Se creó una cita.",
        details={
            "customer_id": str(appointment.customer_id),
            "employee_id": str(appointment.employee_id),
            "service_id": str(appointment.service_id),
            "start_at": appointment.start_at.isoformat(),
            "end_at": appointment.end_at.isoformat(),
            "status": appointment.status.value,
        },
    )

    return appointment


@router.get(
    "",
    response_model=AppointmentListResponse,
)
def list_appointments(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    service_id: UUID | None = Query(default=None),
    appointment_status: AppointmentStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.list_appointments(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        start_at=start_at,
        end_at=end_at,
        customer_id=customer_id,
        employee_id=employee_id,
        service_id=service_id,
        status=appointment_status,
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    appointment_id: UUID,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.get_appointment(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    appointment = appointment_service.update_appointment(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="update",
        entity_type="Appointment",
        entity_id=str(appointment.id),
        description="Se actualizó una cita.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
            "status": appointment.status.value,
        },
    )

    return appointment


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_appointment(
    appointment_id: UUID,
    data: AppointmentCancel,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_DELETE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    appointment = appointment_service.cancel_appointment(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="cancel",
        entity_type="Appointment",
        entity_id=str(appointment.id),
        description="Se canceló una cita.",
        details={
            "cancellation_reason": appointment.cancellation_reason,
            "status": appointment.status.value,
        },
    )

    return appointment