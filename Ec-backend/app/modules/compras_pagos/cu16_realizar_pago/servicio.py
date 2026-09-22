"""Servicio transaccional de dominio para CU16: Realizar Pago Electrónico.

Cierra el ciclo de compra que CU15 dejó abierto: cobra la orden `pendiente`, la marca como
`pagada` y consolida las existencias que estaban retenidas.

**Invariante del inventario:** en un pago confirmado las unidades salen de `cantidad_reservada`
y NO regresan a `cantidad_disponible` — abandonan el almacén. Eso es lo que distingue una venta
consolidada de una cancelación, donde sí vuelven a estar disponibles.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.errors import (
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PaymentRequiredError,
)
from integrations.stripe_service import (
    DatosTarjeta,
    ErrorPasarela,
    PasarelaPagos,
    StripeService,
)
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import VarianteProductoORM, VentaDetalleORM, VentaORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu11_gestionar_carrito.servicio import (
    calcular_iva_incluido,
    redondear,
)
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio
from modules.compras_pagos.cu16_realizar_pago.esquemas import (
    PagoConfirmadoOut,
    PagoItemOut,
    PagoProcesarIn,
    ResumenPagoOut,
)
from modules.compras_pagos.modelos import MINUTOS_RETENCION_VENTA, PagoORM
from modules.reservas.modelos import MovimientoInventarioORM

logger = logging.getLogger("fashionstore.pago_servicio")


class PagoServicio:
    """Orquesta el cobro y la consolidación del inventario en una única transacción."""

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    @staticmethod
    def obtener_resumen_pago(
        db: Session, usuario: UsuarioORM, id_venta: int
    ) -> ResumenPagoOut:
        """Devuelve los datos de la orden pendiente para inicializar la pasarela."""
        venta = PagoServicio._cargar_venta(db, id_venta)
        PagoServicio._verificar_pertenencia(venta, usuario)

        if venta.estado != "pendiente":
            raise ConflictError(
                f"La orden {venta.numero_comprobante} está en estado '{venta.estado}' y no "
                "admite pago.",
                code="VENTA_NO_PAGABLE",
            )

        expira_en = PagoServicio._calcular_expiracion(venta)
        ahora = CarritoRepositorio.ahora_utc()
        restantes = max(0, int((expira_en - ahora).total_seconds()))

        items = [
            PagoItemOut(
                id_variante=d.id_variante,
                sku=d.variante.sku if d.variante else "",
                nombre_producto=(
                    d.variante.producto.nombre if d.variante and d.variante.producto else ""
                ),
                talla_codigo=d.variante.talla.codigo if d.variante and d.variante.talla else "-",
                color_nombre=d.variante.color.nombre if d.variante and d.variante.color else "-",
                imagen_url=(
                    d.variante.producto.imagen_url if d.variante and d.variante.producto else None
                ),
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal_linea=redondear(Decimal(d.precio_unitario) * d.cantidad),
                nombre_sucursal=d.sucursal.nombre if d.sucursal else None,
            )
            for d in venta.detalles
        ]

        # `VentaORM` no declara relación con el cliente, y no hace falta: la pertenencia ya se
        # verificó arriba, así que el usuario autenticado ES el titular de la orden.
        nombre_cliente = f"{usuario.nombres} {usuario.apellidos}".strip() or None

        return ResumenPagoOut(
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            estado=venta.estado,
            subtotal=venta.subtotal,
            descuento=venta.descuento,
            total=venta.total,
            iva_incluido=calcular_iva_incluido(venta.total),
            total_prendas=sum(d.cantidad for d in venta.detalles),
            items=items,
            tipo_entrega=venta.tipo_entrega,
            direccion_envio=venta.direccion_envio,
            nombre_sucursal_retiro=(
                venta.sucursal_retiro.nombre if venta.sucursal_retiro else None
            ),
            nombre_cliente=nombre_cliente,
            fecha_venta=venta.fecha_venta,
            expira_en=expira_en,
            segundos_restantes=restantes,
        )

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    @staticmethod
    def procesar_pago(
        db: Session,
        usuario: UsuarioORM,
        payload: PagoProcesarIn,
        pasarela: Optional[PasarelaPagos] = None,
    ) -> PagoConfirmadoOut:
        """Cobra la orden y consolida el ciclo de compra.

        `pasarela` se inyecta para poder sustituirla en pruebas por un doble sin red ni latencia.
        """
        pasarela = pasarela or StripeService()

        # 1. Cargar y bloquear la venta. El bloqueo serializa dos envíos simultáneos: sin él,
        #    un doble clic podría cobrar dos veces la misma orden.
        venta = PagoServicio._cargar_venta(db, payload.id_venta, bloquear=True)
        PagoServicio._verificar_pertenencia(venta, usuario)

        # 2. Idempotencia: si esta misma clave ya produjo un cobro confirmado, se devuelve aquel
        #    resultado en lugar de volver a cobrar.
        if payload.clave_idempotencia:
            previo = PagoServicio._buscar_pago_idempotente(
                db, venta.id_venta, payload.clave_idempotencia
            )
            if previo:
                return PagoServicio._construir_confirmacion(venta, previo)

        # 3. Estado de la orden.
        if venta.estado == "pagada":
            raise ConflictError(
                f"La orden {venta.numero_comprobante} ya fue liquidada.",
                code="VENTA_YA_LIQUIDADA",
            )
        if venta.estado != "pendiente":
            raise ConflictError(
                f"La orden {venta.numero_comprobante} está en estado '{venta.estado}' y no "
                "admite pago.",
                code="VENTA_ANULADA",
            )

        # 4. Ventana de retención. Al vencer se libera el stock en el acto: es el único momento
        #    en que el sistema sabe con certeza que la retención ya no es válida, y no existe
        #    todavía un proceso automático de expiración.
        expira_en = PagoServicio._calcular_expiracion(venta)
        if CarritoRepositorio.ahora_utc() > expira_en:
            # Se reutiliza la venta ya cargada y bloqueada: recargarla emitiría una consulta
            # redundante y leería fuera del alcance de ese bloqueo.
            CheckoutServicio.liberar_existencias_de_venta(db, venta, usuario)
            raise ConflictError(
                f"La ventana de {MINUTOS_RETENCION_VENTA} minutos de la orden "
                f"{venta.numero_comprobante} ha vencido y las prendas han vuelto a estar "
                "disponibles. Vuelve a tramitar tu pedido.",
                code="ORDEN_EXPIRADA",
            )

        # 5. Cobro en la pasarela.
        tarjeta = PagoServicio._construir_tarjeta(payload)
        try:
            resultado = pasarela.procesar_cargo(
                monto=Decimal(venta.total),
                metodo_pago=payload.metodo_pago,
                tarjeta=tarjeta,
                token=payload.token_pasarela,
                descripcion=f"FashionStore · Orden {venta.numero_comprobante}",
                metadatos={
                    "numero_comprobante": venta.numero_comprobante,
                    "id_venta": str(venta.id_venta),
                },
            )
        except ErrorPasarela as exc:
            # Fallo técnico: el cargo no llegó a evaluarse. No se registra como rechazo, porque
            # la tarjeta no fue denegada; la orden queda intacta para reintentar.
            raise DomainError(str(exc), code="PASARELA_NO_DISPONIBLE") from exc

        # 6. Rechazo: se deja constancia y la orden sigue viva.
        if not resultado.aprobado:
            pago = PagoORM(
                id_venta=venta.id_venta,
                metodo_pago=payload.metodo_pago,
                monto=venta.total,
                estado="rechazado",
                referencia_pasarela=resultado.referencia,
                payload_respuesta=PagoServicio._payload_auditoria(
                    resultado, payload, aprobado=False
                ),
            )
            db.add(pago)
            db.commit()

            raise PaymentRequiredError(
                resultado.mensaje or "La entidad emisora ha rechazado el pago.",
                code="PAGO_RECHAZADO",
            )

        # 7. Aprobación: cobro, cambio de estado y consolidación, todo en una transacción.
        confirmado_en = CarritoRepositorio.ahora_utc()
        pago = PagoORM(
            id_venta=venta.id_venta,
            metodo_pago=payload.metodo_pago,
            monto=venta.total,
            estado="confirmado",
            referencia_pasarela=resultado.referencia,
            payload_respuesta=PagoServicio._payload_auditoria(
                resultado, payload, aprobado=True
            ),
            confirmado_en=confirmado_en,
        )
        db.add(pago)

        venta.estado = "pagada"
        PagoServicio._consolidar_inventario(db, venta, usuario)

        db.commit()
        db.refresh(pago)

        return PagoServicio._construir_confirmacion(venta, pago, resultado)

    # ------------------------------------------------------------------
    # Consolidación de inventario
    # ------------------------------------------------------------------

    @staticmethod
    def _consolidar_inventario(db: Session, venta: VentaORM, usuario: UsuarioORM) -> None:
        """Descuenta las unidades retenidas y deja constancia auditable.

        Las unidades salen de `cantidad_reservada` y no vuelven a `cantidad_disponible`: la
        prenda se vendió. El saldo que registra la bitácora es el de existencias reservadas,
        que es la magnitud que este movimiento altera.
        """
        for detalle in venta.detalles:
            inventario = CarritoRepositorio.obtener_inventario(
                db,
                detalle.id_variante,
                detalle.id_sucursal or venta.id_sucursal,
                cantidad=0,
                bloquear=True,
            )
            if not inventario:
                # Sin fila de inventario no hay nada que consolidar. No se interrumpe el cobro:
                # el pago ya fue aceptado por la pasarela y la orden debe quedar liquidada.
                logger.warning(
                    "Sin inventario para la variante %s en la sucursal %s al consolidar la "
                    "orden %s",
                    detalle.id_variante,
                    detalle.id_sucursal or venta.id_sucursal,
                    venta.numero_comprobante,
                )
                continue

            saldo_anterior = inventario.cantidad_reservada
            inventario.cantidad_reservada = max(
                0, inventario.cantidad_reservada - detalle.cantidad
            )

            db.add(
                MovimientoInventarioORM(
                    id_inventario=inventario.id_inventario,
                    tipo_movimiento="venta_confirmada",
                    # Cantidad negativa: la prenda sale definitivamente del almacén.
                    cantidad=-detalle.cantidad,
                    id_usuario_responsable=usuario.id_usuario,
                    referencia_documento=f"VENTA-{venta.id_venta}",
                    observacion=(
                        f"Salida definitiva por pago confirmado de la orden "
                        f"{venta.numero_comprobante}"
                    ),
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=inventario.cantidad_reservada,
                )
            )

    # ------------------------------------------------------------------
    # Apoyo interno
    # ------------------------------------------------------------------

    @staticmethod
    def _cargar_venta(db: Session, id_venta: int, bloquear: bool = False) -> VentaORM:
        """Carga la venta con todo lo que el servicio necesita resuelto."""
        stmt = (
            select(VentaORM)
            .options(
                selectinload(VentaORM.detalles)
                .selectinload(VentaDetalleORM.variante)
                .selectinload(VarianteProductoORM.producto),
                selectinload(VentaORM.detalles)
                .selectinload(VentaDetalleORM.variante)
                .selectinload(VarianteProductoORM.talla),
                selectinload(VentaORM.detalles)
                .selectinload(VentaDetalleORM.variante)
                .selectinload(VarianteProductoORM.color),
                selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.sucursal),
                selectinload(VentaORM.sucursal_retiro),
            )
            .where(VentaORM.id_venta == id_venta)
        )
        if bloquear:
            # `FOR UPDATE` no admite los JOIN externos que generan los `selectinload`, pero
            # estos se emiten como consultas aparte, de modo que el bloqueo recae solo sobre
            # la fila de `ventas`, que es exactamente lo que se quiere serializar.
            stmt = stmt.with_for_update(of=VentaORM)

        venta = db.execute(stmt).scalars().first()
        if not venta:
            raise NotFoundError(
                f"La orden #{id_venta} no existe.", code="VENTA_NO_ENCONTRADA"
            )
        return venta

    @staticmethod
    def _verificar_pertenencia(venta: VentaORM, usuario: UsuarioORM) -> None:
        """Una orden solo la puede pagar su titular.

        Se responde 403 y no 404 de forma deliberada: el recurso existe, pero es ajeno.
        """
        if venta.id_cliente != usuario.id_usuario:
            raise AuthorizationError(
                "Esta orden pertenece a otro cliente.", code="VENTA_AJENA"
            )

    @staticmethod
    def _calcular_expiracion(venta: VentaORM) -> datetime:
        """Instante en que vence la retención de existencias de la orden."""
        fecha = venta.fecha_venta
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return fecha + timedelta(minutes=MINUTOS_RETENCION_VENTA)

    @staticmethod
    def _construir_tarjeta(payload: PagoProcesarIn) -> Optional[DatosTarjeta]:
        """Traduce el esquema de entrada al objeto que consume la pasarela."""
        if not payload.tarjeta:
            return None
        t = payload.tarjeta
        return DatosTarjeta(
            numero=t.numero,
            titular=t.titular,
            mes_expiracion=t.mes_expiracion,
            anio_expiracion=t.anio_expiracion,
            cvv=t.cvv,
        )

    @staticmethod
    def _buscar_pago_idempotente(
        db: Session, id_venta: int, clave: str
    ) -> Optional[PagoORM]:
        """Localiza un cobro confirmado previo con la misma clave de idempotencia.

        La clave se guarda dentro de `payload_respuesta`, que es `jsonb`, de modo que no hace
        falta ninguna columna adicional.
        """
        stmt = (
            select(PagoORM)
            .where(
                PagoORM.id_venta == id_venta,
                PagoORM.estado == "confirmado",
                PagoORM.payload_respuesta["clave_idempotencia"].astext == clave,
            )
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def _payload_auditoria(
        resultado, payload: PagoProcesarIn, aprobado: bool
    ) -> dict:
        """Compone lo que se persiste en `pagos.payload_respuesta`.

        Solo marca y últimos cuatro dígitos: ni el PAN completo ni el CVV llegan nunca aquí.
        """
        return {
            "clave_idempotencia": payload.clave_idempotencia,
            "metodo_pago": payload.metodo_pago,
            "aprobado": aprobado,
            "codigo_respuesta": resultado.codigo_respuesta,
            "mensaje": resultado.mensaje,
            "marca_tarjeta": resultado.marca,
            "ultimos_digitos": resultado.ultimos_digitos,
            "pasarela": resultado.payload,
        }

    @staticmethod
    def _construir_confirmacion(
        venta: VentaORM, pago: PagoORM, resultado=None
    ) -> PagoConfirmadoOut:
        """Ensambla la respuesta de confirmación a partir del pago persistido."""
        auditoria = pago.payload_respuesta or {}
        return PagoConfirmadoOut(
            id_pago=pago.id_pago,
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            estado_pago=pago.estado,
            estado_venta=venta.estado,
            metodo_pago=pago.metodo_pago,
            referencia_pasarela=pago.referencia_pasarela,
            monto=pago.monto,
            marca_tarjeta=(
                resultado.marca if resultado else auditoria.get("marca_tarjeta")
            ),
            ultimos_digitos=(
                resultado.ultimos_digitos if resultado else auditoria.get("ultimos_digitos")
            ),
            confirmado_en=pago.confirmado_en or CarritoRepositorio.ahora_utc(),
        )
