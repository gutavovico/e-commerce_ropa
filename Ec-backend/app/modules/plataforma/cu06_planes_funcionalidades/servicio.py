"""Servicio de aplicación y dominio para P2-CU06: Gestionar planes y funcionalidades."""

from typing import Optional

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from core.tiempo import hoy
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu06_planes_funcionalidades.esquemas import (
    CambiarEstadoPlanIn,
    FuncionalidadOut,
    PlanActualizarIn,
    PlanCrearIn,
    PlanDetalleOut,
)
from modules.plataforma.cu06_planes_funcionalidades.repositorio import PlanesFuncionalidadesRepositorio
from modules.plataforma.modelos import PlanORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class PlanesFuncionalidadesServicio:
    """Casos de uso de gestión de planes de suscripción y catálogo de funcionalidades."""

    @staticmethod
    def _armar_plan_detalle(
        db: Session,
        plan: PlanORM,
        *,
        advertencias: Optional[list[str]] = None,
    ) -> PlanDetalleOut:
        hoy_bolivia = hoy()
        funcs = PlanesFuncionalidadesRepositorio.funcionalidades_de_plan(db, plan.id_plan)
        vigentes, totales = PlanesFuncionalidadesRepositorio.contar_empresas_del_plan(
            db, plan.id_plan, hoy_bolivia
        )
        return PlanDetalleOut(
            id_plan=plan.id_plan,
            nombre=plan.nombre,
            precio_mensual=plan.precio_mensual,
            max_sucursales_activas=plan.max_sucursales_activas,
            max_empleados=plan.max_empleados,
            activo=plan.activo,
            creado_en=plan.creado_en,
            funcionalidades=[FuncionalidadOut.model_validate(f) for f in funcs],
            codigos_funcionalidades=[f.codigo for f in funcs],
            empresas_suscritas_vigentes=vigentes,
            empresas_suscritas_totales=totales,
            advertencias=advertencias or [],
        )

    @staticmethod
    def _validar_funcionalidades_existentes(db: Session, codigos: list[str]) -> None:
        catalogo = {
            f.codigo for f in PlanesFuncionalidadesRepositorio.listar_funcionalidades(db)
        }
        desconocidas = [c for c in codigos if c not in catalogo]
        if desconocidas:
            raise UnprocessableEntityError(
                f"Las siguientes funcionalidades no existen en el catálogo: {', '.join(desconocidas)} (RN11).",
                code="FUNCIONALIDAD_DESCONOCIDA",
            )

    @staticmethod
    def listar_funcionalidades(db: Session) -> list[FuncionalidadOut]:
        funcs = PlanesFuncionalidadesRepositorio.listar_funcionalidades(db)
        return [FuncionalidadOut.model_validate(f) for f in funcs]

    @staticmethod
    def listar_planes(db: Session, *, solo_activos: bool = False) -> list[PlanDetalleOut]:
        planes = PlanesFuncionalidadesRepositorio.listar_planes(db, solo_activos=solo_activos)
        return [PlanesFuncionalidadesServicio._armar_plan_detalle(db, p) for p in planes]

    @staticmethod
    def crear_plan(
        db: Session,
        datos: PlanCrearIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> PlanDetalleOut:
        nombre_norm = datos.nombre.strip()
        if PlanesFuncionalidadesRepositorio.buscar_por_nombre(db, nombre_norm) is not None:
            raise ConflictError(
                f"Ya existe un plan con el nombre '{nombre_norm}'.",
                code="PLAN_NOMBRE_OCUPADO",
            )

        PlanesFuncionalidadesServicio._validar_funcionalidades_existentes(
            db, datos.funcionalidades
        )

        plan = PlanesFuncionalidadesRepositorio.crear_plan(
            db,
            nombre=nombre_norm,
            precio_mensual=datos.precio_mensual,
            max_sucursales_activas=datos.max_sucursales_activas,
            max_empleados=datos.max_empleados,
            codigos_funcionalidades=datos.funcionalidades,
        )

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="CREAR_PLAN",
            tabla_modulo="plataforma.planes",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_plan": plan.id_plan,
                "nombre": plan.nombre,
                "precio_mensual": str(plan.precio_mensual),
                "max_sucursales_activas": plan.max_sucursales_activas,
                "max_empleados": plan.max_empleados,
                "funcionalidades": datos.funcionalidades,
            },
            db=db,
        )
        return PlanesFuncionalidadesServicio._armar_plan_detalle(db, plan)

    @staticmethod
    def actualizar_plan(
        db: Session,
        id_plan: int,
        datos: PlanActualizarIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> PlanDetalleOut:
        plan = PlanesFuncionalidadesRepositorio.obtener_plan(db, id_plan)
        if not plan:
            raise NotFoundError(
                f"El plan con identificador {id_plan} no existe.",
                code="PLAN_NO_ENCONTRADO",
            )

        nombre_norm = datos.nombre.strip()
        if (
            PlanesFuncionalidadesRepositorio.buscar_por_nombre(
                db, nombre_norm, excluir_id_plan=id_plan
            )
            is not None
        ):
            raise ConflictError(
                f"Ya existe otro plan con el nombre '{nombre_norm}'.",
                code="PLAN_NOMBRE_OCUPADO",
            )

        PlanesFuncionalidadesServicio._validar_funcionalidades_existentes(
            db, datos.funcionalidades
        )

        # Curso Alterno A1: verificar si empresas con suscripción activa quedan por encima del nuevo límite
        advertencias: list[str] = []
        empresas_plan = PlanesFuncionalidadesRepositorio.empresas_con_suscripcion_activa_en_plan(
            db, id_plan
        )
        for emp in empresas_plan:
            suc_activas, emp_activos = PlanesFuncionalidadesRepositorio.uso_recursos_empresa(
                db, emp.id_tenant
            )
            if suc_activas > datos.max_sucursales_activas:
                advertencias.append(
                    f"La empresa '{emp.nombre}' ({emp.codigo}) tiene {suc_activas} sucursales activas "
                    f"(nuevo límite: {datos.max_sucursales_activas}). No podrá activar nuevas sucursales."
                )
            if datos.max_empleados is not None and emp_activos > datos.max_empleados:
                advertencias.append(
                    f"La empresa '{emp.nombre}' ({emp.codigo}) tiene {emp_activos} empleados activos "
                    f"(nuevo límite: {datos.max_empleados}). No podrá dar de alta nuevos empleados."
                )

        anterior = {
            "nombre": plan.nombre,
            "precio_mensual": str(plan.precio_mensual),
            "max_sucursales_activas": plan.max_sucursales_activas,
            "max_empleados": plan.max_empleados,
        }
        plan_actualizado = PlanesFuncionalidadesRepositorio.actualizar_plan(
            db,
            plan,
            nombre=nombre_norm,
            precio_mensual=datos.precio_mensual,
            max_sucursales_activas=datos.max_sucursales_activas,
            max_empleados=datos.max_empleados,
            codigos_funcionalidades=datos.funcionalidades,
        )

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTUALIZAR_PLAN",
            tabla_modulo="plataforma.planes",
            direccion_ip=direccion_ip,
            severidad="WARN" if advertencias else "INFO",
            payload_anterior=anterior,
            payload_nuevo={
                "id_plan": plan_actualizado.id_plan,
                "nombre": plan_actualizado.nombre,
                "precio_mensual": str(plan_actualizado.precio_mensual),
                "max_sucursales_activas": plan_actualizado.max_sucursales_activas,
                "max_empleados": plan_actualizado.max_empleados,
                "funcionalidades": datos.funcionalidades,
                "advertencias": advertencias,
            },
            db=db,
        )
        return PlanesFuncionalidadesServicio._armar_plan_detalle(
            db, plan_actualizado, advertencias=advertencias
        )

    @staticmethod
    def cambiar_estado_plan(
        db: Session,
        id_plan: int,
        datos: CambiarEstadoPlanIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> PlanDetalleOut:
        plan = PlanesFuncionalidadesRepositorio.obtener_plan(db, id_plan)
        if not plan:
            raise NotFoundError(
                f"El plan con identificador {id_plan} no existe.",
                code="PLAN_NO_ENCONTRADO",
            )

        if not datos.activo:
            empresas_activas = PlanesFuncionalidadesRepositorio.empresas_con_suscripcion_activa_en_plan(db, id_plan)
            if empresas_activas:
                raise ConflictError(
                    f"No se puede desactivar el plan '{plan.nombre}' porque existen {len(empresas_activas)} empresa(s) con suscripciones vigentes (CU06 A2).",
                    code="PLAN_CON_EMPRESAS_SUSCRITAS",
                )

        anterior = plan.activo
        plan.activo = datos.activo
        db.commit()
        db.refresh(plan)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTIVAR_PLAN" if datos.activo else "DESACTIVAR_PLAN",
            tabla_modulo="plataforma.planes",
            direccion_ip=direccion_ip,
            severidad="INFO" if datos.activo else "WARN",
            payload_anterior={"id_plan": plan.id_plan, "activo": anterior},
            payload_nuevo={"id_plan": plan.id_plan, "activo": plan.activo},
            db=db,
        )
        return PlanesFuncionalidadesServicio._armar_plan_detalle(db, plan)

