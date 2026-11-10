"""Acceso a datos de P2-CU20. `sucursales=None` significa todas (administrador)."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.sincronizacion.modelos import ConflictoSyncORM


def _alcance(stmt, sucursales: Optional[frozenset[int]]):
    if sucursales is None:
        return stmt
    return stmt.where(ConflictoSyncORM.id_sucursal.in_(sucursales or {-1}))


class ConflictosRepositorio:
    @staticmethod
    def listar(db: Session, sucursales: Optional[frozenset[int]], estado: Optional[str]) -> List[ConflictoSyncORM]:
        stmt = select(ConflictoSyncORM)
        if estado:
            stmt = stmt.where(ConflictoSyncORM.estado == estado)
        stmt = _alcance(stmt, sucursales).order_by(ConflictoSyncORM.creado_en.desc()).limit(200)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener(
        db: Session, id_conflicto: int, sucursales: Optional[frozenset[int]], bloquear: bool = False
    ) -> Optional[ConflictoSyncORM]:
        stmt = _alcance(select(ConflictoSyncORM).where(ConflictoSyncORM.id_conflicto == id_conflicto), sucursales)
        if bloquear:
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def contar(db: Session, sucursales: Optional[frozenset[int]]) -> dict[str, int]:
        stmt = _alcance(
            select(ConflictoSyncORM.estado, func.count()).group_by(ConflictoSyncORM.estado), sucursales
        )
        return {estado: int(n) for estado, n in db.execute(stmt).all()}

    @staticmethod
    def ids_por_reembolsar(db: Session) -> List[int]:
        stmt = (
            select(ConflictoSyncORM.id_conflicto)
            .where(ConflictoSyncORM.estado == "reembolso_pendiente")
            .order_by(ConflictoSyncORM.id_conflicto)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def tomar_para_reembolso(db: Session, id_conflicto: int) -> Optional[ConflictoSyncORM]:
        """`FOR UPDATE SKIP LOCKED`: si otro cierre lo está procesando, se salta (sin doble reembolso)."""
        stmt = (
            select(ConflictoSyncORM)
            .where(
                ConflictoSyncORM.id_conflicto == id_conflicto,
                ConflictoSyncORM.estado == "reembolso_pendiente",
            )
            .with_for_update(skip_locked=True)
        )
        return db.execute(stmt).scalar_one_or_none()
