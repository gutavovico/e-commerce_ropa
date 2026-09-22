"""Router HTTP de FastAPI para CU07: Consultar Detalle de Producto y CU08: Variantes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.catalogo.cu07_detalle_producto.esquemas import ProductoDetalleOut
from modules.catalogo.cu07_detalle_producto.servicio import ProductoDetalleServicio

router = APIRouter(tags=["Detalle de Producto"])


@router.get(
    "/productos/{id_producto}",
    response_model=ProductoDetalleOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de prenda de alta costura",
    description="Retorna la ficha técnica completa, galería multi-ángulo, variantes de talla/color y recomendaciones.",
)
@router.get(
    "/catalogo/productos/{id_producto}",
    response_model=ProductoDetalleOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def obtener_detalle_producto(
    id_producto: int,
    db: Session = Depends(get_db),
) -> ProductoDetalleOut:
    """Endpoint para consultar la ficha de detalle y variantes de una prenda."""
    return ProductoDetalleServicio.consultar_detalle_producto(db, id_producto)
