"""Router REST para CU18: Atender entrega de reserva en boutique."""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.reservas.cu18_entrega_reserva.esquemas import (
    ConfirmarEntregaIn,
    ConvertirVentaReservaOut,
    EntregaReservaOut,
    ListadoReservasPendientesOut,
    NoAsistioReservaOut,
)
from modules.reservas.cu18_entrega_reserva.servicio import ServicioEntregaReserva

router = APIRouter(prefix="/caja", tags=["Caja - Entrega de Reserva [CU18]"])

ROLES_AUTORIZADOS_CAJA = ["cajero", "encargado_sucursal", "administrador", "admin"]


@router.get(
    "/reservas-pendientes",
    response_model=ListadoReservasPendientesOut,
    summary="Listar reservas y citas pendientes para mostrador",
    description="Retorna las citas de fitting room pendientes en la boutique del operador.",
)
def listar_reservas_pendientes(
    q: Optional[str] = Query(None, description="Codigo de reserva o datos de clienta"),
    fecha_cita: Optional[date] = Query(None, description="Fecha de la cita"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal (solo administradores)"),
    limite: int = Query(50, ge=1, le=100),
    salto: int = Query(0, ge=0),
    usuario: UsuarioORM = Depends(require_roles(ROLES_AUTORIZADOS_CAJA)),
    db: Session = Depends(get_db),
) -> ListadoReservasPendientesOut:
    return ServicioEntregaReserva.buscar_reservas_pendientes(
        db=db,
        usuario=usuario,
        q=q,
        fecha_cita=str(fecha_cita) if fecha_cita else None,
        id_sucursal=id_sucursal,
        limite=limite,
        salto=salto,
    )


@router.post(
    "/reservas/{id_reserva}/entregar",
    response_model=EntregaReservaOut,
    summary="Confirmar entrega de prendas y atencion de reserva",
    description="Registra la atencion en fitting room de las prendas apartadas.",
)
def confirmar_entrega_reserva(
    id_reserva: int,
    request: Request,
    payload: Optional[ConfirmarEntregaIn] = None,
    usuario: UsuarioORM = Depends(require_roles(ROLES_AUTORIZADOS_CAJA)),
    db: Session = Depends(get_db),
) -> EntregaReservaOut:
    ip_cliente = request.client.host if request.client else "127.0.0.1"
    return ServicioEntregaReserva.confirmar_entrega(
        db=db,
        usuario=usuario,
        id_reserva=id_reserva,
        datos=payload,
        ip_origen=ip_cliente,
    )


@router.post(
    "/reservas/{id_reserva}/no-asistio",
    response_model=NoAsistioReservaOut,
    summary="Marcar inasistencia de cliente y liberar stock",
    description="Cancela la cita por inasistencia y devuelve el stock apartado al disponible.",
)
def marcar_inasistencia_reserva(
    id_reserva: int,
    request: Request,
    usuario: UsuarioORM = Depends(require_roles(ROLES_AUTORIZADOS_CAJA)),
    db: Session = Depends(get_db),
) -> NoAsistioReservaOut:
    ip_cliente = request.client.host if request.client else "127.0.0.1"
    return ServicioEntregaReserva.marcar_no_asistio(
        db=db,
        usuario=usuario,
        id_reserva=id_reserva,
        ip_origen=ip_cliente,
    )


@router.post(
    "/reservas/{id_reserva}/convertir-venta",
    response_model=ConvertirVentaReservaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Convertir reserva en orden de venta presencial",
    description="Genera una orden de venta de mostrador para cobro inmediato en caja.",
)
def convertir_reserva_a_venta(
    id_reserva: int,
    request: Request,
    usuario: UsuarioORM = Depends(require_roles(ROLES_AUTORIZADOS_CAJA)),
    db: Session = Depends(get_db),
) -> ConvertirVentaReservaOut:
    ip_cliente = request.client.host if request.client else "127.0.0.1"
    return ServicioEntregaReserva.convertir_a_venta(
        db=db,
        usuario=usuario,
        id_reserva=id_reserva,
        ip_origen=ip_cliente,
    )
