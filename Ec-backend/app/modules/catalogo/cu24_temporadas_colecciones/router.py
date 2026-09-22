"""Router REST para CU24: Gestionar temporadas y colecciones."""

from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from .esquemas import (
    ColeccionActualizarIn,
    ColeccionCrearIn,
    ColeccionFiltrosIn,
    ColeccionItemOut,
    EstadoConmutarIn,
    ListaPaginadaColeccionesOut,
    ListaPaginadaTemporadasOut,
    TemporadaActualizarIn,
    TemporadaCrearIn,
    TemporadaFiltrosIn,
    TemporadaItemOut,
)
from .servicio import ServicioGestionColecciones, ServicioGestionTemporadas

router = APIRouter(tags=["Catalogo - Temporadas y Colecciones (Admin)"])


# ============================================================================
# Endpoints de Temporadas (/admin/temporadas)
# ============================================================================

@router.get(
    "/admin/temporadas",
    response_model=ListaPaginadaTemporadasOut,
    status_code=status.HTTP_200_OK,
    summary="Listar temporadas comerciales paginadas",
    description="Retorna el catalogo de temporadas de moda con filtros multicriterio y conteo de colecciones.",
)
def listar_temporadas(
    q: Optional[str] = Query(None, max_length=100, description="Busqueda por nombre"),
    anio: Optional[int] = Query(None, ge=2020, le=2100, description="Filtrar por ano"),
    estado_activo: Optional[Literal["todos", "activas", "inactivas"]] = Query(
        "todos", description="Filtro de estado"
    ),
    ordenar_por: Optional[Literal["anio_desc", "anio_asc", "nombre_asc", "nombre_desc", "fecha_desc"]] = Query(
        "anio_desc", description="Criterio de ordenacion"
    ),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(10, ge=1, le=100, description="Registros por pagina"),
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ListaPaginadaTemporadasOut:
    filtros = TemporadaFiltrosIn(
        q=q,
        anio=anio,
        estado_activo=estado_activo or "todos",
        ordenar_por=ordenar_por or "anio_desc",
        pagina=pagina,
        limite=limite,
    )
    return ServicioGestionTemporadas.listar_temporadas(db, filtros)


@router.post(
    "/admin/temporadas",
    response_model=TemporadaItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva temporada comercial",
    description="Registra una nueva temporada de moda validando el rango cronologico y la unicidad del nombre.",
)
def crear_temporada(
    payload: TemporadaCrearIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> TemporadaItemOut:
    return ServicioGestionTemporadas.crear_temporada(db, payload)


@router.get(
    "/admin/temporadas/{id_temporada}",
    response_model=TemporadaItemOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener ficha de temporada por ID",
    description="Retorna la informacion detallada de una temporada comercial.",
)
def obtener_temporada(
    id_temporada: int,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> TemporadaItemOut:
    return ServicioGestionTemporadas.obtener_temporada_por_id(db, id_temporada)


@router.put(
    "/admin/temporadas/{id_temporada}",
    response_model=TemporadaItemOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de temporada comercial",
    description="Actualiza la denominacion, ano o vigencia formal de la temporada.",
)
def actualizar_temporada(
    id_temporada: int,
    payload: TemporadaActualizarIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> TemporadaItemOut:
    return ServicioGestionTemporadas.actualizar_temporada(db, id_temporada, payload)


@router.patch(
    "/admin/temporadas/{id_temporada}/estado",
    response_model=TemporadaItemOut,
    status_code=status.HTTP_200_OK,
    summary="Conmutar estado activo/inactivo de temporada",
    description="Ejecuta la baja logica o reactivacion de una temporada comercial preservando su historial.",
)
def conmutar_estado_temporada(
    id_temporada: int,
    payload: EstadoConmutarIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> TemporadaItemOut:
    return ServicioGestionTemporadas.conmutar_estado_temporada(db, id_temporada, payload.estado_activo)


# ============================================================================
# Endpoints de Colecciones (/admin/colecciones)
# ============================================================================

@router.get(
    "/admin/colecciones",
    response_model=ListaPaginadaColeccionesOut,
    status_code=status.HTTP_200_OK,
    summary="Listar colecciones capsula paginadas",
    description="Retorna el catalogo de colecciones tematicas con join a su temporada matriz.",
)
def listar_colecciones(
    q: Optional[str] = Query(None, max_length=150, description="Busqueda por nombre o concepto"),
    id_temporada: Optional[int] = Query(None, ge=1, description="Filtrar por temporada matriz"),
    estado_activo: Optional[Literal["todos", "activas", "inactivas"]] = Query(
        "todos", description="Filtro de estado"
    ),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(10, ge=1, le=100, description="Registros por pagina"),
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ListaPaginadaColeccionesOut:
    filtros = ColeccionFiltrosIn(
        q=q,
        id_temporada=id_temporada,
        estado_activo=estado_activo or "todos",
        pagina=pagina,
        limite=limite,
    )
    return ServicioGestionColecciones.listar_colecciones(db, filtros)


@router.post(
    "/admin/colecciones",
    response_model=ColeccionItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva coleccion capsula",
    description="Registra una coleccion capsula vinculada a una temporada activa.",
)
def crear_coleccion(
    payload: ColeccionCrearIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> ColeccionItemOut:
    return ServicioGestionColecciones.crear_coleccion(db, payload)


@router.get(
    "/admin/colecciones/{id_coleccion}",
    response_model=ColeccionItemOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener ficha de coleccion por ID",
    description="Retorna la informacion detallada de una coleccion capsula.",
)
def obtener_coleccion(
    id_coleccion: int,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ColeccionItemOut:
    return ServicioGestionColecciones.obtener_coleccion_por_id(db, id_coleccion)


@router.put(
    "/admin/colecciones/{id_coleccion}",
    response_model=ColeccionItemOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de coleccion capsula",
    description="Actualiza la denominacion, concepto o temporada asociada de la coleccion.",
)
def actualizar_coleccion(
    id_coleccion: int,
    payload: ColeccionActualizarIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> ColeccionItemOut:
    return ServicioGestionColecciones.actualizar_coleccion(db, id_coleccion, payload)


@router.patch(
    "/admin/colecciones/{id_coleccion}/estado",
    response_model=ColeccionItemOut,
    status_code=status.HTTP_200_OK,
    summary="Conmutar estado activo/inactivo de coleccion",
    description="Ejecuta la baja logica o reactivacion de una coleccion preservando las prendas asociadas.",
)
def conmutar_estado_coleccion(
    id_coleccion: int,
    payload: EstadoConmutarIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> ColeccionItemOut:
    return ServicioGestionColecciones.conmutar_estado_coleccion(db, id_coleccion, payload.estado_activo)
