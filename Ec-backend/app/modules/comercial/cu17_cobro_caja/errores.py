"""Excepciones de dominio para CU17: Registrar cobro en caja."""

from core.errors import AuthorizationError, ConflictError, NotFoundError, UnprocessableEntityError


class VentaNoEncontradaError(NotFoundError):
    """Lanzada cuando el ID o comprobante de venta no existe en la base de datos."""

    def __init__(self, identificador: str | int):
        super().__init__(
            f"La orden #{identificador} no existe en el sistema.",
            code="VENTA_NO_ENCONTRADA",
        )


class MontoInsuficienteError(UnprocessableEntityError):
    """Lanzada cuando el dinero recibido es inferior al total facturado."""

    def __init__(self, monto_recibido: str | float, total_orden: str | float):
        super().__init__(
            f"El monto recibido ({monto_recibido} BOB) es inferior al total de la orden ({total_orden} BOB).",
            code="MONTO_INSUFICIENTE",
        )


class SucursalNoAutorizadaError(AuthorizationError):
    """Lanzada cuando un cajero intenta operar sobre una orden de otra sucursal."""

    def __init__(self, sucursal_orden: int, sucursal_usuario: int | None):
        super().__init__(
            f"Operacion restringida: la orden pertenece a la sucursal #{sucursal_orden}, "
            f"pero su usuario esta asignado a la sucursal #{sucursal_usuario}.",
            code="SUCURSAL_NO_AUTORIZADA",
        )


class VentaYaLiquidadaError(ConflictError):
    """Lanzada cuando la orden ya fue pagada con anterioridad."""

    def __init__(self, numero_comprobante: str):
        super().__init__(
            f"La orden {numero_comprobante} ya se encuentra liquidada y pagada.",
            code="VENTA_YA_LIQUIDADA",
        )


class VentaEstadoInvalidoError(ConflictError):
    """Lanzada cuando la orden se encuentra en un estado que no admite cobro (p. ej. anulada)."""

    def __init__(self, numero_comprobante: str, estado_actual: str):
        super().__init__(
            f"La orden {numero_comprobante} se encuentra en estado '{estado_actual}' y no admite cobro.",
            code="VENTA_ESTADO_INVALIDO",
        )


class MetodoPagoInvalidoError(UnprocessableEntityError):
    """Lanzada cuando el metodo de pago no es soportado por la caja."""

    def __init__(self, metodo: str):
        super().__init__(
            f"El metodo de pago '{metodo}' no es valido en terminal de caja. "
            "Metodos permitidos: efectivo, tarjeta_pos, qr_estatico.",
            code="METODO_PAGO_INVALIDO",
        )
