"""Router FastAPI para P2-CU06: Gestionar planes y funcionalidades."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu06_planes_funcionalidades.esquemas import (
    CambiarEstadoPlanIn,
    FuncionalidadOut,
    PlanActualizarIn,
    PlanCrearIn,
    PlanDetalleOut,
)
from modules.plataforma.cu06_planes_funcionalidades.servicio import PlanesFuncionalidadesServicio
from modules.plataforma.dependencias import exigir_super_administrador

router = APIRouter(tags=["Plataforma - Planes y Funcionalidades (P2-CU06)"])


def _ip_cliente(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


@router.get(
    "/funcionalidades",
    response_model=list[FuncionalidadOut],
    summary="Listar el catálogo de funcionalidades de la plataforma (RN11)",
)
def listar_funcionalidades(
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[FuncionalidadOut]:
    return PlanesFuncionalidadesServicio.listar_funcionalidades(db)


@router.get(
    "/planes",
    response_model=list[PlanDetalleOut],
    summary="Listar los planes de suscripción con sus límites y funcionalidades",
)
def listar_planes(
    solo_activos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[PlanDetalleOut]:
    return PlanesFuncionalidadesServicio.listar_planes(db, solo_activos=solo_activos)


@router.post(
    "/planes",
    response_model=PlanDetalleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo plan de suscripción (RN11, RN12)",
)
def crear_plan(
    datos: PlanCrearIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> PlanDetalleOut:
    return PlanesFuncionalidadesServicio.crear_plan(
        db, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.put(
    "/planes/{id_plan}",
    response_model=PlanDetalleOut,
    summary="Editar un plan de suscripción existente y evaluar advertencias de límites (CU06 A1)",
)
def actualizar_plan(
    id_plan: int,
    datos: PlanActualizarIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> PlanDetalleOut:
    return PlanesFuncionalidadesServicio.actualizar_plan(
        db, id_plan, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.patch(
    "/planes/{id_plan}/estado",
    response_model=PlanDetalleOut,
    summary="Activar o desactivar un plan para nuevas suscripciones (CU06 A2)",
)
def cambiar_estado_plan(
    id_plan: int,
    datos: CambiarEstadoPlanIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> PlanDetalleOut:
    return PlanesFuncionalidadesServicio.cambiar_estado_plan(
        db, id_plan, datos, usuario, direccion_ip=_ip_cliente(request)
    )

