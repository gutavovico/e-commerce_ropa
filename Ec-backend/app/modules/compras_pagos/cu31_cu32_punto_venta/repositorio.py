"""Acceso a datos del punto de venta presencial (CU31-CU32). Sin lógica de negocio."""

from datetime import datetime
from typing import Dict, Iterable, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import CategoriaORM, InventarioSucursalORM, ProductoORM, VarianteProductoORM
from modules.comercial.cu27_promociones.modelos import PromocionORM
from modules.comercial.cu28_ventas_reservas.modelos import EmpleadoORM
from modules.compras_pagos.modelos import PagoORM, VentaDetalleORM, VentaORM
from modules.reservas.modelos import MovimientoInventarioORM


class PuntoVentaRepositorio:
    # ------------------------------------------------------------------
    # Catálogo e inventario
    # ------------------------------------------------------------------

    @staticmethod
    def variante_por_sku(db: Session, sku: str) -> Optional[VarianteProductoORM]:
        """Variante activa de un producto activo por SKU exacto (sin distinguir mayúsculas)."""
        stmt = (
            select(VarianteProductoORM)
            .join(ProductoORM, ProductoORM.id_producto == VarianteProductoORM.id_producto)
            .where(
                func.lower(VarianteProductoORM.sku) == sku.strip().lower(),
                VarianteProductoORM.activo.is_(True),
                ProductoORM.activo.is_(True),
            )
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def buscar_variantes(db: Session, texto: str, limite: int = 60) -> List[VarianteProductoORM]:
        """Variantes activas cuyo producto, categoría o SKU contienen el texto (sin distinguir mayúsculas)."""
        patron = f"%{texto.strip()}%"
        stmt = (
            select(VarianteProductoORM)
            .join(ProductoORM, ProductoORM.id_producto == VarianteProductoORM.id_producto)
            .join(CategoriaORM, CategoriaORM.id_categoria == ProductoORM.id_categoria)
            .where(
                VarianteProductoORM.activo.is_(True),
                ProductoORM.activo.is_(True),
                or_(
                    ProductoORM.nombre.ilike(patron),
                    CategoriaORM.nombre.ilike(patron),
                    VarianteProductoORM.sku.ilike(patron),
                ),
            )
            .order_by(ProductoORM.nombre, VarianteProductoORM.sku)
            .limit(limite)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def disponibles_en_sucursal(db: Session, ids_variantes: Iterable[int], id_sucursal: int) -> Dict[int, int]:
        """Stock disponible por variante en la sucursal (suma de temporadas), en una sola consulta."""
        ids = list(set(ids_variantes))
        if not ids:
            return {}
        stmt = (
            select(InventarioSucursalORM.id_variante, func.sum(InventarioSucursalORM.cantidad_disponible))
            .where(InventarioSucursalORM.id_variante.in_(ids), InventarioSucursalORM.id_sucursal == id_sucursal)
            .group_by(InventarioSucursalORM.id_variante)
        )
        return {fila[0]: int(fila[1] or 0) for fila in db.execute(stmt).all()}

    @staticmethod
    def variantes_por_ids(db: Session, ids: Iterable[int]) -> Dict[int, VarianteProductoORM]:
        ids = list(set(ids))
        if not ids:
            return {}
        stmt = select(VarianteProductoORM).where(VarianteProductoORM.id_variante.in_(ids))
        return {v.id_variante: v for v in db.execute(stmt).scalars().all()}

    @staticmethod
    def disponible_en_sucursal(db: Session, id_variante: int, id_sucursal: int) -> int:
        stmt = select(func.coalesce(func.sum(InventarioSucursalORM.cantidad_disponible), 0)).where(
            InventarioSucursalORM.id_variante == id_variante,
            InventarioSucursalORM.id_sucursal == id_sucursal,
        )
        return int(db.execute(stmt).scalar_one())

    @staticmethod
    def inventario_por_id(db: Session, id_inventario: int, bloquear: bool = True) -> Optional[InventarioSucursalORM]:
        stmt = select(InventarioSucursalORM).where(InventarioSucursalORM.id_inventario == id_inventario)
        if bloquear:
            stmt = stmt.with_for_update(of=InventarioSucursalORM)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def buscar_retencion_venta(db: Session, id_venta: int, id_variante: int) -> Optional[MovimientoInventarioORM]:
        """Movimiento `reserva` (retención) que el punto de venta escribió para esta línea.

        Igual que CU13 con las reservas: es la única forma fiable de saber de qué fila (temporada)
        salieron las unidades.
        """
        stmt = (
            select(MovimientoInventarioORM)
            .join(
                InventarioSucursalORM,
                InventarioSucursalORM.id_inventario == MovimientoInventarioORM.id_inventario,
            )
            .where(
                MovimientoInventarioORM.referencia_documento == f"VENTA-{id_venta}",
                MovimientoInventarioORM.tipo_movimiento == "reserva",
                InventarioSucursalORM.id_variante == id_variante,
            )
            .order_by(MovimientoInventarioORM.id_movimiento.desc())
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    # ------------------------------------------------------------------
    # Personas
    # ------------------------------------------------------------------

    @staticmethod
    def buscar_clientes(db: Session, texto: str, limite: int = 20) -> List[UsuarioORM]:
        """Clientes activos cuyo nombre, apellidos, nombre completo o correo contienen el texto."""
        patron = f"%{texto.strip()}%"
        nombre_completo = func.concat(UsuarioORM.nombres, " ", UsuarioORM.apellidos)
        stmt = (
            select(UsuarioORM)
            .join(ClienteORM, ClienteORM.id_cliente == UsuarioORM.id_usuario)
            .where(
                UsuarioORM.activo.is_(True),
                or_(
                    UsuarioORM.email.ilike(patron),
                    UsuarioORM.nombres.ilike(patron),
                    UsuarioORM.apellidos.ilike(patron),
                    nombre_completo.ilike(patron),
                ),
            )
            .order_by(UsuarioORM.nombres, UsuarioORM.apellidos)
            .limit(limite)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def usuario_de_cliente(db: Session, id_cliente: int) -> Optional[UsuarioORM]:
        stmt = (
            select(UsuarioORM)
            .join(ClienteORM, ClienteORM.id_cliente == UsuarioORM.id_usuario)
            .where(UsuarioORM.id_usuario == id_cliente)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def es_empleado(db: Session, id_usuario: int) -> bool:
        return db.get(EmpleadoORM, id_usuario) is not None

    @staticmethod
    def usuario_por_id(db: Session, id_usuario: int) -> Optional[UsuarioORM]:
        return db.get(UsuarioORM, id_usuario)

    # ------------------------------------------------------------------
    # Ventas
    # ------------------------------------------------------------------

    @staticmethod
    def _opciones_venta():
        detalle_variante = selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante)
        return (
            detalle_variante.selectinload(VarianteProductoORM.producto),
            selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.talla),
            selectinload(VentaORM.detalles).selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.color),
            selectinload(VentaORM.pagos),
        )

    @staticmethod
    def cargar_venta(db: Session, id_venta: int, bloquear: bool = False) -> Optional[VentaORM]:
        """Venta con líneas y pagos. `selectinload` usa consultas aparte, compatibles con `FOR UPDATE`."""
        stmt = select(VentaORM).options(*PuntoVentaRepositorio._opciones_venta()).where(VentaORM.id_venta == id_venta)
        if bloquear:
            stmt = stmt.with_for_update(of=VentaORM)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def venta_pendiente_de_reserva(db: Session, id_reserva: int) -> Optional[VentaORM]:
        stmt = select(VentaORM).where(
            VentaORM.id_reserva == id_reserva,
            VentaORM.tipo_venta == "presencial",
            VentaORM.estado == "pendiente",
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def listar_ventas(
        db: Session, id_sucursal: int, estado: Optional[str], desde: Optional[datetime]
    ) -> List[VentaORM]:
        stmt = (
            select(VentaORM)
            .options(*PuntoVentaRepositorio._opciones_venta())
            .where(VentaORM.tipo_venta == "presencial", VentaORM.id_sucursal == id_sucursal)
            .order_by(VentaORM.fecha_venta.desc())
        )
        if estado:
            stmt = stmt.where(VentaORM.estado == estado)
        if desde:
            stmt = stmt.where(VentaORM.fecha_venta >= desde)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def cupones_vigentes(db: Session, texto: Optional[str], ahora: datetime, limite: int = 50) -> List[PromocionORM]:
        """Promociones con código de cupón, activas, en fecha y con usos disponibles.
        Con texto, filtra por código o por nombre de la promoción."""
        stmt = (
            select(PromocionORM)
            .where(
                PromocionORM.codigo_cupon.isnot(None),
                func.trim(PromocionORM.codigo_cupon) != "",
                PromocionORM.estado_activo.is_(True),
                PromocionORM.fecha_inicio <= ahora,
                PromocionORM.fecha_fin >= ahora,
                or_(PromocionORM.limite_usos.is_(None), PromocionORM.usos_actuales < PromocionORM.limite_usos),
            )
            .order_by(PromocionORM.codigo_cupon)
            .limit(limite)
        )
        if texto and texto.strip():
            patron = f"%{texto.strip()}%"
            stmt = stmt.where(or_(PromocionORM.codigo_cupon.ilike(patron), PromocionORM.nombre.ilike(patron)))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def pedidos_web_efectivo(db: Session, id_sucursal: int) -> List[PagoORM]:
        """Pagos en efectivo pendientes de pedidos web que se recogen en esta boutique (CU16)."""
        stmt = (
            select(PagoORM)
            .join(VentaORM, VentaORM.id_venta == PagoORM.id_venta)
            .where(
                PagoORM.metodo_pago == "efectivo",
                PagoORM.estado == "pendiente",
                VentaORM.estado == "pendiente",
                VentaORM.tipo_venta != "presencial",
                VentaORM.id_sucursal_retiro == id_sucursal,
            )
            .order_by(PagoORM.creado_en.asc())
        )
        return list(db.execute(stmt).scalars().all())
