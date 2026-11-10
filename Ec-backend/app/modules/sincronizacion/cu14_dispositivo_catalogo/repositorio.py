"""Acceso a datos de P2-CU14. Todas las lecturas pasan por la RLS: solo la empresa del portal."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from modules.catalogo.modelos import (
    CategoriaORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    SucursalORM,
    TallaORM,
    VarianteProductoORM,
)
from modules.comercial.cu27_promociones.modelos import PromocionORM, PromocionProductoORM
from modules.sincronizacion.modelos import DispositivoORM, SyncLogORM


class DispositivoRepositorio:
    @staticmethod
    def insertar_si_falta(
        db: Session, identificador: uuid.UUID, id_cliente: int, plataforma: str, codigo_corto: str
    ) -> bool:
        """`INSERT … ON CONFLICT DO NOTHING`: dos registros simultáneos del mismo UUID dan un solo
        dispositivo. Devuelve True si lo creó esta llamada."""
        sentencia = (
            insert(DispositivoORM)
            .values(
                identificador=identificador,
                id_cliente=id_cliente,
                plataforma=plataforma,
                codigo_corto=codigo_corto,
            )
            .on_conflict_do_nothing(constraint="uq_dispositivos_identificador")
            .returning(DispositivoORM.id_dispositivo)
        )
        return db.execute(sentencia).scalar_one_or_none() is not None

    @staticmethod
    def por_identificador(db: Session, identificador: uuid.UUID, bloquear: bool = False) -> Optional[DispositivoORM]:
        stmt = select(DispositivoORM).where(DispositivoORM.identificador == identificador)
        if bloquear:
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def registrar_log(db: Session, **campos) -> SyncLogORM:
        fila = SyncLogORM(**campos)
        db.add(fila)
        db.flush()
        return fila


class CatalogoLocalRepositorio:
    @staticmethod
    def productos_activos(db: Session) -> List[ProductoORM]:
        stmt = (
            select(ProductoORM)
            .options(selectinload(ProductoORM.variantes))
            .where(ProductoORM.activo.is_(True))
            .order_by(ProductoORM.id_producto)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def categorias(db: Session) -> List[CategoriaORM]:
        return list(db.execute(select(CategoriaORM).order_by(CategoriaORM.id_categoria)).scalars().all())

    @staticmethod
    def tallas(db: Session, ids: set[int]) -> List[TallaORM]:
        if not ids:
            return []
        stmt = select(TallaORM).where(TallaORM.id_talla.in_(ids)).order_by(TallaORM.orden, TallaORM.id_talla)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def colores(db: Session, ids: set[int]) -> List[ColorORM]:
        if not ids:
            return []
        stmt = select(ColorORM).where(ColorORM.id_color.in_(ids)).order_by(ColorORM.id_color)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def promociones_vigentes(db: Session, instante: datetime) -> List[PromocionORM]:
        stmt = (
            select(PromocionORM)
            .where(
                PromocionORM.estado_activo.is_(True),
                PromocionORM.fecha_inicio <= instante,
                PromocionORM.fecha_fin >= instante,
            )
            .order_by(PromocionORM.id_promocion)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def productos_de_promociones(db: Session, ids: List[int]) -> dict[int, List[int]]:
        if not ids:
            return {}
        filas = db.execute(
            select(PromocionProductoORM.id_promocion, PromocionProductoORM.id_producto).where(
                PromocionProductoORM.id_promocion.in_(ids)
            )
        ).all()
        resultado: dict[int, List[int]] = {}
        for id_promocion, id_producto in filas:
            resultado.setdefault(id_promocion, []).append(id_producto)
        return resultado

    @staticmethod
    def sucursales_activas(db: Session) -> List[SucursalORM]:
        stmt = (
            select(SucursalORM)
            .options(selectinload(SucursalORM.ciudad))
            .where(SucursalORM.activa.is_(True))
            .order_by(SucursalORM.id_sucursal)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def existencias(db: Session, ids_sucursal: List[int]) -> list[tuple[int, int, int]]:
        """Disponible por (variante, sucursal), sumando temporadas (lo que puede reservarse)."""
        if not ids_sucursal:
            return []
        stmt = (
            select(
                InventarioSucursalORM.id_variante,
                InventarioSucursalORM.id_sucursal,
                func.sum(InventarioSucursalORM.cantidad_disponible),
            )
            .join(VarianteProductoORM, VarianteProductoORM.id_variante == InventarioSucursalORM.id_variante)
            .where(
                InventarioSucursalORM.id_sucursal.in_(ids_sucursal),
                VarianteProductoORM.activo.is_(True),
            )
            .group_by(InventarioSucursalORM.id_variante, InventarioSucursalORM.id_sucursal)
            .order_by(InventarioSucursalORM.id_variante, InventarioSucursalORM.id_sucursal)
        )
        return [(int(v), int(s), int(c or 0)) for v, s, c in db.execute(stmt).all()]
