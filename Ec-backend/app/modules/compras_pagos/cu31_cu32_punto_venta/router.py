"""Router del punto de venta presencial (CU31-CU32): solo HTTP, sin lógica de negocio."""

import io
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu31_cu32_punto_venta.esquemas import (
    AnulacionPosIn,
    ClientePosOut,
    CobroPosIn,
    CuponPosOut,
    PedidoWebEfectivoOut,
    PrevisualizacionPosOut,
    ReservaPosOut,
    VariantePosOut,
    VentaPosIn,
    VentaPosOut,
)
from modules.compras_pagos.cu31_cu32_punto_venta.servicio import ROLES_CAJA, PuntoVentaServicio
from modules.plataforma.cu12_validar_suscripcion.dependencias import requiere_funcionalidad

router = APIRouter(prefix="/pos", tags=["Punto de Venta (CU31-CU32)"])

Cajero = Depends(require_roles(list(ROLES_CAJA)))
SucursalQuery = Query(None, gt=0, description="Solo el administrador: boutique en la que opera la caja.")


@router.get(
    "/variantes", response_model=List[VariantePosOut],
    summary="Buscar prendas por nombre, categoría o SKU (todas las coincidencias)",
)
def buscar_variantes(
    q: str = Query(..., min_length=2, max_length=100), id_sucursal: Optional[int] = SucursalQuery,
    usuario: UsuarioORM = Cajero, db: Session = Depends(get_db),
) -> List[VariantePosOut]:
    return PuntoVentaServicio.buscar_variantes(db, usuario, q, id_sucursal)


@router.get("/variantes/{sku}", response_model=VariantePosOut, summary="Buscar prenda por SKU")
def buscar_variante(
    sku: str, id_sucursal: Optional[int] = SucursalQuery, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)
) -> VariantePosOut:
    return PuntoVentaServicio.buscar_variante(db, usuario, sku, id_sucursal)


@router.get(
    "/clientes", response_model=List[ClientePosOut],
    summary="Buscar clientes registrados por nombre, apellidos o correo",
)
def buscar_clientes(
    q: str = Query(..., min_length=2, max_length=255), usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)
) -> List[ClientePosOut]:
    return PuntoVentaServicio.buscar_clientes(db, q)


@router.get(
    "/clientes/{id_cliente}/reservas", response_model=List[ReservaPosOut],
    summary="Reservas activas del cliente que esta caja puede cobrar",
)
def reservas_de_cliente(
    id_cliente: int, id_sucursal: Optional[int] = SucursalQuery, usuario: UsuarioORM = Cajero,
    db: Session = Depends(get_db),
) -> List[ReservaPosOut]:
    return PuntoVentaServicio.reservas_de_cliente(db, usuario, id_cliente, id_sucursal)


@router.get(
    "/cupones", response_model=List[CuponPosOut],
    summary="Cupones vigentes con usos disponibles; con q, los que coinciden por código o nombre",
)
def cupones_disponibles(
    q: Optional[str] = Query(None, max_length=50), usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)
) -> List[CuponPosOut]:
    return PuntoVentaServicio.cupones_disponibles(db, q)


@router.get("/reservas/{referencia}", response_model=ReservaPosOut, summary="Cargar una reserva en caja")
def consultar_reserva(
    referencia: str, id_sucursal: Optional[int] = SucursalQuery, usuario: UsuarioORM = Cajero,
    db: Session = Depends(get_db),
) -> ReservaPosOut:
    return PuntoVentaServicio.consultar_reserva(db, usuario, referencia, id_sucursal)


@router.post("/ventas/previsualizar", response_model=PrevisualizacionPosOut, summary="Totales sin registrar")
def previsualizar(datos: VentaPosIn, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> PrevisualizacionPosOut:
    return PuntoVentaServicio.previsualizar(db, usuario, datos)


@router.post(
    "/ventas", response_model=VentaPosOut, status_code=status.HTTP_201_CREATED,
    summary="CU31 · Registrar venta presencial",
    dependencies=[Depends(requiere_funcionalidad("ventas"))],
)
def registrar_venta(datos: VentaPosIn, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> VentaPosOut:
    return PuntoVentaServicio.registrar_venta(db, usuario, datos)


@router.get("/ventas", response_model=List[VentaPosOut], summary="Ventas de caja de la boutique")
def listar_ventas(
    estado: Optional[Literal["pendiente", "pagada", "anulada"]] = Query(None),
    solo_hoy: bool = Query(True),
    id_sucursal: Optional[int] = SucursalQuery,
    usuario: UsuarioORM = Cajero,
    db: Session = Depends(get_db),
) -> List[VentaPosOut]:
    return PuntoVentaServicio.listar_ventas(db, usuario, id_sucursal, estado, solo_hoy)


@router.get("/ventas/{id_venta}", response_model=VentaPosOut, summary="Detalle y datos del comprobante")
def obtener_venta(id_venta: int, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> VentaPosOut:
    return PuntoVentaServicio.obtener_venta(db, usuario, id_venta)


@router.post("/ventas/{id_venta}/cobrar", response_model=VentaPosOut, summary="CU32 · Cobrar en caja")
def cobrar_venta(
    id_venta: int, datos: CobroPosIn, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)
) -> VentaPosOut:
    return PuntoVentaServicio.cobrar_venta(db, usuario, id_venta, datos)


@router.post("/ventas/{id_venta}/anular", response_model=VentaPosOut, summary="Anular una orden pendiente")
def anular_venta(
    id_venta: int, datos: AnulacionPosIn, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)
) -> VentaPosOut:
    return PuntoVentaServicio.anular_venta(db, usuario, id_venta, datos.motivo)


@router.get(
    "/ventas/{id_venta}/comprobante.pdf", summary="Exportar el comprobante en PDF",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}}, 409: {"description": "La venta sigue pendiente"}},
)
def comprobante_pdf(id_venta: int, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> StreamingResponse:
    nombre, contenido = PuntoVentaServicio.comprobante_pdf(db, usuario, id_venta)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get(
    "/pedidos-web-efectivo", response_model=List[PedidoWebEfectivoOut],
    summary="Pedidos web en efectivo por cobrar en esta boutique (se confirman con los endpoints de CU16)",
)
def pedidos_web_efectivo(
    id_sucursal: Optional[int] = SucursalQuery, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)
) -> List[PedidoWebEfectivoOut]:
    return PuntoVentaServicio.pedidos_web_efectivo(db, usuario, id_sucursal)
