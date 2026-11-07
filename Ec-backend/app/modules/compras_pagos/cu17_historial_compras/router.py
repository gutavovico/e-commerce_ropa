"""Router HTTP de FastAPI para CU17: Consultar historial de compras."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu17_historial_compras.esquemas import HistorialComprasOut
from modules.compras_pagos.cu17_historial_compras.servicio import (
    ServicioHistorialCompras,
)

router = APIRouter(tags=["Compras y Pagos"])


@router.get(
    "/ventas/mias",
    response_model=HistorialComprasOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar el historial de compras del cliente autenticado",
    description=(
        "Retorna todas las compras (digitales web/móvil y presenciales) asociadas al cliente "
        "autenticado, ordenadas cronológicamente de la más reciente a la más antigua, junto "
        "con su desglose de prendas y datos del comprobante."
    ),
)
def listar_mis_compras(
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistorialComprasOut:
    """Endpoint de consulta del historial de compras del cliente."""
    return ServicioHistorialCompras.obtener_historial_cliente(db, usuario)

