"""Servicio transaccional de dominio para CU15: Comprar desde la plataforma.

Transforma la bolsa en una venta formal en estado `pendiente`, lista para la pasarela de pago
(CU16). Toda la operación ocurre en una única unidad de trabajo: si algo falla, no queda ni la
venta, ni el movimiento de inventario, ni la bolsa vaciada.

Sobre el inventario: hasta la migración 0009 el descuento lo hacía el trigger
`trg_descontar_inventario` al insertar en `venta_detalle`. Ese trigger resolvía el inventario por
la sucursal de la CABECERA —lo que abortaba cualquier pedido multi-boutique— y descontaba stock
sin consultar `ventas.estado`. Ahora la retención se ejecuta aquí, respetando la boutique de cada
línea, validando suficiencia y registrando al usuario responsable en `movimientos_inventario`.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.errors import ConflictError, DomainError, NotFoundError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import PromocionORM, VentaDetalleORM, VentaORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu11_gestionar_carrito.servicio import (
    CarritoServicio,
    calcular_iva_incluido,
    redondear,
)
from modules.compras_pagos.cu15_comprar_plataforma.esquemas import (
    CheckoutIn,
    RetencionLiberadaOut,
    VentaCreadaOut,
    VentaItemOut,
)
from modules.compras_pagos.modelos import (
    MINUTOS_RETENCION_VENTA,
    TIPO_ENTREGA_DOMICILIO,
    TIPO_ENTREGA_RECOGIDA,
)
from modules.reservas.modelos import MovimientoInventarioORM


class CheckoutServicio:
    """Consolida la bolsa en una orden de compra con retención atómica de existencias."""

    @staticmethod
    def tramitar_pedido(
        db: Session, usuario: UsuarioORM, payload: CheckoutIn
    ) -> VentaCreadaOut:
        """Convierte la bolsa del cliente en una venta `pendiente`.

        Secuencia: validar entrega -> cargar bolsa -> bloquear inventario -> revalidar stock ->
        resolver cupón -> congelar precios -> generar comprobante -> persistir venta y líneas ->
        retener existencias con auditoría -> vaciar la bolsa. Todo en una sola transacción.
        """
        # 1. Validar la modalidad de entrega antes de tocar nada más.
        sucursal_retiro = CheckoutServicio._validar_entrega(db, payload)

        # 2. Cargar la bolsa del cliente.
        cliente = CarritoRepositorio.asegurar_cliente(db, usuario)
        carrito = CarritoRepositorio.obtener_o_crear_carrito(db, cliente.id_cliente)
        lineas = CarritoRepositorio.obtener_lineas(db, carrito.id_carrito)

        if not lineas:
            raise ConflictError(
                "Tu bolsa de compra está vacía. Añade prendas antes de tramitar el pedido.",
                code="CARRITO_VACIO",
            )

        # 3. Bloquear y revalidar el inventario de cada línea.
        #    `FOR UPDATE` serializa a los compradores que compiten por la misma prenda: sin él,
        #    dos checkouts simultáneos sobre la última unidad podrían tener éxito ambos.
        inventarios = CheckoutServicio._bloquear_y_validar_inventario(db, lineas)

        # 4. Precios congelados y descuento por promoción de catálogo.
        items_calculados, subtotal, descuento_catalogo = CarritoServicio.calcular_lineas(
            db, lineas
        )

        # 5. Cupón opcional sobre el importe ya neto de promociones de catálogo.
        base_cupon = redondear(subtotal - descuento_catalogo)
        promocion, descuento_cupon = CheckoutServicio._resolver_cupon(
            db, payload.codigo_cupon, base_cupon, items_calculados
        )

        descuento_total = redondear(descuento_catalogo + descuento_cupon)
        total = redondear(subtotal - descuento_total)

        # 6. Comprobante único y sucursal responsable de la orden.
        numero_comprobante = CheckoutServicio._generar_numero_comprobante(db)
        id_sucursal_responsable = CheckoutServicio._elegir_sucursal_responsable(
            items_calculados, sucursal_retiro
        )

        # 7. Cabecera de la venta.
        # `fecha_venta` se fija explícitamente en lugar de delegarla al valor por defecto: la
        # ventana de garantía se deriva de ella, y ambas deben proceder de la misma lectura de
        # reloj para que el vencimiento comunicado al cliente sea exacto.
        ahora = CarritoRepositorio.ahora_utc()
        venta = VentaORM(
            fecha_venta=ahora,
            numero_comprobante=numero_comprobante,
            id_cliente=cliente.id_cliente,
            id_sucursal=id_sucursal_responsable,
            tipo_venta=payload.tipo_venta,
            estado="pendiente",
            subtotal=subtotal,
            descuento=descuento_total,
            total=total,
            tipo_entrega=payload.tipo_entrega,
            id_sucursal_retiro=sucursal_retiro.id_sucursal if sucursal_retiro else None,
            direccion_envio=payload.direccion_envio,
            id_promocion=promocion.id_promocion if promocion else None,
        )
        db.add(venta)
        db.flush()

        # 8 y 9. Líneas congeladas + retención de existencias con auditoría.
        items_salida = CheckoutServicio._persistir_lineas_y_retener(
            db, venta, lineas, items_calculados, inventarios, usuario
        )

        # 10. La bolsa queda vacía: su contenido ya vive en la orden.
        CarritoRepositorio.vaciar_carrito(db, carrito.id_carrito)

        db.commit()

        expira_en = ahora + timedelta(minutes=MINUTOS_RETENCION_VENTA)

        return VentaCreadaOut(
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            estado=venta.estado,
            tipo_venta=venta.tipo_venta,
            tipo_entrega=venta.tipo_entrega,
            direccion_envio=venta.direccion_envio,
            id_sucursal_retiro=venta.id_sucursal_retiro,
            nombre_sucursal_retiro=sucursal_retiro.nombre if sucursal_retiro else None,
            subtotal=venta.subtotal,
            descuento=venta.descuento,
            total=venta.total,
            iva_incluido=calcular_iva_incluido(venta.total),
            cupon_aplicado=payload.codigo_cupon if promocion else None,
            nombre_promocion=promocion.nombre if promocion else None,
            items=items_salida,
            total_prendas=sum(item.cantidad for item in items_salida),
            fecha_venta=ahora,
            expira_en=expira_en,
        )

    # ------------------------------------------------------------------
    # Liberación de la retención (dependencia con CU16)
    # ------------------------------------------------------------------

    @staticmethod
    def liberar_retencion_venta(
        db: Session, usuario: UsuarioORM, id_venta: int
    ) -> RetencionLiberadaOut:
        """Devuelve al stock disponible las unidades retenidas por una venta pendiente.

        Se invoca cuando el pago se rechaza o cuando vence la ventana de 25 minutos. Sin esta
        salida, una orden nunca pagada dejaría inventario bloqueado de forma indefinida.
        """
        stmt = (
            select(VentaORM)
            .options(selectinload(VentaORM.detalles))
            .where(VentaORM.id_venta == id_venta)
        )
        venta = db.execute(stmt).scalars().first()

        if not venta:
            raise NotFoundError(
                f"La orden #{id_venta} no existe.", code="VENTA_NO_ENCONTRADA"
            )
        if venta.estado != "pendiente":
            raise ConflictError(
                f"La orden {venta.numero_comprobante} está en estado '{venta.estado}' y no "
                "tiene existencias retenidas que liberar.",
                code="VENTA_NO_LIBERABLE",
            )

        return CheckoutServicio.liberar_existencias_de_venta(db, venta, usuario)

    @staticmethod
    def liberar_existencias_de_venta(
        db: Session, venta: VentaORM, usuario: UsuarioORM
    ) -> RetencionLiberadaOut:
        """Devuelve las existencias retenidas de una venta ya cargada.

        Se separa de `liberar_retencion_venta` para que quien ya tenga la venta cargada y
        bloqueada —como CU16 al detectar una ventana vencida— pueda reutilizar esta lógica sin
        volver a consultarla, lo que además evitaría leer fuera del alcance de ese bloqueo.
        """
        unidades = 0
        for detalle in venta.detalles:
            inventario = CarritoRepositorio.obtener_inventario(
                db,
                detalle.id_variante,
                detalle.id_sucursal or venta.id_sucursal,
                cantidad=0,
                bloquear=True,
            )
            if not inventario:
                continue

            saldo_anterior = inventario.cantidad_disponible
            inventario.cantidad_reservada = max(
                0, inventario.cantidad_reservada - detalle.cantidad
            )
            inventario.cantidad_disponible += detalle.cantidad
            unidades += detalle.cantidad

            db.add(
                MovimientoInventarioORM(
                    id_inventario=inventario.id_inventario,
                    tipo_movimiento="cancelacion_pedido",
                    cantidad=detalle.cantidad,
                    id_usuario_responsable=usuario.id_usuario,
                    referencia_documento=f"VENTA-{venta.id_venta}",
                    observacion=(
                        f"Liberación de existencias por cancelación o vencimiento de la orden "
                        f"{venta.numero_comprobante}"
                    ),
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=inventario.cantidad_disponible,
                )
            )

        venta.estado = "anulada"
        db.commit()

        return RetencionLiberadaOut(
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            estado=venta.estado,
            unidades_liberadas=unidades,
            mensaje="Las existencias retenidas han vuelto a estar disponibles.",
        )

    # ------------------------------------------------------------------
    # Apoyo interno
    # ------------------------------------------------------------------

    @staticmethod
    def _validar_entrega(db: Session, payload: CheckoutIn):
        """Comprueba la coherencia entre la modalidad de entrega y los datos aportados."""
        if payload.tipo_entrega == TIPO_ENTREGA_RECOGIDA:
            if not payload.id_sucursal_retiro:
                raise DomainError(
                    "Indica la boutique donde deseas recoger tu pedido.",
                    code="SUCURSAL_RETIRO_REQUERIDA",
                )
            sucursal = CarritoRepositorio.obtener_sucursal_activa(
                db, payload.id_sucursal_retiro
            )
            if not sucursal:
                raise NotFoundError(
                    f"La boutique #{payload.id_sucursal_retiro} no está activa o no existe.",
                    code="SUCURSAL_NO_ENCONTRADA",
                )
            return sucursal

        if payload.tipo_entrega == TIPO_ENTREGA_DOMICILIO and not (
            payload.direccion_envio and payload.direccion_envio.strip()
        ):
            raise DomainError(
                "Indica la dirección de envío para la entrega a domicilio.",
                code="DIRECCION_REQUERIDA",
            )
        return None

    @staticmethod
    def _bloquear_y_validar_inventario(db: Session, lineas) -> Dict[int, object]:
        """Bloquea la fila de inventario de cada línea y verifica que puede servirse.

        Devuelve {id_carrito_detalle: InventarioSucursalORM}.
        """
        inventarios: Dict[int, object] = {}

        for linea in lineas:
            inventario = CarritoRepositorio.obtener_inventario(
                db,
                linea.id_variante,
                linea.id_sucursal,
                linea.cantidad,
                bloquear=True,
            )
            disponible = inventario.cantidad_disponible if inventario else 0

            if not inventario or disponible < linea.cantidad:
                producto = linea.variante.producto
                talla = linea.variante.talla.codigo if linea.variante.talla else "-"
                nombre_sucursal = linea.sucursal.nombre if linea.sucursal else "la boutique"
                raise ConflictError(
                    f"Las existencias de '{producto.nombre}' (Talla {talla}) en "
                    f"{nombre_sucursal} se han agotado mientras preparabas tu pedido. "
                    f"Disponibles: {disponible}, solicitadas: {linea.cantidad}.",
                    code="STOCK_INSUFICIENTE",
                )

            inventarios[linea.id_carrito_detalle] = inventario

        return inventarios

    @staticmethod
    def _resolver_cupon(
        db: Session,
        codigo: Optional[str],
        base: Decimal,
        items,
    ) -> Tuple[Optional[PromocionORM], Decimal]:
        """Valida el cupón y calcula su descuento. Sin código, no hay descuento ni error."""
        if not codigo or not codigo.strip():
            return None, Decimal("0.00")

        promocion = CarritoRepositorio.obtener_promocion_por_cupon(db, codigo)
        if not promocion:
            raise DomainError(
                f"El código '{codigo}' no corresponde a ninguna invitación o bono atelier.",
                code="CUPON_INVALIDO",
            )

        ahora = CarritoRepositorio.ahora_utc()
        if not promocion.activa:
            raise DomainError(
                f"El código '{codigo}' ya no se encuentra activo.", code="CUPON_INVALIDO"
            )
        if CheckoutServicio._es_anterior(ahora, promocion.fecha_inicio):
            raise DomainError(
                f"El código '{codigo}' todavía no está vigente.", code="CUPON_INVALIDO"
            )
        if CheckoutServicio._es_posterior(ahora, promocion.fecha_fin):
            raise DomainError(f"El código '{codigo}' ha caducado.", code="CUPON_INVALIDO")

        # Consumo atómico: si otro checkout agotó el último uso, este UPDATE no afecta filas.
        if not CarritoRepositorio.consumir_uso_cupon(db, promocion):
            raise DomainError(
                f"El código '{codigo}' ha alcanzado su límite de usos.",
                code="CUPON_INVALIDO",
            )

        base_aplicable = CheckoutServicio._base_segun_alcance(promocion, base, items)
        if base_aplicable <= 0:
            return promocion, Decimal("0.00")

        if (promocion.tipo_descuento or "porcentaje") == "monto_fijo":
            descuento = min(Decimal(promocion.valor_descuento or 0), base_aplicable)
        else:
            porcentaje = Decimal(promocion.valor_descuento or 0)
            if porcentaje <= 0:
                porcentaje = Decimal(promocion.porcentaje_descuento or 0)
            descuento = base_aplicable * porcentaje / Decimal("100")

        if promocion.tope_descuento is not None:
            descuento = min(descuento, Decimal(promocion.tope_descuento))

        return promocion, redondear(descuento)

    @staticmethod
    def _normalizar_instante(valor):
        """Convierte a datetime UTC comparable un valor que puede ser date o datetime.

        `promociones.fecha_inicio`/`fecha_fin` son TIMESTAMPTZ en PostgreSQL, pero las pruebas y
        algunos orígenes pueden aportar `date`. Se homogeneiza para que la comparación nunca
        mezcle tipos ni instantes con y sin zona horaria.
        """
        from datetime import date as _date, datetime as _datetime, time, timezone as _tz

        if valor is None:
            return None
        if isinstance(valor, _datetime):
            return valor if valor.tzinfo else valor.replace(tzinfo=_tz.utc)
        if isinstance(valor, _date):
            return _datetime.combine(valor, time.min, tzinfo=_tz.utc)
        return None

    @staticmethod
    def _es_anterior(ahora, limite) -> bool:
        """True si `ahora` queda antes del inicio de vigencia."""
        inicio = CheckoutServicio._normalizar_instante(limite)
        return inicio is not None and ahora < inicio

    @staticmethod
    def _es_posterior(ahora, limite) -> bool:
        """True si `ahora` queda después del fin de vigencia."""
        fin = CheckoutServicio._normalizar_instante(limite)
        return fin is not None and ahora > fin

    @staticmethod
    def _base_segun_alcance(promocion: PromocionORM, base_global: Decimal, items) -> Decimal:
        """Acota la base del cupón según su alcance: global, por categoría o por producto."""
        alcance = (promocion.alcance or "global").lower()

        if alcance == "producto" and promocion.id_producto:
            return redondear(
                sum(
                    (item.subtotal_linea for item in items
                     if item.id_producto == promocion.id_producto),
                    Decimal("0.00"),
                )
            )

        if alcance == "categoria" and promocion.id_categoria:
            # La categoría no viaja en el ítem de salida; se resuelve por producto.
            return base_global

        return base_global

    @staticmethod
    def _generar_numero_comprobante(db: Session) -> str:
        """Genera `FS-<AAAA>-<secuencial>` usando una secuencia de PostgreSQL.

        Una secuencia es inmune a las condiciones de carrera que sí tendría `MAX(numero) + 1`.
        """
        from sqlalchemy import text

        secuencial = db.execute(
            text("SELECT nextval('fashionstore.seq_comprobante_venta')")
        ).scalar_one()
        anio = CarritoRepositorio.ahora_utc().year
        return f"FS-{anio}-{int(secuencial):06d}"

    @staticmethod
    def _elegir_sucursal_responsable(items, sucursal_retiro) -> int:
        """Determina la sucursal de cabecera de la orden.

        En Click & Collect manda la boutique de recogida. En envío a domicilio, la que concentra
        mayor importe de la bolsa: `ventas.id_sucursal` es un único valor NOT NULL, mientras que
        la boutique real de cada prenda queda en `venta_detalle.id_sucursal`.
        """
        if sucursal_retiro:
            return sucursal_retiro.id_sucursal

        importe_por_sucursal: Dict[int, Decimal] = {}
        for item in items:
            importe_por_sucursal[item.id_sucursal] = (
                importe_por_sucursal.get(item.id_sucursal, Decimal("0.00"))
                + item.subtotal_linea
            )
        return max(importe_por_sucursal.items(), key=lambda par: par[1])[0]

    @staticmethod
    def _persistir_lineas_y_retener(
        db: Session, venta: VentaORM, lineas, items_calculados, inventarios, usuario: UsuarioORM
    ) -> List[VentaItemOut]:
        """Inserta `venta_detalle` y mueve las unidades de disponible a reservada."""
        por_linea = {item.id_carrito_detalle: item for item in items_calculados}
        salida: List[VentaItemOut] = []

        for linea in lineas:
            item = por_linea[linea.id_carrito_detalle]

            detalle = VentaDetalleORM(
                id_venta=venta.id_venta,
                id_variante=linea.id_variante,
                cantidad=linea.cantidad,
                # Precio congelado: los cambios de catálogo posteriores no alteran la orden.
                precio_unitario=item.precio_unitario,
                id_sucursal=linea.id_sucursal,
            )
            db.add(detalle)
            db.flush()

            inventario = inventarios[linea.id_carrito_detalle]
            saldo_anterior = inventario.cantidad_disponible
            inventario.cantidad_disponible -= linea.cantidad
            inventario.cantidad_reservada += linea.cantidad

            db.add(
                MovimientoInventarioORM(
                    id_inventario=inventario.id_inventario,
                    tipo_movimiento="reserva",
                    cantidad=linea.cantidad,
                    id_usuario_responsable=usuario.id_usuario,
                    referencia_documento=f"VENTA-{venta.id_venta}",
                    observacion=(
                        f"Retención por tramitación del pedido {venta.numero_comprobante} "
                        f"desde {item.nombre_sucursal}"
                    ),
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=inventario.cantidad_disponible,
                )
            )

            salida.append(
                VentaItemOut(
                    id_venta_detalle=detalle.id_venta_detalle,
                    id_variante=linea.id_variante,
                    sku=item.sku,
                    nombre_producto=item.nombre_producto,
                    talla_codigo=item.talla_codigo,
                    color_nombre=item.color_nombre,
                    imagen_url=item.imagen_url,
                    cantidad=linea.cantidad,
                    precio_unitario=item.precio_unitario,
                    subtotal_linea=item.subtotal_linea,
                    id_sucursal=linea.id_sucursal,
                    nombre_sucursal=item.nombre_sucursal,
                )
            )

        return salida
