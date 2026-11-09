"""Router FastAPI para P2-CU05: Gestionar empresas y supervisar la plataforma."""

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu05_empresas_supervision.esquemas import (
    BitacoraPlataformaListadoOut,
    CambiarEstadoEmpresaIn,
    EmpresaActualizarIn,
    EmpresaCrearIn,
    EmpresaDetalleOut,
    EmpresaResumenOut,
    MetricasPlataformaOut,
)
from modules.plataforma.cu05_empresas_supervision.servicio import EmpresasSupervisionServicio
from modules.plataforma.dependencias import exigir_super_administrador

router = APIRouter(tags=["Plataforma - Empresas y Supervisión (P2-CU05)"])


def _ip_cliente(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


@router.get(
    "/empresas",
    response_model=list[EmpresaResumenOut],
    summary="Listar empresas registradas con sus indicadores e información de suscripción",
)
def listar_empresas(
    q: Optional[str] = Query(default=None, description="Búsqueda por código, nombre o correo"),
    estado: Optional[Literal["activa", "suspendida", "baja"]] = Query(default=None),
    id_plan: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[EmpresaResumenOut]:
    return EmpresasSupervisionServicio.listar_empresas(db, q=q, estado=estado, id_plan=id_plan)


@router.post(
    "/empresas",
    response_model=EmpresaDetalleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una nueva empresa con su suscripción y administrador inicial",
)
def registrar_empresa(
    datos: EmpresaCrearIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EmpresaDetalleOut:
    return EmpresasSupervisionServicio.registrar_empresa(
        db, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.get(
    "/empresas/{id_tenant}",
    response_model=EmpresaDetalleOut,
    summary="Obtener el detalle y los indicadores agregados de una empresa",
)
def obtener_empresa(
    id_tenant: int,
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EmpresaDetalleOut:
    return EmpresasSupervisionServicio.obtener_empresa(db, id_tenant)


@router.put(
    "/empresas/{id_tenant}",
    response_model=EmpresaDetalleOut,
    summary="Actualizar los datos generales de una empresa",
)
def actualizar_empresa(
    id_tenant: int,
    datos: EmpresaActualizarIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EmpresaDetalleOut:
    return EmpresasSupervisionServicio.actualizar_empresa(
        db, id_tenant, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.patch(
    "/empresas/{id_tenant}/estado",
    response_model=EmpresaDetalleOut,
    summary="Suspender, reactivar o dar de baja una empresa (RN08, RN09, RN10)",
)
def cambiar_estado_empresa(
    id_tenant: int,
    datos: CambiarEstadoEmpresaIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EmpresaDetalleOut:
    return EmpresasSupervisionServicio.cambiar_estado_empresa(
        db, id_tenant, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.get(
    "/metricas",
    response_model=MetricasPlataformaOut,
    summary="Consultar métricas globales de supervisión de la plataforma SaaS",
)
def obtener_metricas_plataforma(
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> MetricasPlataformaOut:
    return EmpresasSupervisionServicio.obtener_metricas_plataforma(db)


@router.get(
    "/bitacora",
    response_model=BitacoraPlataformaListadoOut,
    summary="Consultar bitácora global de eventos de plataforma y empresas",
)
def listar_bitacora_plataforma(
    id_tenant: Optional[int] = Query(default=None, gt=0),
    solo_plataforma: bool = Query(default=False),
    severidad: Optional[str] = Query(default=None),
    accion: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> BitacoraPlataformaListadoOut:
    return EmpresasSupervisionServicio.listar_bitacora(
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

