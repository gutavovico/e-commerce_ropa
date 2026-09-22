"""Routers REST para CU24: Gestionar Inventario, Stock y Existencias por Sucursal."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from .esquemas import (
    ComprobanteTransferenciaOut,
    DisponibilidadPublicaOut,
    HistorialKardexOut,
    InventarioAjusteIn,
    InventarioCrearIn,
    InventarioFiltrosIn,
    InventarioItemOut,
    ListaPaginadaInventarioOut,
    TransferenciaInterSucursalIn,
)
from .servicio import servicio_gestion_inventario

# Router administrativo protegido con RBAC estricto
router_admin = APIRouter(
    prefix="/admin/inventario",
    tags=["Gestion Operativa - Inventario y Stock (Admin)"],
)

# Router publico sin autenticacion para vitrina B2C y apps consumidoras
router_publico = APIRouter(
    prefix="/inventario",
    tags=["Catalogo - Disponibilidad de Inventario"],
)


# =============================================================================
# ENDPOINTS ADMINISTRATIVOS: PROTEGIDOS POR RBAC (ADMINISTRADOR / ENCARGADO)
# =============================================================================

@router_admin.get(
    "",
    response_model=ListaPaginadaInventarioOut,
    status_code=status.HTTP_200_OK,
    summary="Consulta paginada de existencias por boutique fisica",
)
def listar_inventario(
    id_sucursal: Optional[int] = Query(None, description="Filtrar por ID de sucursal"),
    id_categoria: Optional[int] = Query(None, description="Filtrar por categoria de prenda"),
    estado_stock: Optional[str] = Query(None, description="optimo, alerta_baja, agotado"),
    estado: Optional[str] = Query(None, description="Alias para estado_stock"),
    q: Optional[str] = Query(None, max_length=100, description="Busqueda por prenda o SKU"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(20, ge=1, le=100, description="Registros por pagina"),
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ListaPaginadaInventarioOut:
    """Consulta paginada del catalogo de inventario por sede con filtros combinados."""
    filtro_estado = estado_stock if estado_stock is not None else estado
    if filtro_estado in ("todos", "", "null", "undefined"):
        filtro_estado = None

    filtro_sucursal = id_sucursal if (id_sucursal is not None and id_sucursal > 0) else None
    filtro_categoria = id_categoria if (id_categoria is not None and id_categoria > 0) else None

    filtros = InventarioFiltrosIn(
        id_sucursal=filtro_sucursal,
        id_categoria=filtro_categoria,
        estado_stock=filtro_estado,
        q=q.strip() if q and q.strip() else None,
        pagina=pagina,
        limite=limite,
    )
    return servicio_gestion_inventario.listar_inventario(db, filtros, usuario_sesion)


@router_admin.post(
    "",
    response_model=InventarioItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Alta inicial de existencias fisicas para una variante en sucursal",
)
def crear_inventario_inicial(
    payload: InventarioCrearIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> InventarioItemOut:
    """Registra la existencia inicial de una variante en una boutique y genera el primer asiento de Kardex."""
    return servicio_gestion_inventario.crear_inventario_inicial(db, payload, usuario_sesion)


@router_admin.post(
    "/transferencia",
    response_model=ComprobanteTransferenciaOut,
    status_code=status.HTTP_200_OK,
    summary="Traspaso transaccional inter-sucursal con doble registro en Kardex",
)
def transferir_mercaderia(
    payload: TransferenciaInterSucursalIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ComprobanteTransferenciaOut:
    """Ejecuta una transferencia atomica entre dos boutiques fisicas registrando salida y entrada en Kardex."""
    return servicio_gestion_inventario.transferir_mercaderia(db, payload, usuario_sesion)


@router_admin.post(
    "/{id_inventario}/ajuste",
    response_model=InventarioItemOut,
    status_code=status.HTTP_200_OK,
    summary="Ajuste manual fisico por merma, rotura o sobrante",
)
def ajustar_inventario(
    id_inventario: int,
    payload: InventarioAjusteIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> InventarioItemOut:
    """Ajusta manualmente el saldo disponible con validacion de no negatividad y justificacion auditable."""
    return servicio_gestion_inventario.ajustar_inventario(db, id_inventario, payload, usuario_sesion)


@router_admin.get(
    "/{id_inventario}/kardex",
    response_model=HistorialKardexOut,
    status_code=status.HTTP_200_OK,
    summary="Historial cronologico de movimientos contables y fisicos (Kardex)",
)
def obtener_kardex(
    id_inventario: int,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> HistorialKardexOut:
    """Retorna la bitacora completa e inmutable de movimientos de existencias de un inventario."""
    return servicio_gestion_inventario.obtener_kardex(db, id_inventario, usuario_sesion)


# =============================================================================
# ENDPOINTS PUBLICOS: DISPONIBILIDAD FISICA DE PRENDAS
# =============================================================================

@router_publico.get(
    "/disponibilidad/{id_variante}",
    response_model=DisponibilidadPublicaOut,
    status_code=status.HTTP_200_OK,
    summary="Consulta publica de disponibilidad de una variante en boutiques fisicas",
)
def consultar_disponibilidad_publica(
    id_variante: int,
    db: Session = Depends(get_db),
) -> DisponibilidadPublicaOut:
    """Permite al cliente o apps consultar que boutiques cuentan con existencias de una prenda."""
    return servicio_gestion_inventario.consultar_disponibilidad_publica(db, id_variante)


# Router unificado exportable
router = APIRouter()
router.include_router(router_admin)
router.include_router(router_publico)

__all__ = ["router", "router_admin", "router_publico"]
