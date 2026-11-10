"""Esquemas de P2-CU19 · Sincronizar operaciones pendientes."""

from uuid import UUID
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

MAX_OPERACIONES_POR_LOTE = 50


class OperacionIn(BaseModel):
    uuid: UUID = Field(..., description="Identificador único generado en el dispositivo (RN34)")
    tipo: Literal["reserva", "compra_interrumpida"]
    id_sucursal: Optional[int] = None
    registrada_en: datetime = Field(..., description="Instante en que se registró en el dispositivo")
    codigo_provisional: Optional[str] = Field(None, max_length=24)
    datos: dict[str, Any] = Field(default_factory=dict)


class LoteIn(BaseModel):
    dispositivo: UUID
    operaciones: List[OperacionIn] = Field(..., min_length=1, max_length=MAX_OPERACIONES_POR_LOTE)


class ResultadoOperacionOut(BaseModel):
    """`reintentar` no es un estado guardado: el servidor no pudo decidir (p. ej. Stripe no
    respondió) y la app debe conservar la operación y volver a enviarla (A1)."""

    uuid: UUID
    estado: Literal["confirmada", "rechazada", "en_conflicto", "reintentar"]
    motivo: Optional[str] = None
    mensaje: Optional[str] = None
    codigo_reserva: Optional[str] = None
    id_reserva: Optional[int] = None
    id_venta: Optional[int] = None
    id_conflicto: Optional[int] = None
    #: True si la operación ya se había recibido y se devuelve el resultado guardado (A2).
    repetida: bool = False


class LoteOut(BaseModel):
    id_sync_log: int
    resultados: List[ResultadoOperacionOut]


class OperacionOut(BaseModel):
    """Estado actual de una operación del dispositivo (incluye cómo va su conflicto, CU20)."""

    uuid: UUID
    tipo: str
    estado: str
    motivo: Optional[str] = None
    codigo_provisional: Optional[str] = None
    codigo_reserva: Optional[str] = None
    id_reserva: Optional[int] = None
    id_venta: Optional[int] = None
    registrada_en: datetime
    recibida_en: datetime
    estado_conflicto: Optional[str] = None
