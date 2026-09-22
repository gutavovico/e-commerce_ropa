"""Router REST para CU30: Consultar bitacora.

Expone endpoints administrativos en /admin/bitacora protegidos por RBAC.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.seguridad.cu30_bitacora.esquemas import (
    BitacoraEventoDetalle,
    BitacoraFiltrosParametros,
    BitacoraListadoRespuesta,
    OrdenarPorBitacora,
    SeveridadEnum,
)
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

router = APIRouter(prefix="/admin/bitacora", tags=["Admin - Bitacora y Auditoria"])


@router.get(
    "",
    response_model=BitacoraListadoRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Listar eventos de bitacora con metricas (Admin)",
    description="Permite a los superadministradores consultar la bitacora de auditoria con filtros y metricas consolidadas.",
)
def listar_bitacora(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial en formato YYYY-MM-DD"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final en formato YYYY-MM-DD"),
    severidad: Optional[SeveridadEnum] = Query(None, description="Filtrar por severidad (INFO, WARN, ERROR, CRITICAL)"),
    tabla_modulo: Optional[str] = Query(None, description="Filtrar por modulo o tabla afectada"),
    accion: Optional[str] = Query(None, description="Filtrar por accion ejecutada"),
    q: Optional[str] = Query(None, description="Busqueda de texto en usuario, accion, modulo o IP"),
    ordenar_por: OrdenarPorBitacora = Query("creado_en_desc", description="Criterio de ordenacion"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(20, ge=1, le=100, description="Cantidad de registros por pagina"),
    db: Session = Depends(get_db),
    usuario_actual: UsuarioORM = Depends(get_current_user),
) -> BitacoraListadoRespuesta:
    filtros = BitacoraFiltrosParametros(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        severidad=severidad,
        tabla_modulo=tabla_modulo,
        accion=accion,
        q=q,
        ordenar_por=ordenar_por,
        pagina=pagina,
        limite=limite,
    )
    return ServicioBitacoraAuditoria.listar_eventos(
        db=db,
        filtros=filtros,
        usuario_actual=usuario_actual,
    )


@router.get(
    "/{id_bitacora}",
    response_model=BitacoraEventoDetalle,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de evento de bitacora (Admin)",
    description="Retorna el registro completo de un evento de auditoria incluyendo los snapshots JSON de payload.",
)
def obtener_evento_bitacora(
    id_bitacora: int = Path(..., ge=1, description="ID del evento de bitacora"),
    db: Session = Depends(get_db),
    usuario_actual: UsuarioORM = Depends(get_current_user),
) -> BitacoraEventoDetalle:
    return ServicioBitacoraAuditoria.obtener_evento_por_id(
        db=db,
        id_bitacora=id_bitacora,
        usuario_actual=usuario_actual,
    )
