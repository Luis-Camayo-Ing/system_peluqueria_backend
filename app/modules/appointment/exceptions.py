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