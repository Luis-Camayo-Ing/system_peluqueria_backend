from fastapi import HTTPException, status


class SupplierNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado.",
        )


class SupplierAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un proveedor con esa "
                "identificación fiscal."
            ),
        )