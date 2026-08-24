from datetime import datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.appointment.exceptions import (
    AppointmentAlreadyCancelledException,
    AppointmentBlockedException,
    AppointmentConflictException,
    AppointmentFinalizedException,
    AppointmentInPastException,
    AppointmentNotFoundException,
    AppointmentOutsideWorkScheduleException,
    AppointmentRelatedEntityInactiveException,
    AppointmentRelatedEntityNotFoundException,
    AppointmentReminderConflictException,
    AppointmentReminderNotFoundException,
    EmployeeCannotPerformServiceException,
    InvalidAppointmentReminderTimeException,
    InvalidAppointmentReminderTransitionException,
    InvalidAppointmentStatusException,
    InvalidAppointmentTimeException,
    InvalidTimezoneException,
    ScheduleBlockConflictException,
    ScheduleBlockNotFoundException,
    ServiceDurationMismatchException,
    ServiceDurationUnavailableException,
    WorkScheduleConflictException,
    WorkScheduleNotFoundException,
)
from app.modules.appointment.model import (
    Appointment,
    AppointmentHistory,
    AppointmentHistoryType,
    AppointmentReminder,
    AppointmentStatus,
    EmployeeScheduleBlock,
    EmployeeWorkSchedule,
    ReminderChannel,
    ReminderStatus,
    ScheduleBlockType,
)
from app.modules.appointment.repository import AppointmentRepository
from app.modules.appointment.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReminderCreate,
    AppointmentReminderUpdate,
    AppointmentReschedule,
    AppointmentUpdate,
    AvailabilitySlot,
    EmployeeAvailabilityRequest,
    EmployeeAvailabilityResponse,
    EmployeeScheduleBlockCreate,
    EmployeeScheduleBlockUpdate,
    EmployeeWorkScheduleCreate,
    EmployeeWorkScheduleUpdate,
)
from app.modules.customer.model import Customer
from app.modules.customer.repository import CustomerRepository
from app.modules.employee.model import Employee
from app.modules.employee.repository import EmployeeRepository
from app.modules.service.model import Service
from app.modules.service.repository import ServiceRepository


class AppointmentService:
    BUSINESS_TIMEZONE = "America/Bogota"

    ALLOWED_STATUS_TRANSITIONS = {
        AppointmentStatus.SCHEDULED: {
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        },
        AppointmentStatus.CONFIRMED: {
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        },
        AppointmentStatus.IN_PROGRESS: {
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
        },
        AppointmentStatus.COMPLETED: set(),
        AppointmentStatus.CANCELLED: set(),
        AppointmentStatus.NO_SHOW: set(),
    }

    TERMINAL_STATUSES = {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    }

    ALLOWED_REMINDER_TRANSITIONS = {
        ReminderStatus.PENDING: {
            ReminderStatus.SENT,
            ReminderStatus.FAILED,
            ReminderStatus.CANCELLED,
        },
        ReminderStatus.FAILED: {
            ReminderStatus.PENDING,
            ReminderStatus.CANCELLED,
        },
        ReminderStatus.SENT: set(),
        ReminderStatus.CANCELLED: set(),
    }

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        customer_repository: CustomerRepository,
        employee_repository: EmployeeRepository,
        service_repository: ServiceRepository,
    ):
        self.appointment_repository = appointment_repository
        self.customer_repository = customer_repository
        self.employee_repository = employee_repository
        self.service_repository = service_repository

    # ==========================================================
    # Appointments
    # ==========================================================

    def create_appointment(
        self,
        data: AppointmentCreate,
        company_id: UUID,
    ) -> Appointment:
        self._validate_time_range(
            start_at=data.start_at,
            end_at=data.end_at,
        )
        self._validate_not_in_past(data.start_at)

        self._validate_customer(
            customer_id=data.customer_id,
            company_id=company_id,
        )

        employee = self._validate_employee(
            employee_id=data.employee_id,
            company_id=company_id,
        )

        service = self._validate_service(
            service_id=data.service_id,
            company_id=company_id,
        )

        self._validate_employee_service(
            employee=employee,
            service=service,
        )

        self._validate_service_duration(
            service=service,
            start_at=data.start_at,
            end_at=data.end_at,
        )

        self.appointment_repository.lock_employee_agenda(
            employee.id
        )

        self._validate_employee_availability(
            company_id=company_id,
            employee_id=employee.id,
            start_at=data.start_at,
            end_at=data.end_at,
        )

        appointment = Appointment(
            company_id=company_id,
            customer_id=data.customer_id,
            employee_id=data.employee_id,
            service_id=data.service_id,
            start_at=data.start_at,
            end_at=data.end_at,
            status=AppointmentStatus.SCHEDULED,
            notes=data.notes,
        )

        return self.appointment_repository.create(appointment)

    def get_appointment(
        self,
        appointment_id: UUID,
        company_id: UUID,
    ) -> Appointment:
        appointment = self.appointment_repository.get_by_id(
            appointment_id=appointment_id,
            company_id=company_id,
        )

        if appointment is None:
            raise AppointmentNotFoundException()

        return appointment

    def list_appointments(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 20,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        customer_id: UUID | None = None,
        employee_id: UUID | None = None,
        service_id: UUID | None = None,
        status: AppointmentStatus | None = None,
    ) -> dict:
        if (
            start_at is not None
            and end_at is not None
            and end_at <= start_at
        ):
            raise InvalidAppointmentTimeException()

        appointments = self.appointment_repository.list_appointments(
            company_id=company_id,
            skip=skip,
            limit=limit,
            start_at=start_at,
            end_at=end_at,
            customer_id=customer_id,
            employee_id=employee_id,
            service_id=service_id,
            status=status,
        )

        total = self.appointment_repository.count_appointments(
            company_id=company_id,
            start_at=start_at,
            end_at=end_at,
            customer_id=customer_id,
            employee_id=employee_id,
            service_id=service_id,
            status=status,
        )

        return {
            "total": total,
            "items": appointments,
        }

    def update_appointment(
        self,
        appointment_id: UUID,
        company_id: UUID,
        data: AppointmentUpdate,
    ) -> Appointment:
        appointment = self.get_appointment(
            appointment_id=appointment_id,
            company_id=company_id,
        )

        if appointment.status in self.TERMINAL_STATUSES:
            raise AppointmentFinalizedException(
                appointment_status=appointment.status.value,
            )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return appointment

        if "cancellation_reason" in update_data:
            raise InvalidAppointmentStatusException(
                detail=(
                    "Para cancelar una cita debe utilizarse "
                    "el endpoint específico de cancelación."
                ),
            )

        scheduling_fields = {
            "employee_id",
            "service_id",
            "start_at",
            "end_at",
        }

        if scheduling_fields.intersection(update_data):
            raise InvalidAppointmentStatusException(
                detail=(
                    "Para reprogramar una cita o cambiar el empleado "
                    "o servicio debe utilizarse el endpoint específico "
                    "de reprogramación."
                ),
            )

        new_status = update_data.get("status")

        if new_status == AppointmentStatus.CANCELLED:
            raise InvalidAppointmentStatusException(
                detail=(
                    "Para cancelar una cita debe utilizarse "
                    "el endpoint específico de cancelación."
                ),
            )

        if new_status is not None:
            self._validate_status_transition(
                current_status=appointment.status,
                new_status=new_status,
            )

        customer_id = update_data.get(
            "customer_id",
            appointment.customer_id,
        )
        employee_id = update_data.get(
            "employee_id",
            appointment.employee_id,
        )
        service_id = update_data.get(
            "service_id",
            appointment.service_id,
        )
        start_at = update_data.get(
            "start_at",
            appointment.start_at,
        )
        end_at = update_data.get(
            "end_at",
            appointment.end_at,
        )

        self._validate_time_range(
            start_at=start_at,
            end_at=end_at,
        )

        self._validate_customer(
            customer_id=customer_id,
            company_id=company_id,
        )

        employee = self._validate_employee(
            employee_id=employee_id,
            company_id=company_id,
        )

        service = self._validate_service(
            service_id=service_id,
            company_id=company_id,
        )

        self._validate_employee_service(
            employee=employee,
            service=service,
        )

        scheduling_changed = bool(
            scheduling_fields.intersection(update_data)
        )

        target_status = new_status or appointment.status

        if (
            scheduling_changed
            and target_status != AppointmentStatus.NO_SHOW
        ):
            self._validate_not_in_past(start_at)

            self._validate_employee_availability(
                company_id=company_id,
                employee_id=employee_id,
                start_at=start_at,
                end_at=end_at,
                exclude_appointment_id=appointment.id,
            )

        for field, value in update_data.items():
            setattr(appointment, field, value)

        return self.appointment_repository.update(appointment)

    def reschedule_appointment(
        self,
        appointment_id: UUID,
        company_id: UUID,
        changed_by_user_id: UUID,
        data: AppointmentReschedule,
    ) -> Appointment:
        appointment = self.get_appointment(
            appointment_id=appointment_id,
            company_id=company_id,
        )

        self.appointment_repository.lock_appointment(
            appointment.id
        )
        self.appointment_repository.refresh_appointment(
            appointment
        )

        if appointment.status in self.TERMINAL_STATUSES:
            raise AppointmentFinalizedException(
                appointment_status=appointment.status.value,
            )

        employee_id = data.employee_id or appointment.employee_id
        service_id = data.service_id or appointment.service_id

        self._validate_time_range(
            start_at=data.start_at,
            end_at=data.end_at,
        )
        self._validate_not_in_past(data.start_at)

        employee = self._validate_employee(
            employee_id=employee_id,
            company_id=company_id,
        )
        service = self._validate_service(
            service_id=service_id,
            company_id=company_id,
        )

        self._validate_employee_service(
            employee=employee,
            service=service,
        )

        self._validate_service_duration(
            service=service,
            start_at=data.start_at,
            end_at=data.end_at,
        )

        self.appointment_repository.lock_employee_agenda(
            employee.id
        )

        self._validate_employee_availability(
            company_id=company_id,
            employee_id=employee.id,
            start_at=data.start_at,
            end_at=data.end_at,
            exclude_appointment_id=appointment.id,
        )

        reason = data.reason.strip()

        history = AppointmentHistory(
            company_id=company_id,
            appointment_id=appointment.id,
            changed_by_user_id=changed_by_user_id,
            change_type=AppointmentHistoryType.RESCHEDULED,
            previous_start_at=appointment.start_at,
            previous_end_at=appointment.end_at,
            new_start_at=data.start_at,
            new_end_at=data.end_at,
            previous_status=appointment.status,
            new_status=appointment.status,
            reason=reason,
        )

        appointment.employee_id = employee.id
        appointment.service_id = service.id
        appointment.start_at = data.start_at
        appointment.end_at = data.end_at

        self.appointment_repository.cancel_pending_reminders(
            appointment_id=appointment.id,
            at_or_after=data.start_at,
        )

        return self.appointment_repository.update_with_history(
            appointment=appointment,
            history=history,
        )

    def cancel_appointment(
        self,
        appointment_id: UUID,
        company_id: UUID,
        changed_by_user_id: UUID,
        data: AppointmentCancel,
    ) -> Appointment:
        appointment = self.get_appointment(
            appointment_id=appointment_id,
            company_id=company_id,
        )

        self.appointment_repository.lock_appointment(
            appointment.id
        )
        self.appointment_repository.refresh_appointment(
            appointment
        )

        if appointment.status == AppointmentStatus.CANCELLED:
            raise AppointmentAlreadyCancelledException()

        self._validate_status_transition(
            current_status=appointment.status,
            new_status=AppointmentStatus.CANCELLED,
        )

        cancellation_reason = data.cancellation_reason.strip()

        if len(cancellation_reason) < 3:
            raise InvalidAppointmentStatusException(
                detail=(
                    "El motivo de cancelación debe contener "
                    "al menos tres caracteres."
                ),
            )

        previous_status = appointment.status

        history = AppointmentHistory(
            company_id=company_id,
            appointment_id=appointment.id,
            changed_by_user_id=changed_by_user_id,
            change_type=AppointmentHistoryType.CANCELLED,
            previous_start_at=appointment.start_at,
            previous_end_at=appointment.end_at,
            new_start_at=appointment.start_at,
            new_end_at=appointment.end_at,
            previous_status=previous_status,
            new_status=AppointmentStatus.CANCELLED,
            reason=cancellation_reason,
        )

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = cancellation_reason

        self.appointment_repository.cancel_pending_reminders(
            appointment_id=appointment.id,
        )

        return self.appointment_repository.update_with_history(
            appointment=appointment,
            history=history,
        )

    def list_appointment_history(
        self,
        appointment_id: UUID,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        self.get_appointment(
            appointment_id=appointment_id,
            company_id=company_id,
        )

        items = (
            self.appointment_repository
            .list_appointment_history(
                company_id=company_id,
                appointment_id=appointment_id,
                skip=skip,
                limit=limit,
            )
        )

        total = (
            self.appointment_repository
            .count_appointment_history(
                company_id=company_id,
                appointment_id=appointment_id,
            )
        )

        return {
            "total": total,
            "items": items,
        }

    # ==========================================================
    # Employee work schedules
    # ==========================================================

    def create_work_schedule(
        self,
        data: EmployeeWorkScheduleCreate,
        company_id: UUID,
    ) -> EmployeeWorkSchedule:
        employee = self._validate_employee(
            employee_id=data.employee_id,
            company_id=company_id,
        )

        self._validate_schedule_time_range(
            start_time=data.start_time,
            end_time=data.end_time,
        )

        self.appointment_repository.lock_employee_agenda(
            employee.id
        )

        if data.is_active:
            conflict = (
                self.appointment_repository
                .find_work_schedule_conflict(
                    company_id=company_id,
                    employee_id=employee.id,
                    weekday=data.weekday,
                    start_time=data.start_time,
                    end_time=data.end_time,
                )
            )

            if conflict is not None:
                raise WorkScheduleConflictException()

        schedule = EmployeeWorkSchedule(
            company_id=company_id,
            employee_id=employee.id,
            weekday=data.weekday,
            start_time=data.start_time,
            end_time=data.end_time,
            is_active=data.is_active,
        )

        return (
            self.appointment_repository
            .create_work_schedule(schedule)
        )

    def get_work_schedule(
        self,
        schedule_id: UUID,
        company_id: UUID,
    ) -> EmployeeWorkSchedule:
        schedule = (
            self.appointment_repository
            .get_work_schedule_by_id(
                schedule_id=schedule_id,
                company_id=company_id,
            )
        )

        if schedule is None:
            raise WorkScheduleNotFoundException()

        return schedule

    def list_work_schedules(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        employee_id: UUID | None = None,
        weekday: int | None = None,
        is_active: bool | None = None,
    ) -> dict:
        if employee_id is not None:
            self._validate_employee(
                employee_id=employee_id,
                company_id=company_id,
            )

        items = (
            self.appointment_repository
            .list_work_schedules(
                company_id=company_id,
                skip=skip,
                limit=limit,
                employee_id=employee_id,
                weekday=weekday,
                is_active=is_active,
            )
        )

        total = (
            self.appointment_repository
            .count_work_schedules(
                company_id=company_id,
                employee_id=employee_id,
                weekday=weekday,
                is_active=is_active,
            )
        )

        return {
            "total": total,
            "items": items,
        }

    def update_work_schedule(
        self,
        schedule_id: UUID,
        company_id: UUID,
        data: EmployeeWorkScheduleUpdate,
    ) -> EmployeeWorkSchedule:
        schedule = self.get_work_schedule(
            schedule_id=schedule_id,
            company_id=company_id,
        )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return schedule

        weekday = update_data.get(
            "weekday",
            schedule.weekday,
        )
        start_time = update_data.get(
            "start_time",
            schedule.start_time,
        )
        end_time = update_data.get(
            "end_time",
            schedule.end_time,
        )
        is_active = update_data.get(
            "is_active",
            schedule.is_active,
        )

        self._validate_schedule_time_range(
            start_time=start_time,
            end_time=end_time,
        )

        self.appointment_repository.lock_employee_agenda(
            schedule.employee_id
        )

        if is_active:
            conflict = (
                self.appointment_repository
                .find_work_schedule_conflict(
                    company_id=company_id,
                    employee_id=schedule.employee_id,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time,
                    exclude_schedule_id=schedule.id,
                )
            )

            if conflict is not None:
                raise WorkScheduleConflictException()

        for field, value in update_data.items():
            setattr(schedule, field, value)

        return (
            self.appointment_repository
            .update_work_schedule(schedule)
        )

    # ==========================================================
    # Employee schedule blocks
    # ==========================================================

    def create_schedule_block(
        self,
        data: EmployeeScheduleBlockCreate,
        company_id: UUID,
    ) -> EmployeeScheduleBlock:
        employee = self._validate_employee(
            employee_id=data.employee_id,
            company_id=company_id,
        )

        self._validate_time_range(
            start_at=data.start_at,
            end_at=data.end_at,
        )

        self.appointment_repository.lock_employee_agenda(
            employee.id
        )

        if data.is_active:
            conflict = (
                self.appointment_repository
                .find_schedule_block_conflict(
                    company_id=company_id,
                    employee_id=employee.id,
                    start_at=data.start_at,
                    end_at=data.end_at,
                )
            )

            if conflict is not None:
                raise ScheduleBlockConflictException()

            appointment_conflict = (
                self.appointment_repository
                .find_employee_conflict(
                    company_id=company_id,
                    employee_id=employee.id,
                    start_at=data.start_at,
                    end_at=data.end_at,
                )
            )

            if appointment_conflict is not None:
                raise AppointmentConflictException()

        block = EmployeeScheduleBlock(
            company_id=company_id,
            employee_id=employee.id,
            block_type=data.block_type,
            start_at=data.start_at,
            end_at=data.end_at,
            reason=self._normalize_optional_text(
                data.reason
            ),
            is_active=data.is_active,
        )

        return (
            self.appointment_repository
            .create_schedule_block(block)
        )

    def get_schedule_block(
        self,
        block_id: UUID,
        company_id: UUID,
    ) -> EmployeeScheduleBlock:
        block = (
            self.appointment_repository
            .get_schedule_block_by_id(
                block_id=block_id,
                company_id=company_id,
            )
        )

        if block is None:
            raise ScheduleBlockNotFoundException()

        return block

    def list_schedule_blocks(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        employee_id: UUID | None = None,
        block_type: ScheduleBlockType | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        is_active: bool | None = None,
    ) -> dict:
        if (
            start_at is not None
            and end_at is not None
            and end_at <= start_at
        ):
            raise InvalidAppointmentTimeException()

        if employee_id is not None:
            self._validate_employee(
                employee_id=employee_id,
                company_id=company_id,
            )

        items = (
            self.appointment_repository
            .list_schedule_blocks(
                company_id=company_id,
                skip=skip,
                limit=limit,
                employee_id=employee_id,
                block_type=block_type,
                start_at=start_at,
                end_at=end_at,
                is_active=is_active,
            )
        )

        total = (
            self.appointment_repository
            .count_schedule_blocks(
                company_id=company_id,
                employee_id=employee_id,
                block_type=block_type,
                start_at=start_at,
                end_at=end_at,
                is_active=is_active,
            )
        )

        return {
            "total": total,
            "items": items,
        }

    def update_schedule_block(
        self,
        block_id: UUID,
        company_id: UUID,
        data: EmployeeScheduleBlockUpdate,
    ) -> EmployeeScheduleBlock:
        block = self.get_schedule_block(
            block_id=block_id,
            company_id=company_id,
        )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return block

        start_at = update_data.get(
            "start_at",
            block.start_at,
        )
        end_at = update_data.get(
            "end_at",
            block.end_at,
        )
        is_active = update_data.get(
            "is_active",
            block.is_active,
        )

        self._validate_time_range(
            start_at=start_at,
            end_at=end_at,
        )

        self.appointment_repository.lock_employee_agenda(
            block.employee_id
        )

        if is_active:
            conflict = (
                self.appointment_repository
                .find_schedule_block_conflict(
                    company_id=company_id,
                    employee_id=block.employee_id,
                    start_at=start_at,
                    end_at=end_at,
                    exclude_block_id=block.id,
                )
            )

            if conflict is not None:
                raise ScheduleBlockConflictException()

            appointment_conflict = (
                self.appointment_repository
                .find_employee_conflict(
                    company_id=company_id,
                    employee_id=block.employee_id,
                    start_at=start_at,
                    end_at=end_at,
                )
            )

            if appointment_conflict is not None:
                raise AppointmentConflictException()

        if "reason" in update_data:
            update_data["reason"] = (
                self._normalize_optional_text(
                    update_data["reason"]
                )
            )

        for field, value in update_data.items():
            setattr(block, field, value)

        return (
            self.appointment_repository
            .update_schedule_block(block)
        )

    # ==========================================================
    # Appointment reminders
    # ==========================================================

    def create_reminder(
        self,
        appointment_id: UUID,
        company_id: UUID,
        created_by_user_id: UUID,
        data: AppointmentReminderCreate,
    ) -> AppointmentReminder:
        appointment = self.get_appointment(
            appointment_id=appointment_id,
            company_id=company_id,
        )

        self.appointment_repository.lock_appointment(
            appointment.id
        )
        self.appointment_repository.refresh_appointment(
            appointment
        )

        if appointment.status in self.TERMINAL_STATUSES:
            raise AppointmentFinalizedException(
                appointment_status=appointment.status.value,
            )

        now = datetime.now(timezone.utc)

        if (
            data.remind_at.astimezone(timezone.utc) <= now
            or data.remind_at >= appointment.start_at
        ):
            raise InvalidAppointmentReminderTimeException()

        duplicate = (
            self.appointment_repository
            .find_reminder_duplicate(
                company_id=company_id,
                appointment_id=appointment.id,
                channel=data.channel,
                remind_at=data.remind_at,
            )
        )

        if duplicate is not None:
            raise AppointmentReminderConflictException()

        reminder = AppointmentReminder(
            company_id=company_id,
            appointment_id=appointment.id,
            created_by_user_id=created_by_user_id,
            channel=data.channel,
            remind_at=data.remind_at,
            status=ReminderStatus.PENDING,
        )

        return self.appointment_repository.create_reminder(
            reminder
        )

    def get_reminder(
        self,
        reminder_id: UUID,
        company_id: UUID,
    ) -> AppointmentReminder:
        reminder = (
            self.appointment_repository
            .get_reminder_by_id(
                reminder_id=reminder_id,
                company_id=company_id,
            )
        )

        if reminder is None:
            raise AppointmentReminderNotFoundException()

        return reminder

    def list_reminders(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        appointment_id: UUID | None = None,
        employee_id: UUID | None = None,
        channel: ReminderChannel | None = None,
        status: ReminderStatus | None = None,
        remind_from: datetime | None = None,
        remind_until: datetime | None = None,
    ) -> dict:
        if appointment_id is not None:
            self.get_appointment(
                appointment_id=appointment_id,
                company_id=company_id,
            )

        if employee_id is not None:
            self._validate_employee(
                employee_id=employee_id,
                company_id=company_id,
            )

        if remind_from is not None:
            self._validate_timezone_aware_datetime(
                remind_from,
            )

        if remind_until is not None:
            self._validate_timezone_aware_datetime(
                remind_until,
            )

        if (
            remind_from is not None
            and remind_until is not None
            and remind_until < remind_from
        ):
            raise InvalidAppointmentTimeException()

        items = self.appointment_repository.list_reminders(
            company_id=company_id,
            skip=skip,
            limit=limit,
            appointment_id=appointment_id,
            employee_id=employee_id,
            channel=channel,
            status=status,
            remind_from=remind_from,
            remind_until=remind_until,
        )

        total = self.appointment_repository.count_reminders(
            company_id=company_id,
            appointment_id=appointment_id,
            employee_id=employee_id,
            channel=channel,
            status=status,
            remind_from=remind_from,
            remind_until=remind_until,
        )

        return {
            "total": total,
            "items": items,
        }

    def update_reminder(
        self,
        reminder_id: UUID,
        company_id: UUID,
        data: AppointmentReminderUpdate,
    ) -> AppointmentReminder:
        reminder = self.get_reminder(
            reminder_id=reminder_id,
            company_id=company_id,
        )

        appointment = self.get_appointment(
            appointment_id=reminder.appointment_id,
            company_id=company_id,
        )

        self.appointment_repository.lock_appointment(
            appointment.id
        )
        self.appointment_repository.refresh_appointment(
            appointment
        )
        self.appointment_repository.refresh_reminder(
            reminder
        )

        if (
            appointment.status in self.TERMINAL_STATUSES
            and data.status != ReminderStatus.CANCELLED
        ):
            raise AppointmentFinalizedException(
                appointment_status=appointment.status.value,
            )

        if data.status == reminder.status:
            return reminder

        allowed_statuses = self.ALLOWED_REMINDER_TRANSITIONS[
            reminder.status
        ]

        if data.status not in allowed_statuses:
            raise InvalidAppointmentReminderTransitionException(
                detail=(
                    "No se permite cambiar un recordatorio de "
                    f"'{reminder.status.value}' a "
                    f"'{data.status.value}'."
                ),
            )

        if data.status == ReminderStatus.FAILED:
            failure_message = self._normalize_optional_text(
                data.failure_message
            )

            if failure_message is None:
                raise InvalidAppointmentReminderTransitionException(
                    detail=(
                        "Debe indicar failure_message cuando el "
                        "recordatorio cambia a estado 'failed'."
                    ),
                )

            reminder.failure_message = failure_message
            reminder.sent_at = None

        elif data.status == ReminderStatus.SENT:
            reminder.failure_message = None
            reminder.sent_at = datetime.now(timezone.utc)

        else:
            reminder.failure_message = None
            reminder.sent_at = None

        reminder.status = data.status

        return self.appointment_repository.update_reminder(
            reminder
        )

    # ==========================================================
    # Availability
    # ==========================================================

    def get_employee_availability(
        self,
        data: EmployeeAvailabilityRequest,
        company_id: UUID,
    ) -> EmployeeAvailabilityResponse:
        employee = self._validate_employee(
            employee_id=data.employee_id,
            company_id=company_id,
        )

        service = self._validate_service(
            service_id=data.service_id,
            company_id=company_id,
        )

        self._validate_employee_service(
            employee=employee,
            service=service,
        )

        duration_minutes = service.duration_minutes

        if (
            duration_minutes is None
            or duration_minutes <= 0
        ):
            raise ServiceDurationUnavailableException()

        timezone_info = self._get_timezone(data.timezone)

        now_local = datetime.now(timezone.utc).astimezone(
            timezone_info
        )

        if data.target_date < now_local.date():
            raise AppointmentInPastException()

        day_start = datetime.combine(
            data.target_date,
            time.min,
            tzinfo=timezone_info,
        )

        day_end = datetime.combine(
            data.target_date + timedelta(days=1),
            time.min,
            tzinfo=timezone_info,
        )

        schedules = (
            self.appointment_repository
            .get_active_work_schedules_for_weekday(
                company_id=company_id,
                employee_id=employee.id,
                weekday=data.target_date.weekday(),
            )
        )

        appointments = (
            self.appointment_repository
            .list_employee_appointments_in_range(
                company_id=company_id,
                employee_id=employee.id,
                start_at=day_start,
                end_at=day_end,
            )
        )

        blocks = (
            self.appointment_repository
            .list_active_schedule_blocks_in_range(
                company_id=company_id,
                employee_id=employee.id,
                start_at=day_start,
                end_at=day_end,
            )
        )

        duration = timedelta(
            minutes=duration_minutes
        )

        interval = timedelta(
            minutes=data.slot_interval_minutes
        )

        slots: list[AvailabilitySlot] = []
        seen_slots: set[tuple[datetime, datetime]] = set()

        for schedule in schedules:
            schedule_start = datetime.combine(
                data.target_date,
                schedule.start_time,
                tzinfo=timezone_info,
            )

            schedule_end = datetime.combine(
                data.target_date,
                schedule.end_time,
                tzinfo=timezone_info,
            )

            candidate_start = schedule_start

            while candidate_start + duration <= schedule_end:
                candidate_end = candidate_start + duration

                if candidate_start >= now_local:
                    has_appointment = any(
                        self._ranges_overlap(
                            candidate_start,
                            candidate_end,
                            appointment.start_at,
                            appointment.end_at,
                        )
                        for appointment in appointments
                    )

                    has_block = any(
                        self._ranges_overlap(
                            candidate_start,
                            candidate_end,
                            block.start_at,
                            block.end_at,
                        )
                        for block in blocks
                    )

                    slot_key = (
                        candidate_start,
                        candidate_end,
                    )

                    if (
                        not has_appointment
                        and not has_block
                        and slot_key not in seen_slots
                    ):
                        slots.append(
                            AvailabilitySlot(
                                start_at=candidate_start,
                                end_at=candidate_end,
                            )
                        )
                        seen_slots.add(slot_key)

                candidate_start += interval

        slots.sort(key=lambda slot: slot.start_at)

        return EmployeeAvailabilityResponse(
            employee_id=employee.id,
            service_id=service.id,
            target_date=data.target_date,
            timezone=data.timezone,
            duration_minutes=duration_minutes,
            slots=slots,
        )

    # ==========================================================
    # Shared validations
    # ==========================================================

    def _validate_customer(
        self,
        customer_id: UUID,
        company_id: UUID,
    ) -> Customer:
        customer = self.customer_repository.get_by_id(
            customer_id=customer_id,
            company_id=company_id,
        )

        if customer is None:
            raise AppointmentRelatedEntityNotFoundException(
                "El cliente",
            )

        if not customer.is_active:
            raise AppointmentRelatedEntityInactiveException(
                "El cliente",
            )

        return customer

    def _validate_employee(
        self,
        employee_id: UUID,
        company_id: UUID,
    ) -> Employee:
        employee = self.employee_repository.get_by_id(
            employee_id
        )

        if (
            employee is None
            or employee.company_id != company_id
        ):
            raise AppointmentRelatedEntityNotFoundException(
                "El empleado",
            )

        if not employee.is_active:
            raise AppointmentRelatedEntityInactiveException(
                "El empleado",
            )

        return employee

    def _validate_service(
        self,
        service_id: UUID,
        company_id: UUID,
    ) -> Service:
        service = self.service_repository.get_by_id(
            service_id
        )

        if (
            service is None
            or service.company_id != company_id
        ):
            raise AppointmentRelatedEntityNotFoundException(
                "El servicio",
            )

        if not service.is_active:
            raise AppointmentRelatedEntityInactiveException(
                "El servicio",
            )

        return service

    def _validate_employee_service(
        self,
        employee: Employee,
        service: Service,
    ) -> None:
        employee_service_ids = {
            assigned_service.id
            for assigned_service in employee.services
        }

        if service.id not in employee_service_ids:
            raise EmployeeCannotPerformServiceException()

    def _validate_service_duration(
        self,
        service: Service,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        duration_minutes = service.duration_minutes

        if duration_minutes is None or duration_minutes <= 0:
            raise ServiceDurationUnavailableException()

        expected_duration = timedelta(
            minutes=duration_minutes
        )

        if end_at - start_at != expected_duration:
            raise ServiceDurationMismatchException(
                duration_minutes=duration_minutes,
            )

    def _validate_employee_availability(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: UUID | None = None,
    ) -> None:
        self._validate_within_work_schedule(
            company_id=company_id,
            employee_id=employee_id,
            start_at=start_at,
            end_at=end_at,
        )

        block = (
            self.appointment_repository
            .find_schedule_block_conflict(
                company_id=company_id,
                employee_id=employee_id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        if block is not None:
            raise AppointmentBlockedException()

        conflict = (
            self.appointment_repository
            .find_employee_conflict(
                company_id=company_id,
                employee_id=employee_id,
                start_at=start_at,
                end_at=end_at,
                exclude_appointment_id=exclude_appointment_id,
            )
        )

        if conflict is not None:
            raise AppointmentConflictException()

    def _validate_within_work_schedule(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        business_timezone = self._get_timezone(
            self.BUSINESS_TIMEZONE
        )

        local_start = start_at.astimezone(
            business_timezone
        )
        local_end = end_at.astimezone(
            business_timezone
        )

        if local_start.date() != local_end.date():
            raise AppointmentOutsideWorkScheduleException()

        schedules = (
            self.appointment_repository
            .get_active_work_schedules_for_weekday(
                company_id=company_id,
                employee_id=employee_id,
                weekday=local_start.weekday(),
            )
        )

        local_start_time = local_start.time().replace(
            tzinfo=None
        )
        local_end_time = local_end.time().replace(
            tzinfo=None
        )

        is_inside_schedule = any(
            schedule.start_time <= local_start_time
            and schedule.end_time >= local_end_time
            for schedule in schedules
        )

        if not is_inside_schedule:
            raise AppointmentOutsideWorkScheduleException()

    def _validate_time_range(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        if end_at <= start_at:
            raise InvalidAppointmentTimeException()

    def _validate_schedule_time_range(
        self,
        start_time: time,
        end_time: time,
    ) -> None:
        if end_time <= start_time:
            raise InvalidAppointmentTimeException()

    def _validate_not_in_past(
        self,
        start_at: datetime,
    ) -> None:
        current_time = datetime.now(timezone.utc)

        if start_at.astimezone(timezone.utc) <= current_time:
            raise AppointmentInPastException()

    def _validate_timezone_aware_datetime(
        self,
        value: datetime,
    ) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise InvalidTimezoneException(
                "datetime sin zona horaria"
            )

    def _validate_status_transition(
        self,
        current_status: AppointmentStatus,
        new_status: AppointmentStatus,
    ) -> None:
        if new_status == current_status:
            return

        allowed_statuses = self.ALLOWED_STATUS_TRANSITIONS[
            current_status
        ]

        if new_status not in allowed_statuses:
            raise InvalidAppointmentStatusException(
                detail=(
                    "No se permite cambiar una cita de "
                    f"'{current_status.value}' a "
                    f"'{new_status.value}'."
                ),
            )

    def _get_timezone(
        self,
        timezone_name: str,
    ) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)

        except ZoneInfoNotFoundError as error:
            raise InvalidTimezoneException(
                timezone_name
            ) from error

    def _ranges_overlap(
        self,
        first_start: datetime,
        first_end: datetime,
        second_start: datetime,
        second_end: datetime,
    ) -> bool:
        return (
            first_start < second_end
            and first_end > second_start
        )

    def _normalize_optional_text(
        self,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None