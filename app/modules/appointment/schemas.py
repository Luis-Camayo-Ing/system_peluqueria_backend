import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.appointment.model import AppointmentStatus


class AppointmentBase(BaseModel):
    customer_id: uuid.UUID
    employee_id: uuid.UUID
    service_id: uuid.UUID

    start_at: datetime
    end_at: datetime

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    @model_validator(mode="after")
    def validate_time_range(self) -> "AppointmentBase":
        if self.end_at <= self.start_at:
            raise ValueError(
                "La fecha y hora de finalización debe ser posterior al inicio."
            )

        return self


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    employee_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None

    start_at: datetime | None = None
    end_at: datetime | None = None

    status: AppointmentStatus | None = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    cancellation_reason: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_time_range(self) -> "AppointmentUpdate":
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError(
                "La fecha y hora de finalización debe ser posterior al inicio."
            )

        return self


class AppointmentCancel(BaseModel):
    cancellation_reason: str = Field(
        min_length=3,
        max_length=500,
    )


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    employee_id: uuid.UUID
    service_id: uuid.UUID

    start_at: datetime
    end_at: datetime

    status: AppointmentStatus

    notes: str | None
    cancellation_reason: str | None

    created_at: datetime
    updated_at: datetime

class AppointmentListResponse(BaseModel):
    total: int
    items: list[AppointmentResponse]