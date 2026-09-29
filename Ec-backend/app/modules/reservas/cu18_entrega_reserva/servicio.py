"""Servicio transaccional de dominio para CU18: Atender entrega de reserva en boutique.

Permite buscar citas activas por sucursal, confirmar la entrega en fitting room,
marcar inasistencia liberando el stock al Kardex, o convertir la cita en venta directa de mostrador.
"""

from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, selectinload

from core.errors import AuthorizationError
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import ColorORM, InventarioSucursalORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.comercial.cu28_ventas_reservas.modelos import (
    ReservaDetalleORM,
    ReservaORM,
    VentaDetalleORM,
    VentaORM,
)
from modules.gestion_operativa.cu24_inventario_stock.modelos import MovimientoInventarioORM
from modules.gestion_operativa.modelos import SucursalORM
from modules.reservas.cu18_entrega_reserva.errores import (
    ReservaEstadoInvalidoError,
    ReservaNoEncontradaError,
    SucursalReservaNoAutorizadaError,
)
from modules.reservas.cu18_entrega_reserva.esquemas import (
    ConfirmarEntregaIn,
    ConvertirVentaReservaOut,
    EntregaReservaOut,
    ListadoReservasPendientesOut,
    NoAsistioReservaOut,
    PrendaReservaCajaOut,
    ReservaPendienteCajaOut,
)
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class ServicioEntregaReserva:
    """Orquestador transaccional de recepcion, atencion y liquidacion de reservas en boutique."""

    @classmethod
    def resolver_sucursal_operador(
        cls, usuario: UsuarioORM, id_sucursal_solicitada: Optional[int] = None
    ) -> Optional[int]:
        """Aplica la regla de segregacion territorial estricta para atencion de reservas."""
        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol in ("cajero", "encargado_sucursal"):
            if not usuario.id_sucursal:
                raise AuthorizationError(
                    f"El usuario con rol '{rol}' no tiene una sucursal asignada para atender reservas.",
                    code="CAJERO_SIN_SUCURSAL",
                )
            return usuario.id_sucursal

        if rol in ("administrador", "admin"):
            return id_sucursal_solicitada

        raise AuthorizationError(
            "Su rol no esta autorizado para consultar o despachar reservas de mostrador.",
            code="ACCESO_DENEGADO",
        )

    @classmethod
    def buscar_reservas_pendientes(
        cls,
        db: Session,
        usuario: UsuarioORM,
        q: Optional[str] = None,
        fecha_cita: Optional[datetime | str] = None,
        id_sucursal: Optional[int] = None,
        limite: int = 50,
        salto: int = 0,
    ) -> ListadoReservasPendientesOut:
        """Busca reservas en estados atendibles acotadas a la sucursal del cajero."""
        sucursal_filtro = cls.resolver_sucursal_operador(usuario, id_sucursal)

        stmt = (
            select(ReservaORM)
            .options(
                selectinload(ReservaORM.detalles).selectinload(ReservaDetalleORM.variante).selectinload(VarianteProductoORM.producto),
                selectinload(ReservaORM.detalles).selectinload(ReservaDetalleORM.variante).selectinload(VarianteProductoORM.talla),
                selectinload(ReservaORM.detalles).selectinload(ReservaDetalleORM.variante).selectinload(VarianteProductoORM.color),
                selectinload(ReservaORM.cliente).selectinload(ClienteORM.usuario),
                selectinload(ReservaORM.sucursal),
            )
            .where(ReservaORM.estado.in_(["confirmada", "pendiente", "en_atencion"]))
        )

        if sucursal_filtro is not None:
            stmt = stmt.where(ReservaORM.id_sucursal == sucursal_filtro)

        if q and q.strip():
            cadena = q.strip()
            condiciones = []
            if cadena.upper().startswith("RES-"):
                try:
                    num_parte = int(cadena.upper().replace("RES-", "").split("-")[-1])
                    condiciones.append(ReservaORM.id_reserva == num_parte)
                except ValueError:
                    pass
            elif cadena.isdigit():
                condiciones.append(ReservaORM.id_reserva == int(cadena))

            patron = f"%{cadena}%"
            stmt = stmt.outerjoin(ReservaORM.cliente).outerjoin(ClienteORM.usuario)
            condiciones.extend([
                UsuarioORM.nombres.ilike(patron),
                UsuarioORM.apellidos.ilike(patron),
                UsuarioORM.email.ilike(patron),
                UsuarioORM.telefono.ilike(patron),
            ])
            stmt = stmt.where(or_(*condiciones))

        if fecha_cita:
            if isinstance(fecha_cita, str):
                fecha_cita = datetime.fromisoformat(fecha_cita)
            inicio_dia = datetime.combine(fecha_cita.date(), time.min).replace(tzinfo=timezone.utc)
            fin_dia = datetime.combine(fecha_cita.date(), time.max).replace(tzinfo=timezone.utc)
            stmt = stmt.where(ReservaORM.fecha_hora_atencion.between(inicio_dia, fin_dia))

        stmt_count = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = db.execute(stmt_count).scalar_one()

        stmt = stmt.order_by(ReservaORM.fecha_hora_atencion.asc()).offset(salto).limit(limite)
        reservas = db.execute(stmt).scalars().all()

        items = []
        for r in reservas:
            cod_reserva = f"RES-{r.creado_en.year if r.creado_en else 2026}-{r.id_reserva:04d}"
            nom_cliente = "Cliente Boutique"
            tel_cliente = None
            doc_cliente = None
            if r.cliente and r.cliente.usuario:
                nom_cliente = f"{r.cliente.usuario.nombres} {r.cliente.usuario.apellidos}".strip()
                tel_cliente = r.cliente.usuario.telefono
                doc_cliente = f"ID-{r.cliente.id_cliente}"

            prendas_out = []
            for d in (r.detalles or []):
                var = d.variante
                prod = var.producto if var else None
                talla = var.talla.codigo if var and var.talla else "U"
                color = var.color.nombre if var and var.color else "N/A"
                nom_prod = prod.nombre if prod else "Prenda FashionStore"
                sku = var.sku if var else f"SKU-{d.id_variante}"
                precio_base = prod.precio_base if prod else Decimal("0.00")
                precio_extra = var.precio_extra if var and var.precio_extra else Decimal("0.00")
                precio_tot = Decimal(str(precio_base + precio_extra))

                prendas_out.append(
                    PrendaReservaCajaOut(
                        id_reserva_detalle=d.id_reserva_detalle,
                        id_variante=d.id_variante,
                        sku=sku,
                        nombre_producto=nom_prod,
                        talla=talla,
                        color=color,
                        cantidad=d.cantidad,
                        precio_unitario=precio_tot,
                        ubicacion_percha="Mostrador Fitting Room",
                    )
                )

            items.append(
                ReservaPendienteCajaOut(
                    id_reserva=r.id_reserva,
                    codigo_reserva=cod_reserva,
                    id_cliente=r.id_cliente,
                    cliente_nombre=nom_cliente,
                    cliente_documento=doc_cliente,
                    cliente_telefono=tel_cliente,
                    id_sucursal=r.id_sucursal,
                    nombre_sucursal=r.sucursal.nombre if r.sucursal else f"Sucursal #{r.id_sucursal}",
                    fecha_hora_atencion=r.fecha_hora_atencion,
                    estado=r.estado,
                    canal_origen=r.canal_origen,
                    observacion=r.observacion,
                    prendas=prendas_out,
                )
            )

        return ListadoReservasPendientesOut(total=total, items=items)

    @classmethod
    def confirmar_entrega(
        cls,
        db: Session,
        usuario: UsuarioORM,
        id_reserva: int,
        datos: Optional[ConfirmarEntregaIn] = None,
        ip_origen: Optional[str] = None,
    ) -> EntregaReservaOut:
        """Confirma la recepcion de la clienta en boutique y la entrega de prendas para fitting."""
        stmt = (
            select(ReservaORM)
            .options(
                selectinload(ReservaORM.detalles).selectinload(ReservaDetalleORM.variante),
                selectinload(ReservaORM.sucursal),
            )
            .where(ReservaORM.id_reserva == id_reserva)
        )
        bind = db.get_bind()
        if bind and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()

        reserva = db.execute(stmt).scalars().first()
        if not reserva:
            raise ReservaNoEncontradaError(id_reserva)

        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol in ("cajero", "encargado_sucursal"):
            if not usuario.id_sucursal or reserva.id_sucursal != usuario.id_sucursal:
                raise SucursalReservaNoAutorizadaError(
                    sucursal_reserva=reserva.id_sucursal,
                    sucursal_usuario=usuario.id_sucursal,
                )

        cod_reserva = f"RES-{reserva.creado_en.year if reserva.creado_en else 2026}-{reserva.id_reserva:04d}"

        if reserva.estado not in ("confirmada", "pendiente", "en_atencion"):
            raise ReservaEstadoInvalidoError(
                codigo_reserva=cod_reserva,
                estado_actual=reserva.estado,
                accion="entregar",
            )

        ahora_utc = datetime.now(timezone.utc)
        reserva.estado = "atendida"
        reserva.atendido_por = usuario.id_usuario
        reserva.atendido_en = ahora_utc
        if datos and datos.observaciones:
            reserva.observacion = (reserva.observacion or "") + f" | Entrega: {datos.observaciones}"

        # Liberar la cantidad reservada en el inventario fisico ya que la cita concluyo
        for det in (reserva.detalles or []):
            stmt_inv = select(InventarioSucursalORM).where(
                InventarioSucursalORM.id_variante == det.id_variante,
                InventarioSucursalORM.id_sucursal == reserva.id_sucursal,
            )
            if bind and bind.dialect.name != "sqlite":
                stmt_inv = stmt_inv.with_for_update()

            inv = db.execute(stmt_inv).scalars().first()
            if inv:
                saldo_ant = inv.cantidad_disponible
                inv.cantidad_reservada = max(0, inv.cantidad_reservada - det.cantidad)
                # Las prendas de fitting retornan a disponible (si la clienta compra, se descuentan en venta)
                inv.cantidad_disponible += det.cantidad
                saldo_post = inv.cantidad_disponible

                mov = MovimientoInventarioORM(
                    id_inventario=inv.id_inventario,
                    tipo_movimiento="liberacion_reserva",
                    cantidad=det.cantidad,
                    saldo_anterior=saldo_ant,
                    saldo_nuevo=saldo_post,
                    motivo=f"Cita concluida exitosamente {cod_reserva}",
                    id_usuario=usuario.id_usuario,
                    referencia_documento=cod_reserva,
                    creado_en=ahora_utc,
                )
                db.add(mov)

        db.commit()
        db.refresh(reserva)

        cajero_nom = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=cajero_nom,
            accion="ENTREGA_RESERVA",
            tabla_modulo="reservas",
            direccion_ip=ip_origen,
            severidad="INFO",
            payload_nuevo={
                "id_reserva": reserva.id_reserva,
                "codigo_reserva": cod_reserva,
                "estado": "atendida",
                "id_sucursal": reserva.id_sucursal,
                "atendido_por": usuario.id_usuario,
            },
            db=db,
        )

        return EntregaReservaOut(
            id_reserva=reserva.id_reserva,
            codigo_reserva=cod_reserva,
            estado=reserva.estado,
            atendido_por=usuario.id_usuario,
            atendido_en=ahora_utc,
            mensaje="Entrega y atencion de reserva completada exitosamente.",
        )

    @classmethod
    def marcar_no_asistio(
        cls,
        db: Session,
        usuario: UsuarioORM,
        id_reserva: int,
        ip_origen: Optional[str] = None,
    ) -> NoAsistioReservaOut:
        """Cancela la reserva por inasistencia y devuelve el stock apartado al disponible."""
        stmt = (
            select(ReservaORM)
            .options(
                selectinload(ReservaORM.detalles).selectinload(ReservaDetalleORM.variante),
                selectinload(ReservaORM.sucursal),
            )
            .where(ReservaORM.id_reserva == id_reserva)
        )
        bind = db.get_bind()
        if bind and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()

        reserva = db.execute(stmt).scalars().first()
        if not reserva:
            raise ReservaNoEncontradaError(id_reserva)

        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol in ("cajero", "encargado_sucursal"):
            if not usuario.id_sucursal or reserva.id_sucursal != usuario.id_sucursal:
                raise SucursalReservaNoAutorizadaError(
                    sucursal_reserva=reserva.id_sucursal,
                    sucursal_usuario=usuario.id_sucursal,
                )

        cod_reserva = f"RES-{reserva.creado_en.year if reserva.creado_en else 2026}-{reserva.id_reserva:04d}"

        if reserva.estado not in ("confirmada", "pendiente", "en_atencion"):
            raise ReservaEstadoInvalidoError(
                codigo_reserva=cod_reserva,
                estado_actual=reserva.estado,
                accion="marcar como no asistida",
            )

        ahora_utc = datetime.now(timezone.utc)
        reserva.estado = "cancelada"
        reserva.observacion = (reserva.observacion or "") + " | Cancelada por inasistencia del cliente"

        items_liberados = 0
        for det in (reserva.detalles or []):
            stmt_inv = select(InventarioSucursalORM).where(
                InventarioSucursalORM.id_variante == det.id_variante,
                InventarioSucursalORM.id_sucursal == reserva.id_sucursal,
            )
            if bind and bind.dialect.name != "sqlite":
                stmt_inv = stmt_inv.with_for_update()

            inv = db.execute(stmt_inv).scalars().first()
            if inv:
                saldo_ant = inv.cantidad_disponible
                inv.cantidad_reservada = max(0, inv.cantidad_reservada - det.cantidad)
                inv.cantidad_disponible += det.cantidad
                saldo_post = inv.cantidad_disponible
                items_liberados += det.cantidad

                mov = MovimientoInventarioORM(
                    id_inventario=inv.id_inventario,
                    tipo_movimiento="liberacion_reserva",
                    cantidad=det.cantidad,
                    saldo_anterior=saldo_ant,
                    saldo_nuevo=saldo_post,
                    motivo=f"Inasistencia a cita de fitting {cod_reserva}",
                    id_usuario=usuario.id_usuario,
                    referencia_documento=cod_reserva,
                    creado_en=ahora_utc,
                )
                db.add(mov)

        db.commit()
        db.refresh(reserva)

        cajero_nom = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=cajero_nom,
            accion="ENTREGA_RESERVA",
            tabla_modulo="reservas",
            direccion_ip=ip_origen,
            severidad="INFO",
            payload_nuevo={
                "id_reserva": reserva.id_reserva,
                "codigo_reserva": cod_reserva,
                "estado": "cancelada",
                "motivo": "no_asistio",
                "items_liberados": items_liberados,
            },
            db=db,
        )

        return NoAsistioReservaOut(
            id_reserva=reserva.id_reserva,
            codigo_reserva=cod_reserva,
            estado="cancelada",
            items_liberados=items_liberados,
            mensaje="Reserva marcada como no asistida. Existencias liberadas al stock disponible.",
        )

    @classmethod
    def convertir_a_venta(
        cls,
        db: Session,
        usuario: UsuarioORM,
        id_reserva: int,
        ip_origen: Optional[str] = None,
    ) -> ConvertirVentaReservaOut:
        """Convierte una reserva presencial a una orden de venta de mostrador para liquidar en caja."""
        stmt = (
            select(ReservaORM)
            .options(
                selectinload(ReservaORM.detalles).selectinload(ReservaDetalleORM.variante).selectinload(VarianteProductoORM.producto),
                selectinload(ReservaORM.sucursal),
            )
            .where(ReservaORM.id_reserva == id_reserva)
        )
        bind = db.get_bind()
        if bind and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()

        reserva = db.execute(stmt).scalars().first()
        if not reserva:
            raise ReservaNoEncontradaError(id_reserva)

        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol in ("cajero", "encargado_sucursal"):
            if not usuario.id_sucursal or reserva.id_sucursal != usuario.id_sucursal:
                raise SucursalReservaNoAutorizadaError(
                    sucursal_reserva=reserva.id_sucursal,
                    sucursal_usuario=usuario.id_sucursal,
                )

        cod_reserva = f"RES-{reserva.creado_en.year if reserva.creado_en else 2026}-{reserva.id_reserva:04d}"

        if reserva.estado not in ("confirmada", "pendiente", "en_atencion"):
            raise ReservaEstadoInvalidoError(
                codigo_reserva=cod_reserva,
                estado_actual=reserva.estado,
                accion="convertir a venta",
            )

        ahora_utc = datetime.now(timezone.utc)

        # Generar numero de comprobante FS-YYYY-XXXXXX
        secuencia_val = int(ahora_utc.timestamp()) % 1000000
        try:
            sec_db = db.execute(text("SELECT nextval('fashionstore.seq_comprobante_venta')")).scalar_one()
            secuencia_val = int(sec_db)
        except Exception:
            pass

        numero_comprobante = f"FS-{ahora_utc.year}-{secuencia_val:06d}"

        # Computar total de la venta
        total_acum = Decimal("0.00")
        lineas_venta = []
        for det in (reserva.detalles or []):
            var = det.variante
            prod = var.producto if var else None
            p_base = prod.precio_base if prod else Decimal("0.00")
            p_extra = var.precio_extra if var and var.precio_extra else Decimal("0.00")
            p_unit = Decimal(str(p_base + p_extra))
            subt = p_unit * det.cantidad
            total_acum += subt

            lineas_venta.append(
                VentaDetalleORM(
                    id_variante=det.id_variante,
                    cantidad=det.cantidad,
                    precio_unitario=p_unit,
                    id_sucursal=reserva.id_sucursal,
                )
            )

        nueva_venta = VentaORM(
            numero_comprobante=numero_comprobante,
            id_cliente=reserva.id_cliente,
            id_sucursal=reserva.id_sucursal,
            id_reserva=reserva.id_reserva,
            tipo_venta="presencial",
            estado="pendiente",
            subtotal=total_acum,
            descuento=Decimal("0.00"),
            total=total_acum,
            fecha_venta=ahora_utc,
            tipo_entrega="mostrador",
            detalles=lineas_venta,
        )
        db.add(nueva_venta)

        # Marcar la reserva como atendida
        reserva.estado = "atendida"
        reserva.atendido_por = usuario.id_usuario
        reserva.atendido_en = ahora_utc
        reserva.observacion = (reserva.observacion or "") + f" | Convertida a venta presencial {numero_comprobante}"

        db.commit()
        db.refresh(nueva_venta)

        cajero_nom = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=cajero_nom,
            accion="ENTREGA_RESERVA",
            tabla_modulo="reservas",
            direccion_ip=ip_origen,
            severidad="INFO",
            payload_nuevo={
                "id_reserva": reserva.id_reserva,
                "codigo_reserva": cod_reserva,
                "id_venta": nueva_venta.id_venta,
                "numero_comprobante": nueva_venta.numero_comprobante,
                "total": float(nueva_venta.total),
                "accion": "conversion_a_venta",
            },
            db=db,
        )

        id_venta_val = nueva_venta.id_venta if nueva_venta.id_venta is not None else 1

        return ConvertirVentaReservaOut(
            id_venta=id_venta_val,
            numero_comprobante=nueva_venta.numero_comprobante,
            id_reserva=reserva.id_reserva,
            total=nueva_venta.total,
            estado_venta=nueva_venta.estado,
            mensaje="Reserva convertida exitosamente a venta presencial para cobro en caja.",
        )
