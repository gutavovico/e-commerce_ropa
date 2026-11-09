"""Esquemas de P2-CU11 · Parámetros de la empresa.

Spec: `.specs/finalized/P2-CU11-parametros-empresa/spec.md` §3 (C3) y
`.specs/finalized/P2-CU11-fix-moneda-zona-bolivia/spec.md` (M1, M3, M4: moneda y zona editables).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from core.moneda import Moneda
from core.tiempo import ZONA_EMPRESA

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
    #: M3: la empresa ya tiene ventas o pagos y no puede cambiar de moneda.
    moneda_bloqueada: bool = False


class ParametrosEmpresaIn(BaseModel):
    """Parámetros editables. Moneda: BOB o USD (M1). Zona horaria: solo la de Bolivia (M4)."""

    model_config = ConfigDict(extra="ignore")

    moneda: Moneda
    zona_horaria: Literal["America/La_Paz"] = ZONA_EMPRESA

    horas_vencimiento_reserva: int = Field(..., ge=HORAS_RESERVA[0], le=HORAS_RESERVA[1])
    dias_cambio_prenda: int = Field(..., ge=DIAS_CAMBIO[0], le=DIAS_CAMBIO[1])
    operacion_offline_habilitada: bool
    dias_antiguedad_offline: int = Field(..., ge=DIAS_OFFLINE[0], le=DIAS_OFFLINE[1])
