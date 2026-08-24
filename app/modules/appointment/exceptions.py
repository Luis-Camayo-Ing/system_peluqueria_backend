from fastapi import HTTPException, status


class AppointmentNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada.",
        )


class AppointmentConflictException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El empleado ya tiene una cita programada "
                "en ese rango de tiempo."
            ),
        )


class AppointmentAlreadyCancelledException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La cita ya se encuentra cancelada.",
        )


class AppointmentFinalizedException(HTTPException):
    def __init__(self, appointment_status: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La cita se encuentra en un estado final "
                f"('{appointment_status}') y no puede modificarse."
            ),
        )


class InvalidAppointmentStatusException(HTTPException):
    def __init__(
        self,
        detail: str = "El cambio de estado solicitado no está permitido.",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class AppointmentRelatedEntityNotFoundException(HTTPException):
    def __init__(self, entity_name: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"{entity_name} no existe o no pertenece "
                "a la empresa autenticada."
            ),
        )


class AppointmentRelatedEntityInactiveException(HTTPException):
    def __init__(self, entity_name: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity_name} se encuentra inactivo.",
        )


class EmployeeCannotPerformServiceException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El empleado seleccionado no tiene asignado "
                "el servicio solicitado."
            ),
        )


class InvalidAppointmentTimeException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La fecha y hora de finalización debe ser "
                "posterior a la fecha y hora de inicio."
            ),
        )


class WorkScheduleNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horario laboral no encontrado.",
        )


class WorkScheduleConflictException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El horario laboral se superpone con otro "
                "horario activo del empleado."
            ),
        )


class ScheduleBlockNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bloqueo de agenda no encontrado.",
        )


class ScheduleBlockConflictException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El bloqueo de agenda se superpone con otro "
                "bloqueo activo del empleado."
            ),
        )


class AppointmentOutsideWorkScheduleException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La cita solicitada se encuentra fuera del "
                "horario laboral del empleado."
            ),
        )


class AppointmentBlockedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El empleado tiene un bloqueo de agenda "
                "en el rango solicitado."
            ),
        )


class AppointmentInPastException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No es posible programar o reprogramar "
                "una cita en una fecha pasada."
            ),
        )


class InvalidTimezoneException(HTTPException):
    def __init__(self, timezone_name: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"La zona horaria '{timezone_name}' "
                "no es válida."
            ),
        )


class ServiceDurationUnavailableException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El servicio no tiene una duración válida "
                "configurada para calcular la disponibilidad."
            ),
        )


class ServiceDurationMismatchException(HTTPException):
    def __init__(self, duration_minutes: int) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La duración de la cita debe coincidir con "
                f"los {duration_minutes} minutos configurados "
                "para el servicio."
            ),
        )


class AppointmentReminderNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio de cita no encontrado.",
        )


class AppointmentReminderConflictException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un recordatorio para la misma cita, "
                "canal y fecha de envío."
            ),
        )


class InvalidAppointmentReminderTimeException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El recordatorio debe programarse para una fecha "
                "futura y anterior al inicio de la cita."
            ),
        )


class InvalidAppointmentReminderTransitionException(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )