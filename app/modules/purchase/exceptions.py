from fastapi import HTTPException, status


class PurchaseDomainException(HTTPException):
    """Base para errores controlados del módulo de compras."""


class PurchaseOrderNotFoundException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La orden de compra no existe.",
        )


class PurchaseOrderAlreadyExistsException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe una orden de compra con ese número "
                "dentro de la empresa."
            ),
        )


class PurchaseOrderNotEditableException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Solo las órdenes de compra en borrador "
                "pueden modificarse."
            ),
        )


class PurchaseOrderNotApprovableException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Solo las órdenes de compra en borrador "
                "pueden aprobarse."
            ),
        )


class PurchaseOrderNotCancellableException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La orden no puede cancelarse porque ya fue "
                "recibida total o parcialmente."
            ),
        )


class PurchaseOrderNotReceivableException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La orden debe estar aprobada o parcialmente "
                "recibida para registrar una recepción."
            ),
        )


class PurchaseOrderHasNoDetailsException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden de compra debe contener productos.",
        )


class PurchaseOrderDetailNotFoundException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Uno de los detalles no pertenece a la orden "
                "de compra indicada."
            ),
        )


class PurchaseReceiptNotFoundException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La recepción de compra no existe.",
        )


class PurchaseReceiptAlreadyExistsException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe una recepción con ese número "
                "dentro de la empresa."
            ),
        )


class PurchaseReceiptQuantityExceededException(
    PurchaseDomainException
):
    def __init__(
        self,
        product_name: str,
        pending_quantity: str,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"La cantidad recibida para '{product_name}' "
                f"supera la cantidad pendiente "
                f"({pending_quantity})."
            ),
        )


class PurchaseSupplierNotFoundException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El proveedor no existe.",
        )


class PurchaseSupplierInactiveException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El proveedor está inactivo y no puede utilizarse "
                "en una orden de compra."
            ),
        )


class PurchaseProductNotFoundException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno de los productos no existe.",
        )


class PurchaseProductInactiveException(PurchaseDomainException):
    def __init__(self, product_name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El producto '{product_name}' está inactivo "
                "y no puede utilizarse en compras."
            ),
        )


class PurchaseInvalidDiscountException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El descuento no puede superar el subtotal "
                "más los impuestos."
            ),
        )


class PurchaseOrderProcessingException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible procesar la orden de compra."
            ),
        )


class PurchaseReceiptProcessingException(PurchaseDomainException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible procesar la recepción de compra. "
                "No se aplicó ningún cambio al inventario."
            ),
        )