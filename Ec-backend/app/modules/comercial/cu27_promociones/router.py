"""Router REST para CU27: Gestionar promociones."""

from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu27_promociones.esquemas import (
    EstadoConmutarIn,
    FiltrosPromocionIn,
    PromocionActualizarIn,
    PromocionCrearIn,
    PromocionFiltrosIn,
    PromocionItemOut,
    RespuestaPaginadaPromocionesOut,
)
from modules.comercial.cu27_promociones.servicio import ServicioGestionPromociones

router = APIRouter(tags=["Gestion Comercial - Promociones (Admin)"])
servicio_promociones = ServicioGestionPromociones()


@router.get(
    "/admin/promociones",
    response_model=RespuestaPaginadaPromocionesOut,
    status_code=status.HTTP_200_OK,
    summary="Listar promociones comerciales paginadas",
    description="Retorna el listado paginado de campanas y cupones con filtros multicriterio e indicadores de red.",
)
def listar_promociones(
    q: Optional[str] = Query(None, max_length=100, description="Busqueda por nombre o codigo de cupon"),
    tipo_descuento: Optional[Literal["porcentaje", "monto_fijo", "todos"]] = Query(
        "todos", description="Filtrar por tipo de descuento"
    ),
    estado_activo: Optional[Literal["activas", "inactivas", "todos"]] = Query(
        "todos", description="Filtrar por estado operativo"
    ),
    alcance: Optional[Literal["global", "categoria", "producto", "todos"]] = Query(
        "todos", description="Filtrar por alcance de la promocion"
    ),
    ordenar_por: Optional[
        Literal[
            "creado_en_desc",
            "creado_en_asc",
            "fecha_inicio_desc",
            "fecha_fin_asc",
            "nombre_asc",
            "valor_desc",
            "usos_desc",
        ]
    ] = Query("creado_en_desc", description="Criterio de ordenacion"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(10, ge=1, le=100, description="Registros por pagina"),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> RespuestaPaginadaPromocionesOut:
    filtros = PromocionFiltrosIn(
        q=q,
        tipo_descuento=tipo_descuento,
        estado_activo=estado_activo,
        alcance=alcance,
        ordenar_por=ordenar_por,
        pagina=pagina,
        limite=limite,
    )
    return servicio_promociones.listar_promociones(db, filtros)


@router.get(
    "/admin/promociones/{id_promocion}",
    response_model=PromocionItemOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de una promocion comercial",
    description="Retorna la entidad de promocion especificada por ID con relaciones de categoria o producto.",
)
def obtener_promocion(
    id_promocion: int,
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> PromocionItemOut:
    return servicio_promociones.obtener_promocion_por_id(db, id_promocion)


@router.post(
    "/admin/promociones",
    response_model=PromocionItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva promocion o cupon de descuento",
    description="Registra una nueva campana comercial o cupon con validacion de unicidad, fechas y topes.",
)
def crear_promocion(
    datos: PromocionCrearIn,
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(require_roles(["administrador"])),
) -> PromocionItemOut:
    return servicio_promociones.crear_promocion(db, datos)


@router.put(
    "/admin/promociones/{id_promocion}",
    response_model=PromocionItemOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar promocion comercial",
    description="Modifica integralmente los atributos, reglas y vigencia de una promocion existente.",
)
def actualizar_promocion(
    id_promocion: int,
    datos: PromocionActualizarIn,
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(require_roles(["administrador"])),
) -> PromocionItemOut:
    return servicio_promociones.actualizar_promocion(db, id_promocion, datos)


@router.patch(
    "/admin/promociones/{id_promocion}/estado",
    response_model=PromocionItemOut,
    status_code=status.HTTP_200_OK,
    summary="Conmutar estado operativo (baja logica o reactivacion)",
    description="Actualiza el indicador estado_activo de la promocion sin eliminar registros historicos.",
)
def conmutar_estado_promocion(
    id_promocion: int,
    datos: EstadoConmutarIn,
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(require_roles(["administrador"])),
) -> PromocionItemOut:
    return servicio_promociones.conmutar_estado(db, id_promocion, datos.estado_activo)
