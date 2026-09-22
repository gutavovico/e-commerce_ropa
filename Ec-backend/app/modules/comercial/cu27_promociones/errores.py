"""Jerarquia de excepciones semanticas de dominio para CU27: Gestionar promociones."""

from core.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    UnprocessableEntityError,
)


class PromocionError(DomainError):
    """Excepcion base para anomalias en el modulo de promociones."""
    pass


class PromocionNoEncontradaError(NotFoundError):
    """Lanzada cuando la promocion solicitada no existe (HTTP 404)."""

    def __init__(self, id_promocion: int):
        super().__init__(
            message=f"La promocion comercial con ID {id_promocion} no existe.",
            code="PROMOCION_NO_ENCONTRADA",
        )


class CodigoCuponDuplicadoError(ConflictError):
    """Lanzada cuando un codigo de cupon ya se encuentra en uso (HTTP 409)."""

    def __init__(self, codigo_cupon: str):
        super().__init__(
            message=f"El codigo de cupon '{codigo_cupon}' ya se encuentra registrado en otra campana.",
            code="CODIGO_CUPON_DUPLICADO",
        )


class FechasPromocionInvalidasError(UnprocessableEntityError):
    """Lanzada cuando la fecha fin no es posterior a la fecha inicio (HTTP 422)."""

    def __init__(
        self,
        detalle: str = "La fecha de culminacion debe ser estrictamente posterior a la fecha de inicio.",
    ):
        super().__init__(
            message=detalle,
            code="FECHAS_PROMOCION_INVALIDAS",
        )


class ValorDescuentoInvalidoError(UnprocessableEntityError):
    """Lanzada cuando el monto o porcentaje de descuento no es valido (HTTP 422)."""

    def __init__(
        self,
        detalle: str = "El valor o porcentaje de descuento especificado no es valido.",
    ):
        super().__init__(
            message=detalle,
            code="VALOR_DESCUENTO_INVALIDO",
        )


class AlcancePromocionInvalidoError(UnprocessableEntityError):
    """Lanzada cuando la categoria o producto asociado al alcance no existe (HTTP 422)."""

    def __init__(
        self,
        detalle: str = "La entidad referenciada para el alcance de la promocion no existe.",
    ):
        super().__init__(
            message=detalle,
            code="ALCANCE_PROMOCION_INVALIDO",
        )
