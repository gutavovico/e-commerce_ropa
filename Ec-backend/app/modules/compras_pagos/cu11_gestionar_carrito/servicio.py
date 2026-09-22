"""Servicio de dominio para CU11: Gestionar carrito de compras (Bolsa de Compra).

Regla transversal: el servidor es la fuente de verdad de todo importe. Los precios se recalculan
en cada lectura a partir del catálogo y de las promociones vigentes; nunca se confía en cifras
enviadas por el cliente.
"""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.errors import AuthorizationError, ConflictError, NotFoundError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu11_gestionar_carrito.esquemas import (
    CarritoItemOut,
    CarritoOut,
    CarritoResumenOut,
    ItemAgregarIn,
    ItemCantidadIn,
    SucursalExpedicionOut,
)
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.modelos import CarritoDetalleORM, CarritoORM, MINUTOS_RETENCION_VENTA

CENTIMO = Decimal("0.01")

# El IVA español está incluido en los precios de catálogo: se desglosa sólo para mostrarlo.
TASA_IVA = Decimal("0.21")


def redondear(valor: Decimal) -> Decimal:
    """Redondea a dos decimales con redondeo comercial (mitad hacia arriba)."""
    return valor.quantize(CENTIMO, rounding=ROUND_HALF_UP)


def calcular_iva_incluido(total: Decimal) -> Decimal:
    """Extrae el IVA ya contenido en un importe: total - total / (1 + tasa)."""
    if total <= 0:
        return Decimal("0.00")
    base = total / (Decimal("1") + TASA_IVA)
    return redondear(total - base)


class CarritoServicio:
    """Orquesta la bolsa de compra: alta, modificación, eliminación y cálculo financiero."""

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    @staticmethod
    def obtener_carrito(db: Session, usuario: UsuarioORM) -> CarritoOut:
        """Devuelve la bolsa del cliente autenticado, creándola vacía si aún no existe.

        Una bolsa sin prendas es un estado legítimo, no un error: se responde 200 con `items`
        vacío y el resumen en ceros, nunca 404.
        """
        cliente = CarritoRepositorio.asegurar_cliente(db, usuario)
        carrito = CarritoRepositorio.obtener_o_crear_carrito(db, cliente.id_cliente)
        db.commit()
        return CarritoServicio._construir_salida(db, carrito)

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    @staticmethod
    def agregar_item(db: Session, usuario: UsuarioORM, payload: ItemAgregarIn) -> CarritoOut:
        """Añade una prenda a la bolsa, consolidando si ya estaba presente.

        Consolidar por (variante, sucursal) evita líneas duplicadas que después violarían la
        restricción de unicidad y descuadrarían el inventario al tramitar el pedido.
        """
        cliente = CarritoRepositorio.asegurar_cliente(db, usuario)
        carrito = CarritoRepositorio.obtener_o_crear_carrito(db, cliente.id_cliente)

        variante = CarritoRepositorio.obtener_variante(db, payload.id_variante)
        if not variante:
            raise NotFoundError(
                f"La prenda solicitada (variante #{payload.id_variante}) no existe en catálogo.",
                code="VARIANTE_NO_ENCONTRADA",
            )

        id_sucursal = CarritoServicio._resolver_sucursal(db, payload, variante)

        linea = CarritoRepositorio.buscar_linea_equivalente(
            db, carrito.id_carrito, payload.id_variante, id_sucursal
        )
        cantidad_final = (linea.cantidad if linea else 0) + payload.cantidad

        CarritoServicio._validar_stock(
            db, variante, id_sucursal, cantidad_final, nombre_sucursal=None
        )

        if linea:
            linea.cantidad = cantidad_final
        else:
            db.add(
                CarritoDetalleORM(
                    id_carrito=carrito.id_carrito,
                    id_variante=payload.id_variante,
                    id_sucursal=id_sucursal,
                    cantidad=payload.cantidad,
                )
            )

        db.commit()
        return CarritoServicio._construir_salida(db, carrito)

    @staticmethod
    def actualizar_cantidad(
        db: Session, usuario: UsuarioORM, id_carrito_detalle: int, payload: ItemCantidadIn
    ) -> CarritoOut:
        """Fija la cantidad de una línea validando el stock de su boutique de expedición."""
        linea = CarritoServicio._obtener_linea_propia(db, usuario, id_carrito_detalle)

        variante = CarritoRepositorio.obtener_variante(db, linea.id_variante)
        if not variante:
            raise NotFoundError(
                "La prenda de esta línea ya no existe en catálogo.",
                code="VARIANTE_NO_ENCONTRADA",
            )

        CarritoServicio._validar_stock(db, variante, linea.id_sucursal, payload.cantidad)

        linea.cantidad = payload.cantidad
        db.commit()

        carrito = CarritoRepositorio.obtener_o_crear_carrito(db, linea.carrito.id_cliente)
        return CarritoServicio._construir_salida(db, carrito)

    @staticmethod
    def eliminar_item(db: Session, usuario: UsuarioORM, id_carrito_detalle: int) -> CarritoOut:
        """Purga una línea de `carrito_detalle` y devuelve la bolsa recalculada."""
        linea = CarritoServicio._obtener_linea_propia(db, usuario, id_carrito_detalle)
        id_cliente = linea.carrito.id_cliente

        db.delete(linea)
        db.commit()

        carrito = CarritoRepositorio.obtener_o_crear_carrito(db, id_cliente)
        return CarritoServicio._construir_salida(db, carrito)

    # ------------------------------------------------------------------
    # Apoyo interno
    # ------------------------------------------------------------------

    @staticmethod
    def _obtener_linea_propia(
        db: Session, usuario: UsuarioORM, id_carrito_detalle: int
    ) -> CarritoDetalleORM:
        """Recupera una línea verificando que pertenece al cliente autenticado."""
        linea = CarritoRepositorio.obtener_linea(db, id_carrito_detalle)
        if not linea:
            raise NotFoundError(
                f"La línea #{id_carrito_detalle} no existe en ninguna bolsa.",
                code="LINEA_NO_ENCONTRADA",
            )
        if linea.carrito.id_cliente != usuario.id_usuario:
            # Se responde 403 y no 404 de forma deliberada: el recurso existe, pero es ajeno.
            raise AuthorizationError(
                "Esta prenda pertenece a la bolsa de otro cliente.",
                code="CARRITO_AJENO",
            )
        return linea

    @staticmethod
    def _resolver_sucursal(db: Session, payload: ItemAgregarIn, variante) -> int:
        """Determina la boutique de expedición, eligiendo la de mayor stock si no se indicó."""
        if payload.id_sucursal is not None:
            sucursal = CarritoRepositorio.obtener_sucursal_activa(db, payload.id_sucursal)
            if not sucursal:
                raise NotFoundError(
                    f"La boutique #{payload.id_sucursal} no se encuentra activa o no existe.",
                    code="SUCURSAL_NO_ENCONTRADA",
                )
            return sucursal.id_sucursal

        inventario = CarritoRepositorio.elegir_sucursal_con_stock(
            db, payload.id_variante, payload.cantidad
        )
        if not inventario:
            raise ConflictError(
                f"No hay existencias de '{variante.producto.nombre}' "
                f"(Talla {variante.talla.codigo}) en ninguna boutique.",
                code="STOCK_INSUFICIENTE",
            )
        return inventario.id_sucursal

    @staticmethod
    def _validar_stock(
        db: Session,
        variante,
        id_sucursal: int,
        cantidad_solicitada: int,
        nombre_sucursal: Optional[str] = None,
    ) -> None:
        """Comprueba que la boutique puede servir la cantidad pedida."""
        inventario = CarritoRepositorio.obtener_inventario(
            db, variante.id_variante, id_sucursal, cantidad_solicitada
        )
        disponible = inventario.cantidad_disponible if inventario else 0

        if disponible < cantidad_solicitada:
            if nombre_sucursal is None:
                sucursal = CarritoRepositorio.obtener_sucursal_activa(db, id_sucursal)
                nombre_sucursal = sucursal.nombre if sucursal else f"boutique #{id_sucursal}"
            raise ConflictError(
                f"No hay existencias suficientes de '{variante.producto.nombre}' "
                f"(Talla {variante.talla.codigo}) en {nombre_sucursal}. "
                f"Disponibles: {disponible}, solicitadas: {cantidad_solicitada}.",
                code="STOCK_INSUFICIENTE",
            )

    # ------------------------------------------------------------------
    # Construcción del contrato de salida
    # ------------------------------------------------------------------

    @staticmethod
    def calcular_lineas(
        db: Session, lineas: List[CarritoDetalleORM]
    ) -> Tuple[List[CarritoItemOut], Decimal, Decimal]:
        """Convierte las líneas del carrito en ítems de salida y acumula subtotal y descuento.

        Devuelve `(items, subtotal_lista, descuento_total)`, donde `subtotal_lista` agrega los
        precios SIN descuento, de modo que siempre se cumpla `total = subtotal - descuento`,
        en coherencia con las columnas `subtotal`/`descuento`/`total` de `ventas`.
        """
        if not lineas:
            return [], Decimal("0.00"), Decimal("0.00")

        ids_productos = [linea.variante.producto.id_producto for linea in lineas]
        promociones = CarritoRepositorio.obtener_promociones_por_producto(db, ids_productos)

        items: List[CarritoItemOut] = []
        subtotal_lista = Decimal("0.00")
        descuento_total = Decimal("0.00")

        for linea in lineas:
            variante = linea.variante
            producto = variante.producto

            precio_lista = redondear(
                Decimal(producto.precio_base) + Decimal(variante.precio_extra or 0)
            )

            porcentaje, nombre_promo = promociones.get(producto.id_producto, (None, None))
            if porcentaje:
                precio_unitario = redondear(
                    precio_lista * (Decimal("100") - Decimal(porcentaje)) / Decimal("100")
                )
            else:
                precio_unitario = precio_lista

            ahorro_linea = redondear((precio_lista - precio_unitario) * linea.cantidad)
            bruto_linea = redondear(precio_lista * linea.cantidad)

            subtotal_lista += bruto_linea
            descuento_total += ahorro_linea

            inventario = CarritoRepositorio.obtener_inventario(
                db, linea.id_variante, linea.id_sucursal, linea.cantidad
            )
            disponible = inventario.cantidad_disponible if inventario else 0

            items.append(
                CarritoItemOut(
                    id_carrito_detalle=linea.id_carrito_detalle,
                    id_variante=variante.id_variante,
                    id_producto=producto.id_producto,
                    nombre_producto=producto.nombre,
                    linea_confeccion=getattr(producto, "linea_confeccion", None),
                    sku=variante.sku,
                    talla_codigo=variante.talla.codigo if variante.talla else "-",
                    color_nombre=variante.color.nombre if variante.color else "-",
                    color_hex=variante.color.codigo_hex if variante.color else None,
                    imagen_url=producto.imagen_url,
                    precio_lista=precio_lista,
                    precio_unitario=precio_unitario,
                    descuento_linea=ahorro_linea,
                    motivo_descuento=nombre_promo,
                    cantidad=linea.cantidad,
                    id_sucursal=linea.id_sucursal,
                    nombre_sucursal=linea.sucursal.nombre if linea.sucursal else "Boutique",
                    stock_disponible=disponible,
                    # El tope del botón '+' nunca baja de lo ya reservado en la propia línea.
                    cantidad_maxima=max(disponible, linea.cantidad),
                    subtotal_linea=redondear(precio_unitario * linea.cantidad),
                )
            )

        return items, redondear(subtotal_lista), redondear(descuento_total)

    @staticmethod
    def _construir_salida(db: Session, carrito: CarritoORM) -> CarritoOut:
        """Ensambla el contrato completo de la bolsa a partir de su estado persistido."""
        lineas = CarritoRepositorio.obtener_lineas(db, carrito.id_carrito)
        items, subtotal, descuento = CarritoServicio.calcular_lineas(db, lineas)

        total = redondear(subtotal - descuento)
        resumen = CarritoResumenOut(
            total_prendas=sum(item.cantidad for item in items),
            total_lineas=len(items),
            subtotal=subtotal,
            descuento=descuento,
            total=total,
            iva_incluido=calcular_iva_incluido(total),
        )

        # Ventana informativa: la más antigua de las líneas marca el fin de la cortesía.
        # No retiene existencias; la garantía firme se obtiene al tramitar el pedido.
        expira_en = None
        if lineas:
            mas_antigua = min(linea.agregado_en for linea in lineas)
            expira_en = mas_antigua + timedelta(minutes=MINUTOS_RETENCION_VENTA)

        agrupadas: Dict[int, SucursalExpedicionOut] = {}
        for item in items:
            if item.id_sucursal not in agrupadas:
                agrupadas[item.id_sucursal] = SucursalExpedicionOut(
                    id_sucursal=item.id_sucursal,
                    nombre=item.nombre_sucursal,
                    total_lineas=0,
                )
            agrupadas[item.id_sucursal].total_lineas += 1

        return CarritoOut(
            id_carrito=carrito.id_carrito,
            items=items,
            resumen=resumen,
            expira_en=expira_en,
            sucursales_expedicion=list(agrupadas.values()),
        )
