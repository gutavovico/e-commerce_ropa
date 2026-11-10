"""Esquemas de la bandeja de avisos del cliente (decisión D1: sin push)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AvisoOut(BaseModel):
    id_aviso: int
    tipo: str
    titulo: str
    mensaje: str
    id_reserva: Optional[int] = None
    id_venta: Optional[int] = None
    creado_en: datetime
    leido: bool


class BandejaAvisosOut(BaseModel):
    no_leidos: int
    avisos: List[AvisoOut]
