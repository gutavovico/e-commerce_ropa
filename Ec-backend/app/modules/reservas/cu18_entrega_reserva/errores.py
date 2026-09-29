"""Excepciones de dominio para CU18: Atender entrega de reserva en boutique."""

from core.errors import AuthorizationError, ConflictError, NotFoundError


class ReservaNoEncontradaError(NotFoundError):
    """Lanzada cuando el codigo o identificador de reserva no existe."""

    def __init__(self, identificador: str | int):
        super().__init__(
            f"La reserva #{identificador} no existe en el sistema.",
            code="RESERVA_NO_ENCONTRADA",
        )


class SucursalReservaNoAutorizadaError(AuthorizationError):
    """Lanzada cuando un cajero intenta gestionar una reserva de otra sucursal."""

    def __init__(self, sucursal_reserva: int, sucursal_usuario: int | None):
        super().__init__(
            f"Operacion restringida: la cita/reserva pertenece a la sucursal #{sucursal_reserva}, "
            f"pero su usuario esta asignado a la sucursal #{sucursal_usuario}.",
            code="SUCURSAL_NO_AUTORIZADA",
        )


class ReservaEstadoInvalidoError(ConflictError):
    """Lanzada cuando la reserva se encuentra en un estado que no admite la accion solicitada."""

    def __init__(self, codigo_reserva: str, estado_actual: str, accion: str):
        super().__init__(
            f"No es posible {accion} la reserva {codigo_reserva}: se encuentra en estado '{estado_actual}'.",
            code="RESERVA_ESTADO_INVALIDO",
        )
