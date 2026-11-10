"""Repositorio de datos para P2-CU07: Gestionar suscripciones de empresas."""

from datetime import date
from typing import Any, Optional

from sqlalchemy import column, func, select, table
from sqlalchemy.orm import Session

from core.tiempo import ahora

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.modelos import (
    HistorialSuscripcionORM,
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


class SuscripcionesAdminRepositorio:
    """Consultas y mutaciones sobre `suscripciones` e `historial_suscripcion` en modo plataforma."""

    @staticmethod
    def obtener_tenant(db: Session, id_tenant: int) -> Optional[TenantORM]:
        return db.get(TenantORM, id_tenant)

    @staticmethod
    def obtener_plan(db: Session, id_plan: int) -> Optional[PlanORM]:
        return db.get(PlanORM, id_plan)

    @staticmethod
    def suscripcion_actual_empresa(
        db: Session, id_tenant: int
    ) -> Optional[tuple[SuscripcionORM, PlanORM]]:
        stmt = (
            select(SuscripcionORM, PlanORM)
            .join(PlanORM, PlanORM.id_plan == SuscripcionORM.id_plan)
            .where(SuscripcionORM.id_tenant == id_tenant)
            .order_by(SuscripcionORM.id_suscripcion.desc())
            .limit(1)
        )
        fila = db.execute(stmt).first()
        return (fila[0], fila[1]) if fila else None

    @staticmethod
    def listar_suscripciones_empresas(
        db: Session,
        *,
        estado: Optional[str] = None,
        id_plan: Optional[int] = None,
        id_tenant: Optional[int] = None,
    ) -> list[tuple[SuscripcionORM, TenantORM, PlanORM]]:
        # Subconsulta: última suscripción por cada empresa
        subq = (
            select(
                SuscripcionORM.id_tenant,
                func.max(SuscripcionORM.id_suscripcion).label("max_id_suscripcion"),
            )
            .group_by(SuscripcionORM.id_tenant)
            .subquery()
        )
        stmt = (
            select(SuscripcionORM, TenantORM, PlanORM)
            .join(subq, SuscripcionORM.id_suscripcion == subq.c.max_id_suscripcion)
            .join(TenantORM, TenantORM.id_tenant == SuscripcionORM.id_tenant)
            .join(PlanORM, PlanORM.id_plan == SuscripcionORM.id_plan)
        )
        if estado:
            stmt = stmt.where(SuscripcionORM.estado == estado)
        if id_plan is not None:
            stmt = stmt.where(SuscripcionORM.id_plan == id_plan)
        if id_tenant is not None:
            stmt = stmt.where(SuscripcionORM.id_tenant == id_tenant)
        stmt = stmt.order_by(TenantORM.id_tenant.asc())
        return [(r[0], r[1], r[2]) for r in db.execute(stmt).all()]

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
    def listar_historial_empresa(db: Session, id_tenant: int) -> list[HistorialSuscripcionORM]:
        stmt = (
            select(HistorialSuscripcionORM)
            .where(HistorialSuscripcionORM.id_tenant == id_tenant)
            .order_by(HistorialSuscripcionORM.creado_en.desc(), HistorialSuscripcionORM.id_historial.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def registrar_evento_historial(
        db: Session,
        *,
        id_tenant: int,
        id_suscripcion: int,
        evento: str,
        detalle: Optional[dict[str, Any]],
        id_usuario: Optional[int],
    ) -> HistorialSuscripcionORM:
        registro = HistorialSuscripcionORM(
            id_tenant=id_tenant,
            id_suscripcion=id_suscripcion,
            evento=evento,
            detalle=detalle,
            id_usuario=id_usuario,
            creado_en=ahora(),
        )
        db.add(registro)
        return registro

    @staticmethod
    def crear_nueva_suscripcion(
        db: Session,
        *,
        id_tenant: int,
        id_plan: int,
        estado: str,
        fecha_inicio: date,
        fecha_vencimiento: date,
    ) -> SuscripcionORM:
        # CU07 A1: rechazar si ya existe suscripción activa o de prueba vigente
        previas = (
            db.execute(
                select(SuscripcionORM).where(
                    SuscripcionORM.id_tenant == id_tenant,
                    SuscripcionORM.estado.in_(("prueba", "activa")),
                )
            )
            .scalars()
            .all()
        )
        if previas:
            from core.errors import ConflictError

            raise ConflictError(
                "La empresa ya cuenta con una suscripción vigente. Utilice la opción 'Cambiar de plan' o 'Renovar'.",
                code="SUSCRIPCION_VIGENTE_EXISTENTE",
            )

        nueva = SuscripcionORM(
            id_tenant=id_tenant,
            id_plan=id_plan,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            creado_en=ahora(),
        )
        db.add(nueva)
        db.flush()
        return nueva

