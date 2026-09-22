"""Servicio de negocio y analitica para CU28: Consultar ventas y reservas."""

from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import ColorORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.comercial.cu28_ventas_reservas.errores import (
    RangoFechasInvalidoError,
    ReservaNoEncontradaError,
    SucursalConsultaInvalidaError,
    VentaNoEncontradaError,
)
from modules.comercial.cu28_ventas_reservas.esquemas import (
    LineaDetalleOut,
    MetricasTransaccionalesOut,
    PagoItemOut,
    ReservaDetalleCompletoOut,
    RespuestaPaginadaTransaccionesOut,
    TransaccionFiltrosIn,
    TransaccionResumenItemOut,
    VentaDetalleCompletoOut,
)
from modules.comercial.cu28_ventas_reservas.modelos import (
    EmpleadoORM,
    PagoORM,
    ReservaDetalleORM,
    ReservaORM,
    VentaDetalleORM,
    VentaORM,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM


class ServicioConsultarVentasReservas:
    """Orquestador de consultas analiticas y auditoria de transacciones."""

    def resolver_alcance_sucursal(
        self, usuario: UsuarioORM, id_sucursal_solicitado: Optional[int]
    ) -> Optional[int]:
        """Aplica las politicas RBAC de segregacion territorial por sucursal."""
        rol = str(usuario.rol or "").lower().strip()
        if rol in ("administrador", "admin"):
            return id_sucursal_solicitado
        elif rol == "encargado_sucursal":
            if not usuario.id_sucursal:
                raise SucursalConsultaInvalidaError(
                    "El encargado no tiene una sucursal asignada en su perfil."
                )
            return usuario.id_sucursal
        raise SucursalConsultaInvalidaError(
            "No cuenta con privilegios para consultar transacciones de la red."
        )

    def obtener_metricas(
        self, db: Session, id_sucursal: Optional[int] = None
    ) -> MetricasTransaccionalesOut:
        """Calcula indicadores cuantitativos consolidados de ventas y reservas."""
        # 1. Total Facturado y Ventas Concluidas
        q_ventas = select(
            func.coalesce(func.sum(VentaORM.total), 0),
            func.count(VentaORM.id_venta),
        ).where(VentaORM.estado == "pagada")

        if id_sucursal is not None:
            q_ventas = q_ventas.where(VentaORM.id_sucursal == id_sucursal)

        res_v = db.execute(q_ventas).first()
        total_facturado = Decimal(str(res_v[0])) if res_v else Decimal("0.00")
        ventas_concluidas = int(res_v[1]) if res_v else 0

        # 2. Reservas Activas (pendiente, confirmada, en_atencion)
        q_reservas = select(func.count(ReservaORM.id_reserva)).where(
            ReservaORM.estado.in_(["pendiente", "confirmada", "en_atencion"])
        )
        if id_sucursal is not None:
            q_reservas = q_reservas.where(ReservaORM.id_sucursal == id_sucursal)

        reservas_activas = int(db.execute(q_reservas).scalar() or 0)

        # 3. Ticket Promedio
        ticket_promedio = (
            total_facturado / Decimal(str(ventas_concluidas))
            if ventas_concluidas > 0
            else Decimal("0.00")
        )

        return MetricasTransaccionalesOut(
            monto_total_facturado=Decimal(str(round(total_facturado, 2))),
            total_ventas_concluidas=ventas_concluidas,
            reservas_activas=reservas_activas,
            ticket_promedio=Decimal(str(round(ticket_promedio, 2))),
        )

    def _mapear_resumen_venta(self, v: VentaORM) -> TransaccionResumenItemOut:
        """Transforma una entidad VentaORM en item de resumen unificado."""
        nombre_cli = "Cliente Mostrador"
        email_cli = None
        tel_cli = None
        if v.cliente and v.cliente.usuario:
            nombre_cli = f"{v.cliente.usuario.nombres} {v.cliente.usuario.apellidos}".strip()
            email_cli = v.cliente.usuario.email
            tel_cli = v.cliente.usuario.telefono

        nombre_suc = v.sucursal.nombre if v.sucursal else "Sucursal"
        ciudad_suc = v.sucursal.ciudad.nombre if v.sucursal and v.sucursal.ciudad else "Bolivia"
        cant_items = sum(d.cantidad for d in v.detalles) if v.detalles else 0

        return TransaccionResumenItemOut(
            id_transaccion=v.id_venta,
            tipo_operacion="venta",
            codigo_comprobante=v.numero_comprobante,
            fecha=v.fecha_venta,
            id_cliente=v.id_cliente,
            nombre_cliente=nombre_cli,
            email_cliente=email_cli,
            telefono_cliente=tel_cli,
            id_sucursal=v.id_sucursal,
            nombre_sucursal=nombre_suc,
            ciudad_sucursal=ciudad_suc,
            canal=str(v.tipo_venta),
            estado=str(v.estado),
            total_monto=Decimal(str(v.total)),
            cantidad_items=cant_items,
        )

    def _mapear_resumen_reserva(self, r: ReservaORM) -> TransaccionResumenItemOut:
        """Transforma una entidad ReservaORM en item de resumen unificado."""
        nombre_cli = "Cliente Registrado"
        email_cli = None
        tel_cli = None
        if r.cliente and r.cliente.usuario:
            nombre_cli = f"{r.cliente.usuario.nombres} {r.cliente.usuario.apellidos}".strip()
            email_cli = r.cliente.usuario.email
            tel_cli = r.cliente.usuario.telefono

        nombre_suc = r.sucursal.nombre if r.sucursal else "Sucursal"
        ciudad_suc = r.sucursal.ciudad.nombre if r.sucursal and r.sucursal.ciudad else "Bolivia"
        cant_items = sum(d.cantidad for d in r.detalles) if r.detalles else 0

        # Estimacion de valor monetario de las prendas reservadas
        total_estimado = Decimal("0.00")
        if r.detalles:
            for d in r.detalles:
                if d.variante and d.variante.producto:
                    precio = d.variante.producto.precio_base + d.variante.precio_extra
                    total_estimado += Decimal(str(precio)) * d.cantidad

        return TransaccionResumenItemOut(
            id_transaccion=r.id_reserva,
            tipo_operacion="reserva",
            codigo_comprobante=f"RES-{r.id_reserva:05d}",
            fecha=r.creado_en,
            id_cliente=r.id_cliente,
            nombre_cliente=nombre_cli,
            email_cliente=email_cli,
            telefono_cliente=tel_cli,
            id_sucursal=r.id_sucursal,
            nombre_sucursal=nombre_suc,
            ciudad_sucursal=ciudad_suc,
            canal=str(r.canal_origen),
            estado=str(r.estado),
            total_monto=Decimal(str(round(total_estimado, 2))),
            cantidad_items=cant_items,
        )

    def listar_transacciones(
        self,
        db: Session,
        filtros: TransaccionFiltrosIn,
        usuario: UsuarioORM,
    ) -> RespuestaPaginadaTransaccionesOut:
        """Retorna listado paginado unificado de ventas y reservas aplicando filtros multicriterio."""
        if filtros.fecha_desde and filtros.fecha_hasta:
            if filtros.fecha_desde > filtros.fecha_hasta:
                raise RangoFechasInvalidoError()

        id_sucursal_efectivo = self.resolver_alcance_sucursal(usuario, filtros.id_sucursal)

        incluir_ventas = filtros.tipo_operacion in ("venta", "todas")
        incluir_reservas = filtros.tipo_operacion in ("reserva", "todas")

        # Si se especifica un metodo de pago, solo las ventas lo poseen
        if filtros.metodo_pago and filtros.metodo_pago.strip():
            incluir_reservas = False

        lista_items: List[TransaccionResumenItemOut] = []

        # -------------------------------------------------------------
        # 1. Consulta de Ventas
        # -------------------------------------------------------------
        if incluir_ventas:
            query_v = select(VentaORM).options(
                joinedload(VentaORM.cliente).joinedload(ClienteORM.usuario),
                joinedload(VentaORM.sucursal).joinedload(SucursalORM.ciudad),
                selectinload(VentaORM.detalles),
            )
            cond_v = []
            if id_sucursal_efectivo is not None:
                cond_v.append(VentaORM.id_sucursal == id_sucursal_efectivo)

            if filtros.estado and filtros.estado != "todos":
                cond_v.append(VentaORM.estado == filtros.estado)

            if filtros.fecha_desde:
                cond_v.append(VentaORM.fecha_venta >= filtros.fecha_desde)
            if filtros.fecha_hasta:
                cond_v.append(VentaORM.fecha_venta <= filtros.fecha_hasta)

            if filtros.canal_origen and filtros.canal_origen != "todos":
                mapa_canales = {
                    "web": "digital_web",
                    "movil": "digital_movil",
                    "sucursal": "presencial",
                }
                canal_esperado = mapa_canales.get(filtros.canal_origen, filtros.canal_origen)
                cond_v.append(VentaORM.tipo_venta == canal_esperado)

            if filtros.metodo_pago and filtros.metodo_pago != "todos":
                query_v = query_v.join(VentaORM.pagos)
                cond_v.append(PagoORM.metodo_pago == filtros.metodo_pago)

            if filtros.q and filtros.q.strip():
                t = f"%{filtros.q.strip()}%"
                query_v = query_v.outerjoin(VentaORM.cliente).outerjoin(ClienteORM.usuario)
                cond_v.append(
                    or_(
                        VentaORM.numero_comprobante.ilike(t),
                        UsuarioORM.nombres.ilike(t),
                        UsuarioORM.apellidos.ilike(t),
                        UsuarioORM.email.ilike(t),
                    )
                )

            if cond_v:
                query_v = query_v.where(and_(*cond_v))

            ventas_orm = db.execute(query_v).unique().scalars().all()
            lista_items.extend([self._mapear_resumen_venta(v) for v in ventas_orm])

        # -------------------------------------------------------------
        # 2. Consulta de Reservas
        # -------------------------------------------------------------
        if incluir_reservas:
            query_r = select(ReservaORM).options(
                joinedload(ReservaORM.cliente).joinedload(ClienteORM.usuario),
                joinedload(ReservaORM.sucursal).joinedload(SucursalORM.ciudad),
                selectinload(ReservaORM.detalles).joinedload(ReservaDetalleORM.variante).joinedload(VarianteProductoORM.producto),
            )
            cond_r = []
            if id_sucursal_efectivo is not None:
                cond_r.append(ReservaORM.id_sucursal == id_sucursal_efectivo)

            if filtros.estado and filtros.estado != "todos":
                cond_r.append(ReservaORM.estado == filtros.estado)

            if filtros.fecha_desde:
                cond_r.append(ReservaORM.creado_en >= filtros.fecha_desde)
            if filtros.fecha_hasta:
                cond_r.append(ReservaORM.creado_en <= filtros.fecha_hasta)

            if filtros.canal_origen and filtros.canal_origen != "todos":
                cond_r.append(ReservaORM.canal_origen == filtros.canal_origen)

            if filtros.q and filtros.q.strip():
                t = f"%{filtros.q.strip()}%"
                query_r = query_r.outerjoin(ReservaORM.cliente).outerjoin(ClienteORM.usuario)
                cond_r.append(
                    or_(
                        func.cast(ReservaORM.id_reserva, String).ilike(t),
                        UsuarioORM.nombres.ilike(t),
                        UsuarioORM.apellidos.ilike(t),
                        UsuarioORM.email.ilike(t),
                    )
                )

            if cond_r:
                query_r = query_r.where(and_(*cond_r))

            reservas_orm = db.execute(query_r).unique().scalars().all()
            lista_items.extend([self._mapear_resumen_reserva(r) for r in reservas_orm])

        # -------------------------------------------------------------
        # 3. Ordenacion Unificada
        # -------------------------------------------------------------
        criterio = filtros.ordenar_por or "creado_en_desc"
        if criterio == "creado_en_asc":
            lista_items.sort(key=lambda x: x.fecha)
        elif criterio == "total_desc":
            lista_items.sort(key=lambda x: x.total_monto, reverse=True)
        elif criterio == "total_asc":
            lista_items.sort(key=lambda x: x.total_monto)
        elif criterio == "fecha_desc":
            lista_items.sort(key=lambda x: x.fecha, reverse=True)
        else:
            # Por defecto: creado_en_desc
            lista_items.sort(key=lambda x: x.fecha, reverse=True)

        total = len(lista_items)
        total_paginas = max(1, ceil(total / filtros.limite)) if total > 0 else 1

        # -------------------------------------------------------------
        # 4. Paginacion en Memoria
        # -------------------------------------------------------------
        offset = (filtros.pagina - 1) * filtros.limite
        items_paginados = lista_items[offset : offset + filtros.limite]

        # -------------------------------------------------------------
        # 5. Metricas Consolidadas
        # -------------------------------------------------------------
        metricas = self.obtener_metricas(db, id_sucursal_efectivo)

        return RespuestaPaginadaTransaccionesOut(
            items=items_paginados,
            metricas=metricas,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )

    def obtener_detalle_venta(
        self, db: Session, id_venta: int, usuario: UsuarioORM
    ) -> VentaDetalleCompletoOut:
        """Recupera el detalle unitario exhaustivo de una venta con pagos y lineas."""
        stmt = (
            select(VentaORM)
            .options(
                joinedload(VentaORM.cliente).joinedload(ClienteORM.usuario),
                joinedload(VentaORM.sucursal).joinedload(SucursalORM.ciudad),
                joinedload(VentaORM.cajero).joinedload(EmpleadoORM.usuario),
                selectinload(VentaORM.detalles)
                .joinedload(VentaDetalleORM.variante)
                .joinedload(VarianteProductoORM.producto),
                selectinload(VentaORM.detalles)
                .joinedload(VentaDetalleORM.variante)
                .joinedload(VarianteProductoORM.talla),
                selectinload(VentaORM.detalles)
                .joinedload(VentaDetalleORM.variante)
                .joinedload(VarianteProductoORM.color),
                selectinload(VentaORM.pagos),
            )
            .where(VentaORM.id_venta == id_venta)
        )
        venta = db.execute(stmt).unique().scalar_one_or_none()
        if not venta:
            raise VentaNoEncontradaError(id_venta)

        rol = str(usuario.rol or "").lower().strip()
        if rol == "encargado_sucursal" and venta.id_sucursal != usuario.id_sucursal:
            raise SucursalConsultaInvalidaError(
                "No cuenta con autorizacion para consultar una venta de otra sucursal."
            )

        nombre_cli = "Cliente Mostrador"
        email_cli = None
        tel_cli = None
        if venta.cliente and venta.cliente.usuario:
            nombre_cli = f"{venta.cliente.usuario.nombres} {venta.cliente.usuario.apellidos}".strip()
            email_cli = venta.cliente.usuario.email
            tel_cli = venta.cliente.usuario.telefono

        nombre_cajero = None
        if venta.cajero and venta.cajero.usuario:
            nombre_cajero = f"{venta.cajero.usuario.nombres} {venta.cajero.usuario.apellidos}".strip()

        lineas: List[LineaDetalleOut] = []
        for d in venta.detalles:
            v = d.variante
            prod_nombre = v.producto.nombre if v and v.producto else "Prenda"
            talla_cod = v.talla.codigo if v and v.talla else "-"
            color_nom = v.color.nombre if v and v.color else "-"
            color_hex = v.color.codigo_hex if v and v.color else None
            sub_calc = d.subtotal_linea or (d.precio_unitario * d.cantidad)
            img_url = v.producto.imagen_url if v and v.producto else None

            lineas.append(
                LineaDetalleOut(
                    id_detalle=d.id_venta_detalle,
                    id_variante=d.id_variante,
                    sku=v.sku if v else f"VAR-{d.id_variante}",
                    nombre_producto=prod_nombre,
                    talla=talla_cod,
                    color=color_nom,
                    codigo_hex=color_hex,
                    cantidad=d.cantidad,
                    precio_unitario=Decimal(str(d.precio_unitario)),
                    subtotal_linea=Decimal(str(sub_calc)),
                    imagen_url=img_url,
                )
            )

        pagos_out: List[PagoItemOut] = [
            PagoItemOut(
                id_pago=p.id_pago,
                metodo_pago=str(p.metodo_pago),
                monto=Decimal(str(p.monto)),
                estado=str(p.estado),
                referencia_pasarela=p.referencia_pasarela,
                creado_en=p.creado_en,
                confirmado_en=p.confirmado_en,
            )
            for p in venta.pagos
        ]

        return VentaDetalleCompletoOut(
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            fecha_venta=venta.fecha_venta,
            estado=str(venta.estado),
            tipo_venta=str(venta.tipo_venta),
            subtotal=Decimal(str(venta.subtotal)),
            descuento=Decimal(str(venta.descuento)),
            total=Decimal(str(venta.total)),
            id_sucursal=venta.id_sucursal,
            nombre_sucursal=venta.sucursal.nombre if venta.sucursal else "Sucursal",
            ciudad_sucursal=venta.sucursal.ciudad.nombre if venta.sucursal and venta.sucursal.ciudad else "Bolivia",
            id_cliente=venta.id_cliente,
            nombre_cliente=nombre_cli,
            email_cliente=email_cli,
            telefono_cliente=tel_cli,
            cajero_nombre=nombre_cajero,
            lineas=lineas,
            pagos=pagos_out,
        )

    def obtener_detalle_reserva(
        self, db: Session, id_reserva: int, usuario: UsuarioORM
    ) -> ReservaDetalleCompletoOut:
        """Recupera el detalle unitario exhaustivo de una reserva con lineas de prendas."""
        stmt = (
            select(ReservaORM)
            .options(
                joinedload(ReservaORM.cliente).joinedload(ClienteORM.usuario),
                joinedload(ReservaORM.sucursal).joinedload(SucursalORM.ciudad),
                joinedload(ReservaORM.empleado_atencion).joinedload(EmpleadoORM.usuario),
                selectinload(ReservaORM.detalles)
                .joinedload(ReservaDetalleORM.variante)
                .joinedload(VarianteProductoORM.producto),
                selectinload(ReservaORM.detalles)
                .joinedload(ReservaDetalleORM.variante)
                .joinedload(VarianteProductoORM.talla),
                selectinload(ReservaORM.detalles)
                .joinedload(ReservaDetalleORM.variante)
                .joinedload(VarianteProductoORM.color),
            )
            .where(ReservaORM.id_reserva == id_reserva)
        )
        reserva = db.execute(stmt).unique().scalar_one_or_none()
        if not reserva:
            raise ReservaNoEncontradaError(id_reserva)

        rol = str(usuario.rol or "").lower().strip()
        if rol == "encargado_sucursal" and reserva.id_sucursal != usuario.id_sucursal:
            raise SucursalConsultaInvalidaError(
                "No cuenta con autorizacion para consultar una reserva de otra sucursal."
            )

        nombre_cli = "Cliente Registrado"
        email_cli = None
        tel_cli = None
        if reserva.cliente and reserva.cliente.usuario:
            nombre_cli = f"{reserva.cliente.usuario.nombres} {reserva.cliente.usuario.apellidos}".strip()
            email_cli = reserva.cliente.usuario.email
            tel_cli = reserva.cliente.usuario.telefono

        nombre_empleado = None
        if reserva.empleado_atencion and reserva.empleado_atencion.usuario:
            nombre_empleado = (
                f"{reserva.empleado_atencion.usuario.nombres} {reserva.empleado_atencion.usuario.apellidos}".strip()
            )

        lineas: List[LineaDetalleOut] = []
        for d in reserva.detalles:
            v = d.variante
            prod_nombre = v.producto.nombre if v and v.producto else "Prenda"
            talla_cod = v.talla.codigo if v and v.talla else "-"
            color_nom = v.color.nombre if v and v.color else "-"
            color_hex = v.color.codigo_hex if v and v.color else None
            precio = (v.producto.precio_base + v.precio_extra) if v and v.producto else Decimal("0.00")
            sub_calc = precio * d.cantidad
            img_url = v.producto.imagen_url if v and v.producto else None

            lineas.append(
                LineaDetalleOut(
                    id_detalle=d.id_reserva_detalle,
                    id_variante=d.id_variante,
                    sku=v.sku if v else f"VAR-{d.id_variante}",
                    nombre_producto=prod_nombre,
                    talla=talla_cod,
                    color=color_nom,
                    codigo_hex=color_hex,
                    cantidad=d.cantidad,
                    precio_unitario=Decimal(str(precio)),
                    subtotal_linea=Decimal(str(round(sub_calc, 2))),
                    imagen_url=img_url,
                )
            )

        return ReservaDetalleCompletoOut(
            id_reserva=reserva.id_reserva,
            codigo_reserva=f"RES-{reserva.id_reserva:05d}",
            fecha_hora_atencion=reserva.fecha_hora_atencion,
            creado_en=reserva.creado_en,
            estado=str(reserva.estado),
            canal_origen=str(reserva.canal_origen),
            observacion=reserva.observacion,
            id_sucursal=reserva.id_sucursal,
            nombre_sucursal=reserva.sucursal.nombre if reserva.sucursal else "Sucursal",
            ciudad_sucursal=reserva.sucursal.ciudad.nombre if reserva.sucursal and reserva.sucursal.ciudad else "Bolivia",
            id_cliente=reserva.id_cliente,
            nombre_cliente=nombre_cli,
            email_cliente=email_cli,
            telefono_cliente=tel_cli,
            atendido_por_nombre=nombre_empleado,
            lineas=lineas,
        )
