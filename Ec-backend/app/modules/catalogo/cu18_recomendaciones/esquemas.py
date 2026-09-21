"""Esquemas Pydantic para el CU18 - Recibir Recomendaciones Personalizadas."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class VarianteRecomendadaOut(BaseModel):
    """Información resumida de variante disponible para una prenda recomendada."""

    model_config = ConfigDict(from_attributes=True)

    id_variante: int
    sku: str
    talla: str
    id_talla: int
    color: str
    id_color: int
    codigo_hex: Optional[str] = None
    precio_extra: Decimal = Decimal("0.00")
    disponible: bool = True
    cantidad_disponible: int = 0


class ProductoRecomendadoItemOut(BaseModel):
    """Información completa de una prenda sugerida con metadatos Atelier y score."""

    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    categoria: str
    id_categoria: int
    coleccion: Optional[str] = None
    id_coleccion: Optional[int] = None
    temporada: Optional[str] = None
    id_temporada: Optional[int] = None
    precio_base: Decimal
    imagen_url: Optional[str] = None
    modelo_ar_url: Optional[str] = None
    activo: bool = True
    badge_editorial: Optional[str] = None
    subtitulo_atelier: Optional[str] = None
    tono_principal: Optional[str] = None
    score_relevancia: float = Field(default=0.90, ge=0.0, le=1.0)
    motivo_individual: Optional[str] = None
    stock_total_disponible: int = 0
    variantes: List[VarianteRecomendadaOut] = []


class RecomendacionesPersonalizadasOut(BaseModel):
    """Respuesta consolidada para el módulo 'Recomendado para ti' de la vista de Inicio."""

    tiene_historial: bool = Field(
        ...,
        description="True si el cliente posee compras pagadas previas y prendas recomendadas",
    )
    motivo_general: Optional[str] = Field(
        default=None,
        description="Explicación contextual de la selección (IA o síntesis de afinidad)",
    )
    boutique_referencia: Optional[str] = Field(
        default="Boutique Serrano (Madrid)",
        description="Nombre de la boutique o Flagship de referencia",
    )
    mensaje_empty_state: Optional[str] = Field(
        default=None,
        description="Copy normativo para el contenedor en frío de clientes nuevos o anónimos",
    )
    total_recomendados: int = 0
    items: List[ProductoRecomendadoItemOut] = []
