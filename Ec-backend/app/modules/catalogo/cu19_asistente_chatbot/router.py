"""Router FastAPI para CU19: Asistente Inteligente / Chatbot."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user, get_optional_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu19_asistente_chatbot.esquemas import (
    InteraccionChatbotHistorialOut,
    MensajeChatbotIn,
    RespuestaChatbotOut,
)
from modules.catalogo.cu19_asistente_chatbot.servicio import ServicioAsistenteChatbot

router = APIRouter(prefix="/asistente", tags=["Asistente Inteligente"])


@router.post(
    "/chat",
    response_model=RespuestaChatbotOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar al asistente inteligente (CU19)",
    description=(
        "Procesa una consulta en lenguaje natural formulada por el cliente o visitante, "
        "recupera contexto real de catálogo y sucursales (RAG), consulta a Gemini Flash "
        "con fallback determinista de lujo y persiste el intercambio en interacciones_chatbot."
    ),
)
def enviar_mensaje_asistente(
    payload: MensajeChatbotIn,
    db: Session = Depends(get_db),
    usuario: Optional[UsuarioORM] = Depends(get_optional_current_user),
) -> RespuestaChatbotOut:
    """Envía un mensaje al asistente y obtiene respuesta editorial con prendas sugeridas."""
    return ServicioAsistenteChatbot.procesar_mensaje(
        db=db,
        payload=payload,
        usuario=usuario,
    )


@router.get(
    "/historial",
    response_model=List[InteraccionChatbotHistorialOut],
    status_code=status.HTTP_200_OK,
    summary="Consultar historial de interacciones con el asistente (CU19)",
    description="Retorna las interacciones recientes del cliente autenticado.",
)
def obtener_historial_asistente(
    limite: int = Query(default=15, ge=1, le=50, description="Cantidad máxima de registros a retornar"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(get_current_user),
) -> List[InteraccionChatbotHistorialOut]:
    """Obtiene el historial de conversación del cliente autenticado."""
    return ServicioAsistenteChatbot.obtener_historial(
        db=db,
        id_cliente=usuario.id_usuario,
        limite=limite,
    )

