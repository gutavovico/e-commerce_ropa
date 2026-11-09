"""Repositorio de datos para P2-CU06: Gestionar planes y funcionalidades."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import column, delete, distinct, func, select, table
from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.modelos import (
    FuncionalidadORM,
    PlanFuncionalidadORM,
    PlanORM,
    SuscripcionORM,
    TenantORM,
)

_t_sucursales = table(
    "sucursales",
    column("id_sucursal"),
    column("id_tenant"),
    column("activa"),
    schema="fashionstore",
)


class PlanesFuncionalidadesRepositorio:
    """Acceso a datos de planes, funcionalidades y conteo de empresas suscritas."""

    @staticmethod
    def listar_funcionalidades(db: Session) -> list[FuncionalidadORM]:
        stmt = select(FuncionalidadORM).order_by(FuncionalidadORM.codigo.asc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def listar_planes(db: Session, *, solo_activos: bool = False) -> list[PlanORM]:
        stmt = select(PlanORM)
        if solo_activos:
            stmt = stmt.where(PlanORM.activo.is_(True))
        stmt = stmt.order_by(PlanORM.precio_mensual.asc(), PlanORM.id_plan.asc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener_plan(db: Session, id_plan: int) -> Optional[PlanORM]:
        return db.get(PlanORM, id_plan)

    @staticmethod
    def buscar_por_nombre(
        db: Session, nombre: str, *, excluir_id_plan: Optional[int] = None
    ) -> Optional[PlanORM]:
        stmt = select(PlanORM).where(func.lower(PlanORM.nombre) == nombre.strip().lower())
        if excluir_id_plan is not None:
            stmt = stmt.where(PlanORM.id_plan != excluir_id_plan)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def funcionalidades_de_plan(db: Session, id_plan: int) -> list[FuncionalidadORM]:
        stmt = (
            select(FuncionalidadORM)
            .join(
                PlanFuncionalidadORM,
                PlanFuncionalidadORM.codigo_funcionalidad == FuncionalidadORM.codigo,
            )
            .where(PlanFuncionalidadORM.id_plan == id_plan)
            .order_by(FuncionalidadORM.codigo.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def contar_empresas_del_plan(db: Session, id_plan: int, hoy: date) -> tuple[int, int]:
        totales = int(
            db.execute(
                select(func.count(distinct(SuscripcionORM.id_tenant))).where(
                    SuscripcionORM.id_plan == id_plan
                )
            ).scalar_one()
            or 0
        )
        vigentes = int(
            db.execute(
                select(func.count(distinct(SuscripcionORM.id_tenant))).where(
                    SuscripcionORM.id_plan == id_plan,
                    SuscripcionORM.estado.in_(("prueba", "activa")),
                    SuscripcionORM.fecha_inicio <= hoy,
                    SuscripcionORM.fecha_vencimiento >= hoy,
                )
            ).scalar_one()
            or 0
        )
        return vigentes, totales

    @staticmethod
    def empresas_con_suscripcion_activa_en_plan(db: Session, id_plan: int) -> list[TenantORM]:
        stmt = (
            select(TenantORM)
            .join(SuscripcionORM, SuscripcionORM.id_tenant == TenantORM.id_tenant)
            .where(
                SuscripcionORM.id_plan == id_plan,
                SuscripcionORM.estado.in_(("prueba", "activa")),
            )
            .order_by(TenantORM.id_tenant.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def uso_recursos_empresa(db: Session, id_tenant: int) -> tuple[int, int]:
        sucursales_activas = int(
            db.execute(
                select(func.count())
                .select_from(_t_sucursales)
                .where(_t_sucursales.c.id_tenant == id_tenant, _t_sucursales.c.activa.is_(True))
            ).scalar_one()
            or 0
        )
        empleados_activos = int(
            db.execute(
                select(func.count(UsuarioORM.id_usuario)).where(
                    UsuarioORM.id_tenant == id_tenant,
                    UsuarioORM.activo.is_(True),
                )
            ).scalar_one()
            or 0
        )
        return sucursales_activas, empleados_activos

    @staticmethod
    def crear_plan(
        db: Session,
        *,
        nombre: str,
        precio_mensual: Decimal,
        max_sucursales_activas: int,
        max_empleados: Optional[int],
        codigos_funcionalidades: list[str],
    ) -> PlanORM:
        plan = PlanORM(
            nombre=nombre,
            precio_mensual=precio_mensual,
            max_sucursales_activas=max_sucursales_activas,
            max_empleados=max_empleados,
            activo=True,
        )
        db.add(plan)
        db.flush()

        for cod in codigos_funcionalidades:
            db.add(PlanFuncionalidadORM(id_plan=plan.id_plan, codigo_funcionalidad=cod))

        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def actualizar_plan(
        db: Session,
        plan: PlanORM,
        *,
        nombre: str,
        precio_mensual: Decimal,
        max_sucursales_activas: int,
        max_empleados: Optional[int],
        codigos_funcionalidades: list[str],
    ) -> PlanORM:
        plan.nombre = nombre
        plan.precio_mensual = precio_mensual
        plan.max_sucursales_activas = max_sucursales_activas
        plan.max_empleados = max_empleados

        db.execute(delete(PlanFuncionalidadORM).where(PlanFuncionalidadORM.id_plan == plan.id_plan))
        for cod in codigos_funcionalidades:
            db.add(PlanFuncionalidadORM(id_plan=plan.id_plan, codigo_funcionalidad=cod))

        db.commit()
        db.refresh(plan)
        return plan

