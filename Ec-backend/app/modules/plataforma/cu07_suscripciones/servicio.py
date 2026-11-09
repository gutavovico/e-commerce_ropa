"""Servicio de aplicación y dominio para P2-CU07: Gestionar suscripciones de empresas."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from core.tenant import limpiar_cache_tenants
from core.tiempo import ahora, hoy
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu07_suscripciones.esquemas import (
    HistorialSuscripcionItemOut,
    OperacionSuscripcionIn,
    SuscripcionEmpresaOut,
)
from modules.plataforma.cu07_suscripciones.repositorio import SuscripcionesAdminRepositorio
from modules.plataforma.modelos import PlanORM, SuscripcionORM, TenantORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


def _es_vigente(susc: SuscripcionORM, hoy: date) -> bool:
    return susc.estado in ("prueba", "activa") and susc.fecha_inicio <= hoy <= susc.fecha_vencimiento


class SuscripcionesAdminServicio:
    """Casos de uso de administración de suscripciones e historial para el Super Administrador."""

    @staticmethod
    def _armar_suscripcion_out(
        db: Session,
        susc: SuscripcionORM,
        tenant: TenantORM,
        plan: PlanORM,
        hoy: date,
    ) -> SuscripcionEmpresaOut:
        suc_activas, emp_activos = SuscripcionesAdminRepositorio.uso_recursos_empresa(
            db, tenant.id_tenant
        )
        return SuscripcionEmpresaOut(
            id_suscripcion=susc.id_suscripcion,
            id_tenant=tenant.id_tenant,
            codigo_empresa=tenant.codigo,
            nombre_empresa=tenant.nombre,
            estado_empresa=tenant.estado,
            id_plan=plan.id_plan,
            nombre_plan=plan.nombre,
            precio_mensual=plan.precio_mensual,
            estado=susc.estado,
            fecha_inicio=susc.fecha_inicio,
            fecha_vencimiento=susc.fecha_vencimiento,
            vigente=_es_vigente(susc, hoy),
            sucursales_activas=suc_activas,
            max_sucursales_activas=plan.max_sucursales_activas,
            empleados_activos=emp_activos,
            max_empleados=plan.max_empleados,
            creado_en=susc.creado_en,
        )

    @staticmethod
    def _validar_uso_contra_plan(db: Session, id_tenant: int, plan: PlanORM) -> None:
        """Curso Alterno A1 (CU07): rechaza asignar un plan cuyo límite es menor que el uso actual."""
        suc_activas, emp_activos = SuscripcionesAdminRepositorio.uso_recursos_empresa(db, id_tenant)
        excesos: list[str] = []
        if suc_activas > plan.max_sucursales_activas:
            excesos.append(
                f"sucursales activas ({suc_activas} en uso vs máximo {plan.max_sucursales_activas} del plan '{plan.nombre}')"
            )
        if plan.max_empleados is not None and emp_activos > plan.max_empleados:
            excesos.append(
                f"empleados activos ({emp_activos} en uso vs máximo {plan.max_empleados} del plan '{plan.nombre}')"
            )
        if excesos:
            raise ConflictError(
                f"La empresa supera los límites del plan '{plan.nombre}': {'; '.join(excesos)}. "
                "Debe reducir primero los recursos activos o elegir un plan superior (CU07 A1).",
                code="USO_SUPERA_LIMITE_PLAN",
            )

    @staticmethod
    def listar_suscripciones(
        db: Session,
        *,
        estado: Optional[str] = None,
        id_plan: Optional[int] = None,
        id_tenant: Optional[int] = None,
    ) -> list[SuscripcionEmpresaOut]:
        hoy_bolivia = hoy()
        filas = SuscripcionesAdminRepositorio.listar_suscripciones_empresas(
            db, estado=estado, id_plan=id_plan, id_tenant=id_tenant
        )
        return [
            SuscripcionesAdminServicio._armar_suscripcion_out(db, susc, tenant, plan, hoy_bolivia)
            for susc, tenant, plan in filas
        ]

    @staticmethod
    def listar_historial(db: Session, id_tenant: int) -> list[HistorialSuscripcionItemOut]:
        tenant = SuscripcionesAdminRepositorio.obtener_tenant(db, id_tenant)
        if not tenant:
            raise NotFoundError(
                f"La empresa con identificador {id_tenant} no existe.",
                code="EMPRESA_NO_ENCONTRADA",
            )
        items = SuscripcionesAdminRepositorio.listar_historial_empresa(db, id_tenant)
        return [HistorialSuscripcionItemOut.model_validate(i) for i in items]

    @staticmethod
    def operar_suscripcion(
        db: Session,
        id_tenant: int,
        datos: OperacionSuscripcionIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> SuscripcionEmpresaOut:
        tenant = SuscripcionesAdminRepositorio.obtener_tenant(db, id_tenant)
        if not tenant:
            raise NotFoundError(
                f"La empresa con identificador {id_tenant} no existe.",
                code="EMPRESA_NO_ENCONTRADA",
            )

        hoy_bolivia = hoy()
        par_actual = SuscripcionesAdminRepositorio.suscripcion_actual_empresa(db, id_tenant)
        operacion = datos.operacion

        if operacion == "alta":
            if par_actual and par_actual[0].estado in ("prueba", "activa"):
                raise ConflictError(
                    "La empresa ya cuenta con una suscripción vigente. Utilice la opción 'Cambiar de plan' o 'Renovar' (CU07 A1).",
                    code="SUSCRIPCION_VIGENTE_EXISTENTE",
                )
            if datos.id_plan is None or datos.fecha_inicio is None or datos.fecha_vencimiento is None:
                raise UnprocessableEntityError(
                    "Para dar de alta una suscripción debe indicar id_plan, fecha_inicio y fecha_vencimiento.",
                    code="DATOS_SUSCRIPCION_INCOMPLETOS",
                )
            if datos.fecha_vencimiento <= datos.fecha_inicio:
                raise UnprocessableEntityError(
                    "La fecha de vencimiento debe ser posterior a la fecha de inicio (RN13).",
                    code="FECHAS_SUSCRIPCION_INVALIDAS",
                )
            plan = SuscripcionesAdminRepositorio.obtener_plan(db, datos.id_plan)
            if not plan:
                raise NotFoundError(
                    f"El plan con identificador {datos.id_plan} no existe.",
                    code="PLAN_NO_ENCONTRADO",
                )
            if not plan.activo:
                raise ConflictError(
                    f"El plan '{plan.nombre}' está inactivo y no se puede asignar a nuevas suscripciones.",
                    code="PLAN_INACTIVO",
                )
            SuscripcionesAdminServicio._validar_uso_contra_plan(db, id_tenant, plan)
            estado_inicial = datos.estado or "activa"
            susc = SuscripcionesAdminRepositorio.crear_nueva_suscripcion(
                db,
                id_tenant=id_tenant,
                id_plan=plan.id_plan,
                estado=estado_inicial,
                fecha_inicio=datos.fecha_inicio,
                fecha_vencimiento=datos.fecha_vencimiento,
            )
            SuscripcionesAdminRepositorio.registrar_evento_historial(
                db,
                id_tenant=id_tenant,
                id_suscripcion=susc.id_suscripcion,
                evento="alta",
                detalle={
                    "id_plan": plan.id_plan,
                    "plan": plan.nombre,
                    "estado": estado_inicial,
                    "fecha_inicio": datos.fecha_inicio.isoformat(),
                    "fecha_vencimiento": datos.fecha_vencimiento.isoformat(),
                    "motivo": datos.motivo,
                },
                id_usuario=usuario_actual.id_usuario,
            )
            db.commit()
            db.refresh(susc)
            plan_final = plan

        else:
            if not par_actual:
                raise NotFoundError(
                    "La empresa no tiene una suscripción registrada para ejecutar esta operación.",
                    code="SUSCRIPCION_NO_ENCONTRADA",
                )
            susc, plan_anterior = par_actual
            plan_final = plan_anterior

            if operacion == "cambio_plan":
                if datos.id_plan is None:
                    raise UnprocessableEntityError(
                        "Debe indicar el nuevo id_plan para cambiar de plan.",
                        code="DATOS_SUSCRIPCION_INCOMPLETOS",
                    )
                plan_nuevo = SuscripcionesAdminRepositorio.obtener_plan(db, datos.id_plan)
                if not plan_nuevo:
                    raise NotFoundError(
                        f"El plan con identificador {datos.id_plan} no existe.",
                        code="PLAN_NO_ENCONTRADO",
                    )
                if not plan_nuevo.activo:
                    raise ConflictError(
                        f"El plan '{plan_nuevo.nombre}' está inactivo.",
                        code="PLAN_INACTIVO",
                    )
                SuscripcionesAdminServicio._validar_uso_contra_plan(db, id_tenant, plan_nuevo)

                nueva_inicio = datos.fecha_inicio or susc.fecha_inicio
                nueva_venc = datos.fecha_vencimiento or susc.fecha_vencimiento
                if nueva_venc <= nueva_inicio:
                    raise UnprocessableEntityError(
                        "La fecha de vencimiento debe ser posterior a la fecha de inicio (RN13).",
                        code="FECHAS_SUSCRIPCION_INVALIDAS",
                    )
                susc.id_plan = plan_nuevo.id_plan
                if datos.estado:
                    susc.estado = datos.estado
                susc.fecha_inicio = nueva_inicio
                susc.fecha_vencimiento = nueva_venc
                plan_final = plan_nuevo
                SuscripcionesAdminRepositorio.registrar_evento_historial(
                    db,
                    id_tenant=id_tenant,
                    id_suscripcion=susc.id_suscripcion,
                    evento="cambio_plan",
                    detalle={
                        "plan_anterior": plan_anterior.nombre,
                        "plan_nuevo": plan_nuevo.nombre,
                        "id_plan_nuevo": plan_nuevo.id_plan,
                        "fecha_vencimiento": nueva_venc.isoformat(),
                        "motivo": datos.motivo,
                    },
                    id_usuario=usuario_actual.id_usuario,
                )

            elif operacion == "renovacion":
                if datos.fecha_vencimiento is None:
                    raise UnprocessableEntityError(
                        "Debe indicar la nueva fecha_vencimiento para renovar la suscripción.",
                        code="DATOS_SUSCRIPCION_INCOMPLETOS",
                    )
                nueva_inicio = datos.fecha_inicio or susc.fecha_inicio
                if datos.fecha_vencimiento <= nueva_inicio:
                    raise UnprocessableEntityError(
                        "La fecha de vencimiento debe ser posterior a la fecha de inicio (RN13).",
                        code="FECHAS_SUSCRIPCION_INVALIDAS",
                    )
                venc_anterior = susc.fecha_vencimiento.isoformat()
                susc.fecha_inicio = nueva_inicio
                susc.fecha_vencimiento = datos.fecha_vencimiento
                susc.estado = datos.estado or "activa"
                SuscripcionesAdminRepositorio.registrar_evento_historial(
                    db,
                    id_tenant=id_tenant,
                    id_suscripcion=susc.id_suscripcion,
                    evento="renovacion",
                    detalle={
                        "plan": plan_final.nombre,
                        "vencimiento_anterior": venc_anterior,
                        "fecha_vencimiento": datos.fecha_vencimiento.isoformat(),
                        "motivo": datos.motivo,
                    },
                    id_usuario=usuario_actual.id_usuario,
                )

            elif operacion == "suspension":
                estado_previo = susc.estado
                susc.estado = "suspendida"
                SuscripcionesAdminRepositorio.registrar_evento_historial(
                    db,
                    id_tenant=id_tenant,
                    id_suscripcion=susc.id_suscripcion,
                    evento="suspension",
                    detalle={"estado_anterior": estado_previo, "motivo": datos.motivo},
                    id_usuario=usuario_actual.id_usuario,
                )

            elif operacion == "reactivacion":
                if datos.fecha_vencimiento is not None:
                    nueva_inicio = datos.fecha_inicio or susc.fecha_inicio
                    if datos.fecha_vencimiento <= nueva_inicio:
                        raise UnprocessableEntityError(
                            "La fecha de vencimiento debe ser posterior a la fecha de inicio (RN13).",
                            code="FECHAS_SUSCRIPCION_INVALIDAS",
                        )
                    susc.fecha_inicio = nueva_inicio
                    susc.fecha_vencimiento = datos.fecha_vencimiento
                estado_previo = susc.estado
                susc.estado = datos.estado or "activa"
                SuscripcionesAdminRepositorio.registrar_evento_historial(
                    db,
                    id_tenant=id_tenant,
                    id_suscripcion=susc.id_suscripcion,
                    evento="reactivacion",
                    detalle={
                        "estado_anterior": estado_previo,
                        "estado_nuevo": susc.estado,
                        "fecha_vencimiento": susc.fecha_vencimiento.isoformat(),
                        "motivo": datos.motivo,
                    },
                    id_usuario=usuario_actual.id_usuario,
                )

            elif operacion == "cancelacion":
                estado_previo = susc.estado
                susc.estado = "cancelada"
                SuscripcionesAdminRepositorio.registrar_evento_historial(
                    db,
                    id_tenant=id_tenant,
                    id_suscripcion=susc.id_suscripcion,
                    evento="cancelacion",
                    detalle={"estado_anterior": estado_previo, "motivo": datos.motivo},
                    id_usuario=usuario_actual.id_usuario,
                )

            db.commit()
            db.refresh(susc)

        limpiar_cache_tenants()
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion=f"SUSCRIPCION_{operacion.upper()}",
            tabla_modulo="plataforma.suscripciones",
            direccion_ip=direccion_ip,
            severidad="WARN" if operacion in ("suspension", "cancelacion") else "INFO",
            payload_nuevo={
                "id_tenant": tenant.id_tenant,
                "codigo_empresa": tenant.codigo,
                "id_suscripcion": susc.id_suscripcion,
                "operacion": operacion,
                "id_plan": plan_final.id_plan,
                "plan": plan_final.nombre,
                "estado": susc.estado,
                "fecha_vencimiento": susc.fecha_vencimiento.isoformat(),
            },
            db=db,
        )
        return SuscripcionesAdminServicio._armar_suscripcion_out(db, susc, tenant, plan_final, hoy_bolivia)

