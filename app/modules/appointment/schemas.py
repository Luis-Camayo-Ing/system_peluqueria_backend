import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.appointment.model import (
    AppointmentHistoryType,
    AppointmentStatus,
    ReminderChannel,
    ReminderStatus,
    ScheduleBlockType,
)


def validate_timezone_aware(
    value: datetime,
    field_name: str,
) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} debe incluir una zona horaria."
        )


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
        validate_timezone_aware(
            self.start_at,
            "start_at",
        )
        validate_timezone_aware(
            self.end_at,
            "end_at",
        )

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
        if self.start_at is not None:
            validate_timezone_aware(
                self.start_at,
                "start_at",
            )

        if self.end_at is not None:
            validate_timezone_aware(
                self.end_at,
                "end_at",
            )

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


class EmployeeWorkScheduleBase(BaseModel):
    employee_id: uuid.UUID

    weekday: int = Field(
        ge=0,
        le=6,
        description=(
            "Día de la semana: lunes=0, martes=1, "
            "miércoles=2, jueves=3, viernes=4, "
            "sábado=5 y domingo=6."
        ),
    )

    start_time: time
    end_time: time

    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_range(
        self,
    ) -> "EmployeeWorkScheduleBase":
        if self.end_time <= self.start_time:
            raise ValueError(
                "La hora de finalización debe ser posterior a la hora de inicio."
            )

        return self


class EmployeeWorkScheduleCreate(
    EmployeeWorkScheduleBase,
):
    pass


class EmployeeWorkScheduleUpdate(BaseModel):
    weekday: int | None = Field(
        default=None,
        ge=0,
        le=6,
    )

    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_time_range(
        self,
    ) -> "EmployeeWorkScheduleUpdate":
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError(
                "La hora de finalización debe ser posterior a la hora de inicio."
            )

        return self


class EmployeeWorkScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    employee_id: uuid.UUID

    weekday: int
    start_time: time
    end_time: time
    is_active: bool

    created_at: datetime
    updated_at: datetime


class EmployeeWorkScheduleListResponse(BaseModel):
    total: int
    items: list[EmployeeWorkScheduleResponse]


class EmployeeScheduleBlockBase(BaseModel):
    employee_id: uuid.UUID
    block_type: ScheduleBlockType

    start_at: datetime
    end_at: datetime

    reason: str | None = Field(
        default=None,
        max_length=500,
    )

    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_range(
        self,
    ) -> "EmployeeScheduleBlockBase":
        validate_timezone_aware(
            self.start_at,
            "start_at",
        )
        validate_timezone_aware(
            self.end_at,
            "end_at",
        )

        if self.end_at <= self.start_at:
            raise ValueError(
                "La fecha y hora de finalización debe ser posterior al inicio."
            )

        return self


class EmployeeScheduleBlockCreate(
    EmployeeScheduleBlockBase,
):
    pass


class EmployeeScheduleBlockUpdate(BaseModel):
    block_type: ScheduleBlockType | None = None

    start_at: datetime | None = None
    end_at: datetime | None = None

    reason: str | None = Field(
        default=None,
        max_length=500,
    )

    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_time_range(
        self,
    ) -> "EmployeeScheduleBlockUpdate":
        if self.start_at is not None:
            validate_timezone_aware(
                self.start_at,
                "start_at",
            )

        if self.end_at is not None:
            validate_timezone_aware(
                self.end_at,
                "end_at",
            )

        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError(
                "La fecha y hora de finalización debe ser posterior al inicio."
            )

        return self


class EmployeeScheduleBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    employee_id: uuid.UUID

    block_type: ScheduleBlockType

    start_at: datetime
    end_at: datetime

    reason: str | None
    is_active: bool

    created_at: datetime
    updated_at: datetime


class EmployeeScheduleBlockListResponse(BaseModel):
    total: int
    items: list[EmployeeScheduleBlockResponse]


class EmployeeAvailabilityRequest(BaseModel):
    employee_id: uuid.UUID
    service_id: uuid.UUID
    target_date: date

    timezone: str = Field(
        default="America/Bogota",
        min_length=1,
        max_length=100,
    )

    slot_interval_minutes: int = Field(
        default=15,
        ge=5,
        le=120,
    )


class AvailabilitySlot(BaseModel):
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def validate_time_range(
        self,
    ) -> "AvailabilitySlot":
        validate_timezone_aware(
            self.start_at,
            "start_at",
        )
        validate_timezone_aware(
            self.end_at,
            "end_at",
        )

        if self.end_at <= self.start_at:
            raise ValueError(
                "El final del intervalo debe ser posterior al inicio."
            )

        return self


class EmployeeAvailabilityResponse(BaseModel):
    employee_id: uuid.UUID
    service_id: uuid.UUID
    target_date: date
    timezone: str

    duration_minutes: int = Field(
        ge=1,
    )

    slots: list[AvailabilitySlot]


class AppointmentReschedule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None

    start_at: datetime
    end_at: datetime

    reason: str = Field(
        min_length=3,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_time_range(
        self,
    ) -> "AppointmentReschedule":
        validate_timezone_aware(
            self.start_at,
            "start_at",
        )
        validate_timezone_aware(
            self.end_at,
            "end_at",
        )

        if self.end_at <= self.start_at:
            raise ValueError(
                "La fecha y hora de finalización debe ser posterior al inicio."
            )

        return self


class AppointmentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    appointment_id: uuid.UUID
    changed_by_user_id: uuid.UUID | None

    change_type: AppointmentHistoryType

    previous_start_at: datetime | None
    previous_end_at: datetime | None
    new_start_at: datetime | None
    new_end_at: datetime | None

    previous_status: AppointmentStatus | None
    new_status: AppointmentStatus | None

    reason: str | None
    created_at: datetime


class AppointmentHistoryListResponse(BaseModel):
    total: int
    items: list[AppointmentHistoryResponse]


class AppointmentReminderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: ReminderChannel = ReminderChannel.INTERNAL
    remind_at: datetime

    @model_validator(mode="after")
    def validate_remind_at(
        self,
    ) -> "AppointmentReminderCreate":
        validate_timezone_aware(
            self.remind_at,
            "remind_at",
        )

        return self


class AppointmentReminderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ReminderStatus
    failure_message: str | None = Field(
        default=None,
        max_length=500,
    )


class AppointmentReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    appointment_id: uuid.UUID
    created_by_user_id: uuid.UUID | None

    channel: ReminderChannel
    remind_at: datetime
    status: ReminderStatus

    sent_at: datetime | None
    failure_message: str | None

    created_at: datetime
    updated_at: datetime


class AppointmentReminderListResponse(BaseModel):
    total: int
    items: list[AppointmentReminderResponse]