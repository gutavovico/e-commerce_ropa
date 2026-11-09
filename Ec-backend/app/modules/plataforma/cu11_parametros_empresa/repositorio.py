"""Acceso a datos de P2-CU11. Sin lógica de negocio."""

from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from modules.plataforma.modelos import ConfiguracionTenantORM


class ParametrosEmpresaRepositorio:
    @staticmethod
    def leer(db: Session, id_tenant: int, bloquear: bool = False) -> Optional[ConfiguracionTenantORM]:
        stmt = select(ConfiguracionTenantORM).where(ConfiguracionTenantORM.id_tenant == id_tenant)
        if bloquear:
            stmt = stmt.with_for_update()
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def crear_si_falta(db: Session) -> None:
        """C4: fila con los valores por defecto de la base; `id_tenant` lo pone el contexto (RLS)."""
        db.execute(text(
            "INSERT INTO fashionstore.configuracion_tenant DEFAULT VALUES ON CONFLICT (id_tenant) DO NOTHING"
        ))
        db.flush()

    @staticmethod
    def tiene_operaciones(db: Session) -> bool:
        """M3: alguna venta o pago de la empresa de la sesión (la RLS limita a la suya)."""
        return bool(db.execute(text(
            "SELECT EXISTS (SELECT 1 FROM fashionstore.ventas) OR EXISTS (SELECT 1 FROM fashionstore.pagos)"
        )).scalar())
