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