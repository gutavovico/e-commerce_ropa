"""Esquemas Pydantic para el CU19: Consultar Asistente Inteligente."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class MensajeChatbotIn(BaseModel):
    """Petición de mensaje para el asistente inteligente."""

    mensaje: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Pregunta o consulta del cliente en lenguaje natural",
        examples=["¿Tienen vestidos plisados en la boutique de Madrid?"],
    )
    canal: Literal["web", "movil"] = Field(
        default="web",
        description="Canal desde el cual se realiza la consulta",
    )
    id_sucursal_preferida: Optional[int] = Field(
        default=None,
        description="Identificador opcional de la sucursal preferida del cliente",
    )


class ProductoChatbotOut(BaseModel):
    """Resumen de prenda recomendada o consultada."""

    id_producto: int
    nombre: str
    precio: str
    categoria: Optional[str] = None
    imagen_url: Optional[str] = None
    disponible: bool = True
    sucursal_nombre: Optional[str] = None


class SucursalChatbotOut(BaseModel):
    """Resumen de sucursal mencionada o sugerida."""

    id_sucursal: int
    nombre: str
    direccion: str
    horario: str


class RespuestaChatbotOut(BaseModel):
    """Respuesta generada por el asistente inteligente con contexto enriquecido."""

    id_interaccion: int
    respuesta: str
    productos_sugeridos: List[ProductoChatbotOut] = Field(default_factory=list)
    sucursales_sugeridas: List[SucursalChatbotOut] = Field(default_factory=list)
    sugerencias_rapidas: List[str] = Field(default_factory=list)


class InteraccionChatbotHistorialOut(BaseModel):
    """Registro histórico de interacción previa con el asistente."""

    model_config = ConfigDict(from_attributes=True)

    id_interaccion: int
    mensaje_usuario: str
    respuesta_ia: Optional[str] = None
    canal: str
    creado_en: datetime
