"""Jerarquia de excepciones semanticas de dominio para CU24: Gestionar temporadas y colecciones."""

from fastapi import HTTPException, status


class TemporadaColeccionError(HTTPException):
    """Excepcion base para operaciones de temporadas y colecciones."""

    def __init__(self, status_code: int, codigo: str, mensaje: str):
        super().__init__(
            status_code=status_code,
            detail={"codigo": codigo, "mensaje": mensaje},
        )


class TemporadaNoEncontradaError(TemporadaColeccionError):
    """Lanzada cuando una temporada con el ID solicitado no existe."""

    def __init__(self, id_temporada: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            codigo="TEMPORADA_NO_ENCONTRADA",
            mensaje=f"La temporada con ID {id_temporada} no existe en el sistema.",
        )


class TemporadaDuplicadaError(TemporadaColeccionError):
    """Lanzada ante colision de nombre unico de temporada."""

    def __init__(self, nombre: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            codigo="TEMPORADA_NOMBRE_DUPLICADO",
            mensaje=f"Ya existe una temporada registrada con el nombre '{nombre}'.",
        )


class TemporadaFechasInvalidasError(TemporadaColeccionError):
    """Lanzada cuando las fechas de la temporada son cronologicamente inconsistentes."""

    def __init__(self, mensaje: str = "La fecha de finalizacion debe ser estrictamente posterior a la fecha de inicio."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            codigo="FECHAS_TEMPORADA_INVALIDAS",
            mensaje=mensaje,
        )


class ColeccionNoEncontradaError(TemporadaColeccionError):
    """Lanzada cuando una coleccion con el ID solicitado no existe."""

    def __init__(self, id_coleccion: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            codigo="COLECCION_NO_ENCONTRADA",
            mensaje=f"La coleccion con ID {id_coleccion} no existe en el sistema.",
        )


class ColeccionDuplicadaError(TemporadaColeccionError):
    """Lanzada ante colision de nombre unico de coleccion dentro de la misma temporada."""

    def __init__(self, nombre: str, temporada_nombre: str = ""):
        detalle = f" en la temporada '{temporada_nombre}'" if temporada_nombre else " para esta temporada"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            codigo="COLECCION_NOMBRE_DUPLICADO",
            mensaje=f"Ya existe una coleccion con el nombre '{nombre}'{detalle}.",
        )


class TemporadaInactivaParaColeccionError(TemporadaColeccionError):
    """Lanzada cuando se intenta crear una coleccion vinculada a una temporada inactiva."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            codigo="TEMPORADA_INACTIVA_NO_PERMITE_COLECCIONES",
            mensaje="No es posible asociar o crear colecciones bajo una temporada en estado inactivo.",
        )
