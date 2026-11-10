"""Acceso a datos de P2-CU18. La RLS limita todo a la empresa de la sesión."""

from typing import Dict, Iterable, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from modules.catalogo.modelos import InventarioSucursalORM, SucursalORM, TemporadaORM, VarianteProductoORM
from modules.compras_pagos.modelos import CambioPrendaDetalleORM, CambioPrendaORM, VentaDetalleORM, VentaORM


class CambioPrendaRepositorio:
    @staticmethod
    def venta_por_comprobante(db: Session, comprobante: str) -> Optional[VentaORM]:
        stmt = select(VentaORM).where(func.upper(VentaORM.numero_comprobante) == comprobante.strip().upper())
        return db.execute(stmt).scalars().first()

    @staticmethod
    def venta(db: Session, id_venta: int, bloquear: bool = False) -> Optional[VentaORM]:
        """Con `bloquear`, `FOR UPDATE` de la venta: serializa dos cambios sobre la misma (AC-11)."""
        stmt = select(VentaORM).where(VentaORM.id_venta == id_venta)
        if bloquear:
            stmt = stmt.with_for_update(of=VentaORM)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def lineas_de_venta(db: Session, id_venta: int) -> List[VentaDetalleORM]:
        stmt = (
            select(VentaDetalleORM)
            .options(
                selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.producto),
                selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.talla),
                selectinload(VentaDetalleORM.variante).selectinload(VarianteProductoORM.color),
            )
            .where(VentaDetalleORM.id_venta == id_venta)
            .order_by(VentaDetalleORM.id_venta_detalle)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def ya_cambiadas(db: Session, ids_detalle: Iterable[int]) -> Dict[int, int]:
        """Unidades de cada línea devueltas en cambios anteriores (RN31)."""
        ids = list(ids_detalle)
        if not ids:
            return {}
        stmt = (
            select(CambioPrendaDetalleORM.id_venta_detalle, func.sum(CambioPrendaDetalleORM.cantidad))
            .where(
                CambioPrendaDetalleORM.tipo == "devuelta",
                CambioPrendaDetalleORM.id_venta_detalle.in_(ids),
            )
            .group_by(CambioPrendaDetalleORM.id_venta_detalle)
        )
        return {int(i): int(c) for i, c in db.execute(stmt).all()}

    @staticmethod
    def inventario(db: Session, id_variante: int, id_sucursal: int, minimo: int) -> Optional[InventarioSucursalORM]:
        """Fila de la variante en la sucursal con `FOR UPDATE`: la de la temporada más reciente que
        cubra `minimo`; si ninguna lo cubre, la de más existencias."""
        base = select(InventarioSucursalORM).where(
            InventarioSucursalORM.id_variante == id_variante,
            InventarioSucursalORM.id_sucursal == id_sucursal,
        )
        fila = db.execute(
            base.where(InventarioSucursalORM.cantidad_disponible >= minimo)
            .order_by(InventarioSucursalORM.id_temporada.desc())
            .limit(1)
            .with_for_update()
        ).scalars().first()
        if fila is not None:
            return fila
        return db.execute(
            base.order_by(InventarioSucursalORM.cantidad_disponible.desc(), InventarioSucursalORM.id_temporada.desc())
            .limit(1)
            .with_for_update()
        ).scalars().first()

    @staticmethod
    def temporada_para(db: Session, id_variante: int) -> Optional[int]:
        """Temporada para crear la fila de una prenda devuelta en una sucursal que no la tenía: la más
        reciente en la que la variante tiene inventario; si no, la última temporada de la empresa."""
        temporada = db.execute(
            select(func.max(InventarioSucursalORM.id_temporada)).where(InventarioSucursalORM.id_variante == id_variante)
        ).scalar()
        if temporada is not None:
            return int(temporada)
        ultima = db.execute(select(func.max(TemporadaORM.id_temporada))).scalar()
        return int(ultima) if ultima is not None else None

    @staticmethod
    def siguiente_comprobante(db: Session, id_tenant: Optional[int], anio: int) -> str:
        """`CAM-AAAA-NNNNN` correlativo por empresa, bajo un bloqueo de transacción por empresa."""
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('fashionstore.cambio.comprobante'), :t)"),
            {"t": int(id_tenant or 0)},
        )
        prefijo = f"CAM-{anio}-"
        ultimo = db.execute(
            select(func.max(CambioPrendaORM.numero_comprobante)).where(
                CambioPrendaORM.numero_comprobante.like(f"{prefijo}%")
            )
        ).scalar()
        siguiente = int(ultimo.rsplit("-", 1)[1]) + 1 if ultimo else 1
        return f"{prefijo}{siguiente:05d}"

    @staticmethod
    def sucursal(db: Session, id_sucursal: int) -> Optional[SucursalORM]:
        return db.get(SucursalORM, id_sucursal)

    @staticmethod
    def cambio(db: Session, id_cambio: int) -> Optional[CambioPrendaORM]:
        return db.get(CambioPrendaORM, id_cambio)

    @staticmethod
    def cambios(db: Session, id_sucursal: int, desde) -> List[CambioPrendaORM]:
        stmt = select(CambioPrendaORM).where(CambioPrendaORM.id_sucursal == id_sucursal)
        if desde is not None:
            stmt = stmt.where(CambioPrendaORM.creado_en >= desde)
        return list(db.execute(stmt.order_by(CambioPrendaORM.creado_en.desc()).limit(200)).scalars().all())
