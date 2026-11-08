"""Esquemas Pydantic v2 para CU10: Utilizar Vestidor Virtual."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenVestidorDecartOut(BaseModel):
    """Respuesta al solicitar un token de cliente efímero para Decart Lucy VTON."""

    token: str = Field(
        ...,
        description="Token de cliente efímero (~60 s) para establecer la conexión de streaming con Decart",
    )
    expira_en_segundos: int = Field(
        default=60,
        description="Tiempo en segundos de vigencia del token para establecer el enlace",
    )
    servicio: str = Field(
        default="decart_lucy_vton_720p",
        description="Nombre del modelo y servicio de inferencia de IA",
    )


class SesionVestidorCrearIn(BaseModel):
    """Payload de entrada para registrar una sesión en el vestidor virtual (Prueba 3)."""

    id_producto: int = Field(
        ...,
        gt=0,
        description="ID del producto de alta costura que se probó",
    )
    dispositivo: Optional[str] = Field(
        default="android",
        max_length=50,
        description="Plataforma o dispositivo ('android', 'ios', 'web', 'app_flutter')",
    )
    motor: Literal["local", "ia"] = Field(
        default="local",
        description="Motor utilizado: 'local' (Google ML Kit en dispositivo) o 'ia' (Decart Lucy VTON)",
    )
    duracion_segundos: Optional[int] = Field(
        default=None,
        ge=0,
        description="Duración efectiva en segundos de la sesión de prueba activa",
    )
    resultado_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL de la captura fotográfica renderizada si el cliente la guardó",
    )
    genero_interes: bool = Field(
        default=False,
        description="Indica si la prueba derivó en intención comercial (carrito o reserva)",
    )


class SesionVestidorActualizarIn(BaseModel):
    """Payload opcional para actualizar interés comercial o URL de captura tras la prueba."""

    resultado_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Nueva URL de captura fotográfica",
    )
    genero_interes: Optional[bool] = Field(
        default=None,
        description="Marca de interés comercial actualizada",
    )


class SesionVestidorOut(BaseModel):
    """Respuesta con los datos de la sesión de vestidor virtual persistida."""

    model_config = ConfigDict(from_attributes=True)

    id_sesion_ar: int = Field(..., description="Identificador único de la sesión AR")
    id_cliente: int = Field(..., description="ID del cliente que realizó la prueba")
    id_producto: int = Field(..., description="ID del producto probado")
    dispositivo: Optional[str] = Field(default=None, description="Dispositivo del cliente")
    motor: str = Field(default="local", description="Motor de vestidor ejecutado ('local' | 'ia')")
    duracion_segundos: Optional[int] = Field(
        default=None, description="Duración en segundos de la sesión"
    )
    fecha_hora: datetime = Field(..., description="Marca de tiempo UTC de la interacción")
    resultado_url: Optional[str] = Field(
        default=None, description="URL de la captura si fue guardada"
    )
    genero_interes: bool = Field(
        default=False, description="Flag de conversión o intención comercial"
    )

