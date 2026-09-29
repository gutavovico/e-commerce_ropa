"""Router REST para CU17: Registrar cobro en caja."""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu17_cobro_caja.esquemas import (
    CobroCajaIn,
    CobroCajaOut,
    ListadoOrdenesPendientesOut,
)
from modules.comercial.cu17_cobro_caja.servicio import ServicioCobroCaja

router = APIRouter(prefix="/caja", tags=["Caja - Cobro [CU17]"])

ROLES_AUTORIZADOS_CAJA = ["cajero", "encargado_sucursal", "administrador", "admin"]


@router.get(
    "/ordenes-pendientes",
    response_model=ListadoOrdenesPendientesOut,
    summary="Listar ordenes pendientes de cobro en caja",
    description="Retorna las ordenes en estado pendiente acotadas a la sucursal del cajero.",
)
def listar_ordenes_pendientes(
    q: Optional[str] = Query(None, description="Codigo de orden o datos de cliente"),
    fecha_desde: Optional[date] = Query(None, description="Fecha minima de emision"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha maxima de emision"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal a filtrar (solo para administradores)"),
    limite: int = Query(50, ge=1, le=100),
    salto: int = Query(0, ge=0),
    usuario: UsuarioORM = Depends(require_roles(ROLES_AUTORIZADOS_CAJA)),
    db: Session = Depends(get_db),
) -> ListadoOrdenesPendientesOut:
    return ServicioCobroCaja.buscar_ordenes_pendientes(
        db=db,
        usuario=usuario,
        q=q,
        fecha_desde=str(fecha_desde) if fecha_desde else None,
        fecha_hasta=str(fecha_hasta) if fecha_hasta else None,
        id_sucursal=id_sucursal,
        limite=limite,
        salto=salto,
    )


@router.post(
    "/cobrar",
    response_model=CobroCajaOut,
    summary="Registrar cobro de orden en caja",
    description="Asienta el pago presencial en efectivo, tarjeta POS o QR fisico.",
)
def registrar_cobro(
    payload: CobroCajaIn,
    request: Request,
    usuario: UsuarioORM = Depends(require_roles(ROLES_AUTORIZADOS_CAJA)),
    db: Session = Depends(get_db),
) -> CobroCajaOut:
    ip_cliente = request.client.host if request.client else "127.0.0.1"
    return ServicioCobroCaja.cobrar_orden(
        db=db,
        usuario=usuario,
        datos=payload,
        ip_origen=ip_cliente,
    )
