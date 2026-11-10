"""Esquemas de P2-CU20 · Resolver conflictos de sincronización."""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel


class ConflictoResumenOut(BaseModel):
    id_conflicto: int
    tipo: str
    estado: str
    creado_en: datetime
    id_sucursal: int
    nombre_sucursal: Optional[str] = None
    id_venta: int
    numero_comprobante: str
    total: Decimal
    cliente: Optional[str] = None


class LineaCompraOut(BaseModel):
    id_variante: int
    nombre_producto: str
    sku: str
    cantidad: int
    precio_unitario: Decimal


class PagoConflictoOut(BaseModel):
    id_pago: int
    metodo_pago: str
    monto: Decimal
    estado: str
    confirmado_en: Optional[datetime] = None


class ConflictoDetalleOut(ConflictoResumenOut):
    detalle: dict[str, Any]
    lineas: List[LineaCompraOut]
    pago: PagoConflictoOut
    fecha_compra: datetime
    aceptado_por: Optional[str] = None
    aceptado_en: Optional[datetime] = None
    resuelto_en: Optional[datetime] = None
    referencia_reembolso: Optional[str] = None
    intentos_reembolso: int
    ultimo_error: Optional[str] = None


class ResumenConflictosOut(BaseModel):
    pendiente: int
    reembolso_pendiente: int


class CierreIn(BaseModel):
    forzar: bool = False


class ReembolsoFallidoOut(BaseModel):
    id_conflicto: int
    motivo: str


class CierreOut(BaseModel):
    forzado: bool
    procesados: int
    reembolsados: int
    fallidos: List[ReembolsoFallidoOut]


class EstadoCierreOut(BaseModel):
    """Para que la web habilite el botón (S11): el último día del mes, hora de Bolivia."""

    es_ultimo_dia_del_mes: bool
    reembolsos_pendientes: int
