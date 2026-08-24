from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.appointment.model import (
    AppointmentStatus,
    ReminderChannel,
    ReminderStatus,
    ScheduleBlockType,
)
from app.modules.appointment.repository import AppointmentRepository
from app.modules.appointment.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentHistoryListResponse,
    AppointmentListResponse,
    AppointmentReminderCreate,
    AppointmentReminderListResponse,
    AppointmentReminderResponse,
    AppointmentReminderUpdate,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentUpdate,
    EmployeeAvailabilityRequest,
    EmployeeAvailabilityResponse,
    EmployeeScheduleBlockCreate,
    EmployeeScheduleBlockListResponse,
    EmployeeScheduleBlockResponse,
    EmployeeScheduleBlockUpdate,
    EmployeeWorkScheduleCreate,
    EmployeeWorkScheduleListResponse,
    EmployeeWorkScheduleResponse,
    EmployeeWorkScheduleUpdate,
)
from app.modules.appointment.service import AppointmentService
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.customer.repository import CustomerRepository
from app.modules.employee.repository import EmployeeRepository
from app.modules.rbac.constants import (
    APPOINTMENTS_CANCEL,
    APPOINTMENTS_CREATE,
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


@router.post(
    "/availability",
    response_model=EmployeeAvailabilityResponse,
)
def get_employee_availability(
    data: EmployeeAvailabilityRequest,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.get_employee_availability(
        data=data,
        company_id=current_user.company_id,
    )


@router.post(
    "/work-schedules",
    response_model=EmployeeWorkScheduleResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_work_schedule(
    data: EmployeeWorkScheduleCreate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    schedule = appointment_service.create_work_schedule(
        data=data,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="create_work_schedule",
        entity_type="EmployeeWorkSchedule",
        entity_id=str(schedule.id),
        description="Se creó un horario laboral.",
        details={
            "employee_id": str(schedule.employee_id),
            "weekday": schedule.weekday,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "is_active": schedule.is_active,
        },
    )

    return schedule


@router.get(
    "/work-schedules",
    response_model=EmployeeWorkScheduleListResponse,
)
def list_work_schedules(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    employee_id: UUID | None = Query(default=None),
    weekday: int | None = Query(
        default=None,
        ge=0,
        le=6,
    ),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.list_work_schedules(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        weekday=weekday,
        is_active=is_active,
    )


@router.get(
    "/work-schedules/{schedule_id}",
    response_model=EmployeeWorkScheduleResponse,
)
def get_work_schedule(
    schedule_id: UUID,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.get_work_schedule(
        schedule_id=schedule_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/work-schedules/{schedule_id}",
    response_model=EmployeeWorkScheduleResponse,
)
def update_work_schedule(
    schedule_id: UUID,
    data: EmployeeWorkScheduleUpdate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    schedule = appointment_service.update_work_schedule(
        schedule_id=schedule_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="update_work_schedule",
        entity_type="EmployeeWorkSchedule",
        entity_id=str(schedule.id),
        description="Se actualizó un horario laboral.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
            "employee_id": str(schedule.employee_id),
        },
    )

    return schedule


@router.post(
    "/schedule-blocks",
    response_model=EmployeeScheduleBlockResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_schedule_block(
    data: EmployeeScheduleBlockCreate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    block = appointment_service.create_schedule_block(
        data=data,
        company_id=current_user.company_id,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="create_schedule_block",
        entity_type="EmployeeScheduleBlock",
        entity_id=str(block.id),
        description="Se creó un bloqueo de agenda.",
        details={
            "employee_id": str(block.employee_id),
            "block_type": block.block_type.value,
            "start_at": block.start_at.isoformat(),
            "end_at": block.end_at.isoformat(),
            "reason": block.reason,
            "is_active": block.is_active,
        },
    )

    return block


@router.get(
    "/schedule-blocks",
    response_model=EmployeeScheduleBlockListResponse,
)
def list_schedule_blocks(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    employee_id: UUID | None = Query(default=None),
    block_type: ScheduleBlockType | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.list_schedule_blocks(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        block_type=block_type,
        start_at=start_at,
        end_at=end_at,
        is_active=is_active,
    )


@router.get(
    "/schedule-blocks/{block_id}",
    response_model=EmployeeScheduleBlockResponse,
)
def get_schedule_block(
    block_id: UUID,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.get_schedule_block(
        block_id=block_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/schedule-blocks/{block_id}",
    response_model=EmployeeScheduleBlockResponse,
)
def update_schedule_block(
    block_id: UUID,
    data: EmployeeScheduleBlockUpdate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    block = appointment_service.update_schedule_block(
        block_id=block_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="update_schedule_block",
        entity_type="EmployeeScheduleBlock",
        entity_id=str(block.id),
        description="Se actualizó un bloqueo de agenda.",
        details={
            "changes": data.model_dump(
                exclude_unset=True,
                mode="json",
            ),
            "employee_id": str(block.employee_id),
        },
    )

    return block


@router.get(
    "/reminders/due",
    response_model=AppointmentReminderListResponse,
)
def list_due_reminders(
    due_until: datetime | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.list_reminders(
        company_id=current_user.company_id,
        limit=limit,
        status=ReminderStatus.PENDING,
        remind_until=(
            due_until
            if due_until is not None
            else datetime.now(timezone.utc)
        ),
    )


@router.get(
    "/reminders",
    response_model=AppointmentReminderListResponse,
)
def list_reminders(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    appointment_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    channel: ReminderChannel | None = Query(default=None),
    reminder_status: ReminderStatus | None = Query(
        default=None,
        alias="status",
    ),
    remind_from: datetime | None = Query(default=None),
    remind_until: datetime | None = Query(default=None),
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.list_reminders(
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        appointment_id=appointment_id,
        employee_id=employee_id,
        channel=channel,
        status=reminder_status,
        remind_from=remind_from,
        remind_until=remind_until,
    )


@router.get(
    "/reminders/{reminder_id}",
    response_model=AppointmentReminderResponse,
)
def get_reminder(
    reminder_id: UUID,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.get_reminder(
        reminder_id=reminder_id,
        company_id=current_user.company_id,
    )


@router.patch(
    "/reminders/{reminder_id}",
    response_model=AppointmentReminderResponse,
)
def update_reminder(
    reminder_id: UUID,
    data: AppointmentReminderUpdate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    reminder = appointment_service.update_reminder(
        reminder_id=reminder_id,
        company_id=current_user.company_id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="update_reminder",
        entity_type="AppointmentReminder",
        entity_id=str(reminder.id),
        description="Se actualizó un recordatorio de cita.",
        details={
            "appointment_id": str(reminder.appointment_id),
            "status": reminder.status.value,
            "channel": reminder.channel.value,
        },
    )

    return reminder


@router.post(
    "/{appointment_id}/reminders",
    response_model=AppointmentReminderResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_reminder(
    appointment_id: UUID,
    data: AppointmentReminderCreate,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    reminder = appointment_service.create_reminder(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
        created_by_user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="create_reminder",
        entity_type="AppointmentReminder",
        entity_id=str(reminder.id),
        description="Se programó un recordatorio de cita.",
        details={
            "appointment_id": str(reminder.appointment_id),
            "channel": reminder.channel.value,
            "remind_at": reminder.remind_at.isoformat(),
        },
    )

    return reminder


@router.get(
    "/{appointment_id}/history",
    response_model=AppointmentHistoryListResponse,
)
def list_appointment_history(
    appointment_id: UUID,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_permission(APPOINTMENTS_READ)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
):
    return appointment_service.list_appointment_history(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
)
def reschedule_appointment(
    appointment_id: UUID,
    data: AppointmentReschedule,
    current_user: User = Depends(
        require_permission(APPOINTMENTS_UPDATE)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    appointment = appointment_service.reschedule_appointment(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
        changed_by_user_id=current_user.id,
        data=data,
    )

    audit_service.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        module="appointments",
        action="reschedule",
        entity_type="Appointment",
        entity_id=str(appointment.id),
        description="Se reprogramó una cita.",
        details={
            "employee_id": str(appointment.employee_id),
            "service_id": str(appointment.service_id),
            "start_at": appointment.start_at.isoformat(),
            "end_at": appointment.end_at.isoformat(),
            "reason": data.reason.strip(),
        },
    )

    return appointment


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
        require_permission(APPOINTMENTS_CANCEL)
    ),
    appointment_service: AppointmentService = Depends(
        get_appointment_service
    ),
    audit_service: AuditService = Depends(get_audit_service),
):
    appointment = appointment_service.cancel_appointment(
        appointment_id=appointment_id,
        company_id=current_user.company_id,
        changed_by_user_id=current_user.id,
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