"""Jerarquia de excepciones de dominio para CU23: Gestionar Categorias, Tallas y Colores.

Define codigos de error semanticos que se traducen en respuestas HTTP 404, 409 y 422.
"""

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError


# =============================================================================
# EXCEPCIONES: CATEGORIAS
# =============================================================================


class CategoriaNoEncontradaError(NotFoundError):
    """Excepcion emitida cuando una categoria solicitada no existe (HTTP 404)."""

    def __init__(self, id_categoria: int):
        super().__init__(
            message=f"La categoria con identificador {id_categoria} no existe en el catalogo.",
            code="CATEGORIA_NO_ENCONTRADA",
        )


class CategoriaDuplicadaError(ConflictError):
    """Excepcion emitida cuando se intenta registrar un nombre de categoria ya existente (HTTP 409)."""

    def __init__(self, nombre: str):
        super().__init__(
            message=f"Ya existe una categoria registrada con el nombre '{nombre}'.",
            code="CATEGORIA_DUPLICADA",
        )


class ReferenciaCircularError(UnprocessableEntityError):
    """Excepcion emitida cuando se intenta asignar una relacion jerarquica ciclica (HTTP 422)."""

    def __init__(self, id_categoria: int, id_padre: int):
        super().__init__(
            message=(
                f"No se permite asignar la categoria ID {id_padre} como padre de ID {id_categoria} "
                "debido a que generaria una referencia circular o bucle jerarquico."
            ),
            code="REFERENCIA_CIRCULAR_NO_PERMITIDA",
        )


class CategoriaConDependenciasError(ConflictError):
    """Excepcion emitida al intentar eliminar una categoria con productos o subcategorias (HTTP 409)."""

    def __init__(self, motivo: str):
        super().__init__(
            message=f"No se puede eliminar la categoria: {motivo}",
            code="CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS",
        )


# =============================================================================
# EXCEPCIONES: TALLAS
# =============================================================================


class TallaNoEncontradaError(NotFoundError):
    """Excepcion emitida cuando una talla comercial no existe en el sistema (HTTP 404)."""

    def __init__(self, id_talla: int):
        super().__init__(
            message=f"La talla con identificador {id_talla} no existe en el sistema.",
            code="TALLA_NO_ENCONTRADA",
        )


class TallaDuplicadaError(ConflictError):
    """Excepcion emitida cuando el codigo comercial de talla ya esta registrado (HTTP 409)."""

    def __init__(self, codigo: str):
        super().__init__(
            message=f"Ya existe una talla registrada con el codigo comercial '{codigo}'.",
            code="TALLA_DUPLICADA",
        )


class TallaEnUsoError(ConflictError):
    """Excepcion emitida al intentar eliminar una talla asignada a variantes de producto (HTTP 409)."""

    def __init__(self, total_variantes: int):
        super().__init__(
            message=(
                f"No se puede eliminar la talla porque se encuentra asociada a {total_variantes} "
                "variantes de producto en el catalogo e inventario."
            ),
            code="TALLA_EN_USO_EN_VARIANTES",
        )


# =============================================================================
# EXCEPCIONES: COLORES
# =============================================================================


class ColorNoEncontradoError(NotFoundError):
    """Excepcion emitida cuando un color textil no existe en el sistema (HTTP 404)."""

    def __init__(self, id_color: int):
        super().__init__(
            message=f"El color con identificador {id_color} no existe en el sistema.",
            code="COLOR_NO_ENCONTRADO",
        )


class ColorDuplicadoError(ConflictError):
    """Excepcion emitida cuando ya existe un color textil con la misma denominacion (HTTP 409)."""

    def __init__(self, nombre: str):
        super().__init__(
            message=f"Ya existe un color textil registrado con el nombre '{nombre}'.",
            code="COLOR_DUPLICADO",
        )


class ColorEnUsoError(ConflictError):
    """Excepcion emitida al intentar eliminar un color asignado a variantes de prendas (HTTP 409)."""

    def __init__(self, total_variantes: int):
        super().__init__(
            message=(
                f"No se puede eliminar el color porque se encuentra asignado a {total_variantes} "
                "variantes de prendas en el catalogo."
            ),
            code="COLOR_EN_USO_EN_VARIANTES",
        )
