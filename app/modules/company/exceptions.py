class CompanyError(Exception):
    """Excepción base del módulo de empresas."""


class CompanyNotFoundError(CompanyError):
    """Se genera cuando una empresa no existe."""


class CompanyAlreadyExistsError(CompanyError):
    """Se genera cuando ya existe una empresa con el mismo identificador fiscal."""