"""Esquemas Pydantic v2 para CU27: Gestionar promociones."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TipoDescuentoEnum(str, Enum):
    """Tipos de reduccion de precio admitidos."""
    PORCENTAJE = "porcentaje"
    MONTO_FIJO = "monto_fijo"


class AlcancePromocionEnum(str, Enum):
    """Ambitos de aplicabilidad comercial de la promocion."""
    GLOBAL = "global"
    CATEGORIA = "categoria"
    PRODUCTO = "producto"


class PromocionBase(BaseModel):
    """Esquema base para la creacion y actualizacion de promociones comerciales."""

    nombre: str = Field(..., min_length=3, max_length=150, description="Nombre de la promocion o campana")
    descripcion: Optional[str] = Field(None, description="Descripcion comercial detallada")
    codigo_cupon: Optional[str] = Field(None, max_length=50, description="Codigo de canje alfanumerico opcional")
    tipo_descuento: TipoDescuentoEnum = Field(..., description="Tipo de reduccion: porcentaje o monto_fijo")
    valor_descuento: Decimal = Field(..., gt=0, description="Magnitud del descuento (> 0)")
    fecha_inicio: datetime = Field(..., description="Fecha y hora de inicio de vigencia")
    fecha_fin: datetime = Field(..., description="Fecha y hora de culminacion de vigencia")
    tope_descuento: Optional[Decimal] = Field(None, ge=0, description="Tope maximo monetario de descuento si aplica")
    limite_usos: Optional[int] = Field(None, gt=0, description="Cupo maximo de canjes permitidos en la red")
    alcance: AlcancePromocionEnum = Field(default=AlcancePromocionEnum.GLOBAL, description="Alcance comercial")
    id_categoria: Optional[int] = Field(None, description="ID de categoria obligatoria si alcance es categoria")
    id_producto: Optional[int] = Field(None, description="ID de producto obligatorio si alcance es producto")
    estado_activo: bool = Field(default=True, description="Estado operativo del registro")

    @field_validator("codigo_cupon", mode="before")
    @classmethod
    def normalizar_codigo_cupon(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip().upper()
        return s if s else None

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, v: str) -> str:
        s = str(v).strip()
        if len(s) < 3:
            raise ValueError("El nombre debe contener al menos 3 caracteres.")
        return s

    @model_validator(mode="after")
    def validar_consistencia_promocion(self) -> "PromocionBase":
        # 1. Coherencia de fechas
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de culminacion debe ser estrictamente posterior a la fecha de inicio.")

        # 2. Rango de porcentaje
        if self.tipo_descuento == TipoDescuentoEnum.PORCENTAJE:
            if self.valor_descuento < Decimal("1.00") or self.valor_descuento > Decimal("100.00"):
                raise ValueError("El porcentaje de descuento debe situarse entre 1% y 100%.")

        # 3. Integridad de alcance
        if self.alcance == AlcancePromocionEnum.CATEGORIA and not self.id_categoria:
            raise ValueError("Debe especificar una categoria valida cuando el alcance es por categoria.")
        if self.alcance == AlcancePromocionEnum.PRODUCTO and not self.id_producto:
            raise ValueError("Debe especificar un producto valido cuando el alcance es por producto.")

        return self


class PromocionCrearIn(PromocionBase):
    """Payload de entrada para alta de promocion."""
    pass


class PromocionActualizarIn(PromocionBase):
    """Payload de entrada para modificacion de promocion."""
    pass


class EstadoConmutarIn(BaseModel):
    """Payload para conmutacion logica de estado (baja logica o reactivacion)."""
    estado_activo: bool = Field(..., description="Nuevo estado operativo de la promocion")


class PromocionItemOut(BaseModel):
    """Representacion de salida de una promocion comercial."""
    model_config = ConfigDict(from_attributes=True)

    id_promocion: int
    nombre: str
    descripcion: Optional[str]
    codigo_cupon: Optional[str]
    tipo_descuento: str
    valor_descuento: Decimal
    fecha_inicio: datetime
    fecha_fin: datetime
    tope_descuento: Optional[Decimal]
    limite_usos: Optional[int]
    usos_actuales: int
    alcance: str
    id_categoria: Optional[int]
    nombre_categoria: Optional[str] = None
    id_producto: Optional[int]
    nombre_producto: Optional[str] = None
    estado_activo: bool
    creado_en: datetime
    actualizado_en: datetime
    esta_vigente: bool = False


class MetricasPromocionesOut(BaseModel):
    """Indicadores consolidados de la gestion comercial de promociones."""
    promociones_activas: int
    cupones_vigentes: int
    descuento_promedio: Decimal
    usos_totales: int


class RespuestaPaginadaPromocionesOut(BaseModel):
    """Respuesta paginada con listado y metricas de red."""
    items: List[PromocionItemOut]
    metricas: MetricasPromocionesOut
    total: int
    pagina: int
    limite: int
    total_paginas: int


class PromocionFiltrosIn(BaseModel):
    """Parametros de consulta y filtrado multicriterio."""
    q: Optional[str] = None
    tipo_descuento: Optional[Literal["porcentaje", "monto_fijo", "todos"]] = "todos"
    estado_activo: Optional[Literal["activas", "inactivas", "todos"]] = "todos"
    alcance: Optional[Literal["global", "categoria", "producto", "todos"]] = "todos"
    ordenar_por: Optional[
        Literal[
            "creado_en_desc",
            "creado_en_asc",
            "fecha_inicio_desc",
            "fecha_fin_asc",
            "nombre_asc",
            "valor_desc",
            "usos_desc",
        ]
    ] = "creado_en_desc"
    pagina: int = Field(default=1, ge=1)
    limite: int = Field(default=10, ge=1, le=100)


# Alias de conveniencia
FiltrosPromocionIn = PromocionFiltrosIn
ListaPaginadaPromocionesOut = RespuestaPaginadaPromocionesOut

