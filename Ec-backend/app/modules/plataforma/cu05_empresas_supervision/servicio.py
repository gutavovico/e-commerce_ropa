"""Servicio de aplicación y dominio para P2-CU05: Gestionar empresas y supervisar la plataforma."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from core.security import hash_password
from core.tenant import limpiar_cache_tenants
from core.tiempo import hoy
from modules.autenticacion_seguridad.cuentas import correo_ocupado
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu05_empresas_supervision.esquemas import (
    BitacoraPlataformaItemOut,
    BitacoraPlataformaListadoOut,
    CambiarEstadoEmpresaIn,
    CODIGOS_RESERVADOS_EMPRESA,
    EmpresaActualizarIn,
    EmpresaCrearIn,
    EmpresaDetalleOut,
    EmpresaResumenOut,
    IndicadoresEmpresaOut,
    MetricasPlataformaOut,
    MetricasPorEmpresaItem,
    SuscripcionResumenEmpresaOut,
)
from modules.plataforma.cu05_empresas_supervision.repositorio import EmpresasSupervisionRepositorio
from modules.plataforma.modelos import PlanORM, SuscripcionORM, TenantORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


def _es_suscripcion_vigente(suscripcion: SuscripcionORM, hoy: date) -> bool:
    return (
        suscripcion.estado in ("prueba", "activa")
        and suscripcion.fecha_inicio <= hoy <= suscripcion.fecha_vencimiento
    )


def _construir_suscripcion_out(
    par: Optional[tuple[SuscripcionORM, PlanORM]], hoy: date
) -> Optional[SuscripcionResumenEmpresaOut]:
    if not par:
        return None
    susc, plan = par
    return SuscripcionResumenEmpresaOut(
        id_suscripcion=susc.id_suscripcion,
        id_plan=plan.id_plan,
        nombre_plan=plan.nombre,
        estado=susc.estado,
        fecha_inicio=susc.fecha_inicio,
        fecha_vencimiento=susc.fecha_vencimiento,
        vigente=_es_suscripcion_vigente(susc, hoy),
    )


class EmpresasSupervisionServicio:
    """Casos de uso de registro de empresas, supervisión de métricas y bitácora global."""

    @staticmethod
    def _armar_resumen(db: Session, tenant: TenantORM, hoy: date) -> EmpresaResumenOut:
        par_susc = EmpresasSupervisionRepositorio.suscripcion_mas_reciente(db, tenant.id_tenant)
        ind_dict = EmpresasSupervisionRepositorio.indicadores_empresa(db, tenant.id_tenant)
        return EmpresaResumenOut(
            id_tenant=tenant.id_tenant,
            codigo=tenant.codigo,
            nombre=tenant.nombre,
            correo_contacto=tenant.correo_contacto,
            telefono=tenant.telefono,
            estado=tenant.estado,
            creado_en=tenant.creado_en,
            suscripcion_actual=_construir_suscripcion_out(par_susc, hoy),
            indicadores=IndicadoresEmpresaOut(**ind_dict),
        )

    @staticmethod
    def _armar_detalle(db: Session, tenant: TenantORM, hoy: date) -> EmpresaDetalleOut:
        resumen = EmpresasSupervisionServicio._armar_resumen(db, tenant, hoy)
        admin = EmpresasSupervisionRepositorio.admin_principal_empresa(db, tenant.id_tenant)
        admin_nombre = f"{admin.nombres} {admin.apellidos}".strip() if admin else None
        return EmpresaDetalleOut(
            **resumen.model_dump(),
            admin_email=admin.email if admin else None,
            admin_nombre=admin_nombre,
        )

    @staticmethod
    def listar_empresas(
        db: Session,
        *,
        q: Optional[str] = None,
        estado: Optional[str] = None,
        id_plan: Optional[int] = None,
    ) -> list[EmpresaResumenOut]:
        hoy_bolivia = hoy()
        tenants = EmpresasSupervisionRepositorio.listar_tenants(
            db, q=q, estado=estado, id_plan=id_plan
        )
        return [EmpresasSupervisionServicio._armar_resumen(db, t, hoy_bolivia) for t in tenants]

    @staticmethod
    def obtener_empresa(db: Session, id_tenant: int) -> EmpresaDetalleOut:
        tenant = EmpresasSupervisionRepositorio.obtener_tenant(db, id_tenant)
        if not tenant:
            raise NotFoundError(
                f"La empresa con identificador {id_tenant} no existe.",
                code="EMPRESA_NO_ENCONTRADA",
            )
        hoy_bolivia = hoy()
        return EmpresasSupervisionServicio._armar_detalle(db, tenant, hoy_bolivia)

    @staticmethod
    def registrar_empresa(
        db: Session,
        datos: EmpresaCrearIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> EmpresaDetalleOut:
        codigo_norm = datos.codigo.strip().lower()
        if codigo_norm in CODIGOS_RESERVADOS_EMPRESA:
            raise UnprocessableEntityError(
                f"El código '{codigo_norm}' está reservado por la plataforma y no puede usarse para una empresa.",
                code="CODIGO_EMPRESA_RESERVADO",
            )

        if EmpresasSupervisionRepositorio.buscar_por_codigo(db, codigo_norm) is not None:
            raise ConflictError(
                f"Ya existe una empresa registrada con el código '{codigo_norm}' (RN03).",
                code="CODIGO_EMPRESA_OCUPADO",
            )

        plan = EmpresasSupervisionRepositorio.obtener_plan(db, datos.id_plan)
        if not plan:
            raise NotFoundError(
                f"El plan con identificador {datos.id_plan} no existe.",
                code="PLAN_NO_ENCONTRADO",
            )
        if not plan.activo:
            raise ConflictError(
                f"El plan '{plan.nombre}' se encuentra inactivo y no admite nuevas suscripciones.",
                code="PLAN_INACTIVO",
            )

        admin_email = str(datos.admin_inicial.email).strip().lower()
        if correo_ocupado(db, admin_email):
            raise ConflictError(
                f"El correo electrónico '{admin_email}' ya está ocupado en la plataforma (RN05).",
                code="CORREO_OCUPADO",
            )

        password_hash = hash_password(datos.admin_inicial.password)
        tenant, suscripcion, admin_usuario = EmpresasSupervisionRepositorio.crear_empresa_atomica(
            db,
            codigo=codigo_norm,
            nombre=datos.nombre.strip(),
            correo_contacto=str(datos.correo_contacto).strip().lower() if datos.correo_contacto else None,
            telefono=datos.telefono.strip() if datos.telefono else None,
            plan=plan,
            estado_suscripcion=datos.estado_suscripcion,
            fecha_inicio=datos.fecha_inicio,
            fecha_vencimiento=datos.fecha_vencimiento,
            admin_nombres=datos.admin_inicial.nombres.strip(),
            admin_apellidos=datos.admin_inicial.apellidos.strip(),
            admin_email=admin_email,
            admin_password_hash=password_hash,
            admin_telefono=datos.admin_inicial.telefono.strip() if datos.admin_inicial.telefono else None,
            id_usuario_operador=usuario_actual.id_usuario,
        )
        limpiar_cache_tenants()

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ALTA_EMPRESA",
            tabla_modulo="plataforma.tenants",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_tenant": tenant.id_tenant,
                "codigo": tenant.codigo,
                "nombre": tenant.nombre,
                "id_plan": plan.id_plan,
                "plan": plan.nombre,
                "estado_suscripcion": suscripcion.estado,
                "admin_email": admin_usuario.email,
            },
            db=db,
        )

        hoy_bolivia = hoy()
        return EmpresasSupervisionServicio._armar_detalle(db, tenant, hoy_bolivia)

    @staticmethod
    def actualizar_empresa(
        db: Session,
        id_tenant: int,
        datos: EmpresaActualizarIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> EmpresaDetalleOut:
        tenant = EmpresasSupervisionRepositorio.obtener_tenant(db, id_tenant)
        if not tenant:
            raise NotFoundError(
                f"La empresa con identificador {id_tenant} no existe.",
                code="EMPRESA_NO_ENCONTRADA",
            )

        anterior = {
            "nombre": tenant.nombre,
            "correo_contacto": tenant.correo_contacto,
            "telefono": tenant.telefono,
        }
        tenant.nombre = datos.nombre.strip()
        tenant.correo_contacto = (
            str(datos.correo_contacto).strip().lower() if datos.correo_contacto else None
        )
        tenant.telefono = datos.telefono.strip() if datos.telefono else None
        db.commit()
        db.refresh(tenant)
        limpiar_cache_tenants()

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTUALIZAR_EMPRESA",
            tabla_modulo="plataforma.tenants",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_anterior=anterior,
            payload_nuevo={
                "id_tenant": tenant.id_tenant,
                "nombre": tenant.nombre,
                "correo_contacto": tenant.correo_contacto,
                "telefono": tenant.telefono,
            },
            db=db,
        )
        hoy_bolivia = hoy()
        return EmpresasSupervisionServicio._armar_detalle(db, tenant, hoy_bolivia)

    @staticmethod
    def cambiar_estado_empresa(
        db: Session,
        id_tenant: int,
        datos: CambiarEstadoEmpresaIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> EmpresaDetalleOut:
        tenant = EmpresasSupervisionRepositorio.obtener_tenant(db, id_tenant)
        if not tenant:
            raise NotFoundError(
                f"La empresa con identificador {id_tenant} no existe.",
                code="EMPRESA_NO_ENCONTRADA",
            )

        estado_anterior = tenant.estado
        nuevo_estado = datos.estado

        # Curso Alterno A2 (RN10): dar de baja exige que esté suspendida previamente
        if nuevo_estado == "baja" and estado_anterior != "suspendida":
            raise ConflictError(
                "Para dar de baja una empresa primero debe encontrarse en estado suspendida (RN10).",
                code="BAJA_REQUIERE_SUSPENSION_PREVIA",
            )

        tenant.estado = nuevo_estado
        db.commit()
        db.refresh(tenant)
        limpiar_cache_tenants()

        severidad = "WARN" if nuevo_estado in ("suspendida", "baja") else "INFO"
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion=f"CAMBIO_ESTADO_EMPRESA_{nuevo_estado.upper()}",
            tabla_modulo="plataforma.tenants",
            direccion_ip=direccion_ip,
            severidad=severidad,
            payload_anterior={"id_tenant": tenant.id_tenant, "estado": estado_anterior},
            payload_nuevo={
                "id_tenant": tenant.id_tenant,
                "estado": nuevo_estado,
                "motivo": datos.motivo,
            },
            db=db,
        )
        hoy_bolivia = hoy()
        return EmpresasSupervisionServicio._armar_detalle(db, tenant, hoy_bolivia)

    @staticmethod
    def obtener_metricas_plataforma(db: Session) -> MetricasPlataformaOut:
        hoy_bolivia = hoy()
        tenants = EmpresasSupervisionRepositorio.listar_tenants(db)

        empresas_activas = sum(1 for t in tenants if t.estado == "activa")
        empresas_suspendidas = sum(1 for t in tenants if t.estado == "suspendida")
        empresas_baja = sum(1 for t in tenants if t.estado == "baja")

        suscripciones_vigentes = 0
        suscripciones_no_vigentes = 0
        sucursales_activas_tot = 0
        empleados_activos_tot = 0
        ventas_pagadas_tot = 0
        monto_ventas_tot = Decimal("0.00")
        desglose: list[MetricasPorEmpresaItem] = []

        for t in tenants:
            par_susc = EmpresasSupervisionRepositorio.suscripcion_mas_reciente(db, t.id_tenant)
            ind = EmpresasSupervisionRepositorio.indicadores_empresa(db, t.id_tenant)
            nombre_plan: Optional[str] = None
            estado_susc: Optional[str] = None
            if par_susc:
                susc, plan = par_susc
                nombre_plan = plan.nombre
                estado_susc = susc.estado
                if _es_suscripcion_vigente(susc, hoy_bolivia):
                    suscripciones_vigentes += 1
                else:
                    suscripciones_no_vigentes += 1
            else:
                suscripciones_no_vigentes += 1

            sucursales_activas_tot += ind["sucursales_activas"]
            empleados_activos_tot += ind["empleados_activos"]
            ventas_pagadas_tot += ind["ventas_pagadas_cantidad"]
            monto_ventas_tot += ind["ventas_pagadas_monto"]

            desglose.append(
                MetricasPorEmpresaItem(
                    id_tenant=t.id_tenant,
                    codigo=t.codigo,
                    nombre=t.nombre,
                    estado_empresa=t.estado,
                    nombre_plan=nombre_plan,
                    estado_suscripcion=estado_susc,
                    sucursales_activas=ind["sucursales_activas"],
                    empleados_activos=ind["empleados_activos"],
                    productos_activos=ind["productos_activos"],
                    ventas_pagadas_cantidad=ind["ventas_pagadas_cantidad"],
                    ventas_pagadas_monto=ind["ventas_pagadas_monto"],
                )
            )

        return MetricasPlataformaOut(
            empresas_totales=len(tenants),
            empresas_activas=empresas_activas,
            empresas_suspendidas=empresas_suspendidas,
            empresas_baja=empresas_baja,
            suscripciones_vigentes=suscripciones_vigentes,
            suscripciones_vencidas_o_suspendidas=suscripciones_no_vigentes,
            sucursales_activas_totales=sucursales_activas_tot,
            empleados_activos_totales=empleados_activos_tot,
            ventas_pagadas_totales=ventas_pagadas_tot,
            monto_ventas_pagadas_total=monto_ventas_tot,
            desglose_empresas=desglose,
        )

    @staticmethod
    def listar_bitacora(
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
    ) -> BitacoraPlataformaListadoOut:
        filas, total = EmpresasSupervisionRepositorio.listar_bitacora_plataforma(
            db,
            id_tenant=id_tenant,
            solo_plataforma=solo_plataforma,
            severidad=severidad,
            accion=accion,
            q=q,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            pagina=pagina,
            limite=limite,
        )
        total_paginas = max(1, (total + limite - 1) // limite)
        items = [
            BitacoraPlataformaItemOut(
                id_bitacora=b.id_bitacora,
                id_tenant=b.id_tenant,
                codigo_empresa=t.codigo if t else None,
                nombre_empresa=t.nombre if t else None,
                id_usuario=b.id_usuario,
                usuario_nombre=b.usuario_nombre,
                accion=b.accion,
                tabla_modulo=b.tabla_modulo,
                direccion_ip=b.direccion_ip,
                severidad=b.severidad,
                tiene_payload=bool(b.payload_anterior or b.payload_nuevo),
                payload_anterior=b.payload_anterior,
                payload_nuevo=b.payload_nuevo,
                creado_en=b.creado_en,
            )
            for b, t in filas
        ]
        return BitacoraPlataformaListadoOut(
            items=items,
            total=total,
            pagina=pagina,
            limite=limite,
            total_paginas=total_paginas,
        )

