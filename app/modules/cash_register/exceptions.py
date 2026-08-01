from fastapi import HTTPException, status


class CashRegisterException(HTTPException):
    """Excepción base del módulo de caja."""


# ==========================================================
# Cash Registers
# ==========================================================


class CashRegisterNotFoundException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La caja no existe.",
        )


class CashRegisterCodeAlreadyExistsException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una caja con ese código.",
        )


class CashRegisterNameAlreadyExistsException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una caja con ese nombre.",
        )


class CashRegisterInactiveException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La caja se encuentra inactiva.",
        )


class CashRegisterHasOpenSessionException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La caja no puede desactivarse porque "
                "tiene una sesión abierta."
            ),
        )


# ==========================================================
# Cash Sessions
# ==========================================================


class CashSessionNotFoundException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión de caja no existe.",
        )


class CashSessionAlreadyOpenException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La caja ya tiene una sesión abierta.",
        )


class CashSessionClosedException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión de caja ya se encuentra cerrada.",
        )


class CashSessionNotOpenException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión de caja no se encuentra abierta.",
        )


class CashSessionProcessingException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible procesar la sesión de caja.",
        )


# ==========================================================
# Cash Transactions
# ==========================================================


class CashTransactionNotFoundException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El movimiento de caja no existe.",
        )


class InvalidCashTransactionTypeException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tipo de movimiento de caja no es válido.",
        )


class InvalidCashAmountException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto del movimiento de caja no es válido.",
        )


class InsufficientCashException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="La caja no tiene saldo suficiente para registrar el egreso.",
        )


class CashTransactionProcessingException(CashRegisterException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible procesar el movimiento de caja.",
        )