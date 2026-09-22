"""Router REST para CU28: Consultar ventas y reservas."""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu28_ventas_reservas.errores import RangoFechasInvalidoError
from modules.comercial.cu28_ventas_reservas.esquemas import (
    ReservaDetalleCompletoOut,
    RespuestaPaginadaTransaccionesOut,
    TransaccionFiltrosIn,
    VentaDetalleCompletoOut,
)
from modules.comercial.cu28_ventas_reservas.servicio import (
    ServicioConsultarVentasReservas,
)

router = APIRouter(tags=["Gestion Comercial - Ventas y Reservas (Admin)"])
servicio_ventas_reservas = ServicioConsultarVentasReservas()


@router.get(
    "/admin/ventas-reservas",
    response_model=RespuestaPaginadaTransaccionesOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar listado paginado de ventas y reservas",
    description="Retorna el listado unificado y consolidado de ventas y reservas con indicadores cuantitativos de red.",
)
def listar_ventas_reservas(
    q: Optional[str] = Query(None, max_length=100, description="Busqueda por comprobante, cliente o SKU"),
    tipo_operacion: Optional[Literal["venta", "reserva", "todas"]] = Query(
        "todas", description="Filtrar por tipo de operacion"
    ),
    estado: Optional[str] = Query("todos", description="Filtrar por estado de transaccion"),
    id_sucursal: Optional[int] = Query(None, description="Filtrar por sucursal (exclusivo Administrador)"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha limite inferior"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha limite superior"),
    metodo_pago: Optional[str] = Query(None, description="Filtrar por metodo de pago"),
    canal_origen: Optional[Literal["web", "movil", "sucursal", "todos"]] = Query(
        "todos", description="Filtrar por canal de origen"
    ),
    ordenar_por: Optional[
        Literal[
            "creado_en_desc",
            "creado_en_asc",
            "total_desc",
            "total_asc",
            "fecha_desc",
        ]
    ] = Query("creado_en_desc", description="Criterio de ordenacion"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad por pagina"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> RespuestaPaginadaTransaccionesOut:
    try:
        filtros = TransaccionFiltrosIn(
            q=q,
            tipo_operacion=tipo_operacion,
            estado=estado,
            id_sucursal=id_sucursal,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            metodo_pago=metodo_pago,
            canal_origen=canal_origen,
            ordenar_por=ordenar_por,
            pagina=pagina,
            limite=limite,
        )
    except ValidationError as err:
        raise RangoFechasInvalidoError(str(err))

    return servicio_ventas_reservas.listar_transacciones(db, filtros, usuario)


@router.get(
    "/admin/ventas-reservas/ventas/{id_venta}",
    response_model=VentaDetalleCompletoOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle unitario de venta",
    description="Retorna el desglose de prendas, metadatos, sucursal y pagos de un comprobante de venta.",
)
def obtener_detalle_venta(
    id_venta: int,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> VentaDetalleCompletoOut:
    return servicio_ventas_reservas.obtener_detalle_venta(db, id_venta, usuario)


@router.get(
    "/admin/ventas-reservas/reservas/{id_reserva}",
    response_model=ReservaDetalleCompletoOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle unitario de reserva",
    description="Retorna el desglose de prendas apartadas y estado de atencion de una reserva.",
)
def obtener_detalle_reserva(
    id_reserva: int,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ReservaDetalleCompletoOut:
    return servicio_ventas_reservas.obtener_detalle_reserva(db, id_reserva, usuario)
