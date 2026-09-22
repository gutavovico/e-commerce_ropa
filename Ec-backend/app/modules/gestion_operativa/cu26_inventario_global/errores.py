"""Jerarquia de excepciones semanticas de dominio para CU26: Consultar inventario global."""

from core.errors import (
    DomainError,
    NotFoundError,
    UnprocessableEntityError,
)


class InventarioGlobalError(DomainError):
    """Excepcion base para errores del modulo de inventario global."""

    def __init__(self, message: str = "Error en modulo de inventario global", code: str = "INVENTARIO_GLOBAL_ERROR"):
        self.status_code = 400
        super().__init__(message, code=code)


class SucursalInvalidaConsultaError(NotFoundError):
    """Lanzada cuando el filtro id_sucursal especificado no existe o esta inactiva (HTTP 404)."""

    def __init__(self, id_sucursal: int):
        self.status_code = 404
        super().__init__(
            f"La sucursal con ID {id_sucursal} no existe o no se encuentra activa en el sistema.",
            code="SUCURSAL_NO_ENCONTRADA_O_INACTIVA",
        )


class CategoriaInvalidaConsultaError(NotFoundError):
    """Lanzada cuando el filtro id_categoria especificado no existe (HTTP 404)."""

    def __init__(self, id_categoria: int):
        self.status_code = 404
        super().__init__(
            f"La categoria con ID {id_categoria} no existe en el sistema.",
            code="CATEGORIA_NO_ENCONTRADA",
        )


class ParametroConsultaInvalidoError(UnprocessableEntityError):
    """Lanzada cuando un parametro de filtrado o paginacion viola las restricciones de dominio (HTTP 422)."""

    def __init__(self, detalle: str):
        self.status_code = 422
        super().__init__(detalle, code="PARAMETRO_CONSULTA_INVALIDO")
