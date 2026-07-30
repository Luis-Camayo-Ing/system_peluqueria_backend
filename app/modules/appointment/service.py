from datetime import datetime
from uuid import UUID

from app.modules.appointment.exceptions import (
    AppointmentAlreadyCancelledException,
    AppointmentConflictException,
    AppointmentNotFoundException,
    AppointmentRelatedEntityInactiveException,
    AppointmentRelatedEntityNotFoundException,
    EmployeeCannotPerformServiceException,
    InvalidAppointmentStatusException,
    InvalidAppointmentTimeException,
)
from app.modules.appointment.model import (
    Appointment,
    AppointmentStatus,
)
from app.modules.appointment.repository import AppointmentRepository
from app.modules.appointment.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentUpdate,
)
from app.modules.customer.model import Customer
from app.modules.customer.repository import CustomerRepository
from app.modules.employee.model import Employee
from app.modules.employee.repository import EmployeeRepository
from app.modules.service.model import Service
from app.modules.service.repository import ServiceRepository


class AppointmentService:
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

    def create_appointment(
        self,
        data: AppointmentCreate,
        company_id: UUID,
    ) -> Appointment:
        self._validate_time_range(
            start_at=data.start_at,
            end_at=data.end_at,
        )

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

        if appointment.status == AppointmentStatus.CANCELLED:
            raise AppointmentAlreadyCancelledException()

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

        target_status = new_status or appointment.status

        if target_status != AppointmentStatus.NO_SHOW:
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

    def cancel_appointment(
        self,
        appointment_id: UUID,
        company_id: UUID,
        data: AppointmentCancel,
    ) -> Appointment:
        appointment = self.get_appointment(
            appointment_id=appointment_id,
            company_id=company_id,
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

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = cancellation_reason

        return self.appointment_repository.update(appointment)

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
        employee = self.employee_repository.get_by_id(employee_id)

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
        service = self.service_repository.get_by_id(service_id)

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

    def _validate_employee_availability(
        self,
        company_id: UUID,
        employee_id: UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: UUID | None = None,
    ) -> None:
        conflict = (
            self.appointment_repository.find_employee_conflict(
                company_id=company_id,
                employee_id=employee_id,
                start_at=start_at,
                end_at=end_at,
                exclude_appointment_id=exclude_appointment_id,
            )
        )

        if conflict is not None:
            raise AppointmentConflictException()

    def _validate_time_range(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        if end_at <= start_at:
            raise InvalidAppointmentTimeException()

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
                    f"No se permite cambiar una cita de "
                    f"'{current_status.value}' a "
                    f"'{new_status.value}'."
                ),
            )