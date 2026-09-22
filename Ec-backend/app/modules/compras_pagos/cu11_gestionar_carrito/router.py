"""Router HTTP de FastAPI para CU11: Gestionar carrito de compras (Bolsa de Compra)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu11_gestionar_carrito.esquemas import (
    CarritoOut,
    ItemAgregarIn,
    ItemCantidadIn,
)
from modules.compras_pagos.cu11_gestionar_carrito.servicio import CarritoServicio

router = APIRouter(tags=["Bolsa de Compra"])


@router.get(
    "/carrito",
    response_model=CarritoOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar la bolsa de compra del cliente",
    description=(
        "Devuelve la bolsa activa con el desglose de prendas, la boutique de expedición de cada "
        "línea, el stock vigente y el resumen financiero. Una bolsa vacía responde 200 con la "
        "lista de prendas vacía, nunca 404."
    ),
)
def obtener_carrito(
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarritoOut:
    """Endpoint de lectura de la Bolsa de Compra."""
    return CarritoServicio.obtener_carrito(db, usuario)


@router.post(
    "/carrito/items",
    response_model=CarritoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir una prenda a la bolsa",
    description=(
        "Añade una variante a la bolsa validando existencias. Si la prenda ya estaba presente "
        "para la misma boutique, consolida cantidades en lugar de duplicar la línea."
    ),
)
def agregar_item(
    payload: ItemAgregarIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarritoOut:
    """Endpoint de alta de prenda en la Bolsa de Compra."""
    return CarritoServicio.agregar_item(db, usuario, payload)


@router.patch(
    "/carrito/items/{id_carrito_detalle}",
    response_model=CarritoOut,
    status_code=status.HTTP_200_OK,
    summary="Modificar la cantidad de una prenda de la bolsa",
    description=(
        "Fija la cantidad de una línea validando el stock de su boutique de expedición. La "
        "cantidad es absoluta, no un incremento, de modo que la operación es idempotente."
    ),
)
def actualizar_cantidad(
    id_carrito_detalle: int,
    payload: ItemCantidadIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarritoOut:
    """Endpoint de modificación de cantidad en la Bolsa de Compra."""
    return CarritoServicio.actualizar_cantidad(db, usuario, id_carrito_detalle, payload)


@router.delete(
    "/carrito/items/{id_carrito_detalle}",
    response_model=CarritoOut,
    status_code=status.HTTP_200_OK,
    summary="Eliminar una prenda de la bolsa",
    description="Purga la línea de la bolsa y devuelve el resumen financiero recalculado.",
)
def eliminar_item(
    id_carrito_detalle: int,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarritoOut:
    """Endpoint de eliminación de prenda en la Bolsa de Compra."""
    return CarritoServicio.eliminar_item(db, usuario, id_carrito_detalle)
