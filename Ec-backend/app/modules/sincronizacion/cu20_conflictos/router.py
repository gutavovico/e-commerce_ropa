"""Router de P2-CU20 · Resolver conflictos de sincronización. Solo HTTP.

Administrador y encargado de sucursal; el cajero no (su único espacio es la caja). El cierre de mes
es solo del administrador (decisión D2).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.sincronizacion.cu20_conflictos.esquemas import (
    CierreIn,
    CierreOut,
    ConflictoDetalleOut,
    ConflictoResumenOut,
    EstadoCierreOut,
    ResumenConflictosOut,
)
from modules.sincronizacion.cu20_conflictos.servicio import ConflictosServicio

router = APIRouter(prefix="/conflictos-sync", tags=["P2-CU20 Conflictos de sincronización"])

_gestion = require_roles(["administrador", "encargado_sucursal"])
_admin = require_roles(["administrador"])


@router.get("", response_model=List[ConflictoResumenOut], summary="Conflictos de sincronización")
def listar(
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_gestion),
) -> List[ConflictoResumenOut]:
    return ConflictosServicio.listar(db, usuario, estado)


@router.get("/resumen", response_model=ResumenConflictosOut, summary="Conflictos por estado (contador del panel)")
def resumen(db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_gestion)) -> ResumenConflictosOut:
    return ConflictosServicio.resumen(db, usuario)


@router.get("/cierre", response_model=EstadoCierreOut, summary="Si hoy es el último día del mes y cuántos hay por reembolsar")
def estado_cierre(db: Session = Depends(get_db), _usuario: UsuarioORM = Depends(_admin)) -> EstadoCierreOut:
    return ConflictosServicio.estado_cierre(db)


@router.post("/procesar-cierre", response_model=CierreOut, summary="Procesar los reembolsos del cierre de mes")
def procesar_cierre(
    datos: CierreIn, db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_admin)
) -> CierreOut:
    return ConflictosServicio.procesar_cierre(db, usuario, forzar=datos.forzar)


@router.get("/{id_conflicto}", response_model=ConflictoDetalleOut, summary="Detalle de un conflicto")
def detalle(
    id_conflicto: int, db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_gestion)
) -> ConflictoDetalleOut:
    return ConflictosServicio.detalle(db, usuario, id_conflicto)


@router.post("/{id_conflicto}/aceptar-reembolso", response_model=ConflictoDetalleOut, summary="Aceptar el reembolso")
def aceptar_reembolso(
    id_conflicto: int, db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_gestion)
) -> ConflictoDetalleOut:
    return ConflictosServicio.aceptar_reembolso(db, usuario, id_conflicto)
