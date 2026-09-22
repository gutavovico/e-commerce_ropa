"""Jerarquia de excepciones semanticas de dominio para CU29.
Nomenclatura oficial: Visualizar indicadores empresariales
"""

from core.errors import AuthorizationError, DomainError, UnprocessableEntityError


class IndicadoresError(DomainError):
    """Excepcion base para errores del modulo de indicadores empresariales (HTTP 400)."""

    def __init__(
        self,
        message: str = "Error en consulta de indicadores empresariales.",
        code: str = "INDICADORES_ERROR",
    ):
        super().__init__(message, code=code)


class RangoTemporalInvalidoError(UnprocessableEntityError):
    """El rango cronologico proporcionado es inconsistente o incompleto (HTTP 422)."""

    def __init__(
        self,
        message: str = "El rango temporal es invalido: fecha_desde no puede ser posterior a fecha_hasta.",
    ):
        super().__init__(
            message=message,
            code="RANGO_TEMPORAL_INVALIDO",
        )


class AccesoComparativaDenegadoError(AuthorizationError):
    """El usuario no posee permisos para consultar la comparativa de rendimiento entre sucursales (HTTP 403)."""

    def __init__(
        self,
        message: str = "La comparativa de rendimiento entre sucursales es de acceso exclusivo para administradores corporativos.",
    ):
        super().__init__(
            message=message,
            code="ACCESO_COMPARATIVA_DENEGADO",
        )


class SucursalNoAutorizadaError(AuthorizationError):
    """El encargado de sucursal intenta acceder a indicadores de una sucursal distinta a la propia (HTTP 403)."""

    def __init__(
        self,
        message: str = "No cuenta con autorizacion para consultar indicadores analiticos de una sede distinta a su sucursal asignada.",
    ):
        super().__init__(
            message=message,
            code="SUCURSAL_NO_AUTORIZADA",
        )
