"""Router FastAPI para P2-CU07: Gestionar suscripciones de empresas."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu07_suscripciones.esquemas import (
    HistorialSuscripcionItemOut,
    OperacionSuscripcionIn,
    SuscripcionEmpresaOut,
)
from modules.plataforma.cu07_suscripciones.servicio import SuscripcionesAdminServicio
from modules.plataforma.dependencias import exigir_super_administrador

router = APIRouter(tags=["Plataforma - Suscripciones de Empresas (P2-CU07)"])


def _ip_cliente(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


@router.get(
    "/suscripciones",
    response_model=list[SuscripcionEmpresaOut],
    summary="Listar las suscripciones de todas las empresas con uso de recursos y vigencia",
)
def listar_suscripciones(
    estado: Optional[Literal["prueba", "activa", "vencida", "suspendida", "cancelada"]] = Query(
        default=None
    ),
    id_plan: Optional[int] = Query(default=None, gt=0),
    id_tenant: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[SuscripcionEmpresaOut]:
    return SuscripcionesAdminServicio.listar_suscripciones(
        db, estado=estado, id_plan=id_plan, id_tenant=id_tenant
    )


@router.get(
    "/empresas/{id_tenant}/suscripciones/historial",
    response_model=list[HistorialSuscripcionItemOut],
    summary="Consultar el historial de eventos de suscripción de una empresa (RN17)",
)
def listar_historial_suscripcion(
    id_tenant: int,
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[HistorialSuscripcionItemOut]:
    return SuscripcionesAdminServicio.listar_historial(db, id_tenant)


@router.post(
    "/empresas/{id_tenant}/suscripcion",
    response_model=SuscripcionEmpresaOut,
    summary="Ejecutar una operación sobre la suscripción de una empresa (RN13-RN17)",
)
def operar_suscripcion_empresa(
    id_tenant: int,
    datos: OperacionSuscripcionIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> SuscripcionEmpresaOut:
    return SuscripcionesAdminServicio.operar_suscripcion(
        db, id_tenant, datos, usuario, direccion_ip=_ip_cliente(request)
    )

