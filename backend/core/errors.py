"""Jerarquia de excepciones de dominio de FashionStore.

Cada excepcion se traduce a un codigo HTTP en main.py mediante exception handlers.
Los services lanzan estas excepciones; los routers no las atrapan directamente.
"""


class DomainError(Exception):
    """Base para todas las excepciones de dominio."""

    def __init__(self, message: str = "Error de dominio", code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(DomainError):
    """Recurso no encontrado (HTTP 404)."""

    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, code="NOT_FOUND")


class ConflictError(DomainError):
    """Conflicto de estado o unicidad (HTTP 409)."""

    def __init__(self, message: str = "Conflicto"):
        super().__init__(message, code="CONFLICT")


class AuthenticationError(DomainError):
    """Token ausente, invalido o expirado (HTTP 401)."""

    def __init__(self, message: str = "No autenticado"):
        super().__init__(message, code="NOT_AUTHENTICATED")


class AuthorizationError(DomainError):
    """Rol o alcance insuficiente (HTTP 403)."""

    def __init__(self, message: str = "Sin permiso"):
        super().__init__(message, code="FORBIDDEN")
