from datetime import datetime, time
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.appointment.model import (
    Appointment,
    AppointmentHistory,
    AppointmentReminder,
    AppointmentStatus,
    EmployeeScheduleBlock,
    EmployeeWorkSchedule,
    ReminderChannel,
    ReminderStatus,
    ScheduleBlockType,
)


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def lock_employee_agenda(
        self,
        employee_id: UUID,
    ) -> None:
        """Serializa las operaciones que afectan la agenda del empleado."""
        lock_key = employee_id.int & ((1 << 63) - 1)

        self.db.execute(
            select(func.pg_advisory_xact_lock(lock_key))
        )

    def lock_appointment(
        self,
        appointment_id: UUID,
    ) -> None:
        """Serializa los cambios de una cita y sus recordatorios."""
        lock_key = appointment_id.int & ((1 << 63) - 1)

        self.db.execute(
            select(func.pg_advisory_xact_lock(lock_key))
        )

    def refresh_appointment(
        self,
        appointment: Appointment,
    ) -> Appointment:
        self.db.refresh(appointment)

        return appointment

    def create(
        self,
        appointment: Appointment,
    ) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def get_by_id(
        self,
        appointment_id: UUID,
        company_id: UUID,
    ) -> Appointment | None:
        statement = select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.company_id == company_id,
        )

        return self.db.scalar(statement)

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
    ) -> list[Appointment]:
        statement = select(Appointment).where(
            Appointment.company_id == company_id
        )

        if start_at is not None:
            statement = statement.where(
                Appointment.end_at > start_at
            )

        if end_at is not None:
            statement = statement.where(
                Appointment.start_at < end_at
            )

        if customer_id is not None:
            statement = statement.where(
                Appointment.customer_id == customer_id
            )

        if employee_id is not None:
            statement = statement.where(
                Appointment.employee_id == employee_id
            )

        if service_id is not None:
            statement = statement.where(
                Appointment.service_id == service_id
            )

        if status is not None:
            statement = statement.where(
                Appointment.status == status
            )

        statement = (
            statement
            .order_by(Appointment.start_at.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_appointments(
        self,
        company_id: UUID,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        customer_id: UUID | None = None,
        employee_id: UUID | None = None,
        service_id: UUID | None = None,
        status: AppointmentStatus | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.company_id == company_id)
        )

        if start_at is not None:
            statement = statement.where(
                Appointment.end_at > start_at
            )

        if end_at is not None:
            statement = statement.where(
                Appointment.start_at < end_at
            )

        if customer_id is not None:
            statement = statement.where(
                Appointment.customer_id == customer_id
            )

        if employee_id is not None:
            statement = statement.where(
                Appointment.employee_id == employee_id
            )

        if service_id is not None:
            statement = statement.where(
                Appointment.service_id == service_id
            )

        if status is not None:
            statement = statement.where(
                Appointment.status == status
            )

        return self.db.scalar(statement) or 0

    def find_employee_conflict(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: UUID | None = None,
    ) -> Appointment | None:
        statement = select(Appointment).where(
            Appointment.company_id == company_id,
            Appointment.employee_id == employee_id,
            Appointment.status.notin_(
                [
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW,
                ]
            ),
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
        )

        if exclude_appointment_id is not None:
            statement = statement.where(
                Appointment.id != exclude_appointment_id
            )

        return self.db.scalar(statement)

    def list_employee_appointments_in_range(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list[Appointment]:
        statement = (
            select(Appointment)
            .where(
                Appointment.company_id == company_id,
                Appointment.employee_id == employee_id,
                Appointment.status.notin_(
                    [
                        AppointmentStatus.CANCELLED,
                        AppointmentStatus.NO_SHOW,
                    ]
                ),
                Appointment.start_at < end_at,
                Appointment.end_at > start_at,
            )
            .order_by(Appointment.start_at.asc())
        )

        return list(self.db.scalars(statement).all())

    def update(
        self,
        appointment: Appointment,
    ) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def create_work_schedule(
        self,
        schedule: EmployeeWorkSchedule,
    ) -> EmployeeWorkSchedule:
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        return schedule

    def get_work_schedule_by_id(
        self,
        schedule_id: UUID,
        company_id: UUID,
    ) -> EmployeeWorkSchedule | None:
        statement = select(EmployeeWorkSchedule).where(
            EmployeeWorkSchedule.id == schedule_id,
            EmployeeWorkSchedule.company_id == company_id,
        )

        return self.db.scalar(statement)

    def list_work_schedules(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        employee_id: UUID | None = None,
        weekday: int | None = None,
        is_active: bool | None = None,
    ) -> list[EmployeeWorkSchedule]:
        statement = select(EmployeeWorkSchedule).where(
            EmployeeWorkSchedule.company_id == company_id
        )

        if employee_id is not None:
            statement = statement.where(
                EmployeeWorkSchedule.employee_id == employee_id
            )

        if weekday is not None:
            statement = statement.where(
                EmployeeWorkSchedule.weekday == weekday
            )

        if is_active is not None:
            statement = statement.where(
                EmployeeWorkSchedule.is_active == is_active
            )

        statement = (
            statement
            .order_by(
                EmployeeWorkSchedule.weekday.asc(),
                EmployeeWorkSchedule.start_time.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_work_schedules(
        self,
        company_id: UUID,
        employee_id: UUID | None = None,
        weekday: int | None = None,
        is_active: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(EmployeeWorkSchedule)
            .where(
                EmployeeWorkSchedule.company_id == company_id
            )
        )

        if employee_id is not None:
            statement = statement.where(
                EmployeeWorkSchedule.employee_id == employee_id
            )

        if weekday is not None:
            statement = statement.where(
                EmployeeWorkSchedule.weekday == weekday
            )

        if is_active is not None:
            statement = statement.where(
                EmployeeWorkSchedule.is_active == is_active
            )

        return self.db.scalar(statement) or 0

    def find_work_schedule_conflict(
        self,
        company_id: UUID,
        employee_id: UUID,
        weekday: int,
        start_time: time,
        end_time: time,
        exclude_schedule_id: UUID | None = None,
    ) -> EmployeeWorkSchedule | None:
        statement = select(EmployeeWorkSchedule).where(
            EmployeeWorkSchedule.company_id == company_id,
            EmployeeWorkSchedule.employee_id == employee_id,
            EmployeeWorkSchedule.weekday == weekday,
            EmployeeWorkSchedule.is_active.is_(True),
            EmployeeWorkSchedule.start_time < end_time,
            EmployeeWorkSchedule.end_time > start_time,
        )

        if exclude_schedule_id is not None:
            statement = statement.where(
                EmployeeWorkSchedule.id != exclude_schedule_id
            )

        return self.db.scalar(statement)

    def get_active_work_schedules_for_weekday(
        self,
        company_id: UUID,
        employee_id: UUID,
        weekday: int,
    ) -> list[EmployeeWorkSchedule]:
        statement = (
            select(EmployeeWorkSchedule)
            .where(
                EmployeeWorkSchedule.company_id == company_id,
                EmployeeWorkSchedule.employee_id == employee_id,
                EmployeeWorkSchedule.weekday == weekday,
                EmployeeWorkSchedule.is_active.is_(True),
            )
            .order_by(EmployeeWorkSchedule.start_time.asc())
        )

        return list(self.db.scalars(statement).all())

    def update_work_schedule(
        self,
        schedule: EmployeeWorkSchedule,
    ) -> EmployeeWorkSchedule:
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        return schedule

    def create_schedule_block(
        self,
        block: EmployeeScheduleBlock,
    ) -> EmployeeScheduleBlock:
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)

        return block

    def get_schedule_block_by_id(
        self,
        block_id: UUID,
        company_id: UUID,
    ) -> EmployeeScheduleBlock | None:
        statement = select(EmployeeScheduleBlock).where(
            EmployeeScheduleBlock.id == block_id,
            EmployeeScheduleBlock.company_id == company_id,
        )

        return self.db.scalar(statement)

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
    ) -> list[EmployeeScheduleBlock]:
        statement = select(EmployeeScheduleBlock).where(
            EmployeeScheduleBlock.company_id == company_id
        )

        if employee_id is not None:
            statement = statement.where(
                EmployeeScheduleBlock.employee_id == employee_id
            )

        if block_type is not None:
            statement = statement.where(
                EmployeeScheduleBlock.block_type == block_type
            )

        if start_at is not None:
            statement = statement.where(
                EmployeeScheduleBlock.end_at > start_at
            )

        if end_at is not None:
            statement = statement.where(
                EmployeeScheduleBlock.start_at < end_at
            )

        if is_active is not None:
            statement = statement.where(
                EmployeeScheduleBlock.is_active == is_active
            )

        statement = (
            statement
            .order_by(EmployeeScheduleBlock.start_at.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_schedule_blocks(
        self,
        company_id: UUID,
        employee_id: UUID | None = None,
        block_type: ScheduleBlockType | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        is_active: bool | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(EmployeeScheduleBlock)
            .where(
                EmployeeScheduleBlock.company_id == company_id
            )
        )

        if employee_id is not None:
            statement = statement.where(
                EmployeeScheduleBlock.employee_id == employee_id
            )

        if block_type is not None:
            statement = statement.where(
                EmployeeScheduleBlock.block_type == block_type
            )

        if start_at is not None:
            statement = statement.where(
                EmployeeScheduleBlock.end_at > start_at
            )

        if end_at is not None:
            statement = statement.where(
                EmployeeScheduleBlock.start_at < end_at
            )

        if is_active is not None:
            statement = statement.where(
                EmployeeScheduleBlock.is_active == is_active
            )

        return self.db.scalar(statement) or 0

    def find_schedule_block_conflict(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_block_id: UUID | None = None,
    ) -> EmployeeScheduleBlock | None:
        statement = select(EmployeeScheduleBlock).where(
            EmployeeScheduleBlock.company_id == company_id,
            EmployeeScheduleBlock.employee_id == employee_id,
            EmployeeScheduleBlock.is_active.is_(True),
            EmployeeScheduleBlock.start_at < end_at,
            EmployeeScheduleBlock.end_at > start_at,
        )

        if exclude_block_id is not None:
            statement = statement.where(
                EmployeeScheduleBlock.id != exclude_block_id
            )

        return self.db.scalar(statement)

    def list_active_schedule_blocks_in_range(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list[EmployeeScheduleBlock]:
        statement = (
            select(EmployeeScheduleBlock)
            .where(
                EmployeeScheduleBlock.company_id == company_id,
                EmployeeScheduleBlock.employee_id == employee_id,
                EmployeeScheduleBlock.is_active.is_(True),
                EmployeeScheduleBlock.start_at < end_at,
                EmployeeScheduleBlock.end_at > start_at,
            )
            .order_by(EmployeeScheduleBlock.start_at.asc())
        )

        return list(self.db.scalars(statement).all())

    def update_schedule_block(
        self,
        block: EmployeeScheduleBlock,
    ) -> EmployeeScheduleBlock:
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)

        return block

    def update_with_history(
        self,
        appointment: Appointment,
        history: AppointmentHistory,
    ) -> Appointment:
        self.db.add(appointment)
        self.db.add(history)
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def list_appointment_history(
        self,
        company_id: UUID,
        appointment_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AppointmentHistory]:
        statement = (
            select(AppointmentHistory)
            .where(
                AppointmentHistory.company_id == company_id,
                AppointmentHistory.appointment_id == appointment_id,
            )
            .order_by(AppointmentHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_appointment_history(
        self,
        company_id: UUID,
        appointment_id: UUID,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(AppointmentHistory)
            .where(
                AppointmentHistory.company_id == company_id,
                AppointmentHistory.appointment_id == appointment_id,
            )
        )

        return self.db.scalar(statement) or 0

    def create_reminder(
        self,
        reminder: AppointmentReminder,
    ) -> AppointmentReminder:
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def get_reminder_by_id(
        self,
        reminder_id: UUID,
        company_id: UUID,
    ) -> AppointmentReminder | None:
        statement = select(AppointmentReminder).where(
            AppointmentReminder.id == reminder_id,
            AppointmentReminder.company_id == company_id,
        )

        return self.db.scalar(statement)

    def find_reminder_duplicate(
        self,
        company_id: UUID,
        appointment_id: UUID,
        channel: ReminderChannel,
        remind_at: datetime,
    ) -> AppointmentReminder | None:
        statement = select(AppointmentReminder).where(
            AppointmentReminder.company_id == company_id,
            AppointmentReminder.appointment_id == appointment_id,
            AppointmentReminder.channel == channel,
            AppointmentReminder.remind_at == remind_at,
        )

        return self.db.scalar(statement)

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
    ) -> list[AppointmentReminder]:
        statement = (
            select(AppointmentReminder)
            .join(
                Appointment,
                Appointment.id == AppointmentReminder.appointment_id,
            )
            .where(
                AppointmentReminder.company_id == company_id,
                Appointment.company_id == company_id,
            )
        )

        statement = self._apply_reminder_filters(
            statement=statement,
            appointment_id=appointment_id,
            employee_id=employee_id,
            channel=channel,
            status=status,
            remind_from=remind_from,
            remind_until=remind_until,
        )

        statement = (
            statement
            .order_by(AppointmentReminder.remind_at.asc())
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_reminders(
        self,
        company_id: UUID,
        appointment_id: UUID | None = None,
        employee_id: UUID | None = None,
        channel: ReminderChannel | None = None,
        status: ReminderStatus | None = None,
        remind_from: datetime | None = None,
        remind_until: datetime | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(AppointmentReminder)
            .join(
                Appointment,
                Appointment.id == AppointmentReminder.appointment_id,
            )
            .where(
                AppointmentReminder.company_id == company_id,
                Appointment.company_id == company_id,
            )
        )

        statement = self._apply_reminder_filters(
            statement=statement,
            appointment_id=appointment_id,
            employee_id=employee_id,
            channel=channel,
            status=status,
            remind_from=remind_from,
            remind_until=remind_until,
        )

        return self.db.scalar(statement) or 0

    def update_reminder(
        self,
        reminder: AppointmentReminder,
    ) -> AppointmentReminder:
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def refresh_reminder(
        self,
        reminder: AppointmentReminder,
    ) -> AppointmentReminder:
        self.db.refresh(reminder)

        return reminder

    def cancel_pending_reminders(
        self,
        appointment_id: UUID,
        at_or_after: datetime | None = None,
    ) -> None:
        statement = (
            update(AppointmentReminder)
            .where(
                AppointmentReminder.appointment_id == appointment_id,
                AppointmentReminder.status == ReminderStatus.PENDING,
            )
            .values(
                status=ReminderStatus.CANCELLED,
                failure_message=None,
            )
        )

        if at_or_after is not None:
            statement = statement.where(
                AppointmentReminder.remind_at >= at_or_after
            )

        self.db.execute(statement)

    def _apply_reminder_filters(
        self,
        statement,
        appointment_id: UUID | None,
        employee_id: UUID | None,
        channel: ReminderChannel | None,
        status: ReminderStatus | None,
        remind_from: datetime | None,
        remind_until: datetime | None,
    ):
        if appointment_id is not None:
            statement = statement.where(
                AppointmentReminder.appointment_id == appointment_id
            )

        if employee_id is not None:
            statement = statement.where(
                Appointment.employee_id == employee_id
            )

        if channel is not None:
            statement = statement.where(
                AppointmentReminder.channel == channel
            )

        if status is not None:
            statement = statement.where(
                AppointmentReminder.status == status
            )

        if remind_from is not None:
            statement = statement.where(
                AppointmentReminder.remind_at >= remind_from
            )

        if remind_until is not None:
            statement = statement.where(
                AppointmentReminder.remind_at <= remind_until
            )

        return statement