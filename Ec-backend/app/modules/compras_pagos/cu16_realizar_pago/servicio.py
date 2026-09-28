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
    UnprocessableEntityError,
)
from integrations.stripe_service import (
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
from modules.compras_pagos.cu15_comprar_plataforma.esquemas import RetencionLiberadaOut
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio
from modules.compras_pagos.cu16_realizar_pago.esquemas import (
    METODO_EFECTIVO,
    METODOS_DIGITALES,
    PagoConfirmadoOut,
    PagoEfectivoIn,
    PagoIniciarIn,
    PagoIntentoOut,
    PagoItemOut,
    ResumenPagoOut,
)
from modules.compras_pagos.modelos import (
    HORAS_RETENCION_PAGO_EFECTIVO,
    MINUTOS_RETENCION_VENTA,
    TIPO_ENTREGA_RECOGIDA,
    PagoORM,
)
from modules.reservas.modelos import MovimientoInventarioORM

logger = logging.getLogger("fashionstore.pago_servicio")

# Roles con acceso a la confirmación/cancelación administrativa del pago en efectivo. El
# `encargado_sucursal` y el `cajero` quedan acotados a la boutique de recogida de la venta
# (§1.6 de la especificación); el `administrador` no tiene esa restricción.
ROLES_CAJA = ("administrador", "encargado_sucursal", "cajero")


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

        expira_en = PagoServicio._calcular_expiracion(db, venta)
        ahora = CarritoRepositorio.ahora_utc()
        restantes = max(0, int((expira_en - ahora).total_seconds()))

        metodos_disponibles = list(METODOS_DIGITALES)
        if venta.tipo_entrega == TIPO_ENTREGA_RECOGIDA:
            metodos_disponibles.append(METODO_EFECTIVO)

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
            metodos_disponibles=metodos_disponibles,
        )

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    @staticmethod
    def registrar_pago_efectivo(
        db: Session, usuario: UsuarioORM, payload: PagoEfectivoIn
    ) -> PagoConfirmadoOut:
        """Registra la intención de pago en efectivo en sucursal. No cobra nada.

        La venta permanece `pendiente`: la liquidación real ocurre cuando un cajero confirma el
        pago con `confirmar_pago_efectivo` (§1.6).
        """
        venta = PagoServicio._cargar_venta(db, payload.id_venta, bloquear=True)
        PagoServicio._verificar_pertenencia(venta, usuario)

        if payload.clave_idempotencia:
            previo = PagoServicio._buscar_pago_idempotente(
                db, venta.id_venta, payload.clave_idempotencia
            )
            if previo:
                nombre_sucursal = (
                    venta.sucursal_retiro.nombre
                    if venta.sucursal_retiro
                    else "la boutique de recogida"
                )
                mensaje = (
                    f"Pago en efectivo ya registrado. Preséntate en {nombre_sucursal} "
                    f"dentro de las próximas {HORAS_RETENCION_PAGO_EFECTIVO} horas."
                )
                return PagoServicio._construir_confirmacion(venta, previo, mensaje=mensaje)

        PagoServicio._verificar_orden_pagable(db, usuario, venta)

        return PagoServicio._registrar_pago_efectivo(db, venta, payload)

    @staticmethod
    def iniciar_pago(
        db: Session,
        usuario: UsuarioORM,
        payload: PagoIniciarIn,
        pasarela: Optional[PasarelaPagos] = None,
    ) -> PagoIntentoOut:
        """Abre un `PaymentIntent` en Stripe y devuelve su `client_secret`.

        El backend no recibe ningún dato de tarjeta en este paso: el cliente confirma el cobro
        directamente contra Stripe con ese `client_secret`, y luego llama a `confirmar_pago` para
        que el servidor verifique el desenlace por su cuenta.

        `pasarela` se inyecta para poder sustituirla en pruebas por un doble sin red ni latencia.
        """
        pasarela = pasarela or StripeService()

        # 1. Cargar y bloquear la venta. El bloqueo serializa dos envíos simultáneos: sin él,
        #    un doble clic podría abrir dos intentos de cobro para la misma orden.
        venta = PagoServicio._cargar_venta(db, payload.id_venta, bloquear=True)
        PagoServicio._verificar_pertenencia(venta, usuario)

        # 2. Idempotencia: reenviar la misma clave no debe abrir un segundo `PaymentIntent`.
        if payload.clave_idempotencia:
            previo = PagoServicio._buscar_pago_idempotente(
                db, venta.id_venta, payload.clave_idempotencia
            )
            if previo:
                if previo.estado == "confirmado":
                    return PagoIntentoOut(
                        id_pago=previo.id_pago,
                        ya_confirmado=True,
                        confirmacion=PagoServicio._construir_confirmacion(venta, previo),
                    )
                if previo.estado == "pendiente" and previo.referencia_pasarela:
                    client_secret = pasarela.recuperar_client_secret(previo.referencia_pasarela)
                    return PagoIntentoOut(id_pago=previo.id_pago, client_secret=client_secret)

        PagoServicio._verificar_orden_pagable(db, usuario, venta)

        # 3. Abrir el intento en la pasarela.
        try:
            intento = pasarela.crear_intento(
                monto=Decimal(venta.total),
                metodo_pago=payload.metodo_pago,
                descripcion=f"FashionStore · Orden {venta.numero_comprobante}",
                metadatos={
                    "numero_comprobante": venta.numero_comprobante,
                    "id_venta": str(venta.id_venta),
                },
                idempotency_key=payload.clave_idempotencia,
            )
        except ErrorPasarela as exc:
            raise DomainError(str(exc), code="PASARELA_NO_DISPONIBLE") from exc

        pago = PagoORM(
            id_venta=venta.id_venta,
            metodo_pago=payload.metodo_pago,
            monto=venta.total,
            estado="pendiente",
            referencia_pasarela=intento.referencia,
            payload_respuesta={
                "clave_idempotencia": payload.clave_idempotencia,
                "metodo_pago": payload.metodo_pago,
                "escenario_prueba": payload.escenario_prueba,
                "pasarela": intento.payload,
            },
        )
        db.add(pago)
        db.commit()
        db.refresh(pago)

        return PagoIntentoOut(id_pago=pago.id_pago, client_secret=intento.client_secret)

    @staticmethod
    def confirmar_pago(
        db: Session,
        usuario: UsuarioORM,
        id_pago: int,
        pasarela: Optional[PasarelaPagos] = None,
    ) -> PagoConfirmadoOut:
        """Verifica contra Stripe el desenlace de un `PaymentIntent` ya confirmado por el cliente.

        El resultado **nunca** se toma de lo que el cliente reporte: se recupera el intento por
        su id y se decide `aprobado`/`rechazado` según lo que Stripe devuelva, igual que el
        servidor recalcula siempre los importes de una orden en lugar de aceptar los del cliente.
        """
        pasarela = pasarela or StripeService()

        pago = PagoServicio._cargar_pago_digital(db, id_pago, bloquear=True)
        venta = PagoServicio._cargar_venta(db, pago.id_venta, bloquear=True)
        PagoServicio._verificar_pertenencia(venta, usuario)

        # Reenvío idempotente natural (doble clic, reintento de red): el pago ya se resolvió.
        if pago.estado == "confirmado":
            return PagoServicio._construir_confirmacion(venta, pago)
        if pago.estado != "pendiente":
            raise ConflictError(
                f"El pago #{id_pago} está en estado '{pago.estado}' y no admite confirmación.",
                code="PAGO_NO_PENDIENTE",
            )

        PagoServicio._verificar_orden_pagable(db, usuario, venta)

        escenario_prueba = (pago.payload_respuesta or {}).get("escenario_prueba")
        try:
            resultado = pasarela.verificar_intento(
                pago.referencia_pasarela, escenario_prueba=escenario_prueba
            )
        except ErrorPasarela as exc:
            raise DomainError(str(exc), code="PASARELA_NO_DISPONIBLE") from exc

        # Rechazo: se deja constancia y la orden sigue viva.
        if not resultado.aprobado:
            pago.estado = "rechazado"
            pago.payload_respuesta = {
                **(pago.payload_respuesta or {}),
                **PagoServicio._payload_auditoria(resultado, aprobado=False),
            }
            db.add(pago)
            db.commit()

            raise PaymentRequiredError(
                resultado.mensaje or "La entidad emisora ha rechazado el pago.",
                code="PAGO_RECHAZADO",
            )

        # Aprobación: cobro, cambio de estado y consolidación, todo en una transacción.
        confirmado_en = CarritoRepositorio.ahora_utc()
        pago.estado = "confirmado"
        pago.confirmado_en = confirmado_en
        pago.payload_respuesta = {
            **(pago.payload_respuesta or {}),
            **PagoServicio._payload_auditoria(resultado, aprobado=True),
        }
        db.add(pago)

        venta.estado = "pagada"
        PagoServicio._consolidar_inventario(db, venta, usuario)
        # El cobro está confirmado por la pasarela (tarjeta o Bizum/QR): ahora sí, las prendas
        # compradas salen de la bolsa. Antes de este punto la bolsa permanece intacta.
        PagoServicio._retirar_de_la_bolsa(db, venta)

        db.commit()
        db.refresh(pago)

        return PagoServicio._construir_confirmacion(venta, pago, resultado)

    @staticmethod
    def _verificar_orden_pagable(db: Session, usuario: UsuarioORM, venta: VentaORM) -> None:
        """Estado y ventana de la orden, comunes a los tres puntos de entrada de cobro."""
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

        # Ventana de retención. Al vencer se libera el stock en el acto: es el único momento en
        # que el sistema sabe con certeza que la retención ya no es válida, y no existe todavía
        # un proceso automático de expiración. Si ya hay un pago en efectivo `pendiente` para
        # esta venta, la ventana vigente es la de 24h (§1.5.2), no la de 25 minutos de CU15.
        expira_en = PagoServicio._calcular_expiracion(db, venta)
        if CarritoRepositorio.ahora_utc() > expira_en:
            # Se reutiliza la venta ya cargada y bloqueada: recargarla emitiría una consulta
            # redundante y leería fuera del alcance de ese bloqueo.
            CheckoutServicio.liberar_existencias_de_venta(db, venta, usuario)
            raise ConflictError(
                f"La ventana de la orden {venta.numero_comprobante} ha vencido y las prendas "
                "han vuelto a estar disponibles. Vuelve a tramitar tu pedido.",
                code="ORDEN_EXPIRADA",
            )

    # ------------------------------------------------------------------
    # Administración: pago en efectivo en sucursal (§1.5.2/§1.6)
    # ------------------------------------------------------------------

    @staticmethod
    def confirmar_pago_efectivo(
        db: Session, usuario: UsuarioORM, id_pago: int
    ) -> PagoConfirmadoOut:
        """Un cajero confirma en mostrador que el cliente pagó en efectivo.

        Consolida el inventario exactamente igual que la aprobación en línea. Si la ventana de
        24 horas ya venció, libera las existencias y responde 409 en lugar de confirmar: es la
        misma verificación perezosa que ya usa CU15 para los 25 minutos de la bolsa.
        """
        pago, venta = PagoServicio._cargar_pago_efectivo_para_caja(db, id_pago, bloquear=True)
        PagoServicio._verificar_alcance_caja(usuario, venta)

        expira_en = pago.creado_en
        if expira_en.tzinfo is None:
            expira_en = expira_en.replace(tzinfo=timezone.utc)
        expira_en += timedelta(hours=HORAS_RETENCION_PAGO_EFECTIVO)

        if CarritoRepositorio.ahora_utc() > expira_en:
            pago.estado = "rechazado"
            pago.payload_respuesta = {
                **(pago.payload_respuesta or {}),
                "motivo": "Ventana de 24 horas vencida sin que el cliente se presentara a pagar.",
            }
            db.add(pago)
            CheckoutServicio.liberar_existencias_de_venta(db, venta, usuario)
            raise ConflictError(
                f"La ventana de {HORAS_RETENCION_PAGO_EFECTIVO} horas del pago en efectivo de "
                f"la orden {venta.numero_comprobante} ha vencido y las prendas han vuelto a "
                "estar disponibles.",
                code="PAGO_EFECTIVO_EXPIRADO",
            )

        confirmado_en = CarritoRepositorio.ahora_utc()
        pago.estado = "confirmado"
        pago.confirmado_en = confirmado_en
        pago.payload_respuesta = {
            **(pago.payload_respuesta or {}),
            "confirmado_por": usuario.id_usuario,
        }
        db.add(pago)

        venta.estado = "pagada"
        PagoServicio._consolidar_inventario(db, venta, usuario)
        # Solo ahora, cuando el cajero da por cobrado el efectivo, la bolsa del cliente pierde
        # estas prendas. Mientras el pago estuvo `pendiente` las conservó.
        PagoServicio._retirar_de_la_bolsa(db, venta)

        db.commit()
        db.refresh(pago)

        return PagoServicio._construir_confirmacion(
            venta,
            pago,
            mensaje=(
                "Pago en efectivo confirmado. Tu orden entra en preparación en el atelier."
            ),
        )

    @staticmethod
    def cancelar_pago_efectivo(
        db: Session, usuario: UsuarioORM, id_pago: int
    ) -> RetencionLiberadaOut:
        """Un cajero anula un pago en efectivo antes de que expiren las 24 horas.

        Cubre al cliente que se presenta y se arrepiente, o que avisa de que no acudirá: libera
        el stock de inmediato en vez de esperar a que la ventana venza por sí sola.
        """
        pago, venta = PagoServicio._cargar_pago_efectivo_para_caja(db, id_pago, bloquear=True)
        PagoServicio._verificar_alcance_caja(usuario, venta)

        pago.estado = "rechazado"
        pago.payload_respuesta = {
            **(pago.payload_respuesta or {}),
            "motivo": "Cancelado manualmente en mostrador antes del pago.",
            "cancelado_por": usuario.id_usuario,
        }
        db.add(pago)

        return CheckoutServicio.liberar_existencias_de_venta(db, venta, usuario)

    # ------------------------------------------------------------------
    # Consolidación de inventario
    # ------------------------------------------------------------------

    @staticmethod
    def _retirar_de_la_bolsa(db: Session, venta: VentaORM) -> None:
        """Retira de la bolsa las prendas que acaban de pagarse.

        Se resuelve por `venta.id_cliente` y no por el usuario autenticado: al confirmar un pago
        en efectivo el actor es el cajero, y vaciar *su* bolsa en lugar de la del comprador sería
        un despropósito.

        Tampoco se vacía la bolsa entera: desde que sobrevive al checkout, puede contener prendas
        añadidas después de tramitar, que nadie ha comprado todavía.
        """
        if not venta.id_cliente:
            return  # Venta presencial sin cliente asociado: no hay bolsa que tocar.

        carrito = CarritoRepositorio.buscar_carrito(db, venta.id_cliente)
        if not carrito:
            return

        CarritoRepositorio.retirar_lineas_compradas(db, carrito.id_carrito, venta.detalles)

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
    def _calcular_expiracion(db: Session, venta: VentaORM) -> datetime:
        """Instante en que vence la retención de existencias de la orden.

        Son los 25 minutos de CU15 desde `fecha_venta`, salvo que ya exista un pago en efectivo
        `pendiente` para esta venta: en ese caso la ventana vigente pasa a ser la de 24 horas
        desde que se registró ese intento (§1.5.2/§1.6), independiente de la de la bolsa.
        """
        pago_efectivo = PagoServicio._buscar_pago_efectivo_pendiente(db, venta.id_venta)
        if pago_efectivo:
            creado = pago_efectivo.creado_en
            if creado.tzinfo is None:
                creado = creado.replace(tzinfo=timezone.utc)
            return creado + timedelta(hours=HORAS_RETENCION_PAGO_EFECTIVO)

        fecha = venta.fecha_venta
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return fecha + timedelta(minutes=MINUTOS_RETENCION_VENTA)

    @staticmethod
    def _buscar_pago_efectivo_pendiente(db: Session, id_venta: int) -> Optional[PagoORM]:
        """Localiza el pago en efectivo `pendiente` más reciente de la venta, si existe."""
        stmt = (
            select(PagoORM)
            .where(
                PagoORM.id_venta == id_venta,
                PagoORM.metodo_pago == METODO_EFECTIVO,
                PagoORM.estado == "pendiente",
            )
            .order_by(PagoORM.creado_en.desc())
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def _registrar_pago_efectivo(
        db: Session, venta: VentaORM, payload: PagoEfectivoIn
    ) -> PagoConfirmadoOut:
        """Registra la intención de pago en efectivo. No cobra ni consolida inventario.

        La venta permanece `pendiente`: la liquidación real ocurre cuando un cajero confirma el
        pago con `confirmar_pago_efectivo` (§1.6).
        """
        if venta.tipo_entrega != TIPO_ENTREGA_RECOGIDA:
            raise UnprocessableEntityError(
                "El pago en efectivo en sucursal solo está disponible cuando el pedido se "
                "recoge en boutique.",
                code="METODO_NO_SOPORTADO",
            )

        pago = PagoORM(
            id_venta=venta.id_venta,
            metodo_pago=METODO_EFECTIVO,
            monto=venta.total,
            estado="pendiente",
            payload_respuesta={"clave_idempotencia": payload.clave_idempotencia},
        )
        db.add(pago)
        db.commit()
        db.refresh(pago)

        nombre_sucursal = (
            venta.sucursal_retiro.nombre if venta.sucursal_retiro else "la boutique de recogida"
        )
        mensaje = (
            f"Pago en efectivo registrado. Preséntate en {nombre_sucursal} dentro de las "
            f"próximas {HORAS_RETENCION_PAGO_EFECTIVO} horas para liquidarlo y retirar tu "
            "pedido."
        )
        return PagoServicio._construir_confirmacion(venta, pago, mensaje=mensaje)

    @staticmethod
    def _cargar_pago_efectivo_para_caja(
        db: Session, id_pago: int, bloquear: bool = False
    ) -> tuple[PagoORM, VentaORM]:
        """Carga un pago en efectivo con su venta, para confirmarlo o cancelarlo en mostrador."""
        stmt = (
            select(PagoORM)
            .options(
                selectinload(PagoORM.venta)
                .selectinload(VentaORM.detalles)
                .selectinload(VentaDetalleORM.variante)
                .selectinload(VarianteProductoORM.producto),
                selectinload(PagoORM.venta).selectinload(VentaORM.sucursal_retiro),
            )
            .where(PagoORM.id_pago == id_pago)
        )
        if bloquear:
            stmt = stmt.with_for_update(of=PagoORM)

        pago = db.execute(stmt).scalars().first()
        if not pago:
            raise NotFoundError(f"El pago #{id_pago} no existe.", code="PAGO_NO_ENCONTRADO")
        if pago.metodo_pago != METODO_EFECTIVO:
            raise ConflictError(
                f"El pago #{id_pago} no es un pago en efectivo en sucursal.",
                code="METODO_NO_SOPORTADO",
            )
        if pago.estado != "pendiente":
            raise ConflictError(
                f"El pago #{id_pago} está en estado '{pago.estado}' y no admite esta acción.",
                code="PAGO_NO_PENDIENTE",
            )
        return pago, pago.venta

    @staticmethod
    def _cargar_pago_digital(db: Session, id_pago: int, bloquear: bool = False) -> PagoORM:
        """Carga un pago digital (tarjeta/Bizum/QR) para verificarlo contra la pasarela.

        No incluye efectivo: ese método nunca abre un `PaymentIntent`, así que no tiene sentido
        que llegue a `confirmar_pago`.
        """
        stmt = select(PagoORM).where(PagoORM.id_pago == id_pago)
        if bloquear:
            stmt = stmt.with_for_update(of=PagoORM)

        pago = db.execute(stmt).scalars().first()
        if not pago:
            raise NotFoundError(f"El pago #{id_pago} no existe.", code="PAGO_NO_ENCONTRADO")
        if pago.metodo_pago == METODO_EFECTIVO or not pago.referencia_pasarela:
            raise ConflictError(
                f"El pago #{id_pago} no corresponde a un cobro digital en curso.",
                code="METODO_NO_SOPORTADO",
            )
        return pago

    @staticmethod
    def _verificar_alcance_caja(usuario: UsuarioORM, venta: VentaORM) -> None:
        """El `administrador` confirma cualquier boutique; `encargado_sucursal`/`cajero` solo
        la suya, y únicamente si la venta se recoge en ella."""
        if str(usuario.rol) == "administrador":
            return
        if venta.id_sucursal_retiro != usuario.id_sucursal:
            raise AuthorizationError(
                "Solo puedes confirmar o cancelar pagos en efectivo de tu propia sucursal.",
                code="SUCURSAL_AJENA",
            )

    @staticmethod
    def _buscar_pago_idempotente(
        db: Session, id_venta: int, clave: str
    ) -> Optional[PagoORM]:
        """Localiza un cobro previo, vivo, con la misma clave de idempotencia.

        «Vivo» incluye `confirmado` (tarjeta/Bizum/PayPal) y `pendiente` (efectivo, todavía sin
        confirmar en caja): reenviar la misma clave debe devolver ese mismo intento, no crear uno
        nuevo. Un pago `rechazado` no cuenta como vivo: ahí sí cabe un reintento real.

        La clave se guarda dentro de `payload_respuesta`, que es `jsonb`, de modo que no hace
        falta ninguna columna adicional.
        """
        stmt = (
            select(PagoORM)
            .where(
                PagoORM.id_venta == id_venta,
                PagoORM.estado.in_(("confirmado", "pendiente")),
                PagoORM.payload_respuesta["clave_idempotencia"].astext == clave,
            )
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def _payload_auditoria(resultado, aprobado: bool) -> dict:
        """Compone lo que se fusiona sobre `pagos.payload_respuesta` al verificar el intento.

        `clave_idempotencia` y `metodo_pago` ya están en el payload desde `iniciar_pago`; aquí
        solo se añade el desenlace. Solo marca y últimos cuatro dígitos de la tarjeta: ni el PAN
        completo ni el CVV llegan nunca a este servidor.
        """
        return {
            "aprobado": aprobado,
            "codigo_respuesta": resultado.codigo_respuesta,
            "mensaje": resultado.mensaje,
            "marca_tarjeta": resultado.marca,
            "ultimos_digitos": resultado.ultimos_digitos,
            "pasarela": resultado.payload,
        }

    @staticmethod
    def _construir_confirmacion(
        venta: VentaORM,
        pago: PagoORM,
        resultado=None,
        mensaje: Optional[str] = None,
    ) -> PagoConfirmadoOut:
        """Ensambla la respuesta a partir del pago persistido.

        `confirmado_en` refleja exactamente lo que hay en la fila: `None` para un pago en
        efectivo todavía `pendiente`, nunca una fecha inventada por el servidor.
        """
        auditoria = pago.payload_respuesta or {}
        datos = dict(
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
            confirmado_en=pago.confirmado_en,
        )
        if mensaje is not None:
            datos["mensaje_confirmacion"] = mensaje
        return PagoConfirmadoOut(**datos)
