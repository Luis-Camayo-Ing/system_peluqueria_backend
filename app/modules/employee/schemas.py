from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    document_number: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    job_title: str = Field(..., max_length=100)
    salary: Decimal | None = Field(default=None, ge=0)
    commission_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    hire_date: date | None = None
    attendance_code: str | None = Field(default=None, max_length=30)
    biometric_device_user_id: str | None = Field(
        default=None,
        max_length=100,
    )
    biometric_enabled: bool = False
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    company_id: UUID
    service_ids: list[UUID] = Field(default_factory=list)


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    document_number: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    job_title: str | None = Field(default=None, max_length=100)
    salary: Decimal | None = Field(default=None, ge=0)
    commission_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    hire_date: date | None = None
    attendance_code: str | None = Field(default=None, max_length=30)
    biometric_device_user_id: str | None = Field(
        default=None,
        max_length=100,
    )
    biometric_enabled: bool | None = None
    is_active: bool | None = None
    service_ids: list[UUID] | None = None


class EmployeeResponse(EmployeeBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)