"""Router HTTP de FastAPI para CU15: Comprar desde la plataforma."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu15_comprar_plataforma.esquemas import (
    CheckoutIn,
    RetencionLiberadaOut,
    VentaCreadaOut,
)
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio

router = APIRouter(tags=["Compras y Pagos"])


@router.post(
    "/ventas/checkout",
    response_model=VentaCreadaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tramitar el pedido",
    description=(
        "Convierte la bolsa en una venta formal en estado 'pendiente': congela precios, aplica "
        "el cupón si procede, retiene las existencias durante 25 minutos y deja la orden lista "
        "para la pasarela de pago. Los importes enviados por el cliente se ignoran."
    ),
)
def tramitar_pedido(
    payload: CheckoutIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VentaCreadaOut:
    """Endpoint de consolidación de la orden de compra."""
    return CheckoutServicio.tramitar_pedido(db, usuario, payload)


@router.post(
    "/ventas/{id_venta}/liberar-retencion",
    response_model=RetencionLiberadaOut,
    status_code=status.HTTP_200_OK,
    summary="Liberar las existencias retenidas por una orden pendiente",
    description=(
        "Devuelve al stock disponible las unidades retenidas por una orden que no llegó a "
        "pagarse, ya sea por rechazo de la pasarela o por vencimiento de la ventana de 25 "
        "minutos. Sin esta salida, una orden abandonada bloquearía inventario indefinidamente."
    ),
)
def liberar_retencion(
    id_venta: int,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RetencionLiberadaOut:
    """Endpoint de liberación de existencias retenidas."""
    return CheckoutServicio.liberar_retencion_venta(db, usuario, id_venta)
