"""Excepciones de dominio para el caso de uso CU21: Gestionar Sucursales y Ciudades.

Todas las excepciones heredan de la jerarquia de core.errors para ser
traducidas directamente a respuestas JSON y codigos de estado HTTP.
"""

from core.errors import ConflictError, DomainError, NotFoundError


class CiudadDuplicadaError(ConflictError):
    """Lanzada cuando se intenta crear o renombrar una ciudad a un nombre ya existente."""

    def __init__(self, nombre: str):
        super().__init__(
            message=f"La ciudad '{nombre}' ya se encuentra registrada en el sistema.",
            code="CIUDAD_DUPLICADA",
        )


class CiudadNoEncontradaError(NotFoundError):
    """Lanzada cuando el identificador de ciudad no existe en la base de datos."""

    def __init__(self, id_ciudad: int):
        super().__init__(
            message=f"La ciudad con identificador {id_ciudad} no existe.",
            code="CIUDAD_NO_ENCONTRADA",
        )


class CiudadConDependenciasError(ConflictError):
    """Lanzada cuando se intenta eliminar una ciudad que tiene sucursales o clientes asignados."""

    def __init__(self, id_ciudad: int, detalle: str):
        super().__init__(
            message=f"No se puede eliminar la ciudad {id_ciudad}: {detalle}.",
            code="CIUDAD_CON_DEPENDENCIAS_ACTIVAS",
        )


class SucursalDuplicadaError(ConflictError):
    """Lanzada cuando ya existe una sucursal con el mismo nombre en la ciudad indicada."""

    def __init__(self, nombre: str, id_ciudad: int):
        super().__init__(
            message=f"Ya existe una boutique con el nombre '{nombre}' en la ciudad {id_ciudad}.",
            code="SUCURSAL_DUPLICADA",
        )


class SucursalNoEncontradaError(NotFoundError):
    """Lanzada cuando el identificador de sucursal no existe en la base de datos."""

    def __init__(self, id_sucursal: int):
        super().__init__(
            message=f"La sucursal con identificador {id_sucursal} no fue encontrada.",
            code="SUCURSAL_NO_ENCONTRADA",
        )


class SucursalConOperacionesPendientesError(ConflictError):
    """Lanzada cuando se intenta desactivar o eliminar una sucursal con reservas pendientes o stock disponible."""

    def __init__(self, id_sucursal: int, motivo: str):
        super().__init__(
            message=f"No se puede desactivar o eliminar la sucursal {id_sucursal}: {motivo}.",
            code="SUCURSAL_CON_OPERACIONES_PENDIENTES",
        )


class HorarioSucursalInvalidoError(DomainError):
    """Lanzada cuando el horario de cierre no es cronologicamente posterior al de apertura."""

    def __init__(self):
        super().__init__(
            message="El horario de cierre debe ser cronologicamente posterior a la hora de apertura.",
            code="HORARIO_INVALIDO",
        )
