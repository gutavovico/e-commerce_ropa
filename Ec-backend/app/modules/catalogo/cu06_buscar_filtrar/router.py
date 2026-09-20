"""Router de FastAPI para el caso de uso CU06 - Buscar y Filtrar Productos."""

from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.catalogo.cu06_buscar_filtrar.esquemas import (
    CatalogoBuscarIn,
    FiltrosDisponiblesOut,
    ProductoPaginadoOut,
)
from modules.catalogo.cu06_buscar_filtrar.servicio import (
    FiltroInvalidoError,
    ServicioBuscarFiltro,
)

router = APIRouter(tags=["Catálogo y Exploración"])


@router.get(
    "/productos",
    response_model=ProductoPaginadoOut,
    summary="Buscar y filtrar productos (REST Estándar)",
    description=(
        "Permite localizar prendas aplicando coincidencia difusa sobre nombres o descripciones "
        "y filtros combinados de catálogo (categoría, colección, temporada, talla, color, "
        "disponibilidad de inventario y rango de precios) con paginación determinista."
    ),
)
@router.get(
    "/catalogo/productos",
    response_model=ProductoPaginadoOut,
    include_in_schema=False,
)
def buscar_productos(
    q: Optional[str] = Query(default=None, description="Término de búsqueda difusa"),
    categoria_id: Optional[int] = Query(default=None, description="ID de categoría"),
    coleccion_id: Optional[int] = Query(default=None, description="ID de colección / línea"),
    temporada_id: Optional[int] = Query(default=None, description="ID de temporada"),
    talla: Optional[str] = Query(default=None, description="Código de talla (ej. 36, 38)"),
    id_talla: Optional[int] = Query(default=None, description="ID numérico de talla"),
    color: Optional[str] = Query(default=None, description="Nombre de color (ej. Marfil, Camel)"),
    id_color: Optional[int] = Query(default=None, description="ID numérico de color"),
    precio_min: Optional[Decimal] = Query(default=None, ge=0, description="Precio mínimo"),
    precio_max: Optional[Decimal] = Query(default=None, ge=0, description="Precio máximo"),
    solo_en_stock: bool = Query(
        default=True, description="Filtrar solo prendas con stock disponible"
    ),
    ordenar_por: str = Query(
        default="recientes",
        description="Criterio de orden: recientes, precio_asc, precio_desc, nombre_asc, relevancia",
    ),
    pagina: int = Query(default=1, ge=1, description="Número de página"),
    limite: int = Query(default=12, ge=1, le=50, description="Cantidad por página"),
    db: Session = Depends(get_db),
) -> ProductoPaginadoOut:
    """Endpoint principal de catálogo y búsqueda para aplicaciones Web y Móvil."""
    try:
        return ServicioBuscarFiltro.buscar_productos(
            session=db,
            q=q,
            categoria_id=categoria_id,
            coleccion_id=coleccion_id,
            temporada_id=temporada_id,
            id_talla=id_talla,
            talla=talla,
            id_color=id_color,
            color=color,
            precio_min=precio_min,
            precio_max=precio_max,
            solo_en_stock=solo_en_stock,
            ordenar_por=ordenar_por,
            pagina=pagina,
            limite=limite,
        )
    except FiltroInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(exc).__name__}: {str(exc)}",
        ) from exc


@router.get(
    "/catalogo/filtros-disponibles",
    response_model=FiltrosDisponiblesOut,
    summary="Obtener dimensiones y opciones de filtros disponibles",
    description="Devuelve las temporadas, colecciones, categorías, tallas y colores disponibles para alimentar la interfaz.",
)
def obtener_filtros_disponibles(
    db: Session = Depends(get_db),
) -> FiltrosDisponiblesOut:
    """Retorna las opciones de filtros activas en la base de datos."""
    return ServicioBuscarFiltro.obtener_filtros_disponibles(session=db)


@router.post(
    "/catalogo/buscar",
    summary="Buscar y filtrar productos (Compatibilidad SI2-Parcial1.md)",
    description="Endpoint POST compatible con la especificación de pruebas unitarias de SI2-Parcial1.md línea 2950.",
)
def buscar_productos_post(
    payload: CatalogoBuscarIn,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Endpoint POST para búsqueda de catálogo según especificación de pruebas de SI2."""
    filtros = payload.filtros

    resultado = ServicioBuscarFiltro.buscar_productos(
        session=db,
        q=payload.termino_busqueda,
        categoria_id=filtros.id_categoria if filtros else None,
        coleccion_id=filtros.id_coleccion if filtros else None,
        temporada_id=filtros.id_temporada if filtros else None,
        id_talla=filtros.id_talla if filtros else None,
        id_color=filtros.id_color if filtros else None,
        precio_min=filtros.precio_min if filtros else None,
        precio_max=filtros.precio_max if filtros else None,
        solo_en_stock=False,  # En pruebas históricas evalúa catálogo completo
        pagina=payload.pagina,
        limite=payload.limite,
    )

    return {
        "total_resultados": resultado.paginacion.total_registros,
        "total_registros": resultado.paginacion.total_registros,
        "productos": [
            {
                "id_producto": p.id_producto,
                "nombre": p.nombre,
                "precio_base": float(p.precio_base),
                "imagen_url": p.imagen_url,
                "categoria": p.categoria,
                "variantes_coincidentes": [
                    {
                        "id_variante": v.id_variante,
                        "sku": v.sku,
                        "talla": v.talla,
                        "color": v.color,
                        "precio_extra": float(v.precio_extra),
                    }
                    for v in p.variantes
                ],
            }
            for p in resultado.items
        ],
        "items": resultado.items,
        "paginacion": resultado.paginacion,
        "filtros_aplicados": resultado.filtros_aplicados,
    }
