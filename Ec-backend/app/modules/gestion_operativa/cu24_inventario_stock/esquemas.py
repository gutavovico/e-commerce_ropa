"""Esquemas Pydantic v2 para CU24: Gestionar Inventario, Stock y Existencias por Sucursal."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TipoMovimientoEnum(str, Enum):
    INGRESO_PROVEEDOR = "ingreso_proveedor"
    AJUSTE_POSITIVO = "ajuste_positivo"
    AJUSTE_NEGATIVO = "ajuste_negativo"
    TRANSFERENCIA_SALIDA = "transferencia_salida"
    TRANSFERENCIA_ENTRADA = "transferencia_entrada"
    VENTA_CONFIRMADA = "venta_confirmada"
    CANCELACION_PEDIDO = "cancelacion_pedido"


class EstadoStockCalculadoEnum(str, Enum):
    OPTIMO = "optimo"
    ALERTA_BAJA = "alerta_baja"
    AGOTADO = "agotado"


class TipoAjusteManualEnum(str, Enum):
    INCREMENTO = "incremento"
    DECREMENTO = "decremento"


# --- Esquemas de Entrada (Requests) ---

class InventarioCrearIn(BaseModel):
    """Payload para registro inicial de existencias para una variante."""
    id_sucursal: int = Field(..., gt=0, description="Identificador de la boutique fisica")
    id_variante: int = Field(..., gt=0, description="Identificador de la variante de producto")
    id_temporada: int = Field(default=1, gt=0, description="Identificador de temporada comercial")
    cantidad_inicial: int = Field(..., ge=0, description="Existencias fisicas iniciales")
    stock_minimo: int = Field(default=0, ge=0, description="Nivel minimo de seguridad")
    stock_alerta: int = Field(default=5, ge=0, description="Umbral para alerta de reposicion")
    referencia_documento: Optional[str] = Field(None, max_length=100, description="Guia o comprobante")
    observacion: Optional[str] = Field(None, max_length=500, description="Nota de ingreso")


class InventarioAjusteIn(BaseModel):
    """Payload para ajuste manual por merma, rotura o sobrante fisico."""
    tipo_ajuste: TipoAjusteManualEnum = Field(..., description="Direccion del ajuste: incremento o decremento")
    cantidad: int = Field(..., gt=0, description="Numero de unidades a ajustar")
    motivo: str = Field(..., min_length=5, max_length=500, description="Justificacion obligatoria del ajuste")
    referencia_documento: Optional[str] = Field(None, max_length=100, description="Numero de acta o resolucion")

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, valor: str) -> str:
        saneado = valor.strip()
        if len(saneado) < 5:
            raise ValueError("El motivo del ajuste debe tener al menos 5 caracteres significativos.")
        return saneado


class TransferenciaInterSucursalIn(BaseModel):
    """Payload para transferencia atomica entre dos sucursales."""
    id_sucursal_origen: int = Field(..., gt=0, description="Sede que remite la mercaderia")
    id_sucursal_destino: int = Field(..., gt=0, description="Sede receptora de la mercaderia")
    id_variante: int = Field(..., gt=0, description="Variante fisica a transferir")
    cantidad: int = Field(..., gt=0, description="Numero de prendas a trasladar")
    motivo: str = Field(..., min_length=5, max_length=500, description="Motivo del traslado inter-sedes")

    @field_validator("motivo")
    @classmethod
    def validar_motivo_transferencia(cls, valor: str) -> str:
        saneado = valor.strip()
        if len(saneado) < 5:
            raise ValueError("El motivo del traslado debe tener al menos 5 caracteres significativos.")
        return saneado

    @model_validator(mode="after")
    def validar_sedes_distintas(self) -> "TransferenciaInterSucursalIn":
        if self.id_sucursal_origen == self.id_sucursal_destino:
            raise ValueError("La sucursal de origen y la de destino deben ser distintas.")
        return self


class InventarioFiltrosIn(BaseModel):
    """Parametros de consulta y filtrado multicriterio."""
    id_sucursal: Optional[int] = Field(None, gt=0)
    id_categoria: Optional[int] = Field(None, gt=0)
    estado_stock: Optional[str] = Field(None, description="optimo, alerta_baja, agotado")
    q: Optional[str] = Field(None, max_length=100, description="Busqueda por prenda o SKU")
    pagina: int = Field(default=1, ge=1)
    limite: int = Field(default=20, ge=1, le=100)


# --- Esquemas de Salida (Responses) ---

class DatosVarianteInventarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_variante: int
    id_producto: int
    nombre_prenda: str
    sku: str
    talla: str
    color_nombre: str
    color_hex: str
    precio_base: float
    precio_final: float
    imagen_url: Optional[str] = None
    categoria_nombre: str


class DatosSucursalInventarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_sucursal: int
    nombre: str
    ciudad: str


class InventarioItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_inventario: int
    id_sucursal: int
    id_variante: int
    cantidad_disponible: int
    cantidad_reservada: int
    stock_total: int
    stock_minimo: int
    stock_alerta: int
    estado: str
    estado_calculado: EstadoStockCalculadoEnum
    actualizado_en: datetime
    sucursal: DatosSucursalInventarioOut
    variante: DatosVarianteInventarioOut


class ListaPaginadaInventarioOut(BaseModel):
    items: List[InventarioItemOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int


class KardexItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_movimiento: int
    id_inventario: int
    tipo_movimiento: str
    cantidad: int
    saldo_anterior: int
    saldo_nuevo: int
    motivo: str
    referencia_documento: Optional[str] = None
    id_usuario: Optional[int] = None
    usuario_nombre: Optional[str] = None
    creado_en: datetime


class HistorialKardexOut(BaseModel):
    id_inventario: int
    prenda_sku: str
    sucursal_nombre: str
    saldo_actual: int
    movimientos: List[KardexItemOut]


class ComprobanteTransferenciaOut(BaseModel):
    mensaje: str
    id_sucursal_origen: int
    id_sucursal_destino: int
    id_variante: int
    sku: str
    cantidad_transferida: int
    saldo_origen_nuevo: int
    saldo_destino_nuevo: int
    fecha: datetime


class DisponibilidadSucursalOut(BaseModel):
    id_sucursal: int
    nombre_sucursal: str
    ciudad: str
    direccion: str
    cantidad_disponible: int
    estado: str


class DisponibilidadPublicaOut(BaseModel):
    id_variante: int
    sku: str
    nombre_prenda: str
    sucursales: List[DisponibilidadSucursalOut]
