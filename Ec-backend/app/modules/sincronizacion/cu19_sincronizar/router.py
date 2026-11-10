"""Router de P2-CU19 · Sincronizar operaciones pendientes. Solo HTTP."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.sincronizacion.cu19_sincronizar.esquemas import LoteIn, LoteOut, OperacionOut
from modules.sincronizacion.cu19_sincronizar.servicio import SincronizacionServicio

router = APIRouter(prefix="/sin-conexion", tags=["P2-CU19 Sincronización"])

_cliente = require_roles(["cliente"])


@router.post("/sincronizar", response_model=LoteOut, summary="Enviar las operaciones pendientes del dispositivo")
def sincronizar(lote: LoteIn, db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_cliente)) -> LoteOut:
    return SincronizacionServicio.sincronizar(db, usuario, lote)


@router.get("/operaciones", response_model=List[OperacionOut], summary="Estado de las operaciones del dispositivo")
def operaciones(
    dispositivo: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_cliente),
) -> List[OperacionOut]:
    return SincronizacionServicio.operaciones(db, usuario, dispositivo)
