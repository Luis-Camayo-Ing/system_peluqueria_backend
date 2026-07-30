class EmployeeException(Exception):
    """Excepción base del módulo Employee."""


class EmployeeNotFoundException(EmployeeException):
    """El empleado no existe."""


class EmployeeEmailAlreadyExistsException(EmployeeException):
    """Ya existe un empleado con ese correo en la empresa."""


class EmployeeAttendanceCodeAlreadyExistsException(EmployeeException):
    """El código de asistencia ya existe."""


class EmployeeBiometricIdAlreadyExistsException(EmployeeException):
    """El identificador biométrico ya existe."""


class InvalidEmployeeServicesException(EmployeeException):
    """Uno o varios servicios no pertenecen a la empresa."""