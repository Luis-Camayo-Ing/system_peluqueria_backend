import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# Tabla intermedia para la relación muchos a muchos:
# un empleado puede realizar varios servicios
# y un servicio puede ser realizado por varios empleados.
employee_services = Table(
    "employee_services",
    Base.metadata,
    Column(
        "employee_id",
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "service_id",
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Employee(Base):
    __tablename__ = "employees"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "email",
            name="uq_employees_company_email",
        ),
        UniqueConstraint(
            "company_id",
            "attendance_code",
            name="uq_employees_company_attendance_code",
        ),
        UniqueConstraint(
            "company_id",
            "biometric_device_user_id",
            name="uq_employees_company_biometric_user",
        ),
        CheckConstraint(
            "salary IS NULL OR salary >= 0",
            name="ck_employees_salary_non_negative",
        ),
        CheckConstraint(
            """
            commission_percentage IS NULL
            OR (
                commission_percentage >= 0
                AND commission_percentage <= 100
            )
            """,
            name="ck_employees_commission_percentage",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    document_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    job_title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    salary: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    commission_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    hire_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    attendance_code: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    biometric_device_user_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    biometric_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship(
        "Company",
    )

    services = relationship(
        "Service",
        secondary=employee_services,
        backref="employees",
        lazy="selectin",
    )