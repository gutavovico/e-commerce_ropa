"""Router REST para CU26: Consultar inventario global."""

from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from .esquemas import InventarioGlobalFiltrosIn, RespuestaInventarioGlobalOut
from .servicio import ServicioInventarioGlobal

router = APIRouter(
    prefix="/admin/inventario/global",
    tags=["Gestion Operativa - Inventario Global (Admin)"],
)


@router.get(
    "",
    response_model=RespuestaInventarioGlobalOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar inventario global consolidado",
    description="Retorna el consolidado analitico de existencias por prenda y variante, desglose por sucursales y metricas cuantitativas de red.",
)
def consultar_inventario_global(
    q: Optional[str] = Query(None, max_length=100, description="Busqueda por nombre de prenda o SKU"),
    id_categoria: Optional[int] = Query(None, ge=1, description="Filtro opcional por categoria"),
    id_sucursal: Optional[int] = Query(None, ge=1, description="Filtro opcional por sucursal"),
    estado_stock: Optional[Literal["optimo", "alerta_baja", "agotado", "todos"]] = Query(
        "todos", description="Filtro por estado de existencias"
    ),
    ordenar_por: Optional[Literal["stock_asc", "stock_desc", "nombre_asc", "nombre_desc", "sku_asc"]] = Query(
        "nombre_asc", description="Criterio de ordenacion"
    ),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad de registros por pagina"),
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> RespuestaInventarioGlobalOut:
    filtros = InventarioGlobalFiltrosIn(
        q=q,
        id_categoria=id_categoria,
        id_sucursal=id_sucursal,
        estado_stock=estado_stock,
        ordenar_por=ordenar_por,
        pagina=pagina,
        limite=limite,
    )
    return ServicioInventarioGlobal.consultar_inventario_global(db, filtros)
