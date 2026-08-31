from fastapi import HTTPException, status


class InventoryException(HTTPException):
    """Excepción base del módulo de inventario."""


# ==========================================================
# Product Category
# ==========================================================


class ProductCategoryNotFoundException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La categoría no existe.",
        )


class ProductCategoryAlreadyExistsException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con ese nombre.",
        )


class ProductCategoryInactiveException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría se encuentra inactiva.",
        )


# ==========================================================
# Products
# ==========================================================


class ProductNotFoundException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El producto no existe.",
        )


class ProductAlreadyExistsException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto con ese código.",
        )


class BarcodeAlreadyExistsException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="El código de barras ya está registrado.",
        )


class InvalidPriceException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los precios del producto son inválidos.",
        )


class InvalidStockException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El stock del producto es inválido.",
        )


class ProductInactiveException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El producto se encuentra inactivo.",
        )

class ProductCategoryHasProductsException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La categoría no puede eliminarse porque "
                "tiene productos asociados."
            ),
        )

class InventoryMovementNotFoundException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El movimiento de inventario no existe.",
        )


class InventoryMovementProductInactiveException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se pueden registrar movimientos "
                "para productos inactivos."
            ),
        )


class InsufficientStockException(InventoryException):
    def __init__(
        self,
        product_name: str | None = None,
    ):
        detail = "El producto no tiene stock suficiente."

        if product_name:
            detail = (
                f"El producto '{product_name}' "
                "no tiene stock suficiente."
            )

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class InvalidInventoryMovementTypeException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tipo de movimiento de inventario no es válido.",
        )


class InventoryMovementProcessingException(InventoryException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible procesar el movimiento "
                "de inventario."
            ),
        )