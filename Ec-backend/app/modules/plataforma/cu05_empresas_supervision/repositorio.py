"""Repositorio de datos para P2-CU05: Gestionar empresas y supervisar la plataforma."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import column, func, or_, select, table, text
from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.modelos import (
    ConfiguracionTenantORM,
    HistorialSuscripcionORM,
    PlanORM,
    SuscripcionORM,
    TenantORM,
)
from modules.seguridad.cu30_bitacora.modelos import Bitacora

_t_sucursales = table(
    "sucursales",
    column("id_sucursal"),
    column("id_tenant"),
    column("activa"),
    schema="fashionstore",
)
_t_productos = table(
    "productos",
    column("id_producto"),
    column("id_tenant"),
    column("activo"),
    schema="fashionstore",
)
_t_ventas = table(
    "ventas",
    column("id_venta"),
    column("id_tenant"),
    column("estado"),
    column("total"),
    schema="fashionstore",
)
_t_reservas = table(
    "reservas",
    column("id_reserva"),
    column("id_tenant"),
    schema="fashionstore",
)


class EmpresasSupervisionRepositorio:
    """Consultas y persistencia de empresas, indicadores agregados y bitácora de plataforma."""

    @staticmethod
    def obtener_tenant(db: Session, id_tenant: int) -> Optional[TenantORM]:
        return db.get(TenantORM, id_tenant)

    @staticmethod
    def buscar_por_codigo(db: Session, codigo: str) -> Optional[TenantORM]:
        return db.execute(
            select(TenantORM).where(func.lower(TenantORM.codigo) == codigo.strip().lower())
        ).scalar_one_or_none()

    @staticmethod
    def obtener_plan(db: Session, id_plan: int) -> Optional[PlanORM]:
        return db.get(PlanORM, id_plan)

    @staticmethod
    def correo_existe(db: Session, email: str) -> bool:
        email_norm = email.strip().lower()
        fila = db.execute(
            select(UsuarioORM.id_usuario).where(func.lower(UsuarioORM.email) == email_norm)
        ).first()
        return fila is not None

    @staticmethod
    def listar_tenants(
        db: Session,
        *,
        q: Optional[str] = None,
        estado: Optional[str] = None,
        id_plan: Optional[int] = None,
    ) -> list[TenantORM]:
        stmt = select(TenantORM)
        if q and q.strip():
            termino = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    TenantORM.codigo.ilike(termino),
                    TenantORM.nombre.ilike(termino),
                    TenantORM.correo_contacto.ilike(termino),
                )
            )
        if estado:
            stmt = stmt.where(TenantORM.estado == estado)
        if id_plan is not None:
            subq = (
                select(SuscripcionORM.id_tenant)
                .where(SuscripcionORM.id_plan == id_plan)
                .order_by(SuscripcionORM.id_suscripcion.desc())
            )
            stmt = stmt.where(TenantORM.id_tenant.in_(subq))
        stmt = stmt.order_by(TenantORM.id_tenant.asc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def suscripcion_mas_reciente(db: Session, id_tenant: int) -> Optional[tuple[SuscripcionORM, PlanORM]]:
        stmt = (
            select(SuscripcionORM, PlanORM)
            .join(PlanORM, PlanORM.id_plan == SuscripcionORM.id_plan)
            .where(SuscripcionORM.id_tenant == id_tenant)
            .order_by(
                # Priorizar suscripción en prueba o activa; si no, la más reciente
                SuscripcionORM.id_suscripcion.desc()
            )
            .limit(1)
        )
        fila = db.execute(stmt).first()
        return (fila[0], fila[1]) if fila else None

    @staticmethod
    def admin_principal_empresa(db: Session, id_tenant: int) -> Optional[UsuarioORM]:
        stmt = (
            select(UsuarioORM)
            .where(
                UsuarioORM.id_tenant == id_tenant,
                UsuarioORM.rol == "administrador",
            )
            .order_by(UsuarioORM.id_usuario.asc())
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def indicadores_empresa(db: Session, id_tenant: int) -> dict[str, Any]:
        suc_totales = int(
            db.execute(
                select(func.count()).select_from(_t_sucursales).where(_t_sucursales.c.id_tenant == id_tenant)
            ).scalar_one()
            or 0
        )
        suc_activas = int(
            db.execute(
                select(func.count())
                .select_from(_t_sucursales)
                .where(_t_sucursales.c.id_tenant == id_tenant, _t_sucursales.c.activa.is_(True))
            ).scalar_one()
            or 0
        )
        emp_activos = int(
            db.execute(
                select(func.count(UsuarioORM.id_usuario)).where(
                    UsuarioORM.id_tenant == id_tenant,
                    UsuarioORM.activo.is_(True),
                )
            ).scalar_one()
            or 0
        )
        prod_activos = int(
            db.execute(
                select(func.count())
                .select_from(_t_productos)
                .where(_t_productos.c.id_tenant == id_tenant, _t_productos.c.activo.is_(True))
            ).scalar_one()
            or 0
        )
        fila_ventas = db.execute(
            select(
                func.count().label("cantidad"),
                func.coalesce(func.sum(_t_ventas.c.total), Decimal("0.00")).label("monto"),
            )
            .select_from(_t_ventas)
            .where(_t_ventas.c.id_tenant == id_tenant, _t_ventas.c.estado == "pagada")
        ).first()
        ventas_cant = int(fila_ventas.cantidad if fila_ventas else 0)
        ventas_monto = Decimal(str(fila_ventas.monto if fila_ventas else "0.00"))
        reservas_tot = int(
            db.execute(
                select(func.count()).select_from(_t_reservas).where(_t_reservas.c.id_tenant == id_tenant)
            ).scalar_one()
            or 0
        )
        return {
            "sucursales_activas": suc_activas,
            "sucursales_totales": suc_totales,
            "empleados_activos": emp_activos,
            "productos_activos": prod_activos,
            "ventas_pagadas_cantidad": ventas_cant,
            "ventas_pagadas_monto": ventas_monto,
            "reservas_totales": reservas_tot,
        }

    @staticmethod
    def crear_empresa_atomica(
        db: Session,
        *,
        codigo: str,
        nombre: str,
        correo_contacto: Optional[str],
        telefono: Optional[str],
        plan: PlanORM,
        estado_suscripcion: str,
        fecha_inicio: date,
        fecha_vencimiento: date,
        admin_nombres: str,
        admin_apellidos: str,
        admin_email: str,
        admin_password_hash: str,
        admin_telefono: Optional[str],
        id_usuario_operador: Optional[int],
    ) -> tuple[TenantORM, SuscripcionORM, UsuarioORM]:
        now_utc = datetime.now(timezone.utc)
        tenant = TenantORM(
            codigo=codigo,
            nombre=nombre,
            correo_contacto=correo_contacto,
            telefono=telefono,
            estado="activa",
            creado_en=now_utc,
        )
        db.add(tenant)
        db.flush()

        config = ConfiguracionTenantORM(
            id_tenant=tenant.id_tenant,
            moneda="EUR",
            zona_horaria="Europe/Madrid",
            horas_vencimiento_reserva=24,
            dias_cambio_prenda=15,
            operacion_offline_habilitada=True,
            dias_antiguedad_offline=7,
            actualizado_en=now_utc,
        )
        db.add(config)

        suscripcion = SuscripcionORM(
            id_tenant=tenant.id_tenant,
            id_plan=plan.id_plan,
            estado=estado_suscripcion,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            creado_en=now_utc,
        )
        db.add(suscripcion)
        db.flush()

        historial = HistorialSuscripcionORM(
            id_tenant=tenant.id_tenant,
            id_suscripcion=suscripcion.id_suscripcion,
            evento="alta",
            detalle={
                "id_plan": plan.id_plan,
                "plan": plan.nombre,
                "estado": estado_suscripcion,
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_vencimiento": fecha_vencimiento.isoformat(),
            },
            id_usuario=id_usuario_operador,
            creado_en=now_utc,
        )
        db.add(historial)

        admin_usuario = UsuarioORM(
            id_tenant=tenant.id_tenant,
            email=admin_email,
            password_hash=admin_password_hash,
            nombres=admin_nombres,
            apellidos=admin_apellidos,
            telefono=admin_telefono,
            rol="administrador",
            id_sucursal=None,
            activo=True,
            fecha_registro=now_utc,
        )
        db.add(admin_usuario)
        db.flush()

        db.execute(
            text(
                "INSERT INTO fashionstore.empleados (id_tenant, id_empleado, codigo_empleado, cargo) "
                "VALUES (:id_tenant, :uid, :codigo, :cargo) ON CONFLICT (id_empleado) DO NOTHING"
            ),
            {
                "id_tenant": tenant.id_tenant,
                "uid": admin_usuario.id_usuario,
                "codigo": f"EMP-{admin_usuario.id_usuario}",
                "cargo": "Administrador",
            },
        )
        db.commit()
        db.refresh(tenant)
        db.refresh(suscripcion)
        db.refresh(admin_usuario)
        return tenant, suscripcion, admin_usuario

    @staticmethod
    def listar_bitacora_plataforma(
        db: Session,
        *,
        id_tenant: Optional[int] = None,
        solo_plataforma: bool = False,
        severidad: Optional[str] = None,
        accion: Optional[str] = None,
        q: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        pagina: int = 1,
        limite: int = 20,
    ) -> tuple[list[tuple[Bitacora, Optional[TenantORM]]], int]:
        condiciones = []
        if solo_plataforma:
            condiciones.append(Bitacora.id_tenant.is_(None))
        elif id_tenant is not None:
            condiciones.append(Bitacora.id_tenant == id_tenant)

        if severidad and severidad.strip():
            condiciones.append(Bitacora.severidad == severidad.strip().upper())

        if accion and accion.strip():
            condiciones.append(Bitacora.accion.ilike(f"%{accion.strip()}%"))

        if q and q.strip():
            termino = f"%{q.strip()}%"
            condiciones.append(
                or_(
                    Bitacora.usuario_nombre.ilike(termino),
                    Bitacora.accion.ilike(termino),
                    Bitacora.tabla_modulo.ilike(termino),
                    Bitacora.direccion_ip.ilike(termino),
                )
            )

        if fecha_inicio:
            inicio_utc = datetime.combine(fecha_inicio, time.min).replace(tzinfo=timezone.utc)
            condiciones.append(Bitacora.creado_en >= inicio_utc)

        if fecha_fin:
            fin_utc = datetime.combine(fecha_fin + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
            condiciones.append(Bitacora.creado_en < fin_utc)

        stmt_count = select(func.count(Bitacora.id_bitacora))
        if condiciones:
            stmt_count = stmt_count.where(*condiciones)
        total = int(db.execute(stmt_count).scalar_one() or 0)
        if total == 0:
            return [], 0

        offset = (max(1, pagina) - 1) * limite
        stmt = (
            select(Bitacora, TenantORM)
            .outerjoin(TenantORM, TenantORM.id_tenant == Bitacora.id_tenant)
        )
        if condiciones:
            stmt = stmt.where(*condiciones)
        stmt = stmt.order_by(Bitacora.creado_en.desc()).offset(offset).limit(limite)
        filas = [(r[0], r[1]) for r in db.execute(stmt).all()]
        return filas, total

