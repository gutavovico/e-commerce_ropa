"""Esquemas Pydantic v2 para P2-CU07: Gestionar suscripciones de empresas.

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` §3.2 (CU07).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

TipoOperacionSuscripcion = Literal[
    "alta",
    "cambio_plan",
    "renovacion",
    "suspension",
    "reactivacion",
    "cancelacion",
]


class OperacionSuscripcionIn(BaseModel):
    """Payload unificado para asignar, cambiar de plan, renovar, suspender, reactivar o cancelar una suscripción."""

    operacion: TipoOperacionSuscripcion
    id_plan: Optional[int] = Field(default=None, gt=0)
    estado: Optional[Literal["prueba", "activa"]] = None
    fecha_inicio: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    motivo: Optional[str] = Field(default=None, max_length=500)


class SuscripcionEmpresaOut(BaseModel):
    """Vista enriquecida de la suscripción de una empresa y su consumo frente a los límites del plan."""

    model_config = ConfigDict(from_attributes=True)

    id_suscripcion: int
    id_tenant: int
    codigo_empresa: str
    nombre_empresa: str
    estado_empresa: str
    id_plan: int
    nombre_plan: str
    precio_mensual: Decimal
    estado: str
    fecha_inicio: date
    fecha_vencimiento: date
    vigente: bool
    sucursales_activas: int
    max_sucursales_activas: int
    empleados_activos: int
    max_empleados: Optional[int] = None
    creado_en: datetime


class HistorialSuscripcionItemOut(BaseModel):
    """Entrada del historial inmutable de eventos de suscripción (RN17)."""

    model_config = ConfigDict(from_attributes=True)

    id_historial: int
    id_tenant: int
    id_suscripcion: int
    evento: str
    detalle: Optional[dict[str, Any]] = None
    id_usuario: Optional[int] = None
    creado_en: datetime

