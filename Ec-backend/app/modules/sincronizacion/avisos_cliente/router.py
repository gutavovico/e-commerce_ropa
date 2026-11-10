"""Router de la bandeja de avisos del cliente. Solo HTTP."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.sincronizacion.avisos_cliente.esquemas import AvisoOut, BandejaAvisosOut
from modules.sincronizacion.avisos_cliente.servicio import AvisosServicio

router = APIRouter(prefix="/avisos", tags=["P2 Avisos al cliente"])

_cliente = require_roles(["cliente"])


@router.get("", response_model=BandejaAvisosOut, summary="Bandeja de avisos del cliente")
def bandeja(db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_cliente)) -> BandejaAvisosOut:
    return AvisosServicio.bandeja(db, usuario)


@router.post("/{id_aviso}/leido", response_model=AvisoOut, summary="Marcar un aviso como leído")
def marcar_leido(
    id_aviso: int, db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_cliente)
) -> AvisoOut:
    return AvisosServicio.marcar_leido(db, usuario, id_aviso)
