"""Repositorio de acceso a datos para CU07: Detalle de Producto y CU08: Variantes."""

from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.catalogo.modelos import (
    ProductoORM,
    PromocionORM,
    PromocionProductoORM,
    VarianteProductoORM,
)


class ProductoDetalleRepositorio:
    """Acceso a datos optimizado para la ficha de detalle de producto de alta costura."""

    @staticmethod
    def obtener_producto_con_variantes(db: Session, id_producto: int) -> Optional[ProductoORM]:
        """Obtiene un producto activo con todas sus variantes, tallas, colores e inventario."""
        stmt = (
            select(ProductoORM)
            .options(
                selectinload(ProductoORM.categoria),
                selectinload(ProductoORM.coleccion),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.talla),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.color),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.inventarios),
            )
            .where(ProductoORM.id_producto == id_producto, ProductoORM.activo.is_(True))
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def obtener_promocion_activa(db: Session, id_producto: int) -> Optional[PromocionORM]:
        """Consulta si el producto cuenta con una promoción vigente en fecha actual."""
        hoy = date.today()
        stmt = (
            select(PromocionORM)
            .join(PromocionProductoORM, PromocionProductoORM.id_promocion == PromocionORM.id_promocion)
            .where(
                PromocionProductoORM.id_producto == id_producto,
                PromocionORM.activa.is_(True),
                PromocionORM.fecha_inicio <= hoy,
                PromocionORM.fecha_fin >= hoy,
            )
            .order_by(PromocionORM.porcentaje_descuento.desc())
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def obtener_prendas_complementarias(
        db: Session, id_producto_actual: int, limite: int = 3
    ) -> List[ProductoORM]:
        """Obtiene hasta `limite` prendas activas distintas para la sección 'Completa el look atelier'."""
        stmt = (
            select(ProductoORM)
            .options(selectinload(ProductoORM.categoria))
            .where(
                ProductoORM.id_producto != id_producto_actual,
                ProductoORM.activo.is_(True),
            )
            .order_by(ProductoORM.id_producto.desc())
            .limit(limite)
        )
        return list(db.execute(stmt).scalars().all())
