"""Jerarquia de excepciones semanticas de dominio para CU24: Gestionar Inventario, Stock y Existencias por Sucursal."""

from core.errors import (
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    UnprocessableEntityError,
)


class InventarioError(DomainError):
    """Excepcion base para errores del modulo de inventario."""

    def __init__(self, message: str = "Error en modulo de inventario", code: str = "INVENTARIO_ERROR", status_code: int = 400):
        self.status_code = status_code
        super().__init__(message, code=code)


class InventarioNoEncontradoError(NotFoundError):
    """Lanzada cuando un registro de inventario no existe (HTTP 404)."""

    def __init__(self, id_inventario: int):
        self.status_code = 404
        super().__init__(
            f"El registro de inventario con ID {id_inventario} no fue encontrado.",
            code="INVENTARIO_NO_ENCONTRADO",
        )


class InventarioDuplicadoError(ConflictError):
    """Lanzada cuando ya existe inventario para la variante en la sucursal (HTTP 409)."""

    def __init__(self, id_sucursal: int, id_variante: int):
        self.status_code = 409
        super().__init__(
            f"Ya existe un inventario registrado para la variante {id_variante} en la sucursal {id_sucursal}. Utilice la funcion de ajuste.",
            code="INVENTARIO_DUPLICADO",
        )


class StockInsuficienteError(ConflictError):
    """Lanzada cuando el stock disponible es insuficiente para el decremento o traspaso (HTTP 409)."""

    def __init__(self, disponible: int, solicitado: int):
        self.status_code = 409
        super().__init__(
            f"Stock insuficiente para completar la operacion. Disponible: {disponible}, Solicitado: {solicitado}.",
            code="STOCK_INSUFICIENTE",
        )


class AutoTransferenciaError(UnprocessableEntityError):
    """Lanzada cuando se intenta transferir a la misma sucursal de origen (HTTP 422)."""

    def __init__(self):
        self.status_code = 422
        super().__init__(
            "No se puede transferir mercaderia a la misma sucursal de origen.",
            code="TRANSFERENCIA_MISMA_SUCURSAL",
        )


class MotivoInvalidoError(UnprocessableEntityError):
    """Lanzada cuando la justificacion del ajuste o transferencia no cumple criterios (HTTP 422)."""

    def __init__(self, detalle: str):
        self.status_code = 422
        super().__init__(
            f"Motivo de operacion invalido: {detalle}.",
            code="MOTIVO_OPERACION_INVALIDO",
        )


class SucursalNoAutorizadaError(AuthorizationError):
    """Lanzada cuando un encargado intenta operar sobre una sucursal ajena (HTTP 403)."""

    def __init__(self, id_sucursal_solicitada: int, id_sucursal_usuario: int):
        self.status_code = 403
        super().__init__(
            f"Acceso denegado: Su perfil solo le permite gestionar la sucursal {id_sucursal_usuario}, no la sucursal {id_sucursal_solicitada}.",
            code="SUCURSAL_NO_AUTORIZADA",
        )


class EntidadInactivaError(UnprocessableEntityError):
    """Lanzada cuando se intenta operar con una sucursal, producto o variante inactiva (HTTP 422)."""

    def __init__(self, entidad: str):
        self.status_code = 422
        super().__init__(
            f"No se puede operar inventario sobre una entidad inactiva o descontinuada: {entidad}.",
            code="ENTIDAD_INACTIVA_PARA_INVENTARIO",
        )


__all__ = [
    "InventarioError",
    "InventarioNoEncontradoError",
    "InventarioDuplicadoError",
    "StockInsuficienteError",
    "AutoTransferenciaError",
    "MotivoInvalidoError",
    "SucursalNoAutorizadaError",
    "EntidadInactivaError",
]
