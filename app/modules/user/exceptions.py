class UserNotFoundError(Exception):
    """Se lanza cuando no existe el usuario solicitado."""

    def __init__(self, message: str = "Usuario no encontrado"):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsError(Exception):
    """Se lanza cuando ya existe un usuario con el mismo correo."""

    def __init__(self, message: str = "Ya existe un usuario con este correo"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(Exception):
    """Se lanza cuando el correo o la contraseña son incorrectos."""

    def __init__(self, message: str = "Credenciales inválidas"):
        self.message = message
        super().__init__(self.message)


class InactiveUserError(Exception):
    """Se lanza cuando un usuario inactivo intenta autenticarse."""

    def __init__(self, message: str = "El usuario está inactivo"):
        self.message = message
        super().__init__(self.message)