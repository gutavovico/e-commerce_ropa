"""Router de FastAPI para CU36: Consultar Colecciones.

Expone:
- GET /colecciones/activas: Colecciones de la temporada vigente con colección destacada.
- GET /colecciones/{id_coleccion}/productos: Prendas exclusivas de una colección específica.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.catalogo.cu36_colecciones.esquemas import (
    ColeccionDetalleOut,
    ColeccionesActivasResponseOut,
)
from modules.catalogo.cu36_colecciones.servicio import (
    ColeccionNoEncontradaError,
    ColeccionesService,
)

router = APIRouter(prefix="/colecciones", tags=["Colecciones"])


@router.get(
    "/activas",
    response_model=ColeccionesActivasResponseOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar colecciones activas de la temporada vigente",
    description=(
        "Recupera las colecciones vigentes de la temporada comercial activa, "
        "con desglose de colección destacada (hero), piezas clave y precio de entrada 'Desde X €'."
    ),
)
def obtener_colecciones_activas(
    limite_piezas_clave: int = Query(
        4, ge=1, le=12, description="Número de piezas clave a precargar para la colección destacada"
    ),
    db: Session = Depends(get_db),
) -> ColeccionesActivasResponseOut:
    """Retorna las colecciones activas de la temporada actual."""
    return ColeccionesService.obtener_colecciones_activas(
        db=db, limite_piezas_clave=limite_piezas_clave
    )


@router.get(
    "/{id_coleccion}/productos",
    response_model=ColeccionDetalleOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar prendas exclusivas de una colección",
    description=(
        "Recupera los metadatos de una colección y su grilla de prendas activas "
        "con fotos, precios, stock y badges editoriales."
    ),
)
def obtener_prendas_de_coleccion(
    id_coleccion: int,
    db: Session = Depends(get_db),
) -> ColeccionDetalleOut:
    """Retorna las prendas de una colección específica."""
    try:
        return ColeccionesService.obtener_prendas_por_coleccion(
            db=db, id_coleccion=id_coleccion
        )
    except ColeccionNoEncontradaError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.mensaje,
        ) from exc
