"""Router HTTP de FastAPI para CU16: Realizar Pago Electrónico."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu16_realizar_pago.esquemas import (
    PagoConfirmadoOut,
    PagoProcesarIn,
    ResumenPagoOut,
)
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio

router = APIRouter(tags=["Pagos"])


@router.get(
    "/ventas/{id_venta}/resumen-pago",
    response_model=ResumenPagoOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar el resumen de pago de una orden pendiente",
    description=(
        "Devuelve el importe, las líneas congeladas, el destino de la entrega y el tiempo "
        "restante de la retención de existencias, para inicializar la pasarela de pago."
    ),
)
def obtener_resumen_pago(
    id_venta: int,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumenPagoOut:
    """Endpoint de lectura previa al cobro."""
    return PagoServicio.obtener_resumen_pago(db, usuario, id_venta)


@router.post(
    "/pagos/procesar",
    response_model=PagoConfirmadoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Procesar el pago electrónico de una orden",
    description=(
        "Cobra la orden contra la pasarela, la marca como pagada y consolida las existencias "
        "retenidas. Un rechazo de la tarjeta responde 402 y deja la orden intacta para "
        "reintentar; una orden vencida responde 409 y libera las existencias."
    ),
    responses={
        402: {"description": "La pasarela rechazó el cargo; la orden admite reintento"},
        409: {"description": "La orden ya fue liquidada, está anulada o su ventana venció"},
    },
)
def procesar_pago(
    payload: PagoProcesarIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PagoConfirmadoOut:
    """Endpoint transaccional de cobro y cierre del ciclo de compra."""
    return PagoServicio.procesar_pago(db, usuario, payload)
