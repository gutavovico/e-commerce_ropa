"""Repositorio de acceso a datos para CU11 (Bolsa de Compra) y CU15 (Tramitación).

Concentra las consultas de carrito, inventario y promociones. Ninguna función de este módulo
abre ni cierra transacciones: la unidad de trabajo la gobierna el servicio.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import (
    InventarioSucursalORM,
    PromocionORM,
    PromocionProductoORM,
    SucursalORM,
    VarianteProductoORM,
)
from modules.compras_pagos.modelos import CarritoDetalleORM, CarritoORM


class CarritoRepositorio:
    """Acceso a datos de la bolsa de compra y del inventario que la respalda."""

    # ------------------------------------------------------------------
    # Cliente y carrito
    # ------------------------------------------------------------------

    @staticmethod
    def asegurar_cliente(db: Session, usuario: UsuarioORM) -> ClienteORM:
        """Obtiene la ficha de cliente del usuario autenticado, creándola si no existe."""
        stmt = select(ClienteORM).where(ClienteORM.id_cliente == usuario.id_usuario)
        cliente = db.execute(stmt).scalar_one_or_none()
        if not cliente:
            cliente = ClienteORM(
                id_cliente=usuario.id_usuario,
                talla_preferida="38",
                acepta_marketing=True,
            )
            db.add(cliente)
            db.flush()
        return cliente

    @staticmethod
    def obtener_o_crear_carrito(db: Session, id_cliente: int) -> CarritoORM:
        """Devuelve el carrito activo del cliente, creándolo vacío la primera vez.

        Si por cualquier motivo existiese más de un carrito para el mismo cliente, se toma el
        más reciente en lugar de fallar: `carritos` no declara unicidad por cliente en la base.
        """
        stmt = (
            select(CarritoORM)
            .where(CarritoORM.id_cliente == id_cliente)
            .order_by(CarritoORM.id_carrito.desc())
            .limit(1)
        )
        carrito = db.execute(stmt).scalars().first()
        if not carrito:
            carrito = CarritoORM(id_cliente=id_cliente)
            db.add(carrito)
            db.flush()
        return carrito

    @staticmethod
    def obtener_lineas(db: Session, id_carrito: int) -> List[CarritoDetalleORM]:
        """Carga las líneas del carrito con producto, talla, color y sucursal resueltos."""
        stmt = (
            select(CarritoDetalleORM)
            .options(
                selectinload(CarritoDetalleORM.variante).selectinload(
                    VarianteProductoORM.producto
                ),
                selectinload(CarritoDetalleORM.variante).selectinload(VarianteProductoORM.talla),
                selectinload(CarritoDetalleORM.variante).selectinload(VarianteProductoORM.color),
                selectinload(CarritoDetalleORM.sucursal),
            )
            .where(CarritoDetalleORM.id_carrito == id_carrito)
            .order_by(CarritoDetalleORM.agregado_en.asc(), CarritoDetalleORM.id_carrito_detalle.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener_linea(db: Session, id_carrito_detalle: int) -> Optional[CarritoDetalleORM]:
        """Obtiene una línea concreta con su carrito asociado, para validar pertenencia."""
        stmt = (
            select(CarritoDetalleORM)
            .options(
                selectinload(CarritoDetalleORM.carrito),
                selectinload(CarritoDetalleORM.variante).selectinload(
                    VarianteProductoORM.producto
                ),
                selectinload(CarritoDetalleORM.variante).selectinload(VarianteProductoORM.talla),
            )
            .where(CarritoDetalleORM.id_carrito_detalle == id_carrito_detalle)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def buscar_linea_equivalente(
        db: Session, id_carrito: int, id_variante: int, id_sucursal: int
    ) -> Optional[CarritoDetalleORM]:
        """Localiza la línea de la misma variante y sucursal, para consolidar cantidades."""
        stmt = select(CarritoDetalleORM).where(
            CarritoDetalleORM.id_carrito == id_carrito,
            CarritoDetalleORM.id_variante == id_variante,
            CarritoDetalleORM.id_sucursal == id_sucursal,
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def vaciar_carrito(db: Session, id_carrito: int) -> int:
        """Elimina todas las líneas del carrito. Devuelve cuántas se purgaron."""
        lineas = CarritoRepositorio.obtener_lineas(db, id_carrito)
        for linea in lineas:
            db.delete(linea)
        db.flush()
        return len(lineas)

    # ------------------------------------------------------------------
    # Catálogo e inventario
    # ------------------------------------------------------------------

    @staticmethod
    def obtener_variante(db: Session, id_variante: int) -> Optional[VarianteProductoORM]:
        """Obtiene la variante con producto, talla y color resueltos."""
        stmt = (
            select(VarianteProductoORM)
            .options(
                selectinload(VarianteProductoORM.producto),
                selectinload(VarianteProductoORM.talla),
                selectinload(VarianteProductoORM.color),
            )
            .where(VarianteProductoORM.id_variante == id_variante)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def obtener_sucursal_activa(db: Session, id_sucursal: int) -> Optional[SucursalORM]:
        """Obtiene una boutique activa por identificador."""
        stmt = select(SucursalORM).where(
            SucursalORM.id_sucursal == id_sucursal,
            SucursalORM.activa.is_(True),
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def obtener_inventario(
        db: Session,
        id_variante: int,
        id_sucursal: int,
        cantidad: int = 1,
        bloquear: bool = False,
    ) -> Optional[InventarioSucursalORM]:
        """Resuelve la fila de inventario de una variante en una boutique.

        La clave única real de `inventario_sucursal` es (id_variante, id_sucursal, id_temporada),
        de modo que una misma variante puede tener existencias repartidas en varias temporadas
        dentro de la misma boutique. Usar `scalar_one_or_none()` sobre el par (variante, sucursal)
        lanzaría `MultipleResultsFound` —un HTTP 500— en cuanto existiese stock de una segunda
        temporada; es el mismo defecto ya corregido en CU12.

        Se elige de forma determinista la fila de la temporada más reciente que cubra la cantidad
        solicitada y, si ninguna la cubre, la de mayor stock, para que el mensaje de existencias
        insuficientes informe la disponibilidad real más favorable.

        `bloquear=True` aplica `SELECT ... FOR UPDATE`; se usa exclusivamente en el checkout,
        donde la lectura y la escritura deben ser atómicas frente a compras simultáneas.
        """
        base = select(InventarioSucursalORM).where(
            InventarioSucursalORM.id_variante == id_variante,
            InventarioSucursalORM.id_sucursal == id_sucursal,
        )

        stmt = (
            base.where(InventarioSucursalORM.cantidad_disponible >= cantidad)
            .order_by(InventarioSucursalORM.id_temporada.desc())
            .limit(1)
        )
        if bloquear:
            stmt = stmt.with_for_update()

        inventario = db.execute(stmt).scalars().first()
        if inventario:
            return inventario

        stmt_sin_stock = (
            base.order_by(
                InventarioSucursalORM.cantidad_disponible.desc(),
                InventarioSucursalORM.id_temporada.desc(),
            )
            .limit(1)
        )
        if bloquear:
            stmt_sin_stock = stmt_sin_stock.with_for_update()

        return db.execute(stmt_sin_stock).scalars().first()

    @staticmethod
    def elegir_sucursal_con_stock(
        db: Session, id_variante: int, cantidad: int = 1
    ) -> Optional[InventarioSucursalORM]:
        """Selecciona la boutique activa con mayor disponibilidad para una variante.

        Se usa cuando el cliente añade una prenda sin indicar boutique de expedición.
        """
        stmt = (
            select(InventarioSucursalORM)
            .join(SucursalORM, SucursalORM.id_sucursal == InventarioSucursalORM.id_sucursal)
            .where(
                InventarioSucursalORM.id_variante == id_variante,
                InventarioSucursalORM.cantidad_disponible >= cantidad,
                SucursalORM.activa.is_(True),
            )
            .order_by(
                InventarioSucursalORM.cantidad_disponible.desc(),
                InventarioSucursalORM.id_temporada.desc(),
            )
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    # ------------------------------------------------------------------
    # Promociones
    # ------------------------------------------------------------------

    @staticmethod
    def obtener_promociones_por_producto(
        db: Session, ids_productos: List[int]
    ) -> Dict[int, Tuple[Decimal, str]]:
        """Devuelve {id_producto: (porcentaje_descuento, nombre)} de las promociones vigentes.

        Replica la regla de CU05: ante varias promociones aplicables a un mismo producto, gana
        la de mayor descuento.
        """
        if not ids_productos:
            return {}

        hoy = date.today()
        stmt = (
            select(
                PromocionProductoORM.id_producto,
                PromocionORM.porcentaje_descuento,
                PromocionORM.nombre,
            )
            .join(PromocionORM, PromocionORM.id_promocion == PromocionProductoORM.id_promocion)
            .where(
                PromocionProductoORM.id_producto.in_(ids_productos),
                PromocionORM.activa == True,  # noqa: E712 - columna booleana de PostgreSQL
                PromocionORM.fecha_inicio <= hoy,
                PromocionORM.fecha_fin >= hoy,
                PromocionORM.porcentaje_descuento.is_not(None),
                PromocionORM.porcentaje_descuento > 0,
            )
        )

        mapa: Dict[int, Tuple[Decimal, str]] = {}
        for id_producto, porcentaje, nombre in db.execute(stmt).all():
            if id_producto not in mapa or porcentaje > mapa[id_producto][0]:
                mapa[id_producto] = (porcentaje, nombre)
        return mapa

    @staticmethod
    def obtener_promocion_por_cupon(db: Session, codigo: str) -> Optional[PromocionORM]:
        """Busca una promoción por su código de cupón, sin distinguir mayúsculas."""
        stmt = select(PromocionORM).where(
            PromocionORM.codigo_cupon.isnot(None),
            PromocionORM.codigo_cupon.ilike(codigo.strip()),
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def consumir_uso_cupon(db: Session, promocion: PromocionORM) -> bool:
        """Incrementa `usos_actuales` de forma atómica respetando `limite_usos`.

        Devuelve False si el cupón ya agotó sus usos. Se emplea un UPDATE condicional en vez de
        leer-comprobar-escribir para que dos checkouts simultáneos no puedan superar el límite.
        """
        from sqlalchemy import or_, update

        stmt = (
            update(PromocionORM)
            .where(
                PromocionORM.id_promocion == promocion.id_promocion,
                or_(
                    PromocionORM.limite_usos.is_(None),
                    PromocionORM.usos_actuales < PromocionORM.limite_usos,
                ),
            )
            .values(usos_actuales=PromocionORM.usos_actuales + 1)
        )
        resultado = db.execute(stmt)
        return resultado.rowcount == 1

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def ahora_utc() -> datetime:
        """Instante actual en UTC, centralizado para poder sustituirlo en pruebas."""
        return datetime.now(timezone.utc)
