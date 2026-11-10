"""Acceso a datos de `avisos_cliente`. La RLS limita a la empresa; aquí se filtra además por cliente."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.sincronizacion.modelos import AvisoClienteORM

LIMITE_BANDEJA = 50


class AvisosRepositorio:
    @staticmethod
    def de_cliente(db: Session, id_cliente: int) -> List[AvisoClienteORM]:
        stmt = (
            select(AvisoClienteORM)
            .where(AvisoClienteORM.id_cliente == id_cliente)
            .order_by(AvisoClienteORM.creado_en.desc(), AvisoClienteORM.id_aviso.desc())
            .limit(LIMITE_BANDEJA)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def no_leidos(db: Session, id_cliente: int) -> int:
        stmt = select(func.count()).select_from(AvisoClienteORM).where(
            AvisoClienteORM.id_cliente == id_cliente, AvisoClienteORM.leido_en.is_(None)
        )
        return int(db.execute(stmt).scalar_one() or 0)

    @staticmethod
    def del_cliente(db: Session, id_cliente: int, id_aviso: int) -> Optional[AvisoClienteORM]:
        stmt = select(AvisoClienteORM).where(
            AvisoClienteORM.id_aviso == id_aviso, AvisoClienteORM.id_cliente == id_cliente
        )
        return db.execute(stmt).scalar_one_or_none()
