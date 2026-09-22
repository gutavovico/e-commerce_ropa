"""Jerarquia de excepciones de dominio para CU25: Gestionar Proveedores."""

from core.errors import ConflictError, DomainError, NotFoundError


class ProveedorNoEncontradoError(NotFoundError):
    """Lanzada cuando un id_proveedor solicitado no existe en la base de datos (HTTP 404)."""

    def __init__(self, id_proveedor: int):
        super().__init__(f"No se encontro ningun proveedor registrado con el ID {id_proveedor}.")


class ProveedorDuplicadoError(ConflictError):
    """Lanzada cuando se intenta registrar o actualizar con un NIT/RUT o Razon Social ya ocupada (HTTP 409)."""

    def __init__(self, campo: str, valor: str):
        super().__init__(f"Ya existe un proveedor registrado con el {campo} '{valor}'.")


class ProveedorInvalidoError(DomainError):
    """Lanzada cuando los datos comerciales incumplen reglas de negocio de la cadena (HTTP 422)."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
