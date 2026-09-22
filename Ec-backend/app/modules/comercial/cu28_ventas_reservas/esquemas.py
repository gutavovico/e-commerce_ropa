"""Esquemas Pydantic v2 para CU28: Consultar ventas y reservas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TransaccionFiltrosIn(BaseModel):
    """Filtros multicriterio para consulta consolidada de ventas y reservas."""

    q: Optional[str] = Field(None, max_length=100, description="Busqueda textual")
    tipo_operacion: Optional[Literal["venta", "reserva", "todas"]] = "todas"
    estado: Optional[str] = Field("todos", description="Estado de operacion o 'todos'")
    id_sucursal: Optional[int] = Field(None, description="Filtro de sucursal (para superusuario admin)")
    fecha_desde: Optional[datetime] = Field(None, description="Limite inferior del rango temporal")
    fecha_hasta: Optional[datetime] = Field(None, description="Limite superior del rango temporal")
    metodo_pago: Optional[str] = Field(None, description="Metodo de pago en ventas")
    canal_origen: Optional[Literal["web", "movil", "sucursal", "todos"]] = "todos"
    ordenar_por: Optional[
        Literal[
            "creado_en_desc",
            "creado_en_asc",
            "total_desc",
            "total_asc",
            "fecha_desc",
        ]
    ] = "creado_en_desc"
    pagina: int = Field(default=1, ge=1, description="Numero de pagina")
    limite: int = Field(default=10, ge=1, le=100, description="Cantidad por pagina")

    @field_validator("q", mode="before")
    @classmethod
    def normalizar_busqueda(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @model_validator(mode="after")
    def validar_rango_fechas(self) -> "TransaccionFiltrosIn":
        if self.fecha_desde and self.fecha_hasta:
            if self.fecha_desde > self.fecha_hasta:
                raise ValueError("La fecha_desde no puede ser posterior a fecha_hasta.")
        return self


class LineaDetalleOut(BaseModel):
    """Desglose de una prenda o variante en venta o reserva."""
    model_config = ConfigDict(from_attributes=True)

    id_detalle: int
    id_variante: int
    sku: str
    nombre_producto: str
    talla: str
    color: str
    codigo_hex: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal_linea: Decimal
    imagen_url: Optional[str] = None


class PagoItemOut(BaseModel):
    """Liquidacion de pago asociada a una venta."""
    model_config = ConfigDict(from_attributes=True)

    id_pago: int
    metodo_pago: str
    monto: Decimal
    estado: str
    referencia_pasarela: Optional[str] = None
    creado_en: datetime
    confirmado_en: Optional[datetime] = None


class TransaccionResumenItemOut(BaseModel):
    """Elemento resumido de transaccion para la tabla maestra consolidada."""
    model_config = ConfigDict(from_attributes=True)

    id_transaccion: int
    tipo_operacion: Literal["venta", "reserva"]
    codigo_comprobante: str
    fecha: datetime
    id_cliente: Optional[int] = None
    nombre_cliente: str
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    id_sucursal: int
    nombre_sucursal: str
    ciudad_sucursal: str
    canal: str
    estado: str
    total_monto: Decimal
    cantidad_items: int


class MetricasTransaccionalesOut(BaseModel):
    """Indicadores cuantitativos consolidados de la red comercial."""
    monto_total_facturado: Decimal
    total_ventas_concluidas: int
    reservas_activas: int
    ticket_promedio: Decimal


class RespuestaPaginadaTransaccionesOut(BaseModel):
    """Respuesta paginada unificada con items y metricas."""
    items: List[TransaccionResumenItemOut]
    metricas: MetricasTransaccionalesOut
    total: int
    pagina: int
    limite: int
    total_paginas: int


class VentaDetalleCompletoOut(BaseModel):
    """Detalle exhaustivo de una transaccion de venta."""
    model_config = ConfigDict(from_attributes=True)

    id_venta: int
    numero_comprobante: str
    fecha_venta: datetime
    estado: str
    tipo_venta: str
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    id_sucursal: int
    nombre_sucursal: str
    ciudad_sucursal: str
    id_cliente: Optional[int] = None
    nombre_cliente: str
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    cajero_nombre: Optional[str] = None
    lineas: List[LineaDetalleOut]
    pagos: List[PagoItemOut]


class ReservaDetalleCompletoOut(BaseModel):
    """Detalle exhaustivo de una orden de reserva."""
    model_config = ConfigDict(from_attributes=True)

    id_reserva: int
    codigo_reserva: str
    fecha_hora_atencion: datetime
    creado_en: datetime
    estado: str
    canal_origen: str
    observacion: Optional[str] = None
    id_sucursal: int
    nombre_sucursal: str
    ciudad_sucursal: str
    id_cliente: int
    nombre_cliente: str
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    atendido_por_nombre: Optional[str] = None
    lineas: List[LineaDetalleOut]
