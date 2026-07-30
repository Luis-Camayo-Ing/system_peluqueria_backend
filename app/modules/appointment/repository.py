from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.appointment.model import (
    Appointment,
    AppointmentStatus,
)


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

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

    def update(
        self,
        appointment: Appointment,
    ) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)

        return appointment