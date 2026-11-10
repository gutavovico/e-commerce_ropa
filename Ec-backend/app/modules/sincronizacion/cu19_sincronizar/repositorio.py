"""Acceso a datos de P2-CU19."""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.sincronizacion.modelos import ConflictoSyncORM, DispositivoORM, OperacionSyncORM


class SincronizacionRepositorio:
    @staticmethod
    def operacion(db: Session, uuid_operacion: uuid.UUID) -> Optional[OperacionSyncORM]:
        stmt = select(OperacionSyncORM).where(OperacionSyncORM.uuid_operacion == uuid_operacion)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def conflicto_de_venta(db: Session, id_venta: int) -> Optional[ConflictoSyncORM]:
        stmt = select(ConflictoSyncORM).where(ConflictoSyncORM.id_venta == id_venta)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def dispositivo(db: Session, id_dispositivo: int) -> Optional[DispositivoORM]:
        return db.get(DispositivoORM, id_dispositivo)

    @staticmethod
    def operaciones_del_dispositivo(
        db: Session, id_dispositivo: int
    ) -> List[tuple[OperacionSyncORM, Optional[str]]]:
        stmt = (
            select(OperacionSyncORM, ConflictoSyncORM.estado)
            .outerjoin(ConflictoSyncORM, ConflictoSyncORM.id_operacion_sync == OperacionSyncORM.id_operacion_sync)
            .where(OperacionSyncORM.id_dispositivo == id_dispositivo)
            .order_by(OperacionSyncORM.recibida_en.desc(), OperacionSyncORM.id_operacion_sync.desc())
            .limit(200)
        )
        return [(op, estado) for op, estado in db.execute(stmt).all()]
