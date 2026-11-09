"""Esquemas de P2-CU11 · Parámetros de la empresa.

Spec: `.specs/finalized/P2-CU11-parametros-empresa/spec.md` §3 (C2, C3).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

#: C3: rangos que admite la API (la base solo comprueba los mínimos).
HORAS_RESERVA = (1, 168)
DIAS_CAMBIO = (0, 90)
DIAS_OFFLINE = (1, 30)


class ParametrosEmpresaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    moneda: str
    zona_horaria: str
    horas_vencimiento_reserva: int
    dias_cambio_prenda: int
    operacion_offline_habilitada: bool
    dias_antiguedad_offline: int
    actualizado_en: datetime


class ParametrosEmpresaIn(BaseModel):
    """Los cuatro parámetros editables (C2: moneda y zona horaria no se cambian aquí; si llegan,
    se ignoran)."""

    model_config = ConfigDict(extra="ignore")

    horas_vencimiento_reserva: int = Field(..., ge=HORAS_RESERVA[0], le=HORAS_RESERVA[1])
    dias_cambio_prenda: int = Field(..., ge=DIAS_CAMBIO[0], le=DIAS_CAMBIO[1])
    operacion_offline_habilitada: bool
    dias_antiguedad_offline: int = Field(..., ge=DIAS_OFFLINE[0], le=DIAS_OFFLINE[1])
