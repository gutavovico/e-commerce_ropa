"""Servicio de logica de negocio transaccional para CU24: Gestionar Inventario, Stock y Existencias por Sucursal."""

from datetime import datetime, timezone
import math
from typing import Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import ProductoORM, VarianteProductoORM
from modules.gestion_operativa.modelos import SucursalORM
from .modelos import InventarioSucursalORM, MovimientoInventarioORM
from .esquemas import (
    ComprobanteTransferenciaOut,
    DatosSucursalInventarioOut,
    DatosVarianteInventarioOut,
    DisponibilidadPublicaOut,
    DisponibilidadSucursalOut,
    EstadoStockCalculadoEnum,
    HistorialKardexOut,
    InventarioAjusteIn,
    InventarioCrearIn,
    InventarioFiltrosIn,
    InventarioItemOut,
    KardexItemOut,
    ListaPaginadaInventarioOut,
    TipoAjusteManualEnum,
    TipoMovimientoEnum,
    TransferenciaInterSucursalIn,
)
from .errores import (
    AutoTransferenciaError,
    EntidadInactivaError,
    InventarioDuplicadoError,
    InventarioNoEncontradoError,
    StockInsuficienteError,
    SucursalNoAutorizadaError,
)


class ServicioGestionInventario:
    """Logica de negocio transaccional para la gestion de existencias y kardex."""

    @staticmethod
    def _calcular_estado_stock(disponible: int, alerta: int) -> EstadoStockCalculadoEnum:
        if disponible <= 0:
            return EstadoStockCalculadoEnum.AGOTADO
        if disponible <= alerta:
            return EstadoStockCalculadoEnum.ALERTA_BAJA
        return EstadoStockCalculadoEnum.OPTIMO

    @staticmethod
    def _validar_acceso_sucursal(usuario_sesion: UsuarioORM, id_sucursal_solicitada: int) -> None:
        """Aplica la regla de segregacion territorial estricta para encargados de sucursal."""
        if usuario_sesion.rol == "encargado_sucursal":
            if usuario_sesion.id_sucursal != id_sucursal_solicitada:
                raise SucursalNoAutorizadaError(
                    id_sucursal_solicitada, usuario_sesion.id_sucursal or 0
                )

    def _to_inventario_item_out(
        self, inv: InventarioSucursalORM, estado_calc: EstadoStockCalculadoEnum
    ) -> InventarioItemOut:
        sucursal = inv.sucursal
        ciudad_nombre = ""
        if sucursal and getattr(sucursal, "ciudad", None):
            ciudad_nombre = getattr(sucursal.ciudad, "nombre", "") or ""

        sucursal_out = DatosSucursalInventarioOut(
            id_sucursal=getattr(sucursal, "id_sucursal", inv.id_sucursal) if sucursal else inv.id_sucursal,
            nombre=getattr(sucursal, "nombre", "Sucursal") if sucursal else "Sucursal",
            ciudad=ciudad_nombre,
        )

        variante = inv.variante
        producto = variante.producto if variante else None

        talla_val = ""
        if variante and variante.talla:
            talla_val = getattr(variante.talla, "codigo", None) or getattr(variante.talla, "nombre", "") or ""

        color_nombre = ""
        color_hex = "#000000"
        if variante and variante.color:
            color_nombre = getattr(variante.color, "nombre", "") or ""
            color_hex = getattr(variante.color, "codigo_hex", "") or "#000000"

        precio_base = float(producto.precio_base) if (producto and producto.precio_base is not None) else 0.0
        precio_extra = float(variante.precio_extra) if (variante and variante.precio_extra is not None) else 0.0
        precio_final = precio_base + precio_extra

        categoria_nombre = ""
        if producto and producto.categoria:
            categoria_nombre = getattr(producto.categoria, "nombre", "") or ""

        variante_out = DatosVarianteInventarioOut(
            id_variante=variante.id_variante if variante else inv.id_variante,
            id_producto=producto.id_producto if producto else 0,
            nombre_prenda=producto.nombre if producto else "",
            sku=variante.sku if variante else "",
            talla=talla_val,
            color_nombre=color_nombre,
            color_hex=color_hex,
            precio_base=precio_base,
            precio_final=precio_final,
            imagen_url=producto.imagen_url if producto else None,
            categoria_nombre=categoria_nombre,
        )

        return InventarioItemOut(
            id_inventario=inv.id_inventario or 0,
            id_sucursal=inv.id_sucursal,
            id_variante=inv.id_variante,
            cantidad_disponible=inv.cantidad_disponible,
            cantidad_reservada=inv.cantidad_reservada,
            stock_total=inv.cantidad_disponible + inv.cantidad_reservada,
            stock_minimo=inv.stock_minimo,
            stock_alerta=inv.stock_alerta,
            estado=inv.estado,
            estado_calculado=estado_calc,
            actualizado_en=inv.actualizado_en or datetime.now(timezone.utc),
            sucursal=sucursal_out,
            variante=variante_out,
        )

    def listar_inventario(
        self, db: Session, filtros: InventarioFiltrosIn, usuario_sesion: UsuarioORM
    ) -> ListaPaginadaInventarioOut:
        # Segregacion forzada para encargado_sucursal
        id_sucursal_consulta = filtros.id_sucursal
        if usuario_sesion.rol == "encargado_sucursal":
            if filtros.id_sucursal and filtros.id_sucursal != usuario_sesion.id_sucursal:
                raise SucursalNoAutorizadaError(filtros.id_sucursal, usuario_sesion.id_sucursal or 0)
            id_sucursal_consulta = usuario_sesion.id_sucursal
        elif id_sucursal_consulta:
            self._validar_acceso_sucursal(usuario_sesion, id_sucursal_consulta)

        condiciones = []
        if id_sucursal_consulta:
            condiciones.append(InventarioSucursalORM.id_sucursal == id_sucursal_consulta)

        stmt = (
            select(InventarioSucursalORM)
            .join(InventarioSucursalORM.variante)
            .join(VarianteProductoORM.producto)
            .options(
                joinedload(InventarioSucursalORM.sucursal).joinedload(SucursalORM.ciudad),
                joinedload(InventarioSucursalORM.variante).joinedload(VarianteProductoORM.producto).joinedload(ProductoORM.categoria),
                joinedload(InventarioSucursalORM.variante).joinedload(VarianteProductoORM.talla),
                joinedload(InventarioSucursalORM.variante).joinedload(VarianteProductoORM.color),
            )
        )

        if filtros.id_categoria:
            condiciones.append(ProductoORM.id_categoria == filtros.id_categoria)

        if filtros.q:
            termino = f"%{filtros.q.strip()}%"
            condiciones.append(
                or_(
                    ProductoORM.nombre.ilike(termino),
                    VarianteProductoORM.sku.ilike(termino),
                )
            )

        if filtros.estado_stock == "agotado":
            condiciones.append(InventarioSucursalORM.cantidad_disponible <= 0)
        elif filtros.estado_stock == "alerta_baja":
            condiciones.append(
                and_(
                    InventarioSucursalORM.cantidad_disponible > 0,
                    InventarioSucursalORM.cantidad_disponible <= InventarioSucursalORM.stock_alerta,
                )
            )
        elif filtros.estado_stock == "optimo":
            condiciones.append(
                InventarioSucursalORM.cantidad_disponible > InventarioSucursalORM.stock_alerta
            )

        if condiciones:
            stmt = stmt.where(and_(*condiciones))

        # Conteo total
        stmt_count = select(func.count(InventarioSucursalORM.id_inventario)).join(
            InventarioSucursalORM.variante
        ).join(VarianteProductoORM.producto)
        if condiciones:
            stmt_count = stmt_count.where(and_(*condiciones))
        total = db.scalar(stmt_count) or 0

        # Paginacion
        offset = (filtros.pagina - 1) * filtros.limite
        stmt = stmt.order_by(InventarioSucursalORM.id_inventario.desc()).offset(offset).limit(filtros.limite)
        registros = db.scalars(stmt).unique().all()

        items_out = []
        for inv in registros:
            estado_calc = self._calcular_estado_stock(inv.cantidad_disponible, inv.stock_alerta)
            items_out.append(self._to_inventario_item_out(inv, estado_calc))

        total_paginas = math.ceil(total / filtros.limite) if total > 0 else 1
        return ListaPaginadaInventarioOut(
            items=items_out,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )

    def crear_inventario_inicial(
        self, db: Session, payload: InventarioCrearIn, usuario_sesion: UsuarioORM
    ) -> InventarioItemOut:
        self._validar_acceso_sucursal(usuario_sesion, payload.id_sucursal)

        # 1. Validar sucursal activa
        sucursal = db.get(SucursalORM, payload.id_sucursal)
        if not sucursal or not sucursal.activa:
            raise EntidadInactivaError(f"Sucursal ID {payload.id_sucursal}")

        # 2. Validar variante y prenda activa
        variante = db.get(VarianteProductoORM, payload.id_variante)
        if not variante or not variante.activo or not (variante.producto and variante.producto.activo):
            raise EntidadInactivaError(f"Variante ID {payload.id_variante}")

        # 3. Comprobar no duplicidad
        existente = db.scalar(
            select(InventarioSucursalORM).where(
                and_(
                    InventarioSucursalORM.id_sucursal == payload.id_sucursal,
                    InventarioSucursalORM.id_variante == payload.id_variante,
                )
            )
        )
        if existente:
            raise InventarioDuplicadoError(payload.id_sucursal, payload.id_variante)

        # 4. Crear entidad de inventario
        nuevo_inv = InventarioSucursalORM(
            id_sucursal=payload.id_sucursal,
            id_variante=payload.id_variante,
            id_temporada=payload.id_temporada,
            cantidad_disponible=payload.cantidad_inicial,
            cantidad_reservada=0,
            stock_minimo=payload.stock_minimo,
            stock_alerta=payload.stock_alerta,
            estado="disponible" if payload.cantidad_inicial > 0 else "agotada",
            actualizado_en=datetime.now(timezone.utc),
        )
        db.add(nuevo_inv)
        db.flush()

        # 5. Generar movimiento inicial en Kardex si hubo carga inicial
        if payload.cantidad_inicial > 0:
            mov = MovimientoInventarioORM(
                id_inventario=nuevo_inv.id_inventario,
                tipo_movimiento=TipoMovimientoEnum.INGRESO_PROVEEDOR.value,
                cantidad=payload.cantidad_inicial,
                saldo_anterior=0,
                saldo_nuevo=payload.cantidad_inicial,
                motivo=payload.observacion or "Carga inicial de existencias",
                id_usuario=usuario_sesion.id_usuario,
                referencia_documento=payload.referencia_documento,
            )
            db.add(mov)

        db.commit()
        db.refresh(nuevo_inv)
        estado_calc = self._calcular_estado_stock(nuevo_inv.cantidad_disponible, nuevo_inv.stock_alerta)
        return self._to_inventario_item_out(nuevo_inv, estado_calc)

    def ajustar_inventario(
        self, db: Session, id_inventario: int, payload: InventarioAjusteIn, usuario_sesion: UsuarioORM
    ) -> InventarioItemOut:
        inv = db.get(InventarioSucursalORM, id_inventario)
        if not inv:
            raise InventarioNoEncontradoError(id_inventario)

        self._validar_acceso_sucursal(usuario_sesion, inv.id_sucursal)

        saldo_anterior = inv.cantidad_disponible
        if payload.tipo_ajuste == TipoAjusteManualEnum.INCREMENTO:
            saldo_nuevo = saldo_anterior + payload.cantidad
            tipo_mov = TipoMovimientoEnum.AJUSTE_POSITIVO.value
            delta = payload.cantidad
        else:
            if saldo_anterior < payload.cantidad:
                raise StockInsuficienteError(disponible=saldo_anterior, solicitado=payload.cantidad)
            saldo_nuevo = saldo_anterior - payload.cantidad
            tipo_mov = TipoMovimientoEnum.AJUSTE_NEGATIVO.value
            delta = -payload.cantidad

        inv.cantidad_disponible = saldo_nuevo
        inv.estado = "disponible" if saldo_nuevo > 0 else "agotada"
        inv.actualizado_en = datetime.now(timezone.utc)

        # Registro inmutable en Kardex
        mov = MovimientoInventarioORM(
            id_inventario=inv.id_inventario,
            tipo_movimiento=tipo_mov,
            cantidad=delta,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            motivo=payload.motivo,
            id_usuario=usuario_sesion.id_usuario,
            referencia_documento=payload.referencia_documento,
        )
        db.add(mov)
        db.commit()
        db.refresh(inv)

        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

        nombre_u = f"{usuario_sesion.nombres} {usuario_sesion.apellidos}".strip() or usuario_sesion.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_sesion.id_usuario,
            usuario_nombre=nombre_u,
            accion="AJUSTE_INVENTARIO",
            tabla_modulo="inventario",
            severidad="INFO",
            payload_anterior={"cantidad_disponible": saldo_anterior},
            payload_nuevo={
                "id_inventario": id_inventario,
                "cantidad_disponible": saldo_nuevo,
                "delta": delta,
                "motivo": payload.motivo,
            },
            db=db,
        )

        estado_calc = self._calcular_estado_stock(inv.cantidad_disponible, inv.stock_alerta)
        return self._to_inventario_item_out(inv, estado_calc)

    def transferir_mercaderia(
        self, db: Session, payload: TransferenciaInterSucursalIn, usuario_sesion: UsuarioORM
    ) -> ComprobanteTransferenciaOut:
        if payload.id_sucursal_origen == payload.id_sucursal_destino:
            raise AutoTransferenciaError()

        self._validar_acceso_sucursal(usuario_sesion, payload.id_sucursal_origen)

        # 1. Validar sedes activas
        origen_suc = db.get(SucursalORM, payload.id_sucursal_origen)
        destino_suc = db.get(SucursalORM, payload.id_sucursal_destino)
        if not origen_suc or not origen_suc.activa:
            raise EntidadInactivaError(f"Sucursal Origen ID {payload.id_sucursal_origen}")
        if not destino_suc or not destino_suc.activa:
            raise EntidadInactivaError(f"Sucursal Destino ID {payload.id_sucursal_destino}")

        # 2. Localizar y bloquear inventario origen
        inv_origen = db.scalar(
            select(InventarioSucursalORM).where(
                and_(
                    InventarioSucursalORM.id_sucursal == payload.id_sucursal_origen,
                    InventarioSucursalORM.id_variante == payload.id_variante,
                )
            ).with_for_update()
        )
        if not inv_origen or inv_origen.cantidad_disponible < payload.cantidad:
            disponible = inv_origen.cantidad_disponible if inv_origen else 0
            raise StockInsuficienteError(disponible=disponible, solicitado=payload.cantidad)

        # 3. Localizar o instanciar inventario destino
        inv_destino = db.scalar(
            select(InventarioSucursalORM).where(
                and_(
                    InventarioSucursalORM.id_sucursal == payload.id_sucursal_destino,
                    InventarioSucursalORM.id_variante == payload.id_variante,
                )
            ).with_for_update()
        )

        saldo_origen_ant = inv_origen.cantidad_disponible
        inv_origen.cantidad_disponible -= payload.cantidad
        inv_origen.estado = "disponible" if inv_origen.cantidad_disponible > 0 else "agotada"
        inv_origen.actualizado_en = datetime.now(timezone.utc)

        if not inv_destino:
            inv_destino = InventarioSucursalORM(
                id_sucursal=payload.id_sucursal_destino,
                id_variante=payload.id_variante,
                id_temporada=inv_origen.id_temporada,
                cantidad_disponible=payload.cantidad,
                cantidad_reservada=0,
                stock_minimo=inv_origen.stock_minimo,
                stock_alerta=inv_origen.stock_alerta,
                estado="disponible",
            )
            db.add(inv_destino)
            db.flush()
            saldo_destino_ant = 0
            saldo_destino_nuevo = payload.cantidad
        else:
            saldo_destino_ant = inv_destino.cantidad_disponible
            inv_destino.cantidad_disponible += payload.cantidad
            saldo_destino_nuevo = inv_destino.cantidad_disponible
            inv_destino.estado = "disponible"
            inv_destino.actualizado_en = datetime.now(timezone.utc)

        # Insercion de movimientos espejo en Kardex
        mov_salida = MovimientoInventarioORM(
            id_inventario=inv_origen.id_inventario,
            tipo_movimiento=TipoMovimientoEnum.TRANSFERENCIA_SALIDA.value,
            cantidad=-payload.cantidad,
            saldo_anterior=saldo_origen_ant,
            saldo_nuevo=inv_origen.cantidad_disponible,
            motivo=f"Transferencia hacia {destino_suc.nombre}: {payload.motivo}",
            id_usuario=usuario_sesion.id_usuario,
            referencia_documento=f"TRF-OUT->{destino_suc.id_sucursal}",
        )
        mov_entrada = MovimientoInventarioORM(
            id_inventario=inv_destino.id_inventario,
            tipo_movimiento=TipoMovimientoEnum.TRANSFERENCIA_ENTRADA.value,
            cantidad=payload.cantidad,
            saldo_anterior=saldo_destino_ant,
            saldo_nuevo=saldo_destino_nuevo,
            motivo=f"Transferencia desde {origen_suc.nombre}: {payload.motivo}",
            id_usuario=usuario_sesion.id_usuario,
            referencia_documento=f"TRF-IN<-{origen_suc.id_sucursal}",
        )
        db.add_all([mov_salida, mov_entrada])
        db.commit()

        variante = db.get(VarianteProductoORM, payload.id_variante)
        return ComprobanteTransferenciaOut(
            mensaje="Transferencia inter-sucursal completada exitosamente.",
            id_sucursal_origen=payload.id_sucursal_origen,
            id_sucursal_destino=payload.id_sucursal_destino,
            id_variante=payload.id_variante,
            sku=variante.sku if variante else "N/A",
            cantidad_transferida=payload.cantidad,
            saldo_origen_nuevo=inv_origen.cantidad_disponible,
            saldo_destino_nuevo=saldo_destino_nuevo,
            fecha=datetime.now(timezone.utc),
        )

    def obtener_kardex(
        self, db: Session, id_inventario: int, usuario_sesion: UsuarioORM
    ) -> HistorialKardexOut:
        inv = db.get(InventarioSucursalORM, id_inventario)
        if not inv:
            raise InventarioNoEncontradoError(id_inventario)

        self._validar_acceso_sucursal(usuario_sesion, inv.id_sucursal)

        movs = db.scalars(
            select(MovimientoInventarioORM)
            .options(joinedload(MovimientoInventarioORM.usuario_responsable))
            .where(MovimientoInventarioORM.id_inventario == id_inventario)
            .order_by(MovimientoInventarioORM.creado_en.desc())
        ).all()

        kardex_items = []
        for m in movs:
            nombre_u = "Sistema"
            if m.usuario_responsable:
                nombre_u = f"{m.usuario_responsable.nombres} {m.usuario_responsable.apellidos}".strip()
            kardex_items.append(
                KardexItemOut(
                    id_movimiento=m.id_movimiento,
                    id_inventario=m.id_inventario,
                    tipo_movimiento=m.tipo_movimiento,
                    cantidad=m.cantidad,
                    saldo_anterior=m.saldo_anterior,
                    saldo_nuevo=m.saldo_nuevo,
                    motivo=m.motivo,
                    referencia_documento=m.referencia_documento,
                    id_usuario=m.id_usuario,
                    usuario_nombre=nombre_u,
                    creado_en=m.creado_en,
                )
            )

        prenda_sku = "Prenda"
        if inv.variante:
            if inv.variante.producto:
                prenda_sku = f"{inv.variante.producto.nombre} ({inv.variante.sku})"
            else:
                prenda_sku = inv.variante.sku

        sucursal_nombre = inv.sucursal.nombre if inv.sucursal else f"Sucursal {inv.id_sucursal}"

        return HistorialKardexOut(
            id_inventario=inv.id_inventario,
            prenda_sku=prenda_sku,
            sucursal_nombre=sucursal_nombre,
            saldo_actual=inv.cantidad_disponible,
            movimientos=kardex_items,
        )

    def consultar_disponibilidad_publica(
        self, db: Session, id_variante: int
    ) -> DisponibilidadPublicaOut:
        variante = db.get(VarianteProductoORM, id_variante)
        if not variante or not variante.activo or not (variante.producto and variante.producto.activo):
            raise EntidadInactivaError(f"Variante ID {id_variante}")

        registros = db.scalars(
            select(InventarioSucursalORM)
            .join(InventarioSucursalORM.sucursal)
            .options(joinedload(InventarioSucursalORM.sucursal).joinedload(SucursalORM.ciudad))
            .where(
                and_(
                    InventarioSucursalORM.id_variante == id_variante,
                    SucursalORM.activa.is_(True),
                )
            )
        ).all()

        sucursales_out = []
        for r in registros:
            sucursales_out.append(
                DisponibilidadSucursalOut(
                    id_sucursal=r.id_sucursal,
                    nombre_sucursal=r.sucursal.nombre,
                    ciudad=r.sucursal.ciudad.nombre if (r.sucursal and r.sucursal.ciudad) else "",
                    direccion=r.sucursal.direccion if r.sucursal else "",
                    cantidad_disponible=r.cantidad_disponible,
                    estado="disponible" if r.cantidad_disponible > 0 else "agotada",
                )
            )

        return DisponibilidadPublicaOut(
            id_variante=variante.id_variante,
            sku=variante.sku,
            nombre_prenda=variante.producto.nombre if variante.producto else "",
            sucursales=sucursales_out,
        )


servicio_gestion_inventario = ServicioGestionInventario()
