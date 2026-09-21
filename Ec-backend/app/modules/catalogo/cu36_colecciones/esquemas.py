"""Esquemas Pydantic v2 para CU36: Consultar Colecciones.

Define las estructuras de serialización para colecciones activas,
resumen editorial de colecciones y prendas exclusivas por colección.
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class VarianteColeccionOut(BaseModel):
    """Resumen de variante de talla y color de una prenda."""

    id_variante: int
    talla: str
    color: str
    codigo_hex: Optional[str] = None
    sku: str
    precio_final: Decimal
    stock_disponible: int

    model_config = ConfigDict(from_attributes=True)


class ProductoColeccionItemOut(BaseModel):
    """Prenda activa perteneciente a una colección."""

    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    imagen_url: Optional[str] = None
    badge_editorial: str = Field(
        default="DISPONIBLE",
        description="Etiqueta visual de lujo (ej. COLECCIÓN 07, EN SERRANO, BÁSICO DE LUJO, SASTRERÍA ATELIER)",
    )
    subtitulo_textil: str = Field(
        default="ALTA COSTURA",
        description="Origen de hilatura o tejido (ej. SEDA LYON · ALTA COSTURA, BIELLA 380G)",
    )
    categoria: str
    colores_disponibles: List[str] = []
    stock_total_disponible: int
    tiene_stock: bool
    variantes: List[VarianteColeccionOut] = []

    model_config = ConfigDict(from_attributes=True)


class ColeccionResumenOut(BaseModel):
    """Resumen de colección para la vista principal y grilla editorial."""

    id_coleccion: int
    nombre: str
    descripcion: Optional[str] = None
    temporada_id: int
    temporada_nombre: str
    temporada_tipo: str
    proveedor_nombre: Optional[str] = None
    taller_origen: str = Field(
        default="Atelier Central",
        description="Taller u origen artesanal (ej. Molinos de Biella & Como, Alpaca Suri de los Andes)",
    )
    precio_desde: Decimal = Field(
        default=Decimal("0.00"),
        description="Precio de entrada (mínimo precio base entre las prendas activas)",
    )
    total_prendas: int
    es_destacada: bool = False
    badge_edicion: str = Field(
        default="EDICIÓN VIGENTE",
        description="Badge de temporada/edición (ej. EDICIÓN SS24 MILANO, EDICIÓN Nº 03 INVIERNO, LÍNEA PERMANENTE)",
    )
    badge_disponibilidad: str = Field(
        default="DISPONIBLE",
        description="DISPONIBLE, ÚLTIMAS UNIDADES, PIEZAS ICÓNICAS",
    )
    imagen_portada: Optional[str] = None
    piezas_clave: List[ProductoColeccionItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class ColeccionesActivasResponseOut(BaseModel):
    """Respuesta del endpoint principal de colecciones activas."""

    temporada_activa_id: Optional[int] = None
    temporada_activa_nombre: Optional[str] = None
    temporada_activa_tipo: Optional[str] = None
    coleccion_destacada: Optional[ColeccionResumenOut] = None
    otras_colecciones: List[ColeccionResumenOut] = []
    total_colecciones: int

    model_config = ConfigDict(from_attributes=True)


class ColeccionDetalleOut(BaseModel):
    """Detalle completo de una colección y su listado de prendas activas."""

    id_coleccion: int
    nombre: str
    descripcion: Optional[str] = None
    temporada_id: int
    temporada_nombre: str
    temporada_tipo: str
    proveedor_nombre: Optional[str] = None
    taller_origen: str
    total_prendas: int
    mensaje_empty_state: Optional[str] = None
    productos: List[ProductoColeccionItemOut] = []

    model_config = ConfigDict(from_attributes=True)
