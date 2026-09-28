"""Router HTTP de FastAPI para CU16: Realizar Pago Electrónico."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu15_comprar_plataforma.esquemas import RetencionLiberadaOut
from modules.compras_pagos.cu16_realizar_pago.esquemas import (
    PagoConfirmadoOut,
    PagoEfectivoIn,
    PagoIniciarIn,
    PagoIntentoOut,
    ResumenPagoOut,
)
from modules.compras_pagos.cu16_realizar_pago.servicio import ROLES_CAJA, PagoServicio

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
    "/pagos/efectivo",
    response_model=PagoConfirmadoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la intención de pago en efectivo en sucursal",
    description=(
        "Deja constancia de que el cliente pagará en efectivo al recoger su pedido. No cobra "
        "nada: la venta permanece `pendiente` hasta que un cajero confirme el pago en mostrador "
        "(§1.6). Una orden vencida responde 409 y libera las existencias."
    ),
    responses={
        409: {"description": "La orden ya fue liquidada, está anulada o su ventana venció"},
        422: {"description": "El pedido no se recoge en boutique: el efectivo no aplica"},
    },
)
def registrar_pago_efectivo(
    payload: PagoEfectivoIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PagoConfirmadoOut:
    """Endpoint de registro del pago en efectivo en sucursal (§1.5.2/§1.6)."""
    return PagoServicio.registrar_pago_efectivo(db, usuario, payload)


@router.post(
    "/pagos/intentos",
    response_model=PagoIntentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir un intento de cobro digital contra Stripe",
    description=(
        "Crea un `PaymentIntent` en Stripe y devuelve su `client_secret`. El backend no recibe "
        "ningún dato de tarjeta: el cliente recolecta la tarjeta y confirma el cobro "
        "directamente contra Stripe con Stripe.js (Web) o el SDK de Flutter (Mobile), y luego "
        "llama a `POST /pagos/{id_pago}/confirmar` para que el servidor verifique el desenlace."
    ),
    responses={
        409: {"description": "La orden ya fue liquidada, está anulada o su ventana venció"},
    },
)
def iniciar_pago(
    payload: PagoIniciarIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PagoIntentoOut:
    """Endpoint que abre el cobro; nunca recibe el PAN ni el CVV."""
    return PagoServicio.iniciar_pago(db, usuario, payload)


@router.post(
    "/pagos/{id_pago}/confirmar",
    response_model=PagoConfirmadoOut,
    status_code=status.HTTP_200_OK,
    summary="Verificar y cerrar un cobro digital ya confirmado con Stripe",
    description=(
        "Recupera el `PaymentIntent` de Stripe y decide el desenlace según lo que la pasarela "
        "responda, nunca según lo que el cliente reporte. Si fue aprobado, marca la venta como "
        "pagada y consolida las existencias. Un rechazo responde 402 y deja la orden intacta "
        "para reintentar con un nuevo intento."
    ),
    responses={
        402: {"description": "La pasarela rechazó el cargo; la orden admite reintento"},
        409: {"description": "El pago no está pendiente, o la orden ya no admite cobro"},
    },
)
def confirmar_pago(
    id_pago: int,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PagoConfirmadoOut:
    """Endpoint que cierra el ciclo de compra tras la confirmación en Stripe."""
    return PagoServicio.confirmar_pago(db, usuario, id_pago)


@router.post(
    "/admin/pagos/{id_pago}/confirmar-efectivo",
    response_model=PagoConfirmadoOut,
    status_code=status.HTTP_200_OK,
    summary="Confirmar en mostrador un pago en efectivo en sucursal",
    description=(
        "Un cajero o encargado de la boutique de recogida confirma que el cliente pagó en "
        "efectivo: liquida la venta y consolida el inventario. Si la ventana de 24 horas ya "
        "venció, libera las existencias y responde 409 en su lugar."
    ),
    responses={
        403: {"description": "El pago pertenece a una sucursal ajena a la del cajero"},
        409: {"description": "El pago no está pendiente, o su ventana de 24h ya venció"},
    },
)
def confirmar_pago_efectivo(
    id_pago: int,
    usuario: UsuarioORM = Depends(require_roles(list(ROLES_CAJA))),
    db: Session = Depends(get_db),
) -> PagoConfirmadoOut:
    """Endpoint administrativo de confirmación del pago en efectivo (§1.6)."""
    return PagoServicio.confirmar_pago_efectivo(db, usuario, id_pago)


@router.post(
    "/admin/pagos/{id_pago}/cancelar-efectivo",
    response_model=RetencionLiberadaOut,
    status_code=status.HTTP_200_OK,
    summary="Cancelar en mostrador un pago en efectivo en sucursal",
    description=(
        "Un cajero o encargado anula un pago en efectivo pendiente antes de que expiren las "
        "24 horas, liberando de inmediato las existencias retenidas."
    ),
    responses={
        403: {"description": "El pago pertenece a una sucursal ajena a la del cajero"},
        409: {"description": "El pago no está pendiente"},
    },
)
def cancelar_pago_efectivo(
    id_pago: int,
    usuario: UsuarioORM = Depends(require_roles(list(ROLES_CAJA))),
    db: Session = Depends(get_db),
) -> RetencionLiberadaOut:
    """Endpoint administrativo de cancelación del pago en efectivo (§1.6)."""
    return PagoServicio.cancelar_pago_efectivo(db, usuario, id_pago)
