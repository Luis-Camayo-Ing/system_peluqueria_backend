"""HTTP exceptions for the reports module."""

from fastapi import HTTPException, status


class ReportException(HTTPException):
    """Base exception for report validation errors."""


class InvalidReportPeriodException(ReportException):
    """Raised when the requested date range is invalid."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "La fecha final del reporte debe ser igual "
                "o posterior a la fecha inicial."
            ),
        )


class ReportPeriodTooLargeException(ReportException):
    """Raised when a report exceeds the supported range."""

    def __init__(self, maximum_days: int) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "El período solicitado no puede superar "
                f"{maximum_days} días."
            ),
        )


class InvalidReportTimezoneException(ReportException):
    """Raised when an unknown IANA timezone is supplied."""

    def __init__(self, timezone_name: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"La zona horaria '{timezone_name}' no es válida."
            ),
        )