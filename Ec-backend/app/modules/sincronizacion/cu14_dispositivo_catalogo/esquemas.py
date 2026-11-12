"""Esquemas de P2-CU14 · Descargar catálogo y registrar dispositivo.

Los importes van como `Decimal` (FastAPI los serializa como cadena, igual que el resto de la API).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel


class DispositivoIn(BaseModel):
    identificador: uuid.UUID
    plataforma: Literal["pwa", "flutter"]
    token_push: Optional[str] = None


class DispositivoTokenPushIn(BaseModel):
    identificador: uuid.UUID
    token_push: str


class DispositivoTokenPushOut(BaseModel):
    ok: bool = True
    identificador: uuid.UUID
    token_push: str


class ProbarPushOut(BaseModel):
    ok: bool = True
    dispositivos_notificados: int
    mensaje: str


class DispositivoOut(BaseModel):
    id_dispositivo: int
    identificador: uuid.UUID
    plataforma: str
    codigo_corto: str
    registrado_en: datetime
    ultima_descarga_en: Optional[datetime] = None
    token_push: Optional[str] = None
    # Parámetros de la empresa que la app aplica sin conexión (CU11, RN33, RN41)
    operacion_offline_habilitada: bool
    dias_antiguedad_offline: int
    horas_vencimiento_reserva: int
    moneda: str


class VarianteLocalOut(BaseModel):
    id_variante: int
    sku: str
    id_talla: int
    id_color: int
    precio: Decimal


class ProductoLocalOut(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    id_categoria: int
    precio_base: Decimal
    imagen_url: Optional[str] = None
    variantes: List[VarianteLocalOut]


class CategoriaLocalOut(BaseModel):
    id_categoria: int
    nombre: str
    id_categoria_padre: Optional[int] = None


class TallaLocalOut(BaseModel):
    id_talla: int
    codigo: str
    orden: int


class ColorLocalOut(BaseModel):
    id_color: int
    nombre: str
    codigo_hex: Optional[str] = None


class PromocionLocalOut(BaseModel):
    id_promocion: int
    nombre: str
    tipo_descuento: str
    valor_descuento: Decimal
    alcance: str
    id_categoria: Optional[int] = None
    id_producto: Optional[int] = None
    productos: List[int]
    fecha_fin: datetime


class SucursalLocalOut(BaseModel):
    id_sucursal: int
    nombre: str
    direccion: str
    ciudad: Optional[str] = None
    horario_apertura: Optional[str] = None
    horario_cierre: Optional[str] = None


class ExistenciaLocalOut(BaseModel):
    id_variante: int
    id_sucursal: int
    cantidad_disponible: int


class CatalogoLocalOut(BaseModel):
    """Paquete completo de la empresa para consultar y reservar sin conexión (CU14 paso 3)."""

    generado_en: datetime
    modo: Literal["completo", "indispensable"]
    moneda: str
    productos: List[ProductoLocalOut]
    categorias: List[CategoriaLocalOut]
    tallas: List[TallaLocalOut]
    colores: List[ColorLocalOut]
    promociones: List[PromocionLocalOut]
    sucursales: List[SucursalLocalOut]
    existencias: List[ExistenciaLocalOut]
