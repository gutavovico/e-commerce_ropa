"""Servicio de dominio para CU17: Consultar historial de compras."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu11_gestionar_carrito.servicio import redondear
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.compras_pagos.cu17_historial_compras.esquemas import (
    HistorialComprasOut,
    ItemHistorialCompraOut,
    PedidoHistorialOut,
)
from modules.compras_pagos.cu17_historial_compras.repositorio import (
    RepositorioHistorialCompras,
)
from modules.compras_pagos.modelos import PagoORM, VentaORM


class ServicioHistorialCompras:
    """Construye el historial consolidado de compras del cliente autenticado."""

    @staticmethod
    def obtener_historial_cliente(
        db: Session, usuario: UsuarioORM
    ) -> HistorialComprasOut:
        """Retorna las compras del cliente, expirando perezosamente órdenes pendientes vencidas."""
        ventas = RepositorioHistorialCompras.listar_ventas_cliente(db, usuario.id_usuario)
        ahora = CarritoRepositorio.ahora_utc()

        pedidos_out: List[PedidoHistorialOut] = []
        for venta in ventas:
            if venta.estado == "pendiente":
                expira_en = PagoServicio._calcular_expiracion(db, venta)
                if ahora > expira_en:
                    CheckoutServicio.liberar_existencias_de_venta(db, venta, usuario)

            pedidos_out.append(ServicioHistorialCompras._mapear_venta(venta))

        pedidos_completados = sum(1 for p in pedidos_out if p.estado == "pagada")
        return HistorialComprasOut(
            total_pedidos=len(pedidos_out),
            pedidos_completados=pedidos_completados,
            pedidos=pedidos_out,
        )

    @staticmethod
    def _seleccionar_pago_relevante(pagos: List[PagoORM]) -> Optional[PagoORM]:
        """Prioriza el pago confirmado; si no existe, devuelve el intento más reciente."""
        if not pagos:
            return None
        confirmados = [p for p in pagos if p.estado == "confirmado"]
        if confirmados:
            return confirmados[-1]
        return pagos[-1]

    @staticmethod
    def _mapear_venta(venta: VentaORM) -> PedidoHistorialOut:
        """Transforma una entidad `VentaORM` en su representación `PedidoHistorialOut`."""
        nombre_sucursal_cabecera = venta.sucursal.nombre if venta.sucursal else None
        pago = ServicioHistorialCompras._seleccionar_pago_relevante(list(venta.pagos or []))

        items: List[ItemHistorialCompraOut] = []
        for d in venta.detalles or []:
            variante = d.variante
            producto = variante.producto if variante else None
            talla = variante.talla if variante else None
            color = variante.color if variante else None
            subtotal_linea = (
                Decimal(d.subtotal_linea)
                if d.subtotal_linea is not None
                else redondear(Decimal(d.precio_unitario) * d.cantidad)
            )
            nombre_sucursal_linea = (
                d.sucursal.nombre if d.sucursal else nombre_sucursal_cabecera
            )

            items.append(
                ItemHistorialCompraOut(
                    id_venta_detalle=d.id_venta_detalle,
                    id_producto=producto.id_producto if producto else 0,
                    id_variante=d.id_variante,
                    sku=variante.sku if variante else "",
                    nombre_producto=producto.nombre if producto else "Prenda FashionStore",
                    imagen_url=producto.imagen_url if producto else None,
                    talla=talla.codigo if talla else "-",
                    color=color.nombre if color else "-",
                    color_hex=color.codigo_hex if color else None,
                    cantidad=d.cantidad,
                    precio_unitario=Decimal(d.precio_unitario),
                    subtotal_linea=subtotal_linea,
                    nombre_sucursal=nombre_sucursal_linea,
                )
            )

        codigo_promocion = None
        if venta.promocion:
            codigo_promocion = venta.promocion.codigo_cupon or venta.promocion.nombre

        return PedidoHistorialOut(
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            fecha_venta=venta.fecha_venta,
            tipo_venta=venta.tipo_venta,
            estado=venta.estado,
            tipo_entrega=venta.tipo_entrega,
            nombre_sucursal=nombre_sucursal_cabecera,
            nombre_sucursal_retiro=(
                venta.sucursal_retiro.nombre if venta.sucursal_retiro else None
            ),
            direccion_envio=venta.direccion_envio,
            codigo_promocion=codigo_promocion,
            subtotal=Decimal(venta.subtotal),
            descuento=Decimal(venta.descuento),
            total=Decimal(venta.total),
            metodo_pago=pago.metodo_pago if pago else None,
            referencia_pasarela=pago.referencia_pasarela if pago else None,
            items=items,
        )

