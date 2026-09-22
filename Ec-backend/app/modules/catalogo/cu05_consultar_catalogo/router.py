"""Router HTTP para CU05: Consultar Catálogo de Productos."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from modules.catalogo.cu05_consultar_catalogo.esquemas import CatalogoOut
from modules.catalogo.cu05_consultar_catalogo.servicio import CatalogoServicio

router = APIRouter(tags=["Catálogo General (CU05)"])


@router.get(
    "/catalogo",
    response_model=CatalogoOut,
    summary="Consultar catálogo de prendas de alta costura",
    description=(
        "Retorna la colección general paginada de prendas de FashionStore, enriquecida con "
        "resumen de categorías para chips de selección, variantes (tallas, colores), "
        "disponibilidad de stock omnicanal y aplicación de promociones activas."
    ),
)
def consultar_catalogo(
    categoria_id: Optional[int] = Query(
        default=None, description="ID de categoría para filtrado rápido por chip"
    ),
    ordenar_por: str = Query(
        default="recientes",
        description="Criterio de ordenación: recientes, precio_asc, precio_desc, nombre_asc, rating",
    ),
    pagina: int = Query(default=1, ge=1, description="Número de página solicitado"),
    limite: int = Query(default=8, ge=1, le=50, description="Cantidad de prendas por página"),
    db: Session = Depends(get_db),
) -> CatalogoOut:
    """Endpoint principal para alimentar la vista raíz de Catálogo en Web y Móvil."""
    return CatalogoServicio.consultar_catalogo(
        db=db,
        categoria_id=categoria_id,
        ordenar_por=ordenar_por,
        pagina=pagina,
        limite=limite,
    )
