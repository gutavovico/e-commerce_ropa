"""Jerarquia de excepciones semanticas de dominio para CU28: Consultar ventas y reservas."""

from core.errors import AuthorizationError, DomainError, NotFoundError, UnprocessableEntityError


class VentasReservasError(DomainError):
    """Excepcion base para errores del modulo de ventas y reservas."""

    def __init__(
        self,
        message: str = "Error en consulta de ventas y reservas",
        code: str = "VENTAS_RESERVAS_ERROR",
    ):
        super().__init__(message, code=code)


class VentaNoEncontradaError(NotFoundError):
    """La transaccion de venta solicitada no existe (HTTP 404)."""

    def __init__(self, id_venta: int):
        super().__init__(
            message=f"La transaccion de venta con ID {id_venta} no fue localizada.",
            code="VENTA_NO_ENCONTRADA",
        )


class ReservaNoEncontradaError(NotFoundError):
    """La reserva solicitada no existe (HTTP 404)."""

    def __init__(self, id_reserva: int):
        super().__init__(
            message=f"La reserva con ID {id_reserva} no fue localizada.",
            code="RESERVA_NO_ENCONTRADA",
        )


class SucursalConsultaInvalidaError(AuthorizationError):
    """El encargado intenta acceder a transacciones de una sucursal no autorizada (HTTP 403)."""

    def __init__(
        self,
        message: str = "No cuenta con autorizacion para consultar transacciones de una sucursal distinta a su sede asignada.",
    ):
        super().__init__(
            message=message,
            code="SUCURSAL_NO_AUTORIZADA",
        )


class RangoFechasInvalidoError(UnprocessableEntityError):
    """El rango cronologico proporcionado es inconsistente (HTTP 422)."""

    def __init__(
        self,
        message: str = "La fecha_desde no puede ser cronologicamente posterior a fecha_hasta.",
    ):
        super().__init__(
            message=message,
            code="RANGO_FECHAS_INVALIDO",
        )
