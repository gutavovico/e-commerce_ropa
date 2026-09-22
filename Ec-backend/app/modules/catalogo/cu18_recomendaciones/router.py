"""Router de FastAPI para CU18: Recibir Recomendaciones Personalizadas."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_optional_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu18_recomendaciones.esquemas import (
    RecomendacionesPersonalizadasOut,
)
from modules.catalogo.cu18_recomendaciones.servicio import RecomendacionesService

router = APIRouter(tags=["Catálogo y Recomendaciones"])


@router.get(
    "/catalogo/recomendaciones/personalizadas",
    response_model=RecomendacionesPersonalizadasOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener recomendaciones personalizadas basadas en compras (CU18)",
    description=(
        "Consulta las compras históricas pagadas del cliente autenticado para sugerir prendas afines "
        "en stock físico real (> 0). Si el usuario es nuevo o navega como visitante anónimo, devuelve "
        "un estado en frío (Empty State) con el copy normativo de alta costura sin inventar prendas."
    ),
)
@router.get(
    "/recomendaciones/personalizadas",
    response_model=RecomendacionesPersonalizadasOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def obtener_recomendaciones_personalizadas(
    limite: int = Query(
        default=6,
        ge=1,
        le=12,
        description="Cantidad máxima de prendas sugeridas",
    ),
    id_sucursal: Optional[int] = Query(
        default=None,
        description="ID de sucursal para verificar stock local",
    ),
    usuario: Optional[UsuarioORM] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> RecomendacionesPersonalizadasOut:
    """Endpoint de recomendaciones para el módulo 'Recomendado para ti' de la vista de Inicio."""
    servicio = RecomendacionesService(db)
    return servicio.obtener_recomendaciones_personalizadas(
        usuario=usuario,
        limite=limite,
        id_sucursal=id_sucursal,
    )
