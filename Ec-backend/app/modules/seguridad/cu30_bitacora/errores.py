"""Jerarquia de excepciones de dominio para CU30: Consultar bitacora."""

from core.errors import AuthorizationError, NotFoundError


class EventoBitacoraNoEncontradoError(NotFoundError):
    """Lanzada cuando se solicita un registro de auditoria inexistente."""

    def __init__(self, id_bitacora: int) -> None:
        super().__init__(
            message=f"El evento de bitacora con ID {id_bitacora} no existe en los registros de auditoria.",
            code="BITACORA_NO_ENCONTRADA",
        )


class PermisoDenegadoBitacoraError(AuthorizationError):
    """Lanzada cuando un operador sin privilegios de superadministrador intenta acceder a la bitacora."""

    def __init__(self, rol_actual: str) -> None:
        super().__init__(
            message=(
                f"Acceso restringido a la bitacora de auditoria. Se requiere rol de superadministrador; "
                f"el rol actual '{rol_actual}' no dispone de autorizacion."
            ),
            code="PERMISO_DENEGADO_BITACORA",
        )
