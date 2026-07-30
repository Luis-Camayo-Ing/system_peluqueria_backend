from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.service.model import Service


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, employee: Employee) -> Employee:
        """
        Guarda un nuevo empleado en la base de datos.
        """

        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)

        return employee

    def get_by_id(self, employee_id: UUID) -> Employee | None:
        """
        Busca un empleado por su identificador.
        """

        statement = select(Employee).where(
            Employee.id == employee_id
        )

        return self.db.scalar(statement)

    def get_by_email(
        self,
        company_id: UUID,
        email: str,
    ) -> Employee | None:
        """
        Busca un empleado por correo dentro de una empresa.
        """

        statement = select(Employee).where(
            Employee.company_id == company_id,
            Employee.email == email,
        )

        return self.db.scalar(statement)

    def get_by_attendance_code(
        self,
        company_id: UUID,
        attendance_code: str,
    ) -> Employee | None:
        """
        Busca un empleado por su código de asistencia.
        """

        statement = select(Employee).where(
            Employee.company_id == company_id,
            Employee.attendance_code == attendance_code,
        )

        return self.db.scalar(statement)

    def get_by_biometric_user_id(
        self,
        company_id: UUID,
        biometric_device_user_id: str,
    ) -> Employee | None:
        """
        Busca un empleado por el identificador asignado
        en el dispositivo biométrico.
        """

        statement = select(Employee).where(
            Employee.company_id == company_id,
            Employee.biometric_device_user_id
            == biometric_device_user_id,
        )

        return self.db.scalar(statement)

    def get_all_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Employee]:
        """
        Lista los empleados pertenecientes a una empresa.
        """

        statement = (
            select(Employee)
            .where(Employee.company_id == company_id)
            .order_by(
                Employee.first_name,
                Employee.last_name,
            )
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_services_by_ids(
        self,
        company_id: UUID,
        service_ids: list[UUID],
    ) -> list[Service]:
        """
        Obtiene los servicios indicados y verifica que
        pertenezcan a la misma empresa del empleado.
        """

        if not service_ids:
            return []

        statement = select(Service).where(
            Service.company_id == company_id,
            Service.id.in_(service_ids),
        )

        return list(self.db.scalars(statement).all())

    def update(self, employee: Employee) -> Employee:
        """
        Guarda los cambios realizados sobre un empleado.
        """

        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)

        return employee

    def delete(self, employee: Employee) -> None:
        """
        Elimina un empleado de la base de datos.
        """

        self.db.delete(employee)
        self.db.commit()