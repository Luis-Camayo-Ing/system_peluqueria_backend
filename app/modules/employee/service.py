from uuid import UUID

from app.modules.company.repository import CompanyRepository
from app.modules.employee.exceptions import (
    EmployeeAttendanceCodeAlreadyExistsException,
    EmployeeBiometricIdAlreadyExistsException,
    EmployeeEmailAlreadyExistsException,
    EmployeeNotFoundException,
    InvalidEmployeeServicesException,
)
from app.modules.employee.model import Employee
from app.modules.employee.repository import EmployeeRepository
from app.modules.employee.schemas import EmployeeCreate, EmployeeUpdate


class EmployeeService:

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        company_repository: CompanyRepository,
    ):
        self.employee_repository = employee_repository
        self.company_repository = company_repository

    def create(self, data: EmployeeCreate) -> Employee:

        company = self.company_repository.get_by_id(data.company_id)

        if company is None:
            raise ValueError("La empresa no existe.")

        if data.email:
            employee = self.employee_repository.get_by_email(
                data.company_id,
                data.email,
            )

            if employee:
                raise EmployeeEmailAlreadyExistsException()

        if data.attendance_code:
            employee = self.employee_repository.get_by_attendance_code(
                data.company_id,
                data.attendance_code,
            )

            if employee:
                raise EmployeeAttendanceCodeAlreadyExistsException()

        if data.biometric_device_user_id:
            employee = self.employee_repository.get_by_biometric_user_id(
                data.company_id,
                data.biometric_device_user_id,
            )

            if employee:
                raise EmployeeBiometricIdAlreadyExistsException()

        employee = Employee(
            company_id=data.company_id,
            first_name=data.first_name,
            last_name=data.last_name,
            document_number=data.document_number,
            email=data.email,
            phone=data.phone,
            job_title=data.job_title,
            salary=data.salary,
            commission_percentage=data.commission_percentage,
            hire_date=data.hire_date,
            attendance_code=data.attendance_code,
            biometric_device_user_id=data.biometric_device_user_id,
            biometric_enabled=data.biometric_enabled,
            is_active=data.is_active,
        )

        services = self.employee_repository.get_services_by_ids(
            data.company_id,
            data.service_ids,
        )

        if len(services) != len(data.service_ids):
            raise InvalidEmployeeServicesException()

        employee.services = services

        return self.employee_repository.create(employee)

    def get_by_id(self, employee_id: UUID) -> Employee:

        employee = self.employee_repository.get_by_id(employee_id)

        if employee is None:
            raise EmployeeNotFoundException()

        return employee

    def get_all_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Employee]:

        return self.employee_repository.get_all_by_company(
            company_id,
            skip,
            limit,
        )

    def update(
        self,
        employee_id: UUID,
        data: EmployeeUpdate,
    ) -> Employee:

        employee = self.get_by_id(employee_id)

        values = data.model_dump(exclude_unset=True)

        if (
            "email" in values
            and values["email"]
            and values["email"] != employee.email
        ):
            existing = self.employee_repository.get_by_email(
                employee.company_id,
                values["email"],
            )

            if existing and existing.id != employee.id:
                raise EmployeeEmailAlreadyExistsException()

        if (
            "attendance_code" in values
            and values["attendance_code"]
            and values["attendance_code"] != employee.attendance_code
        ):
            existing = self.employee_repository.get_by_attendance_code(
                employee.company_id,
                values["attendance_code"],
            )

            if existing and existing.id != employee.id:
                raise EmployeeAttendanceCodeAlreadyExistsException()

        if (
            "biometric_device_user_id" in values
            and values["biometric_device_user_id"]
            and values["biometric_device_user_id"]
            != employee.biometric_device_user_id
        ):
            existing = self.employee_repository.get_by_biometric_user_id(
                employee.company_id,
                values["biometric_device_user_id"],
            )

            if existing and existing.id != employee.id:
                raise EmployeeBiometricIdAlreadyExistsException()

        service_ids = values.pop("service_ids", None)

        for key, value in values.items():
            setattr(employee, key, value)

        if service_ids is not None:
            services = self.employee_repository.get_services_by_ids(
                employee.company_id,
                service_ids,
            )

            if len(services) != len(service_ids):
                raise InvalidEmployeeServicesException()

            employee.services = services

        return self.employee_repository.update(employee)

    def delete(
        self,
        employee_id: UUID,
    ) -> None:

        employee = self.get_by_id(employee_id)

        self.employee_repository.delete(employee)