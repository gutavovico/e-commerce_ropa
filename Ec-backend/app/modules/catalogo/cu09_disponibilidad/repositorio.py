"""Repositorio de acceso a datos para CU09: Disponibilidad por Sucursal."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.catalogo.modelos import (
    InventarioSucursalORM,
    ProductoORM,
    SucursalORM,
    VarianteProductoORM,
)


class DisponibilidadRepositorio:
    """Acceso a datos de sucursales físicas e inventario en tiempo real."""

    @staticmethod
    def obtener_producto_con_variantes(db: Session, id_producto: int) -> Optional[ProductoORM]:
        """Verifica la existencia del producto y precarga sus variantes."""
        stmt = (
            select(ProductoORM)
            .options(selectinload(ProductoORM.variantes))
            .where(ProductoORM.id_producto == id_producto, ProductoORM.activo.is_(True))
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def obtener_sucursales_activas(db: Session) -> List[SucursalORM]:
        """Obtiene todas las boutiques físicas activas con su información geográfica."""
        stmt = (
            select(SucursalORM)
            .options(selectinload(SucursalORM.ciudad))
            .where(SucursalORM.activa.is_(True))
            .order_by(SucursalORM.id_sucursal.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener_inventario_variante(
        db: Session, id_variante: int
    ) -> List[InventarioSucursalORM]:
        """Obtiene las existencias físicas de una variante específica en todas las sucursales."""
        stmt = (
            select(InventarioSucursalORM)
            .where(InventarioSucursalORM.id_variante == id_variante)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener_inventario_producto(
        db: Session, id_producto: int
    ) -> List[InventarioSucursalORM]:
        """Obtiene las existencias físicas de todas las variantes de un producto."""
        stmt = (
            select(InventarioSucursalORM)
            .join(VarianteProductoORM, VarianteProductoORM.id_variante == InventarioSucursalORM.id_variante)
            .where(VarianteProductoORM.id_producto == id_producto)
        )
        return list(db.execute(stmt).scalars().all())
