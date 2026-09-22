"""Esquemas Pydantic para CU07 (Detalle de Producto) y CU08 (Variantes y Características)."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class ComposicionNobleOut(BaseModel):
    """Composición noble y técnica de confección de la prenda de alta costura."""
    cuerpo_principal: str = Field(..., description="Composición del tejido principal (ej. 100% Seda Natural 22 Momme)")
    forro_interior: str = Field(..., description="Forro interior (ej. Crepé de seda puro transpirable)")
    tecnica_textil: str = Field(..., description="Técnica textil aplicada (ej. Plisado artesanal al vapor de Lyon)")
    descripcion_confeccion: str = Field(..., description="Explicación del modelado artesanal y horas de trabajo")
    instrucciones_cuidado: List[str] = Field(default_factory=list, description="Directrices de conservación textil")


class ColorResumenOut(BaseModel):
    """Color disponible para la prenda con código hex e indicador de existencias."""
    id_color: int
    nombre: str
    codigo_hex: Optional[str] = None
    disponible: bool = True
    imagen_url: Optional[str] = None


class TallaResumenOut(BaseModel):
    """Talla normalizada disponible para la prenda con indicador de disponibilidad."""
    id_talla: int
    codigo: str
    orden: int
    disponible: bool = True
    stock_total: int = 0


class VarianteDetalleOut(BaseModel):
    """Variante específica (talla + color) con SKU, precio y stock."""
    id_variante: int
    id_producto: int
    id_talla: int
    talla_codigo: str
    talla_orden: int
    id_color: int
    color_nombre: str
    color_hex: Optional[str] = None
    sku: str
    precio_extra: Decimal = Decimal("0.00")
    precio_final_variante: Decimal
    stock_total_disponible: int = 0
    tiene_stock: bool = True
    imagen_url: Optional[str] = None


class GaleriaTomaOut(BaseModel):
    """Perspectiva o toma fotográfica editorial de alta resolución."""
    url: str
    etiqueta: str = Field(..., description="FRONTAL, TEXTURA SEDA, ESPALDA, COSTURA")
    orden: int = 1


class PrendaComplementariaOut(BaseModel):
    """Prenda de alta costura sugerida en la sección 'Completa el look atelier'."""
    id_producto: int
    nombre: str
    subtitulo_atelier: str
    categoria: str
    precio_base: Decimal
    precio_final: Decimal
    imagen_url: Optional[str] = None


class ProductoDetalleOut(BaseModel):
    """Contrato consolidado de la ficha técnica de producto de alta costura (CU07 + CU08)."""
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    precio_final: Decimal
    tiene_descuento: bool = False
    descuento_monto: Decimal = Decimal("0.00")
    porcentaje_descuento: Optional[int] = None
    cuotas_info: str = Field(..., description="Cálculo informativo de pagos sin intereses")
    subtitulo_atelier: str = Field(..., description="Línea textil o atelier (ej. ALTA COSTURA · MILÁN / LYON)")
    linea_confeccion: str = Field(..., description="Insignia de confección (ej. ALTA COSTURA LYON)")
    etiqueta_badge: Optional[str] = Field(None, description="EDICIÓN LIMITADA, NOVEDAD, etc.")
    sku_base: str
    rating_promedio: float = 4.9
    total_resenas: int = 38
    beneficio_membresia: Optional[str] = "Beneficio Membresía Atelier aplicado en liquidación privada"
    categoria_id: int
    categoria_nombre: str
    coleccion_id: Optional[int] = None
    coleccion_nombre: Optional[str] = None
    imagen_principal: Optional[str] = None
    galeria: List[GaleriaTomaOut] = Field(default_factory=list)
    modelo_ar_url: Optional[str] = None
    modelo_info: Optional[str] = "MODELO: 1,77M - TALLA 38 ES"
    composicion: ComposicionNobleOut
    colores_disponibles: List[ColorResumenOut] = Field(default_factory=list)
    tallas_disponibles: List[TallaResumenOut] = Field(default_factory=list)
    variantes: List[VarianteDetalleOut] = Field(default_factory=list)
    piezas_look_complementario: List[PrendaComplementariaOut] = Field(default_factory=list)
    total_guardados: int = 142
