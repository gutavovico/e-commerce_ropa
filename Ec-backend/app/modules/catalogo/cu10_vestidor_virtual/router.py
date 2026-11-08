"""Router de FastAPI para CU10: Utilizar Vestidor Virtual (Dos Motores)."""

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu10_vestidor_virtual.esquemas import (
    SesionVestidorActualizarIn,
    SesionVestidorCrearIn,
    SesionVestidorOut,
    TokenVestidorDecartOut,
)
from modules.catalogo.cu10_vestidor_virtual.servicio import ServicioProcesarAR

router = APIRouter(tags=["Vestidor Virtual AR"])


@router.post(
    "/vestidor/token",
    response_model=TokenVestidorDecartOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener token temporal para vestidor realista (Decart Lucy VTON) - CU10",
    description=(
        "Genera y entrega un token de cliente efímero (~60 s como tiempo máximo para establecer la conexión con Decart) "
        "para autenticar la sesión de streaming con Decart Lucy VTON desde el WebView de la app móvil sin exponer "
        "la clave maestra permanente del servidor. La petición no requiere cuerpo (la app obtiene la imagen de la prenda "
        "directamente del catálogo). Requiere cliente autenticado con cabecera Authorization: Bearer <token_jwt>. "
        "Si Decart no está disponible o carece de saldo de créditos, retorna 503 Service Unavailable para activar el "
        "fallback automático al Motor 1 (Local)."
    ),
)
def obtener_token_vestidor_decart(
    canal: Literal["web", "movil"] = Query(
        "web",
        description=(
            "Canal cliente. 'web' restringe el token a los orígenes de CORS_ORIGINS; 'movil' lo emite "
            "sin restricción de origen porque el WebView de la app carga la página como asset local "
            "(Origin null)."
        ),
    ),
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TokenVestidorDecartOut:
    """Solicita un token efímero de conexión hacia Decart Lucy VTON (Prueba 3b)."""
    servicio = ServicioProcesarAR(db)
    return servicio.solicitar_token_decart(usuario, canal=canal)


@router.post(
    "/vestidor/sesion",
    response_model=SesionVestidorOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar sesión de prueba en vestidor virtual - CU10",
    description=(
        "Registra la interacción del cliente con el vestidor virtual en realidad aumentada, especificando si se "
        "utilizó el motor local en dispositivo o el motor realista con IA generativa Decart, junto con la duración "
        "activa de la prueba en segundos y el indicador de interés comercial. Valida que la prenda cuente con un "
        "recurso visual 2D (modelo_ar_url) configurado en el catálogo."
    ),
)
def registrar_sesion_vestidor(
    datos: SesionVestidorCrearIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SesionVestidorOut:
    """Registra la sesión completada en el vestidor virtual (Prueba 3)."""
    servicio = ServicioProcesarAR(db)
    return servicio.crear_sesion(usuario=usuario, datos=datos)


@router.patch(
    "/vestidor/sesion/{id_sesion_ar}",
    response_model=SesionVestidorOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar captura o interés comercial de una sesión de vestidor - CU10",
    description=(
        "Permite registrar la URL de una fotografía capturada o actualizar el flag 'genero_interes' "
        "si el cliente agrega la prenda al carrito o genera una reserva física tras la experiencia."
    ),
)
def actualizar_sesion_vestidor(
    datos: SesionVestidorActualizarIn,
    id_sesion_ar: int = Path(..., gt=0, description="ID de la sesión de vestidor"),
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SesionVestidorOut:
    """Actualiza la sesión de vestidor previamente registrada."""
    servicio = ServicioProcesarAR(db)
    return servicio.actualizar_sesion(
        id_sesion_ar=id_sesion_ar,
        datos=datos,
        usuario=usuario,
    )

