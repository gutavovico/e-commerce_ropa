"""Repositorio de acceso a datos para P2-CU09 y P2-CU10 (Suscripción y uso de la empresa + Stripe)."""

from datetime import date
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from modules.plataforma.modelos import (
    ConfiguracionTenantORM,
    FuncionalidadORM,
    HistorialSuscripcionORM,
    PlanFuncionalidadORM,
    PlanORM,
    SuscripcionORM,
    TenantORM,
)

ROLES_EMPLEADO = ("administrador", "encargado_sucursal", "cajero")


class MiSuscripcionRepositorio:
    """Consultas y escrituras de suscripción, uso y planes para el administrador de una empresa."""

    @staticmethod
    def obtener_tenant(db: Session, id_tenant: int) -> Optional[TenantORM]:
        return db.get(TenantORM, id_tenant)

    @staticmethod
    def obtener_moneda_empresa(db: Session, id_tenant: int) -> str:
        cfg = db.get(ConfiguracionTenantORM, id_tenant)
        if cfg and cfg.moneda:
            return cfg.moneda.upper()
        return "BOB"

    @staticmethod
    def suscripcion_actual(db: Session, id_tenant: int) -> Optional[tuple[SuscripcionORM, PlanORM]]:
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
    def obtener_plan(db: Session, id_plan: int) -> Optional[PlanORM]:
        return db.get(PlanORM, id_plan)

    @staticmethod
    def listar_planes_activos(db: Session) -> list[PlanORM]:
        stmt = (
            select(PlanORM)
            .where(PlanORM.activo.is_(True))
            .order_by(PlanORM.precio_mensual.asc(), PlanORM.id_plan.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def listar_catalogo_funcionalidades(db: Session) -> list[FuncionalidadORM]:
        stmt = select(FuncionalidadORM).order_by(FuncionalidadORM.codigo.asc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def funcionalidades_por_plan(db: Session, id_plan: int) -> list[str]:
        stmt = (
            select(PlanFuncionalidadORM.codigo_funcionalidad)
            .where(PlanFuncionalidadORM.id_plan == id_plan)
            .order_by(PlanFuncionalidadORM.codigo_funcionalidad.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def planes_activos_con_funcionalidad(db: Session, codigo_funcionalidad: str) -> list[str]:
        stmt = (
            select(PlanORM.nombre)
            .join(PlanFuncionalidadORM, PlanFuncionalidadORM.id_plan == PlanORM.id_plan)
            .where(
                PlanFuncionalidadORM.codigo_funcionalidad == codigo_funcionalidad,
                PlanORM.activo.is_(True),
            )
            .order_by(PlanORM.precio_mensual.asc(), PlanORM.id_plan.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def listar_sucursales_activas(db: Session, id_tenant: int) -> list[dict]:
        filas = db.execute(
            text(
                "SELECT id_sucursal, nombre, direccion "
                "FROM fashionstore.sucursales "
                "WHERE id_tenant = :t AND activa = true "
                "ORDER BY id_sucursal ASC"
            ),
            {"t": id_tenant},
        ).all()
        return [
            {"id_sucursal": int(f[0]), "nombre": str(f[1]), "direccion": str(f[2]) if f[2] else None}
            for f in filas
        ]

    @staticmethod
    def contar_empleados_activos(db: Session, id_tenant: int) -> int:
        return int(
            db.execute(
                text(
                    "SELECT count(*) FROM fashionstore.usuarios "
                    "WHERE id_tenant = :t AND activo = true AND rol::text = ANY(:roles)"
                ),
                {"t": id_tenant, "roles": list(ROLES_EMPLEADO)},
            ).scalar_one()
        )

    @staticmethod
    def listar_historial(db: Session, id_tenant: int) -> list[HistorialSuscripcionORM]:
        stmt = (
            select(HistorialSuscripcionORM)
            .where(HistorialSuscripcionORM.id_tenant == id_tenant)
            .order_by(HistorialSuscripcionORM.id_historial.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def referencia_pago_ya_utilizada(db: Session, referencia_pago: str) -> bool:
        """Verifica si una referencia de PaymentIntent ya fue aplicada en `historial_suscripcion`."""
        ref = (referencia_pago or "").strip()
        if not ref:
            return False
        fila = db.execute(
            text(
                "SELECT 1 FROM fashionstore.historial_suscripcion "
                "WHERE detalle->>'referencia_pago' = :ref LIMIT 1"
            ),
            {"ref": ref},
        ).first()
        return fila is not None

    @staticmethod
    def actualizar_suscripcion_y_registrar_historial(
        db: Session,
        *,
        suscripcion: SuscripcionORM,
        id_tenant: int,
        id_plan: int,
        estado: str,
        fecha_inicio: date,
        fecha_vencimiento: date,
        evento: str,
        detalle: dict,
        id_usuario: Optional[int],
    ) -> SuscripcionORM:
        suscripcion.id_plan = id_plan
        suscripcion.estado = estado
        suscripcion.fecha_inicio = fecha_inicio
        suscripcion.fecha_vencimiento = fecha_vencimiento
        db.flush()

        item = HistorialSuscripcionORM(
            id_tenant=id_tenant,
            id_suscripcion=suscripcion.id_suscripcion,
            evento=evento,
            detalle=detalle,
            id_usuario=id_usuario,
        )
        db.add(item)
        db.flush()
        return suscripcion
