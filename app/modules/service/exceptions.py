from fastapi import HTTPException, status


class ServiceNotFoundError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado.",
        )


class ServiceAlreadyExistsError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un servicio con ese nombre en la empresa.",
        )


class CompanyNotFoundForServiceError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La empresa asociada al servicio no existe.",
        )