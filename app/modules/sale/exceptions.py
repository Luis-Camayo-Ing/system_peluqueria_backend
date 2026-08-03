"""Domain exceptions for sales and point-of-sale operations."""

from fastapi import HTTPException, status


class SaleDomainException(HTTPException):
    """Base exception for expected sale business errors."""


class SaleNotFoundException(SaleDomainException):
    """Raised when the requested sale does not exist."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La venta solicitada no existe.",
        )


class SaleAlreadyExistsException(SaleDomainException):
    """Raised when a sale number already exists."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe una venta con ese número "
                "dentro de la empresa."
            ),
        )


class SaleAlreadyCancelledException(SaleDomainException):
    """Raised when attempting to cancel an already cancelled sale."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La venta ya se encuentra cancelada.",
        )


class SaleCompanyNotFoundException(SaleDomainException):
    """Raised when the company cannot be found."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La empresa asociada a la venta no existe.",
        )


class SaleCompanyInactiveException(SaleDomainException):
    """Raised when attempting to sell for an inactive company."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La empresa se encuentra inactiva.",
        )


class SaleCustomerNotFoundException(SaleDomainException):
    """Raised when the selected customer does not exist."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente seleccionado no existe.",
        )


class SaleCustomerInactiveException(SaleDomainException):
    """Raised when the selected customer is inactive."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cliente seleccionado se encuentra inactivo.",
        )


class SaleCashSessionNotFoundException(SaleDomainException):
    """Raised when the cash session cannot be found."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión de caja seleccionada no existe.",
        )


class SaleCashSessionClosedException(SaleDomainException):
    """Raised when the sale uses a closed cash session."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La sesión de caja se encuentra cerrada "
                "y no permite registrar ventas."
            ),
        )


class SaleCashSessionNotOpenException(SaleDomainException):
    """Raised when the cash session is not open."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La sesión de caja debe encontrarse abierta "
                "para registrar la venta."
            ),
        )


class SaleCancellationCashSessionClosedException(
    SaleDomainException
):
    """Raised when cancelling a sale from a closed session."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La venta no puede cancelarse porque su sesión "
                "de caja ya se encuentra cerrada."
            ),
        )


class SaleProductNotFoundException(SaleDomainException):
    """Raised when a product does not exist."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno de los productos seleccionados no existe.",
        )


class SaleProductInactiveException(SaleDomainException):
    """Raised when an inactive product is included."""

    def __init__(
        self,
        product_name: str,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El producto '{product_name}' "
                "se encuentra inactivo."
            ),
        )


class SaleServiceNotFoundException(SaleDomainException):
    """Raised when a service does not exist."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno de los servicios seleccionados no existe.",
        )


class SaleServiceInactiveException(SaleDomainException):
    """Raised when an inactive service is included."""

    def __init__(
        self,
        service_name: str,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El servicio '{service_name}' "
                "se encuentra inactivo."
            ),
        )


class SaleInsufficientStockException(SaleDomainException):
    """Raised when a product has insufficient stock."""

    def __init__(
        self,
        product_name: str,
        requested_quantity: str,
        available_quantity: str,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stock insuficiente para '{product_name}'. "
                f"Cantidad solicitada: {requested_quantity}. "
                f"Cantidad disponible: {available_quantity}."
            ),
        )


class SaleDiscountExceededException(SaleDomainException):
    """Raised when a discount exceeds the line subtotal."""

    def __init__(
        self,
        item_name: str,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El descuento aplicado a '{item_name}' "
                "supera el subtotal del detalle."
            ),
        )


class SalePaymentTotalMismatchException(SaleDomainException):
    """Raised when payments do not match the sale total."""

    def __init__(
        self,
        sale_total: str,
        payment_total: str,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La suma de los pagos debe ser igual "
                "al total de la venta. "
                f"Total de venta: {sale_total}. "
                f"Total de pagos: {payment_total}."
            ),
        )


class SaleInvalidCashPaymentException(SaleDomainException):
    """Raised when cash payment values are inconsistent."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Los valores del pago en efectivo "
                "no permiten calcular correctamente el cambio."
            ),
        )


class SaleInvalidTotalException(SaleDomainException):
    """Raised when the calculated sale total is not positive."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="El total de la venta debe ser mayor que cero.",
        )


class SaleInsufficientCashForRefundException(
    SaleDomainException
):
    """Raised when the session cannot cover a cash refund."""

    def __init__(
        self,
        available_amount: str,
        refund_amount: str,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La caja no dispone de suficiente efectivo "
                "para cancelar la venta. "
                f"Efectivo disponible: {available_amount}. "
                f"Reembolso requerido: {refund_amount}."
            ),
        )


class SaleProcessingException(HTTPException):
    """Raised when an unexpected error prevents sale completion."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible completar la venta. "
                "La operación fue revertida."
            ),
        )


class SaleCancellationProcessingException(HTTPException):
    """Raised when an unexpected error prevents cancellation."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible cancelar la venta. "
                "La operación fue revertida."
            ),
        )


class SaleReceiptGenerationException(HTTPException):
    """Raised when the PDF receipt cannot be generated."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible generar el comprobante en PDF.",
        )


class SaleReceiptRecipientRequiredException(
    HTTPException
):
    """Raised when no receipt email recipient is available."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Debe proporcionar un correo destinatario "
                "o la venta debe tener un correo del cliente."
            ),
        )


class SaleEmailConfigurationException(HTTPException):
    """Raised when SMTP delivery is not configured."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El servicio de correo no se encuentra "
                "configurado correctamente."
            ),
        )


class SaleEmailSendingException(HTTPException):
    """Raised when the receipt email cannot be delivered."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "No fue posible enviar el comprobante "
                "por correo electrónico."
            ),
        )
