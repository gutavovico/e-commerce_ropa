"""Router HTTP de FastAPI para CU09: Consultar Disponibilidad por Sucursal."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.catalogo.cu09_disponibilidad.esquemas import DisponibilidadSucursalesOut
from modules.catalogo.cu09_disponibilidad.servicio import DisponibilidadServicio

router = APIRouter(tags=["Disponibilidad por Sucursal"])


@router.get(
    "/productos/{id_producto}/disponibilidad",
    response_model=DisponibilidadSucursalesOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar disponibilidad física en boutiques",
    description="Retorna el stock físico en tiempo real en la red de boutiques para la prenda o variante especificada.",
)
@router.get(
    "/catalogo/productos/{id_producto}/disponibilidad",
    response_model=DisponibilidadSucursalesOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def obtener_disponibilidad_producto(
    id_producto: int,
    id_variante: Optional[int] = Query(None, description="ID de variante específica (talla/color)"),
    db: Session = Depends(get_db),
) -> DisponibilidadSucursalesOut:
    """Endpoint para consultar disponibilidad física multisede."""
    return DisponibilidadServicio.consultar_disponibilidad(db, id_producto, id_variante)
