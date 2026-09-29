"""Servicio transaccional de dominio para CU17: Registrar cobro en caja.

Implementa la logica de autorizacion territorial, calculo de vuelto, liquidacion
de ordenes presenciales y Click & Collect, asiento contable en Kardex y auditoria.
"""

from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from core.errors import AuthorizationError
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import ColorORM, InventarioSucursalORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.comercial.cu17_cobro_caja.errores import (
    MetodoPagoInvalidoError,
    MontoInsuficienteError,
    SucursalNoAutorizadaError,
    VentaEstadoInvalidoError,
    VentaNoEncontradaError,
    VentaYaLiquidadaError,
)
from modules.comercial.cu17_cobro_caja.esquemas import (
    CobroCajaIn,
    CobroCajaOut,
    DetallePrendaCajaOut,
    ListadoOrdenesPendientesOut,
    OrdenPendienteOut,
)
from modules.comercial.cu28_ventas_reservas.modelos import (
    EmpleadoORM,
    PagoORM,
    VentaDetalleORM,
    VentaORM,
)
from modules.gestion_operativa.cu24_inventario_stock.modelos import MovimientoInventarioORM
from modules.gestion_operativa.modelos import SucursalORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class ServicioCobroCaja:
    """Orquestador transaccional de punto de venta y cobro en mostrador."""

    MAPA_METODOS_PAGO = {
        "efectivo": "efectivo",
        "tarjeta_pos": "tarjeta_debito",
        "tarjeta_debito": "tarjeta_debito",
        "tarjeta_credito": "tarjeta_credito",
        "qr_estatico": "qr",
        "qr": "qr",
    }

    @classmethod
    def resolver_sucursal_operador(
        cls, usuario: UsuarioORM, id_sucursal_solicitada: Optional[int] = None
    ) -> Optional[int]:
        """Aplica la regla de segregacion territorial estricta segun el rol del usuario."""
        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol in ("cajero", "encargado_sucursal"):
            if not usuario.id_sucursal:
                raise AuthorizationError(
                    f"El usuario con rol '{rol}' no tiene una sucursal asignada para operar.",
                    code="CAJERO_SIN_SUCURSAL",
                )
            return usuario.id_sucursal

        if rol in ("administrador", "admin"):
            return id_sucursal_solicitada

        raise AuthorizationError(
            "Su rol no esta autorizado para operar o supervisar operaciones de caja.",
            code="ACCESO_DENEGADO",
        )

    @classmethod
    def buscar_ordenes_pendientes(
        cls,
        db: Session,
        usuario: UsuarioORM,
        q: Optional[str] = None,
        fecha_desde: Optional[datetime | str] = None,
        fecha_hasta: Optional[datetime | str] = None,
        id_sucursal: Optional[int] = None,
        limite: int = 50,
        salto: int = 0,
    ) -> ListadoOrdenesPendientesOut:
        """Busca ordenes en estado pendiente dentro del alcance territorial del operador."""
        sucursal_filtro = cls.resolver_sucursal_operador(usuario, id_sucursal)

        stmt = (
            select(VentaORM)
            .options(
                selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.producto),
                selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.talla),
                selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.color),
                selectinload(VentaORM.cliente).selectinload(ClienteORM.usuario),
                selectinload(VentaORM.sucursal),
            )
            .where(VentaORM.estado == "pendiente")
        )

        if sucursal_filtro is not None:
            stmt = stmt.where(VentaORM.id_sucursal == sucursal_filtro)

        if q and q.strip():
            patron = f"%{q.strip()}%"
            stmt = stmt.outerjoin(VentaORM.cliente).outerjoin(ClienteORM.usuario)
            stmt = stmt.where(
                or_(
                    VentaORM.numero_comprobante.ilike(patron),
                    UsuarioORM.nombres.ilike(patron),
                    UsuarioORM.apellidos.ilike(patron),
                    UsuarioORM.email.ilike(patron),
                    UsuarioORM.telefono.ilike(patron),
                )
            )

        if fecha_desde:
            if isinstance(fecha_desde, str):
                fecha_desde = datetime.fromisoformat(fecha_desde)
            if fecha_desde.tzinfo is None:
                fecha_desde = fecha_desde.replace(tzinfo=timezone.utc)
            stmt = stmt.where(VentaORM.fecha_venta >= fecha_desde)

        if fecha_hasta:
            if isinstance(fecha_hasta, str):
                fecha_hasta = datetime.fromisoformat(fecha_hasta)
            if fecha_hasta.tzinfo is None:
                fecha_hasta = fecha_hasta.replace(tzinfo=timezone.utc)
            stmt = stmt.where(VentaORM.fecha_venta <= fecha_hasta)

        # Conteo total
        stmt_count = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = db.execute(stmt_count).scalar_one()

        stmt = stmt.order_by(VentaORM.fecha_venta.desc()).offset(salto).limit(limite)
        ventas = db.execute(stmt).scalars().all()

        items = []
        for v in ventas:
            nom_cliente = "Cliente General"
            tel_cliente = None
            doc_cliente = None
            if v.cliente and v.cliente.usuario:
                nom_cliente = f"{v.cliente.usuario.nombres} {v.cliente.usuario.apellidos}".strip()
                tel_cliente = v.cliente.usuario.telefono
                doc_cliente = f"ID-{v.cliente.id_cliente}"

            detalles_out = []
            for d in (v.detalles or []):
                var = d.variante
                prod = var.producto if var else None
                talla = var.talla.codigo if var and var.talla else "U"
                color = var.color.nombre if var and var.color else "N/A"
                nom_prod = prod.nombre if prod else "Prenda FashionStore"
                sku = var.sku if var else f"SKU-{d.id_variante}"
                subtotal_calc = d.subtotal_linea or (d.cantidad * d.precio_unitario)

                detalles_out.append(
                    DetallePrendaCajaOut(
                        id_venta_detalle=d.id_venta_detalle,
                        id_variante=d.id_variante,
                        sku=sku,
                        nombre_producto=nom_prod,
                        talla=talla,
                        color=color,
                        cantidad=d.cantidad,
                        precio_unitario=Decimal(str(d.precio_unitario)),
                        subtotal_linea=Decimal(str(subtotal_calc)),
                    )
                )

            items.append(
                OrdenPendienteOut(
                    id_venta=v.id_venta,
                    numero_comprobante=v.numero_comprobante,
                    fecha_venta=v.fecha_venta,
                    id_sucursal=v.id_sucursal,
                    nombre_sucursal=v.sucursal.nombre if v.sucursal else f"Sucursal #{v.id_sucursal}",
                    id_cliente=v.id_cliente,
                    cliente_nombre=nom_cliente,
                    cliente_documento=doc_cliente,
                    cliente_telefono=tel_cliente,
                    tipo_venta=v.tipo_venta,
                    estado=v.estado,
                    subtotal=Decimal(str(v.subtotal)),
                    descuento=Decimal(str(v.descuento)),
                    total=Decimal(str(v.total)),
                    detalles=detalles_out,
                )
            )

        return ListadoOrdenesPendientesOut(total=total, items=items)

    @classmethod
    def cobrar_orden(
        cls,
        db: Session,
        usuario: UsuarioORM,
        datos: CobroCajaIn,
        ip_origen: Optional[str] = None,
    ) -> CobroCajaOut:
        """Asienta el cobro presencial de una orden en mostrador con validacion de vuelto y Kardex."""
        # 1. Cargar la orden con bloqueo transaccional si el motor lo soporta
        stmt = (
            select(VentaORM)
            .options(
                selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante),
                selectinload(VentaORM.cliente).selectinload(ClienteORM.usuario),
                selectinload(VentaORM.sucursal),
            )
            .where(VentaORM.id_venta == datos.id_venta)
        )
        bind = db.get_bind()
        if bind and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()

        venta = db.execute(stmt).scalars().first()
        if not venta:
            raise VentaNoEncontradaError(datos.id_venta)

        # 2. Segregacion territorial obligatoria
        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol in ("cajero", "encargado_sucursal"):
            if not usuario.id_sucursal or venta.id_sucursal != usuario.id_sucursal:
                raise SucursalNoAutorizadaError(
                    sucursal_orden=venta.id_sucursal,
                    sucursal_usuario=usuario.id_sucursal,
                )

        # 3. Validar estado de la orden
        if venta.estado == "pagada":
            raise VentaYaLiquidadaError(venta.numero_comprobante)
        if venta.estado != "pendiente":
            raise VentaEstadoInvalidoError(venta.numero_comprobante, venta.estado)

        # 4. Validar dinero entregado y computar vuelto
        monto_recibido_dec = Decimal(str(datos.monto_recibido))
        total_orden_dec = Decimal(str(venta.total))

        if monto_recibido_dec < total_orden_dec:
            raise MontoInsuficienteError(monto_recibido_dec, total_orden_dec)

        cambio_devuelto_dec = monto_recibido_dec - total_orden_dec

        # 5. Normalizar metodo de pago
        metodo_db = cls.MAPA_METODOS_PAGO.get(datos.metodo_pago)
        if not metodo_db:
            raise MetodoPagoInvalidoError(datos.metodo_pago)

        ahora_utc = datetime.now(timezone.utc)

        # 6. Crear registro inmutable en pagos
        payload_audit = {
            "monto_recibido": float(monto_recibido_dec),
            "cambio_devuelto": float(cambio_devuelto_dec),
            "metodo_ingresado": datos.metodo_pago,
            "observaciones": datos.observaciones,
            "cajero_id": usuario.id_usuario,
            "cajero_nombre": f"{usuario.nombres} {usuario.apellidos}".strip(),
        }

        pago = PagoORM(
            id_venta=venta.id_venta,
            metodo_pago=metodo_db,
            monto=total_orden_dec,
            estado="confirmado",
            referencia_pasarela=f"POS-CAJA-{venta.id_venta}-{int(ahora_utc.timestamp())}",
            payload_respuesta=payload_audit,
            creado_en=ahora_utc,
            confirmado_en=ahora_utc,
        )
        db.add(pago)

        # 7. Actualizar estado de venta
        venta.estado = "pagada"

        # Asociar cajero si existe registro de empleado
        stmt_emp = select(EmpleadoORM).where(EmpleadoORM.id_empleado == usuario.id_usuario)
        empleado = db.execute(stmt_emp).scalars().first()
        if empleado:
            venta.id_cajero = empleado.id_empleado

        # 8. Movimiento de Kardex inmutable
        for det in (venta.detalles or []):
            stmt_inv = select(InventarioSucursalORM).where(
                InventarioSucursalORM.id_variante == det.id_variante,
                InventarioSucursalORM.id_sucursal == venta.id_sucursal,
            )
            if bind and bind.dialect.name != "sqlite":
                stmt_inv = stmt_inv.with_for_update()

            inv = db.execute(stmt_inv).scalars().first()
            if inv:
                saldo_ant = inv.cantidad_disponible
                # Si la venta proviene de una reserva, la existencia ya estaba en cantidad_reservada
                if venta.id_reserva:
                    inv.cantidad_reservada = max(0, inv.cantidad_reservada - det.cantidad)
                    saldo_post = inv.cantidad_disponible
                else:
                    # Si es venta presencial directa sin retencion previa, descontar de disponible
                    # Verificamos si no hubo retencion previa por CU15
                    if venta.tipo_venta == "presencial":
                        inv.cantidad_disponible = max(0, inv.cantidad_disponible - det.cantidad)
                    saldo_post = inv.cantidad_disponible

                mov = MovimientoInventarioORM(
                    id_inventario=inv.id_inventario,
                    tipo_movimiento="venta_confirmada",
                    cantidad=det.cantidad,
                    saldo_anterior=saldo_ant,
                    saldo_nuevo=saldo_post,
                    motivo=f"Cobro en caja fisica comprobante {venta.numero_comprobante}",
                    id_usuario=usuario.id_usuario,
                    referencia_documento=venta.numero_comprobante,
                    creado_en=ahora_utc,
                )
                db.add(mov)

        db.commit()
        db.refresh(pago)
        db.refresh(venta)

        # 9. Trazabilidad inmutable en bitacora no bloqueante
        cajero_nom = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=cajero_nom,
            accion="COBRO_CAJA",
            tabla_modulo="ventas",
            direccion_ip=ip_origen,
            severidad="INFO",
            payload_nuevo={
                "id_venta": venta.id_venta,
                "numero_comprobante": venta.numero_comprobante,
                "id_pago": pago.id_pago,
                "total": float(total_orden_dec),
                "monto_recibido": float(monto_recibido_dec),
                "cambio_devuelto": float(cambio_devuelto_dec),
                "metodo_pago": datos.metodo_pago,
                "id_sucursal": venta.id_sucursal,
            },
            db=db,
        )

        id_pago_val = pago.id_pago if pago.id_pago is not None else 1

        return CobroCajaOut(
            id_pago=id_pago_val,
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            monto_total=total_orden_dec,
            monto_recibido=monto_recibido_dec,
            cambio_devuelto=cambio_devuelto_dec,
            metodo_pago=datos.metodo_pago,
            estado_venta=venta.estado,
            estado_pago=pago.estado,
            cajero_id=usuario.id_usuario,
            cajero_nombre=cajero_nom,
            fecha_cobro=pago.confirmado_en or ahora_utc,
            observaciones=datos.observaciones,
        )
