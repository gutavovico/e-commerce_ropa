"""Esquemas Pydantic v2 para P2-CU06: Gestionar planes y funcionalidades.

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` §3.2 (CU06).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FuncionalidadOut(BaseModel):
    """Funcionalidad del catálogo de plataforma (RN11)."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    descripcion: Optional[str] = None


class PlanBaseIn(BaseModel):
    """Atributos comunes para crear o editar un plan de suscripción (RN11, RN12)."""

    nombre: str = Field(..., min_length=2, max_length=60)
    precio_mensual: Decimal = Field(..., ge=Decimal("0.00"), max_digits=10, decimal_places=2)
    max_sucursales_activas: int = Field(..., ge=1)
    max_empleados: Optional[int] = Field(
        default=None,
        ge=1,
        description="Máximo de empleados activos permitidos; None significa sin límite (F14)",
    )
    funcionalidades: list[str] = Field(..., min_length=1)

    @field_validator("funcionalidades")
    @classmethod
    def normalizar_funcionalidades(cls, v: list[str]) -> list[str]:
        limpios: list[str] = []
        vistos: set[str] = set()
        for item in v:
            cod = item.strip().lower()
            if cod and cod not in vistos:
                vistos.add(cod)
                limpios.append(cod)
        if not limpios:
            raise ValueError("El plan debe incluir al menos una funcionalidad.")
        return limpios


class PlanCrearIn(PlanBaseIn):
    """Payload de creación de un plan de suscripción."""


class PlanActualizarIn(PlanBaseIn):
    """Payload de actualización de un plan de suscripción."""


class CambiarEstadoPlanIn(BaseModel):
    """Solicitud para activar o desactivar un plan (CU06 A2)."""

    activo: bool


class PlanDetalleOut(BaseModel):
    """Representación completa de un plan con sus funcionalidades, métricas y advertencias (CU06 A1)."""

    model_config = ConfigDict(from_attributes=True)

    id_plan: int
    nombre: str
    precio_mensual: Decimal
    max_sucursales_activas: int
    max_empleados: Optional[int] = None
    activo: bool
    creado_en: datetime
    funcionalidades: list[FuncionalidadOut]
    codigos_funcionalidades: list[str]
    empresas_suscritas_vigentes: int = 0
    empresas_suscritas_totales: int = 0
    advertencias: list[str] = Field(default_factory=list)

