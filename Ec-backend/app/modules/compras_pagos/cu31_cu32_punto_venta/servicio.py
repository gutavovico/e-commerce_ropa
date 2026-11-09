"""Punto de venta presencial: CU31 (registrar venta) y CU32 (cobrar y emitir comprobante).

Modelo de stock (spec.md §0.2, D1-A), el mismo de CU15/CU16:
- Registrar retiene las líneas añadidas en caja: `disponible → reservada`, movimiento `reserva` con
  `referencia_documento = VENTA-{id}`.
- Las líneas de una reserva NO se retienen otra vez: ya están en `reservada` desde CU12 (D5).
- Cobrar consolida (`venta_confirmada`) sobre la fila exacta de cada retención; lo que el cliente
  dejó de la reserva se libera (`liberacion_reserva`) y la reserva pasa a `atendida`.
- Anular (manual o por vencimiento de 2 h) libera solo lo que retuvo el punto de venta
  (`cancelacion_pedido`); la reserva vuelve a `confirmada` con su stock apartado.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu11_gestionar_carrito.servicio import (
    CarritoServicio,
    calcular_iva_incluido,
    redondear,
)
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio
from modules.compras_pagos.cu31_cu32_punto_venta.esquemas import (
    ClientePosOut,
    CobroPosIn,
    CuponPosOut,
    LineaReservaPosOut,
    LineaVentaPosOut,
    PagoPosOut,
    PedidoWebEfectivoOut,
    PrevisualizacionPosOut,
    ReservaPosOut,
    VariantePosOut,
    VentaPosIn,
    VentaPosOut,
)
from modules.compras_pagos.cu31_cu32_punto_venta.repositorio import PuntoVentaRepositorio
from modules.compras_pagos.modelos import PagoORM, VentaDetalleORM, VentaORM
from modules.reservas.atencion_caja import ReservaCajaServicio
from modules.reservas.modelos import MovimientoInventarioORM
from core.tiempo import inicio_del_dia

logger = logging.getLogger("fashionstore.punto_venta")

#: Roles que operan la caja (los mismos que CU16, D9).
ROLES_CAJA = ("administrador", "encargado_sucursal", "cajero")

#: Una orden de caja sin cobrar más tiempo que esto se anula sola (D2).
TIEMPO_MAXIMO_PENDIENTE = timedelta(hours=2)


@dataclass
class _Linea:
    """Línea calculada. `subtotal_linea` e `id_producto` los usa la validación del cupón."""

    variante: object
    cantidad: int
    precio_lista: Decimal
    precio_unitario: Decimal
    bruto: Decimal
    ahorro: Decimal
    motivo_descuento: Optional[str]
    origen: str  # "reserva" | "caja"

    @property
    def id_producto(self) -> int:
        return self.variante.producto.id_producto

    @property
    def subtotal_linea(self) -> Decimal:
        return redondear(self.precio_unitario * self.cantidad)


@dataclass
class _Calculo:
    lineas: List[_Linea]
    excluidas: list  # ReservaDetalleORM que el cliente no se lleva
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    promocion: object
    codigo_cupon: Optional[str]


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _con_tz(fecha: datetime) -> datetime:
    return fecha if fecha.tzinfo is not None else fecha.replace(tzinfo=timezone.utc)


def _talla(variante) -> str:
    return variante.talla.codigo if getattr(variante, "talla", None) else "-"


def _color(variante) -> str:
    return variante.color.nombre if getattr(variante, "color", None) else "-"


class PuntoVentaServicio:
    # ==================================================================
    # Alcance: sucursal y empleado
    # ==================================================================

    @staticmethod
    def _es_admin(usuario: UsuarioORM) -> bool:
        return str(usuario.rol) == "administrador"

    @staticmethod
    def resolver_sucursal(db: Session, usuario: UsuarioORM, solicitada: Optional[int]) -> int:
        """Administrador: la que elija (D9). Cajero y encargado: una de sus sucursales autorizadas
        (RN07, P2-CU03); sin indicarla, la principal."""
        if PuntoVentaServicio._es_admin(usuario):
            if not solicitada:
                raise UnprocessableEntityError(
                    "Selecciona la boutique en la que vas a operar la caja.", code="SUCURSAL_REQUERIDA"
                )
            id_sucursal = solicitada
        else:
            autorizadas = SucursalesEmpleadoServicio.autorizadas(usuario)
            if not autorizadas:
                raise ConflictError(
                    "Tu usuario no tiene boutique asignada. Pide a un administrador que la configure.",
                    code="SUCURSAL_NO_ASIGNADA",
                )
            if solicitada and solicitada not in autorizadas:
                raise AuthorizationError(
                    "Solo puedes operar la caja de tus boutiques autorizadas.", code="SUCURSAL_AJENA"
                )
            id_sucursal = solicitada or usuario.id_sucursal or min(autorizadas)

        if not CarritoRepositorio.obtener_sucursal_activa(db, id_sucursal):
            raise UnprocessableEntityError("La boutique no existe o está inactiva.", code="SUCURSAL_INVALIDA")
        return id_sucursal

    @staticmethod
    def _verificar_alcance(usuario: UsuarioORM, venta: VentaORM) -> None:
        if not SucursalesEmpleadoServicio.autoriza(usuario, venta.id_sucursal):
            raise AuthorizationError(
                "Solo puedes operar las ventas de tus boutiques autorizadas.", code="SUCURSAL_AJENA"
            )

    # ==================================================================
    # Consultas de apoyo (SKU, cliente, reserva)
    # ==================================================================

    @staticmethod
    def _variante_out(variante, promociones, disponible: int) -> VariantePosOut:
        precio_lista, precio_unitario, _, _, _ = CarritoServicio.precio_linea(variante, 1, promociones)
        categoria = getattr(variante.producto, "categoria", None)
        return VariantePosOut(
            id_variante=variante.id_variante,
            sku=variante.sku,
            id_producto=variante.producto.id_producto,
            nombre_producto=variante.producto.nombre,
            categoria_nombre=categoria.nombre if categoria is not None else None,
            talla_codigo=_talla(variante),
            color_nombre=_color(variante),
            imagen_url=variante.producto.imagen_url,
            precio_lista=precio_lista,
            precio_final=precio_unitario,
            disponible_en_sucursal=disponible,
        )

    @staticmethod
    def buscar_variante(db: Session, usuario: UsuarioORM, sku: str, id_sucursal: Optional[int]) -> VariantePosOut:
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        variante = PuntoVentaRepositorio.variante_por_sku(db, sku)
        if variante is None:
            raise NotFoundError(f"No existe ninguna prenda con el SKU «{sku}».", code="SKU_NO_ENCONTRADO")
        promociones = CarritoRepositorio.obtener_promociones_por_producto(db, [variante.producto.id_producto])
        return PuntoVentaServicio._variante_out(
            variante, promociones, PuntoVentaRepositorio.disponible_en_sucursal(db, variante.id_variante, sucursal)
        )

    @staticmethod
    def buscar_variantes(db: Session, usuario: UsuarioORM, texto: str, id_sucursal: Optional[int]) -> List[VariantePosOut]:
        """Todas las tallas y colores de las prendas cuyo nombre, categoría o SKU coinciden, con el
        precio vigente y el stock de esta boutique (también las agotadas, para que el cajero lo vea)."""
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        variantes = PuntoVentaRepositorio.buscar_variantes(db, texto)
        if not variantes:
            return []
        promociones = CarritoRepositorio.obtener_promociones_por_producto(
            db, list({v.producto.id_producto for v in variantes})
        )
        stock = PuntoVentaRepositorio.disponibles_en_sucursal(db, [v.id_variante for v in variantes], sucursal)
        return [PuntoVentaServicio._variante_out(v, promociones, stock.get(v.id_variante, 0)) for v in variantes]

    @staticmethod
    def buscar_clientes(db: Session, texto: str) -> List[ClientePosOut]:
        """Clientes registrados por nombre, apellidos o correo. Sin coincidencias, la venta se hace
        igualmente como presencial sin cuenta."""
        return [PuntoVentaServicio._cliente_out(u) for u in PuntoVentaRepositorio.buscar_clientes(db, texto)]

    @staticmethod
    def reservas_de_cliente(
        db: Session, usuario: UsuarioORM, id_cliente: int, id_sucursal: Optional[int]
    ) -> List[ReservaPosOut]:
        """Reservas activas del cliente que esta caja puede cargar (solo lectura)."""
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        cliente = PuntoVentaRepositorio.usuario_de_cliente(db, id_cliente)
        if cliente is None:
            raise NotFoundError("El cliente indicado no existe.", code="CLIENTE_NO_ENCONTRADO")
        return [
            PuntoVentaServicio._reserva_out(r, cliente)
            for r in ReservaCajaServicio.atendibles_de_cliente(db, id_cliente, sucursal)
        ]

    @staticmethod
    def cupones_disponibles(db: Session, texto: Optional[str]) -> List[CuponPosOut]:
        """Cupones vigentes con usos disponibles. El descuento lo sigue calculando `previsualizar`."""
        return [
            CuponPosOut(
                codigo=p.codigo_cupon.strip(),
                nombre=p.nombre,
                descripcion=p.descripcion,
                tipo_descuento=p.tipo_descuento or "porcentaje",
                valor_descuento=p.valor_descuento,
                alcance=p.alcance or "global",
                fecha_fin=p.fecha_fin,
                usos_restantes=(p.limite_usos - (p.usos_actuales or 0)) if p.limite_usos is not None else None,
            )
            for p in PuntoVentaRepositorio.cupones_vigentes(db, texto, _ahora())
        ]

    @staticmethod
    def _cliente_out(usuario: UsuarioORM) -> ClientePosOut:
        return ClientePosOut(
            id_cliente=usuario.id_usuario,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            email=str(usuario.email),
        )

    @staticmethod
    def _cargar_reserva(db: Session, usuario: UsuarioORM, referencia: str, id_sucursal: int):
        """Carga y valida la reserva. Si el vencimiento perezoso la venció, se confirma ese
        cambio antes de rechazarla, para que el stock liberado no se pierda con el rollback."""
        try:
            reserva = ReservaCajaServicio.obtener_para_caja(db, referencia, id_sucursal, usuario)
        except ConflictError as error:
            if error.code == "RESERVA_NO_ATENDIBLE":
                db.commit()
            raise
        en_caja = PuntoVentaRepositorio.venta_pendiente_de_reserva(db, reserva.id_reserva)
        if en_caja is not None:
            raise ConflictError(
                f"La reserva {ReservaCajaServicio.codigo(reserva)} ya está en la orden de caja "
                f"{en_caja.numero_comprobante}, pendiente de cobro.",
                code="RESERVA_NO_ATENDIBLE",
            )
        return reserva

    @staticmethod
    def consultar_reserva(db: Session, usuario: UsuarioORM, referencia: str, id_sucursal: Optional[int]) -> ReservaPosOut:
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        reserva = PuntoVentaServicio._cargar_reserva(db, usuario, referencia, sucursal)
        cliente = PuntoVentaRepositorio.usuario_de_cliente(db, reserva.id_cliente)
        return PuntoVentaServicio._reserva_out(reserva, cliente)

    @staticmethod
    def _reserva_out(reserva, cliente: Optional[UsuarioORM]) -> ReservaPosOut:
        return ReservaPosOut(
            id_reserva=reserva.id_reserva,
            codigo=ReservaCajaServicio.codigo(reserva),
            estado=reserva.estado,
            fecha_hora_atencion=reserva.fecha_hora_atencion,
            cliente=PuntoVentaServicio._cliente_out(cliente) if cliente else None,
            lineas=[PuntoVentaServicio._linea_reserva_out(d) for d in reserva.detalles],
        )

    @staticmethod
    def _linea_reserva_out(detalle) -> LineaReservaPosOut:
        variante = detalle.variante
        return LineaReservaPosOut(
            id_variante=detalle.id_variante,
            sku=variante.sku,
            nombre_producto=variante.producto.nombre,
            talla_codigo=_talla(variante),
            color_nombre=_color(variante),
            cantidad=detalle.cantidad,
        )

    # ==================================================================
    # Cálculo (compartido por previsualizar y registrar)
    # ==================================================================

    @staticmethod
    def _calcular(db: Session, datos: VentaPosIn, reserva) -> _Calculo:
        detalles_reserva = {d.id_variante: d for d in (reserva.detalles if reserva else [])}

        desconocidas = set(datos.lineas_reserva_excluidas) - set(detalles_reserva)
        if desconocidas:
            raise UnprocessableEntityError(
                "Solo pueden excluirse prendas que pertenecen a la reserva cargada.",
                code="LINEA_RESERVA_DESCONOCIDA",
            )

        # Líneas añadidas en caja, consolidadas por variante.
        cantidades: Dict[int, int] = {}
        for linea in datos.lineas:
            if linea.id_variante in detalles_reserva:
                raise UnprocessableEntityError(
                    "Esa prenda ya forma parte de la reserva cargada.", code="VARIANTE_YA_EN_RESERVA"
                )
            cantidades[linea.id_variante] = cantidades.get(linea.id_variante, 0) + linea.cantidad

        variantes = PuntoVentaRepositorio.variantes_por_ids(db, cantidades)
        for id_variante in cantidades:
            variante = variantes.get(id_variante)
            if variante is None or not variante.activo or not variante.producto.activo:
                raise NotFoundError(
                    f"La prenda {id_variante} no existe o no está a la venta.", code="SKU_NO_ENCONTRADO"
                )

        conservadas = [d for v, d in detalles_reserva.items() if v not in datos.lineas_reserva_excluidas]
        excluidas = [d for v, d in detalles_reserva.items() if v in datos.lineas_reserva_excluidas]
        if not conservadas and not cantidades:
            raise UnprocessableEntityError("Añade al menos una prenda a la venta.", code="VENTA_VACIA")

        productos = [d.variante.producto.id_producto for d in conservadas] + [
            variantes[v].producto.id_producto for v in cantidades
        ]
        promociones = CarritoRepositorio.obtener_promociones_por_producto(db, productos)

        lineas: List[_Linea] = []
        pares = [(d.variante, d.cantidad, "reserva") for d in conservadas] + [
            (variantes[v], c, "caja") for v, c in cantidades.items()
        ]
        for variante, cantidad, origen in pares:
            precio_lista, precio_unitario, bruto, ahorro, motivo = CarritoServicio.precio_linea(
                variante, cantidad, promociones
            )
            lineas.append(_Linea(variante, cantidad, precio_lista, precio_unitario, bruto, ahorro, motivo, origen))

        subtotal = redondear(sum((l.bruto for l in lineas), Decimal("0.00")))
        descuento_catalogo = redondear(sum((l.ahorro for l in lineas), Decimal("0.00")))
        promocion, descuento_cupon = CheckoutServicio.evaluar_cupon(
            db, datos.codigo_cupon, redondear(subtotal - descuento_catalogo), lineas, consumir=False
        )
        descuento = redondear(descuento_catalogo + descuento_cupon)
        return _Calculo(
            lineas=lineas,
            excluidas=excluidas,
            subtotal=subtotal,
            descuento=descuento,
            total=redondear(subtotal - descuento),
            promocion=promocion,
            codigo_cupon=datos.codigo_cupon.strip().upper() if promocion and datos.codigo_cupon else None,
        )

    @staticmethod
    def _error_stock(variante, disponible: int, solicitada: int) -> ConflictError:
        return ConflictError(
            f"No hay existencias suficientes de «{variante.producto.nombre}» (talla {_talla(variante)}, "
            f"{_color(variante)}) en esta boutique. Disponibles: {disponible}, solicitadas: {solicitada}.",
            code="STOCK_INSUFICIENTE",
        )

    @staticmethod
    def previsualizar(db: Session, usuario: UsuarioORM, datos: VentaPosIn) -> PrevisualizacionPosOut:
        """Totales autoritativos sin persistir ni consumir el cupón (la web no deriva importes)."""
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, datos.id_sucursal)
        reserva = PuntoVentaServicio._cargar_reserva(db, usuario, datos.reserva, sucursal) if datos.reserva else None
        calculo = PuntoVentaServicio._calcular(db, datos, reserva)
        for linea in calculo.lineas:
            if linea.origen == "caja":
                disponible = PuntoVentaRepositorio.disponible_en_sucursal(db, linea.variante.id_variante, sucursal)
                if disponible < linea.cantidad:
                    raise PuntoVentaServicio._error_stock(linea.variante, disponible, linea.cantidad)
        return PrevisualizacionPosOut(
            subtotal=calculo.subtotal,
            descuento=calculo.descuento,
            total=calculo.total,
            iva_incluido=calcular_iva_incluido(calculo.total),
            cupon_aplicado=calculo.codigo_cupon,
            lineas=[PuntoVentaServicio._linea_calculada_out(l) for l in calculo.lineas],
            lineas_reserva_excluidas=[PuntoVentaServicio._linea_reserva_out(d) for d in calculo.excluidas],
        )

    @staticmethod
    def _linea_calculada_out(linea: _Linea) -> LineaVentaPosOut:
        variante = linea.variante
        return LineaVentaPosOut(
            id_variante=variante.id_variante,
            sku=variante.sku,
            nombre_producto=variante.producto.nombre,
            talla_codigo=_talla(variante),
            color_nombre=_color(variante),
            imagen_url=variante.producto.imagen_url,
            cantidad=linea.cantidad,
            precio_lista=linea.precio_lista,
            precio_unitario=linea.precio_unitario,
            subtotal_linea=linea.subtotal_linea,
            motivo_descuento=linea.motivo_descuento,
            origen=linea.origen,
        )

    # ==================================================================
    # CU31 · Registrar venta presencial
    # ==================================================================

    @staticmethod
    def registrar_venta(db: Session, usuario: UsuarioORM, datos: VentaPosIn) -> VentaPosOut:
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, datos.id_sucursal)
        if not PuntoVentaRepositorio.es_empleado(db, usuario.id_usuario):
            raise ConflictError(
                "Tu usuario no tiene ficha de empleado y no puede figurar como cajero. "
                "Pide a un administrador que la regularice.",
                code="EMPLEADO_NO_REGISTRADO",
            )

        reserva = PuntoVentaServicio._cargar_reserva(db, usuario, datos.reserva, sucursal) if datos.reserva else None

        if reserva is not None:
            id_cliente = reserva.id_cliente
        elif datos.id_cliente:
            if PuntoVentaRepositorio.usuario_de_cliente(db, datos.id_cliente) is None:
                raise NotFoundError("El cliente indicado no existe.", code="CLIENTE_NO_ENCONTRADO")
            id_cliente = datos.id_cliente
        else:
            id_cliente = None  # venta sin registro previo (D4)

        calculo = PuntoVentaServicio._calcular(db, datos, reserva)

        # Bloqueo y revalidación del inventario de las líneas añadidas en caja (POS-02).
        inventarios = {}
        for linea in calculo.lineas:
            if linea.origen != "caja":
                continue
            inventario = CarritoRepositorio.obtener_inventario(
                db, linea.variante.id_variante, sucursal, linea.cantidad, bloquear=True
            )
            disponible = inventario.cantidad_disponible if inventario else 0
            if inventario is None or disponible < linea.cantidad:
                raise PuntoVentaServicio._error_stock(linea.variante, disponible, linea.cantidad)
            inventarios[linea.variante.id_variante] = inventario

        venta = VentaORM(
            fecha_venta=_ahora(),
            numero_comprobante=CheckoutServicio.generar_numero_comprobante(db),
            id_cliente=id_cliente,
            id_sucursal=sucursal,
            id_cajero=usuario.id_usuario,
            id_reserva=reserva.id_reserva if reserva else None,
            tipo_venta="presencial",
            estado="pendiente",
            subtotal=calculo.subtotal,
            descuento=calculo.descuento,
            total=calculo.total,
            # El cliente se lleva la prenda en la propia boutique.
            tipo_entrega="recogida_boutique",
            id_sucursal_retiro=sucursal,
            id_promocion=calculo.promocion.id_promocion if calculo.promocion else None,
        )
        db.add(venta)
        db.flush()

        for linea in calculo.lineas:
            db.add(
                VentaDetalleORM(
                    id_venta=venta.id_venta,
                    id_variante=linea.variante.id_variante,
                    cantidad=linea.cantidad,
                    precio_unitario=linea.precio_unitario,
                    id_sucursal=sucursal,
                )
            )
            inventario = inventarios.get(linea.variante.id_variante)
            if inventario is None:
                continue  # línea de la reserva: ya está apartada
            saldo_anterior = inventario.cantidad_disponible
            inventario.cantidad_disponible -= linea.cantidad
            inventario.cantidad_reservada += linea.cantidad
            db.add(
                MovimientoInventarioORM(
                    id_inventario=inventario.id_inventario,
                    tipo_movimiento="reserva",
                    cantidad=linea.cantidad,
                    id_usuario=usuario.id_usuario,
                    referencia_documento=f"VENTA-{venta.id_venta}",
                    motivo=f"Retención en caja de la venta presencial {venta.numero_comprobante}",
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=inventario.cantidad_disponible,
                )
            )

        if reserva is not None:
            ReservaCajaServicio.marcar_en_atencion(reserva)

        PuntoVentaServicio._auditar(
            db, usuario, "POS_REGISTRAR_VENTA",
            {"id_venta": venta.id_venta, "comprobante": venta.numero_comprobante, "total": str(venta.total),
             "id_reserva": venta.id_reserva},
        )
        db.commit()
        return PuntoVentaServicio.obtener_venta(db, usuario, venta.id_venta)

    # ==================================================================
    # CU32 · Cobrar y emitir comprobante
    # ==================================================================

    @staticmethod
    def _cargar_para_operar(db: Session, usuario: UsuarioORM, id_venta: int) -> VentaORM:
        venta = PuntoVentaRepositorio.cargar_venta(db, id_venta, bloquear=True)
        if venta is None or venta.tipo_venta != "presencial":
            raise NotFoundError("La venta de caja no existe.", code="VENTA_NO_ENCONTRADA")
        PuntoVentaServicio._verificar_alcance(usuario, venta)
        return venta

    @staticmethod
    def _esta_vencida(venta: VentaORM) -> bool:
        return venta.estado == "pendiente" and _ahora() - _con_tz(venta.fecha_venta) > TIEMPO_MAXIMO_PENDIENTE

    @staticmethod
    def _exigir_pendiente(venta: VentaORM) -> None:
        if venta.estado != "pendiente":
            raise ConflictError(
                f"La venta {venta.numero_comprobante} está «{venta.estado}» y ya no admite esta operación.",
                code="VENTA_NO_PENDIENTE",
            )

    @staticmethod
    def _validar_cobro(venta: VentaORM, datos: CobroPosIn) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Devuelve `(monto_recibido, cambio)` para efectivo; `(None, None)` en el resto."""
        if datos.metodo_pago == "efectivo":
            if not datos.aprobado:
                raise UnprocessableEntityError("Un pago en efectivo no puede registrarse como rechazado.", code="COBRO_INVALIDO")
            if datos.monto_recibido is None:
                raise UnprocessableEntityError("Indica el importe recibido en efectivo.", code="MONTO_REQUERIDO")
            recibido = redondear(datos.monto_recibido)
            if recibido < venta.total:
                raise UnprocessableEntityError(
                    f"El importe recibido ({recibido}) no cubre el total ({venta.total}).",
                    code="MONTO_INSUFICIENTE",
                )
            return recibido, redondear(recibido - venta.total)
        if not datos.referencia:
            raise UnprocessableEntityError(
                "Indica la referencia de la operación (autorización del datáfono, QR o transferencia).",
                code="REFERENCIA_REQUERIDA",
            )
        return None, None

    @staticmethod
    def cobrar_venta(db: Session, usuario: UsuarioORM, id_venta: int, datos: CobroPosIn) -> VentaPosOut:
        venta = PuntoVentaServicio._cargar_para_operar(db, usuario, id_venta)
        if PuntoVentaServicio._esta_vencida(venta):
            PuntoVentaServicio._anular(db, usuario, venta, "Vencida sin cobrar en el plazo de caja.")
            db.commit()
            raise ConflictError(
                f"La venta {venta.numero_comprobante} venció sin cobrarse y se anuló. Regístrala de nuevo.",
                code="VENTA_NO_PENDIENTE",
            )
        PuntoVentaServicio._exigir_pendiente(venta)
        recibido, cambio = PuntoVentaServicio._validar_cobro(venta, datos)

        if not datos.aprobado:
            db.add(PagoORM(
                id_venta=venta.id_venta, metodo_pago=datos.metodo_pago, monto=venta.total, estado="rechazado",
                referencia_pasarela=datos.referencia,
                payload_respuesta={"canal": "pos", "id_usuario_caja": usuario.id_usuario, "resultado": "rechazado"},
            ))
            PuntoVentaServicio._auditar(db, usuario, "POS_COBRO_RECHAZADO",
                                        {"id_venta": venta.id_venta, "metodo": datos.metodo_pago})
            db.commit()
            return PuntoVentaServicio.obtener_venta(db, usuario, venta.id_venta)

        # Cupón: se consume ahora, al cobrar (D7).
        if venta.id_promocion and venta.promocion is not None and venta.promocion.codigo_cupon:
            if not CarritoRepositorio.consumir_uso_cupon(db, venta.promocion):
                raise ConflictError(
                    f"El cupón «{venta.promocion.codigo_cupon}» agotó sus usos. Anula la orden y regístrala sin él.",
                    code="CUPON_AGOTADO",
                )

        PuntoVentaServicio._consolidar_stock(db, usuario, venta)

        ahora = _ahora()
        db.add(PagoORM(
            id_venta=venta.id_venta, metodo_pago=datos.metodo_pago, monto=venta.total, estado="confirmado",
            referencia_pasarela=datos.referencia, confirmado_en=ahora,
            payload_respuesta={
                "canal": "pos",
                "id_usuario_caja": usuario.id_usuario,
                "monto_recibido": str(recibido) if recibido is not None else None,
                "cambio": str(cambio) if cambio is not None else None,
            },
        ))
        venta.estado = "pagada"
        PuntoVentaServicio._auditar(
            db, usuario, "POS_COBRAR_VENTA",
            {"id_venta": venta.id_venta, "comprobante": venta.numero_comprobante, "metodo": datos.metodo_pago,
             "total": str(venta.total)},
        )
        db.commit()
        return PuntoVentaServicio.obtener_venta(db, usuario, venta.id_venta)

    @staticmethod
    def _reserva_de(db: Session, venta: VentaORM):
        return ReservaCajaServicio.bloquear(db, venta.id_reserva) if venta.id_reserva else None

    @staticmethod
    def _consolidar_stock(db: Session, usuario: UsuarioORM, venta: VentaORM) -> None:
        reserva = PuntoVentaServicio._reserva_de(db, venta)
        detalles_reserva = {d.id_variante: d for d in (reserva.detalles if reserva else [])}
        vendidas = set()

        for detalle in venta.detalles:
            vendidas.add(detalle.id_variante)
            if detalle.id_variante in detalles_reserva:
                ReservaCajaServicio.consolidar_linea(
                    db, reserva, detalles_reserva[detalle.id_variante], usuario,
                    venta.id_venta, venta.numero_comprobante,
                )
                continue
            inventario = PuntoVentaServicio._fila_retenida(db, venta, detalle.id_variante)
            if inventario is None:
                continue
            saldo_anterior = inventario.cantidad_reservada
            inventario.cantidad_reservada = max(0, inventario.cantidad_reservada - detalle.cantidad)
            db.add(MovimientoInventarioORM(
                id_inventario=inventario.id_inventario, tipo_movimiento="venta_confirmada",
                cantidad=-detalle.cantidad, id_usuario=usuario.id_usuario,
                referencia_documento=f"VENTA-{venta.id_venta}",
                motivo=f"Salida definitiva por cobro en caja de {venta.numero_comprobante}",
                saldo_anterior=saldo_anterior, saldo_nuevo=inventario.cantidad_reservada,
            ))

        if reserva is not None:
            for id_variante, detalle in detalles_reserva.items():
                if id_variante not in vendidas:
                    ReservaCajaServicio.liberar_linea(db, reserva, detalle, usuario, venta.numero_comprobante)
            ReservaCajaServicio.marcar_atendida(reserva, usuario)

    @staticmethod
    def _fila_retenida(db: Session, venta: VentaORM, id_variante: int):
        movimiento = PuntoVentaRepositorio.buscar_retencion_venta(db, venta.id_venta, id_variante)
        if movimiento is None:
            # Ventas sembradas antes del punto de venta no tienen retención que mover.
            logger.warning("Sin retención de caja para la variante %s de %s", id_variante, venta.numero_comprobante)
            return None
        return PuntoVentaRepositorio.inventario_por_id(db, movimiento.id_inventario)

    # ==================================================================
    # Anulación y vencimiento
    # ==================================================================

    @staticmethod
    def anular_venta(db: Session, usuario: UsuarioORM, id_venta: int, motivo: str) -> VentaPosOut:
        venta = PuntoVentaServicio._cargar_para_operar(db, usuario, id_venta)
        PuntoVentaServicio._exigir_pendiente(venta)
        PuntoVentaServicio._anular(db, usuario, venta, motivo)
        db.commit()
        return PuntoVentaServicio.obtener_venta(db, usuario, venta.id_venta)

    @staticmethod
    def _anular(db: Session, usuario: UsuarioORM, venta: VentaORM, motivo: str) -> None:
        reserva = PuntoVentaServicio._reserva_de(db, venta)
        de_reserva = {d.id_variante for d in (reserva.detalles if reserva else [])}

        for detalle in venta.detalles:
            if detalle.id_variante in de_reserva:
                continue  # sigue apartada por la reserva
            inventario = PuntoVentaServicio._fila_retenida(db, venta, detalle.id_variante)
            if inventario is None:
                continue
            cantidad = min(detalle.cantidad, inventario.cantidad_reservada)
            if cantidad <= 0:
                continue
            saldo_anterior = inventario.cantidad_disponible
            inventario.cantidad_reservada -= cantidad
            inventario.cantidad_disponible += cantidad
            db.add(MovimientoInventarioORM(
                id_inventario=inventario.id_inventario, tipo_movimiento="cancelacion_pedido",
                cantidad=cantidad, id_usuario=usuario.id_usuario,
                referencia_documento=f"VENTA-{venta.id_venta}",
                motivo=f"Anulación en caja de {venta.numero_comprobante}: {motivo}",
                saldo_anterior=saldo_anterior, saldo_nuevo=inventario.cantidad_disponible,
            ))

        if reserva is not None:
            ReservaCajaServicio.devolver_a_confirmada(reserva)
        venta.estado = "anulada"
        PuntoVentaServicio._auditar(
            db, usuario, "POS_ANULAR_VENTA",
            {"id_venta": venta.id_venta, "comprobante": venta.numero_comprobante, "motivo": motivo},
        )

    @staticmethod
    def _vencer_pendientes(db: Session, usuario: UsuarioORM, id_sucursal: int) -> None:
        for venta in PuntoVentaRepositorio.listar_ventas(db, id_sucursal, "pendiente", None):
            if not PuntoVentaServicio._esta_vencida(venta):
                continue
            bloqueada = PuntoVentaRepositorio.cargar_venta(db, venta.id_venta, bloquear=True)
            if bloqueada is not None and PuntoVentaServicio._esta_vencida(bloqueada):
                PuntoVentaServicio._anular(db, usuario, bloqueada, "Vencida sin cobrar en el plazo de caja.")
                db.commit()

    # ==================================================================
    # Lecturas
    # ==================================================================

    @staticmethod
    def listar_ventas(
        db: Session, usuario: UsuarioORM, id_sucursal: Optional[int], estado: Optional[str], solo_hoy: bool
    ) -> List[VentaPosOut]:
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        PuntoVentaServicio._vencer_pendientes(db, usuario, sucursal)
        desde = None
        if solo_hoy:
            desde = inicio_del_dia()  # medianoche de Bolivia (fix P2-CU11, M5)
        ventas = PuntoVentaRepositorio.listar_ventas(db, sucursal, estado, desde)
        return [PuntoVentaServicio._salida(db, v) for v in ventas]

    @staticmethod
    def obtener_venta(db: Session, usuario: UsuarioORM, id_venta: int) -> VentaPosOut:
        db.expire_all()
        venta = PuntoVentaRepositorio.cargar_venta(db, id_venta)
        if venta is None or venta.tipo_venta != "presencial":
            raise NotFoundError("La venta de caja no existe.", code="VENTA_NO_ENCONTRADA")
        PuntoVentaServicio._verificar_alcance(usuario, venta)
        return PuntoVentaServicio._salida(db, venta)

    @staticmethod
    def comprobante_pdf(db: Session, usuario: UsuarioORM, id_venta: int) -> Tuple[str, bytes]:
        from modules.compras_pagos.cu31_cu32_punto_venta.comprobante_pdf import generar_comprobante_pdf

        venta = PuntoVentaServicio.obtener_venta(db, usuario, id_venta)
        if venta.estado == "pendiente":
            raise ConflictError(
                "La venta aún no está cobrada: su comprobante no es definitivo.", code="COMPROBANTE_NO_DISPONIBLE"
            )
        moneda = ParametrosEmpresaServicio.moneda(db)
        return f"{venta.numero_comprobante}.pdf", generar_comprobante_pdf(venta, moneda)

    @staticmethod
    def pedidos_web_efectivo(db: Session, usuario: UsuarioORM, id_sucursal: Optional[int]) -> List[PedidoWebEfectivoOut]:
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        salida = []
        for pago in PuntoVentaRepositorio.pedidos_web_efectivo(db, sucursal):
            venta = pago.venta
            cliente = PuntoVentaRepositorio.usuario_de_cliente(db, venta.id_cliente) if venta.id_cliente else None
            salida.append(PedidoWebEfectivoOut(
                id_pago=pago.id_pago, id_venta=venta.id_venta, numero_comprobante=venta.numero_comprobante,
                cliente_nombre=f"{cliente.nombres} {cliente.apellidos}".strip() if cliente else None,
                total=venta.total, creado_en=pago.creado_en,
            ))
        return salida

    @staticmethod
    def _salida(db: Session, venta: VentaORM) -> VentaPosOut:
        reserva = venta.reserva
        detalles_reserva = {d.id_variante: d for d in (reserva.detalles if reserva else [])}
        promociones = CarritoRepositorio.obtener_promociones_por_producto(
            db, [d.variante.producto.id_producto for d in venta.detalles]
        )

        lineas = []
        for detalle in venta.detalles:
            variante = detalle.variante
            precio_lista = CarritoServicio.precio_linea(variante, detalle.cantidad, promociones)[0]
            precio_unitario = Decimal(detalle.precio_unitario)
            lineas.append(LineaVentaPosOut(
                id_variante=detalle.id_variante, sku=variante.sku, nombre_producto=variante.producto.nombre,
                talla_codigo=_talla(variante), color_nombre=_color(variante), imagen_url=variante.producto.imagen_url,
                cantidad=detalle.cantidad, precio_lista=max(precio_lista, precio_unitario),
                precio_unitario=precio_unitario, subtotal_linea=redondear(precio_unitario * detalle.cantidad),
                origen="reserva" if detalle.id_variante in detalles_reserva else "caja",
            ))

        vendidas = {d.id_variante for d in venta.detalles}
        excluidas = [PuntoVentaServicio._linea_reserva_out(d) for v, d in detalles_reserva.items() if v not in vendidas]

        pagos = []
        for pago in sorted(venta.pagos, key=lambda p: p.creado_en):
            datos = pago.payload_respuesta or {}
            pagos.append(PagoPosOut(
                id_pago=pago.id_pago, metodo_pago=str(pago.metodo_pago), monto=pago.monto, estado=str(pago.estado),
                referencia=pago.referencia_pasarela,
                monto_recibido=Decimal(datos["monto_recibido"]) if datos.get("monto_recibido") else None,
                cambio=Decimal(datos["cambio"]) if datos.get("cambio") else None,
                creado_en=pago.creado_en, confirmado_en=pago.confirmado_en,
            ))

        cajero = venta.cajero.usuario if venta.cajero is not None and venta.cajero.usuario is not None else None
        cliente = PuntoVentaRepositorio.usuario_de_cliente(db, venta.id_cliente) if venta.id_cliente else None
        return VentaPosOut(
            id_venta=venta.id_venta, numero_comprobante=venta.numero_comprobante, estado=str(venta.estado),
            fecha_venta=venta.fecha_venta, id_sucursal=venta.id_sucursal,
            nombre_sucursal=venta.sucursal.nombre if venta.sucursal else "Boutique",
            direccion_sucursal=getattr(venta.sucursal, "direccion", None),
            cajero_nombre=f"{cajero.nombres} {cajero.apellidos}".strip() if cajero else None,
            cliente=PuntoVentaServicio._cliente_out(cliente) if cliente else None,
            reserva_codigo=ReservaCajaServicio.codigo(reserva) if reserva else None,
            subtotal=venta.subtotal, descuento=venta.descuento, total=venta.total,
            iva_incluido=calcular_iva_incluido(Decimal(venta.total)),
            cupon_aplicado=venta.promocion.codigo_cupon if venta.id_promocion and venta.promocion else None,
            lineas=lineas, lineas_reserva_excluidas=excluidas, pagos=pagos,
        )

    # ==================================================================
    # Bitácora (CU30), por su servicio
    # ==================================================================

    @staticmethod
    def _auditar(db: Session, usuario: UsuarioORM, accion: str, payload: dict) -> None:
        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=f"{usuario.nombres} {usuario.apellidos}".strip() or str(usuario.email),
            accion=accion,
            tabla_modulo="ventas",
            severidad="INFO",
            payload_nuevo=payload,
            db=db,
        )
