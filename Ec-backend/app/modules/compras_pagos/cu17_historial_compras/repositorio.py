"""Repositorio de acceso a datos para CU17: Consultar historial de compras."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.catalogo.modelos import VarianteProductoORM
from modules.compras_pagos.modelos import VentaDetalleORM, VentaORM


class RepositorioHistorialCompras:
    """Consultas de solo lectura sobre las ventas del cliente."""

    @staticmethod
    def listar_ventas_cliente(db: Session, id_cliente: int) -> Sequence[VentaORM]:
        """Retorna todas las ventas del cliente ordenadas de la más reciente a la más antigua."""
        stmt = (
            select(VentaORM)
            .options(
                selectinload(VentaORM.sucursal),
                selectinload(VentaORM.sucursal_retiro),
                selectinload(VentaORM.promocion),
                selectinload(VentaORM.pagos),
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
            )
            .where(VentaORM.id_cliente == id_cliente)
            .order_by(VentaORM.fecha_venta.desc(), VentaORM.id_venta.desc())
        )
        return db.execute(stmt).scalars().all()

