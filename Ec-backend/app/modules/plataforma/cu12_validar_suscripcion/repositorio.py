"""Acceso a datos de P2-CU12. Sin lógica de negocio."""

from datetime import date
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from modules.plataforma.modelos import PlanFuncionalidadORM, PlanORM, SuscripcionORM

#: Roles que cuentan para el límite de empleados del plan.
ROLES_EMPLEADO = ("administrador", "encargado_sucursal", "cajero")


class SuscripcionRepositorio:
    @staticmethod
    def suscripcion_vigente(db: Session, id_tenant: int, hoy: date) -> Optional[SuscripcionORM]:
        """Suscripción en prueba o activa y dentro de sus fechas (RN13, RN14)."""
        stmt = select(SuscripcionORM).where(
            SuscripcionORM.id_tenant == id_tenant,
            SuscripcionORM.estado.in_(("prueba", "activa")),
            SuscripcionORM.fecha_inicio <= hoy,
            SuscripcionORM.fecha_vencimiento >= hoy,
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def plan(db: Session, id_plan: int) -> Optional[PlanORM]:
        return db.get(PlanORM, id_plan)

    @staticmethod
    def plan_incluye(db: Session, id_plan: int, funcionalidad: str) -> bool:
        stmt = select(PlanFuncionalidadORM.id_plan).where(
            PlanFuncionalidadORM.id_plan == id_plan,
            PlanFuncionalidadORM.codigo_funcionalidad == funcionalidad,
        )
        return db.execute(stmt).first() is not None

    @staticmethod
    def planes_con(db: Session, funcionalidad: str) -> List[str]:
        stmt = (
            select(PlanORM.nombre)
            .join(PlanFuncionalidadORM, PlanFuncionalidadORM.id_plan == PlanORM.id_plan)
            .where(PlanFuncionalidadORM.codigo_funcionalidad == funcionalidad, PlanORM.activo.is_(True))
            .order_by(PlanORM.max_sucursales_activas)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def bloquear_recurso(db: Session, id_tenant: int, recurso: str) -> None:
        """P2-CU04 B8: serializa por empresa y recurso las altas que cuentan para un límite.

        Bloqueo consultivo de transacción: se libera en el `commit`/`rollback`, no necesita permisos
        sobre ninguna tabla y funciona con PgBouncer en modo transacción. La segunda solicitud
        espera y, al contar (READ COMMITTED), ya ve la fila que confirmó la primera.
        """
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:clave), CAST(:t AS integer))"),
            {"clave": f"fashionstore.limite.{recurso}", "t": id_tenant},
        )

    @staticmethod
    def sucursales_activas(db: Session, id_tenant: int) -> int:
        return int(db.execute(
            text("SELECT count(*) FROM fashionstore.sucursales WHERE id_tenant = :t AND activa"),
            {"t": id_tenant},
        ).scalar_one())

    @staticmethod
    def empleados_activos(db: Session, id_tenant: int) -> int:
        return int(db.execute(
            text("SELECT count(*) FROM fashionstore.usuarios "
                 "WHERE id_tenant = :t AND activo AND rol::text = ANY(:roles)"),
            {"t": id_tenant, "roles": list(ROLES_EMPLEADO)},
        ).scalar_one())
