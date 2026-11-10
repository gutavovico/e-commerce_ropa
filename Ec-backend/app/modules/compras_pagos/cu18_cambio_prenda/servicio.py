"""P2-CU18 · Registrar cambio de prenda (RN30, RN31, RN32).

- **Valor devuelto (decisión F2):** lo pagado por unidad = `precio_unitario × total / Σ subtotal_linea`.
  Las líneas ya llevan las promociones de la prenda y `total` es lo pagado, así que el factor reparte
  solo el cupón; nunca supera el precio de la línea.
- **Prendas nuevas:** precio vigente con sus promociones (el mismo cálculo que la caja), sin cupón.
- **Diferencia** = nuevo − devuelto: positiva se cobra; negativa se devuelve en efectivo (F1).
- **Una transacción por cambio:** `FOR UPDATE` de la venta (dos cambios sobre la misma venta se
  serializan) y de cada fila de inventario. La devuelta entra en la sucursal del cambio (`devolucion`),
  la nueva sale (`venta_confirmada`), ambas con `CAMBIO-{id}`. La venta original sigue `pagada`.
"""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from core.tenant import tenant_actual
from core.tiempo import ZONA_EMPRESA, ahora, hoy, inicio_del_dia
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import InventarioSucursalORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu11_gestionar_carrito.servicio import CarritoServicio, redondear
from modules.compras_pagos.cu18_cambio_prenda.esquemas import (
    CambioIn,
    CambioOut,
    CambioPrevioOut,
    LineaCambiableOut,
    LineaCambioOut,
    VentaCambiableOut,
)
from modules.compras_pagos.cu18_cambio_prenda.repositorio import CambioPrendaRepositorio
from modules.compras_pagos.cu31_cu32_punto_venta.repositorio import PuntoVentaRepositorio
from modules.compras_pagos.cu31_cu32_punto_venta.servicio import PuntoVentaServicio
from modules.compras_pagos.modelos import CambioPrendaDetalleORM, CambioPrendaORM, VentaDetalleORM, VentaORM
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio
from modules.reservas.modelos import MovimientoInventarioORM

CERO = Decimal("0.00")


def _talla(variante) -> str:
    return getattr(getattr(variante, "talla", None), "codigo", "") or ""


def _color(variante) -> str:
    return getattr(getattr(variante, "color", None), "nombre", "") or ""


@dataclass
class _Calculo:
    devueltas: List[LineaCambioOut]
    nuevas: List[LineaCambioOut]
    valor_devuelto: Decimal
    valor_nuevo: Decimal
    variantes_nuevas: Dict[int, object]

    @property
    def diferencia(self) -> Decimal:
        return redondear(self.valor_nuevo - self.valor_devuelto)


class CambioPrendaServicio:
    # ------------------------------------------------------------------ plazo y valores

    @staticmethod
    def plazo_dias(db: Session) -> int:
        """`dias_cambio_prenda` de la empresa (CU11); 0 = sin cambios."""
        return ParametrosEmpresaServicio.vigentes(db).dias_cambio_prenda

    @staticmethod
    def dias_desde(venta: VentaORM) -> int:
        """Días calendario desde la fecha de la venta, en hora de Bolivia."""
        from zoneinfo import ZoneInfo

        fecha = venta.fecha_venta
        dia = fecha.astimezone(ZoneInfo(ZONA_EMPRESA)).date() if fecha.tzinfo else fecha.date()
        return (hoy() - dia).days

    @staticmethod
    def _exigir_plazo(db: Session, venta: VentaORM) -> Tuple[int, int]:
        plazo = CambioPrendaServicio.plazo_dias(db)
        dias = CambioPrendaServicio.dias_desde(venta)
        if plazo <= 0:
            raise ConflictError(
                "Esta tienda no admite cambios de prenda.",
                code="PLAZO_DE_CAMBIO_VENCIDO",
                datos={"dias_transcurridos": dias, "plazo_dias": plazo},
            )
        if dias > plazo:
            raise ConflictError(
                f"Pasaron {dias} días desde la venta y el plazo de cambio es de {plazo} días.",
                code="PLAZO_DE_CAMBIO_VENCIDO",
                datos={"dias_transcurridos": dias, "plazo_dias": plazo},
            )
        return dias, plazo

    @staticmethod
    def factor_pagado(venta: VentaORM, lineas: List[VentaDetalleORM]) -> Decimal:
        """Parte de cada línea que se pagó de verdad (reparte el cupón). Nunca mayor que 1."""
        suma = sum((Decimal(l.precio_unitario) * l.cantidad for l in lineas), CERO)
        if suma <= 0:
            return Decimal("1")
        return min(Decimal("1"), Decimal(venta.total) / suma)

    @staticmethod
    def valor_unitario(precio_unitario: Decimal, factor: Decimal) -> Decimal:
        return min(redondear(Decimal(precio_unitario)), redondear(Decimal(precio_unitario) * factor))

    @staticmethod
    def _venta_pagada(venta: Optional[VentaORM]) -> VentaORM:
        """A4: inexistente, de otra empresa (RLS) o no pagada → no existe para el cambio."""
        if venta is None or venta.estado != "pagada":
            raise NotFoundError("No existe una venta pagada con ese comprobante.", code="VENTA_NO_ENCONTRADA")
        return venta

    # ------------------------------------------------------------------ AC-1

    @staticmethod
    def venta_cambiable(db: Session, usuario: UsuarioORM, comprobante: str, id_sucursal: Optional[int]) -> VentaCambiableOut:
        PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        venta = CambioPrendaServicio._venta_pagada(CambioPrendaRepositorio.venta_por_comprobante(db, comprobante))
        dias, plazo = CambioPrendaServicio._exigir_plazo(db, venta)
        lineas = CambioPrendaRepositorio.lineas_de_venta(db, venta.id_venta)
        ya = CambioPrendaRepositorio.ya_cambiadas(db, [l.id_venta_detalle for l in lineas])
        factor = CambioPrendaServicio.factor_pagado(venta, lineas)
        cliente = db.get(UsuarioORM, venta.id_cliente) if venta.id_cliente else None
        return VentaCambiableOut(
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            fecha_venta=venta.fecha_venta,
            cliente_nombre=f"{cliente.nombres} {cliente.apellidos}".strip() if cliente else None,
            total=venta.total,
            dias_transcurridos=dias,
            plazo_dias=plazo,
            lineas=[
                LineaCambiableOut(
                    id_venta_detalle=l.id_venta_detalle,
                    id_variante=l.id_variante,
                    sku=l.variante.sku,
                    nombre_producto=l.variante.producto.nombre,
                    talla_codigo=_talla(l.variante),
                    color_nombre=_color(l.variante),
                    vendidas=l.cantidad,
                    ya_cambiadas=ya.get(l.id_venta_detalle, 0),
                    cambiables=max(0, l.cantidad - ya.get(l.id_venta_detalle, 0)),
                    valor_unitario=CambioPrendaServicio.valor_unitario(l.precio_unitario, factor),
                )
                for l in lineas
            ],
        )

    # ------------------------------------------------------------------ cálculo (AC-4, AC-6)

    @staticmethod
    def _calcular(db: Session, venta: VentaORM, datos: CambioIn) -> _Calculo:
        lineas = CambioPrendaRepositorio.lineas_de_venta(db, venta.id_venta)
        por_id = {l.id_venta_detalle: l for l in lineas}
        ya = CambioPrendaRepositorio.ya_cambiadas(db, por_id)
        factor = CambioPrendaServicio.factor_pagado(venta, lineas)

        pedidas: Dict[int, int] = defaultdict(int)
        for d in datos.devueltas:
            pedidas[d.id_venta_detalle] += d.cantidad
        devueltas: List[LineaCambioOut] = []
        for id_detalle, cantidad in pedidas.items():
            linea = por_id.get(id_detalle)
            quedan = linea.cantidad - ya.get(id_detalle, 0) if linea else 0
            if linea is None or cantidad > quedan:
                raise ConflictError(
                    "Esa prenda no es de la venta." if linea is None
                    else f"De «{linea.variante.producto.nombre}» quedan {quedan} unidades por cambiar.",
                    code="CANTIDAD_NO_CAMBIABLE",
                )
            unitario = CambioPrendaServicio.valor_unitario(linea.precio_unitario, factor)
            devueltas.append(LineaCambioOut(
                tipo="devuelta", id_venta_detalle=id_detalle, id_variante=linea.id_variante,
                sku=linea.variante.sku, nombre_producto=linea.variante.producto.nombre,
                talla_codigo=_talla(linea.variante), color_nombre=_color(linea.variante),
                cantidad=cantidad, precio_unitario=unitario, subtotal=redondear(unitario * cantidad),
            ))

        cantidades: Dict[int, int] = defaultdict(int)
        for n in datos.nuevas:
            cantidades[n.id_variante] += n.cantidad
        variantes = PuntoVentaRepositorio.variantes_por_ids(db, cantidades)
        for id_variante in cantidades:
            v = variantes.get(id_variante)
            if v is None or not v.activo or not v.producto.activo:
                raise NotFoundError(f"La prenda {id_variante} no existe o no está a la venta.", code="SKU_NO_ENCONTRADO")
        promociones = CarritoRepositorio.obtener_promociones_por_producto(
            db, list({variantes[i].producto.id_producto for i in cantidades})
        )
        nuevas: List[LineaCambioOut] = []
        for id_variante, cantidad in cantidades.items():
            v = variantes[id_variante]
            _, unitario, _, _, motivo = CarritoServicio.precio_linea(v, cantidad, promociones)
            nuevas.append(LineaCambioOut(
                tipo="nueva", id_variante=id_variante, sku=v.sku, nombre_producto=v.producto.nombre,
                talla_codigo=_talla(v), color_nombre=_color(v), cantidad=cantidad,
                precio_unitario=redondear(unitario), subtotal=redondear(unitario * cantidad), motivo_descuento=motivo,
            ))

        return _Calculo(
            devueltas=devueltas,
            nuevas=nuevas,
            valor_devuelto=redondear(sum((l.subtotal for l in devueltas), CERO)),
            valor_nuevo=redondear(sum((l.subtotal for l in nuevas), CERO)),
            variantes_nuevas=variantes,
        )

    @staticmethod
    def previsualizar(db: Session, usuario: UsuarioORM, datos: CambioIn) -> CambioPrevioOut:
        id_sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, datos.id_sucursal)
        venta = CambioPrendaServicio._venta_pagada(CambioPrendaRepositorio.venta(db, datos.id_venta))
        CambioPrendaServicio._exigir_plazo(db, venta)
        calculo = CambioPrendaServicio._calcular(db, venta, datos)
        for linea in calculo.nuevas:  # AC-5 también al previsualizar
            disponible = PuntoVentaRepositorio.disponible_en_sucursal(db, linea.id_variante, id_sucursal)
            if disponible < linea.cantidad:
                raise CambioPrendaServicio._sin_stock(linea, disponible)
        return CambioPrevioOut(
            devueltas=calculo.devueltas, nuevas=calculo.nuevas, valor_devuelto=calculo.valor_devuelto,
            valor_nuevo=calculo.valor_nuevo, diferencia=calculo.diferencia,
        )

    @staticmethod
    def _sin_stock(linea: LineaCambioOut, disponible: int) -> ConflictError:
        return ConflictError(
            f"No hay existencias suficientes de «{linea.nombre_producto}» ({linea.talla_codigo}) en esta "
            f"sucursal. Disponibles: {disponible}.",
            code="STOCK_INSUFICIENTE",
            datos={"id_variante": linea.id_variante, "disponible": disponible},
        )

    # ------------------------------------------------------------------ cobro (AC-7)

    @staticmethod
    def _cobro(diferencia: Decimal, datos: CambioIn) -> Tuple[Optional[str], Optional[Decimal], Optional[Decimal], Optional[str]]:
        """`(metodo, monto_recibido, vuelto, referencia)`."""
        if diferencia < 0:
            return "efectivo", None, None, None  # F1: se devuelve en efectivo
        if diferencia == 0:
            return None, None, None, None
        cobro = datos.cobro
        if cobro is None:
            raise UnprocessableEntityError(
                f"El cliente debe pagar la diferencia ({diferencia}). Indica cómo paga.", code="COBRO_REQUERIDO"
            )
        if cobro.metodo_pago == "efectivo":
            if cobro.monto_recibido is None:
                raise UnprocessableEntityError("Indica el importe recibido en efectivo.", code="MONTO_REQUERIDO")
            recibido = redondear(cobro.monto_recibido)
            if recibido < diferencia:
                raise UnprocessableEntityError(
                    f"El importe recibido ({recibido}) no cubre la diferencia ({diferencia}).", code="MONTO_INSUFICIENTE"
                )
            return "efectivo", recibido, redondear(recibido - diferencia), None
        if not cobro.referencia:
            raise UnprocessableEntityError(
                "Indica la referencia de la operación (autorización del datáfono, QR o transferencia).",
                code="REFERENCIA_REQUERIDA",
            )
        return cobro.metodo_pago, None, None, cobro.referencia

    # ------------------------------------------------------------------ AC-8

    @staticmethod
    def registrar(db: Session, usuario: UsuarioORM, datos: CambioIn) -> CambioOut:
        id_sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, datos.id_sucursal)
        venta = CambioPrendaServicio._venta_pagada(CambioPrendaRepositorio.venta(db, datos.id_venta, bloquear=True))
        CambioPrendaServicio._exigir_plazo(db, venta)
        calculo = CambioPrendaServicio._calcular(db, venta, datos)
        metodo, recibido, vuelto, referencia = CambioPrendaServicio._cobro(calculo.diferencia, datos)

        cambio = CambioPrendaORM(
            numero_comprobante=CambioPrendaRepositorio.siguiente_comprobante(db, tenant_actual(db), ahora().year),
            id_venta=venta.id_venta,
            id_sucursal=id_sucursal,
            id_usuario=usuario.id_usuario,
            valor_devuelto=calculo.valor_devuelto,
            valor_nuevo=calculo.valor_nuevo,
            diferencia=calculo.diferencia,
            metodo_pago=metodo,
            monto_recibido=recibido,
            vuelto=vuelto,
            referencia=referencia,
        )
        db.add(cambio)
        db.flush()
        for l in calculo.devueltas + calculo.nuevas:
            db.add(CambioPrendaDetalleORM(
                id_cambio=cambio.id_cambio, tipo=l.tipo, id_venta_detalle=l.id_venta_detalle,
                id_variante=l.id_variante, cantidad=l.cantidad, precio_unitario=l.precio_unitario, subtotal=l.subtotal,
            ))

        # RN32: primero entra lo devuelto y después sale lo nuevo, en orden de variante (sin interbloqueos).
        referencia_doc = f"CAMBIO-{cambio.id_cambio}"
        for l in sorted(calculo.devueltas, key=lambda x: x.id_variante):
            CambioPrendaServicio._ingresar(db, usuario, l.id_variante, id_sucursal, l.cantidad, referencia_doc, cambio)
        for l in sorted(calculo.nuevas, key=lambda x: x.id_variante):
            CambioPrendaServicio._retirar(db, usuario, l, id_sucursal, referencia_doc, cambio)

        PuntoVentaServicio._auditar(db, usuario, "CAMBIO_PRENDA", {
            "id_cambio": cambio.id_cambio,
            "numero_comprobante": cambio.numero_comprobante,
            "id_venta": venta.id_venta,
            "diferencia": str(calculo.diferencia),
        })
        db.commit()
        return CambioPrendaServicio.obtener(db, usuario, cambio.id_cambio)

    @staticmethod
    def _ingresar(db, usuario, id_variante, id_sucursal, cantidad, referencia_doc, cambio) -> None:
        fila = CambioPrendaRepositorio.inventario(db, id_variante, id_sucursal, 0)
        if fila is None:
            temporada = CambioPrendaRepositorio.temporada_para(db, id_variante)
            if temporada is None:
                raise ConflictError("La empresa no tiene temporadas para registrar la prenda devuelta.", code="SIN_TEMPORADA")
            fila = InventarioSucursalORM(
                id_variante=id_variante, id_sucursal=id_sucursal, id_temporada=temporada,
                cantidad_disponible=0, cantidad_reservada=0,
            )
            db.add(fila)
            db.flush()
        anterior = fila.cantidad_disponible
        fila.cantidad_disponible += cantidad
        db.add(MovimientoInventarioORM(
            id_inventario=fila.id_inventario, tipo_movimiento="devolucion", cantidad=cantidad,
            id_usuario_responsable=usuario.id_usuario, referencia_documento=referencia_doc,
            observacion=f"Prenda devuelta en el cambio {cambio.numero_comprobante}",
            saldo_anterior=anterior, saldo_nuevo=fila.cantidad_disponible,
        ))

    @staticmethod
    def _retirar(db, usuario, linea: LineaCambioOut, id_sucursal, referencia_doc, cambio) -> None:
        fila = CambioPrendaRepositorio.inventario(db, linea.id_variante, id_sucursal, linea.cantidad)
        disponible = fila.cantidad_disponible if fila else 0
        if fila is None or disponible < linea.cantidad:
            raise CambioPrendaServicio._sin_stock(linea, disponible)
        fila.cantidad_disponible -= linea.cantidad
        db.add(MovimientoInventarioORM(
            id_inventario=fila.id_inventario, tipo_movimiento="venta_confirmada", cantidad=-linea.cantidad,
            id_usuario_responsable=usuario.id_usuario, referencia_documento=referencia_doc,
            observacion=f"Prenda entregada en el cambio {cambio.numero_comprobante}",
            saldo_anterior=disponible, saldo_nuevo=fila.cantidad_disponible,
        ))

    # ------------------------------------------------------------------ consulta (AC-9)

    @staticmethod
    def obtener(db: Session, usuario: UsuarioORM, id_cambio: int) -> CambioOut:
        cambio = CambioPrendaRepositorio.cambio(db, id_cambio)
        if cambio is None or not SucursalesEmpleadoServicio.autoriza(usuario, cambio.id_sucursal):
            raise NotFoundError("El cambio no existe.", code="CAMBIO_NO_ENCONTRADO")
        return CambioPrendaServicio._salida(db, cambio)

    @staticmethod
    def listar(db: Session, usuario: UsuarioORM, id_sucursal: Optional[int], solo_hoy: bool) -> List[CambioOut]:
        sucursal = PuntoVentaServicio.resolver_sucursal(db, usuario, id_sucursal)
        cambios = CambioPrendaRepositorio.cambios(db, sucursal, inicio_del_dia() if solo_hoy else None)
        return [CambioPrendaServicio._salida(db, c) for c in cambios]

    @staticmethod
    def _salida(db: Session, cambio: CambioPrendaORM) -> CambioOut:
        detalles = list(cambio.detalles)
        variantes = PuntoVentaRepositorio.variantes_por_ids(db, [d.id_variante for d in detalles])
        lineas = [
            LineaCambioOut(
                tipo=d.tipo, id_venta_detalle=d.id_venta_detalle, id_variante=d.id_variante,
                sku=variantes[d.id_variante].sku if d.id_variante in variantes else "",
                nombre_producto=variantes[d.id_variante].producto.nombre if d.id_variante in variantes else "",
                talla_codigo=_talla(variantes.get(d.id_variante)), color_nombre=_color(variantes.get(d.id_variante)),
                cantidad=d.cantidad, precio_unitario=d.precio_unitario, subtotal=d.subtotal,
            )
            for d in detalles
        ]
        venta = CambioPrendaRepositorio.venta(db, cambio.id_venta)
        sucursal = CambioPrendaRepositorio.sucursal(db, cambio.id_sucursal)
        atendio = db.get(UsuarioORM, cambio.id_usuario)
        return CambioOut(
            id_cambio=cambio.id_cambio,
            numero_comprobante=cambio.numero_comprobante,
            creado_en=cambio.creado_en,
            id_venta=cambio.id_venta,
            comprobante_venta=venta.numero_comprobante if venta else "",
            id_sucursal=cambio.id_sucursal,
            nombre_sucursal=sucursal.nombre if sucursal else "",
            atendido_por=f"{atendio.nombres} {atendio.apellidos}".strip() if atendio else None,
            devueltas=[l for l in lineas if l.tipo == "devuelta"],
            nuevas=[l for l in lineas if l.tipo == "nueva"],
            valor_devuelto=cambio.valor_devuelto,
            valor_nuevo=cambio.valor_nuevo,
            diferencia=cambio.diferencia,
            metodo_pago=cambio.metodo_pago,
            monto_recibido=cambio.monto_recibido,
            vuelto=cambio.vuelto,
            referencia=cambio.referencia,
            devuelto_al_cliente=max(CERO, -Decimal(cambio.diferencia)),
        )
