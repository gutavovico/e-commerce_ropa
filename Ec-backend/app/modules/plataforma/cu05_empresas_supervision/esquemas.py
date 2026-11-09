"""Esquemas Pydantic v2 para P2-CU05: Gestionar empresas y supervisar la plataforma.

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` §3.2 (CU05).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

CODIGOS_RESERVADOS_EMPRESA = frozenset({
    "admin",
    "login",
    "registro",
    "recuperar-acceso",
    "recuperar-password",
    "iniciar-sesion",
    "api",
    "ar",
    "static",
    "assets",
    "mis-tiendas",
    "pago",
    "plataforma",
})


class AdminInicialEmpresaIn(BaseModel):
    """Datos del primer usuario con rol `administrador` de la nueva empresa."""

    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    telefono: Optional[str] = Field(default=None, max_length=30)


class EmpresaCrearIn(BaseModel):
    """Payload de alta atómica de empresa, suscripción inicial y administrador."""

    codigo: str = Field(
        ...,
        min_length=3,
        max_length=60,
        pattern=r"^[a-z0-9-]{3,60}$",
        description="Identificador corto único de la empresa (3-60 caracteres: minúsculas, números y guiones)",
    )
    nombre: str = Field(..., min_length=2, max_length=150)
    correo_contacto: Optional[EmailStr] = None
    telefono: Optional[str] = Field(default=None, max_length=30)
    id_plan: int = Field(..., gt=0)
    estado_suscripcion: Literal["prueba", "activa"] = "activa"
    fecha_inicio: date
    fecha_vencimiento: date
    admin_inicial: AdminInicialEmpresaIn

    @field_validator("codigo", mode="before")
    @classmethod
    def normalizar_codigo(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @model_validator(mode="after")
    def validar_fechas(self) -> "EmpresaCrearIn":
        if self.fecha_vencimiento <= self.fecha_inicio:
            raise ValueError("La fecha de vencimiento debe ser posterior a la fecha de inicio (RN13).")
        return self


class EmpresaActualizarIn(BaseModel):
    """Datos editables de una empresa registrada (el código es inmutable por RN03)."""

    nombre: str = Field(..., min_length=2, max_length=150)
    correo_contacto: Optional[EmailStr] = None
    telefono: Optional[str] = Field(default=None, max_length=30)


class CambiarEstadoEmpresaIn(BaseModel):
    """Solicitud de cambio de estado operativo de una empresa (RN08, RN09, RN10)."""

    estado: Literal["activa", "suspendida", "baja"]
    motivo: Optional[str] = Field(default=None, max_length=500)


class SuscripcionResumenEmpresaOut(BaseModel):
    """Resumen de la suscripción actual de la empresa."""

    model_config = ConfigDict(from_attributes=True)

    id_suscripcion: int
    id_plan: int
    nombre_plan: str
    estado: str
    fecha_inicio: date
    fecha_vencimiento: date
    vigente: bool


class IndicadoresEmpresaOut(BaseModel):
    """Indicadores agregados de actividad de una empresa sin exponer datos privados."""

    sucursales_activas: int
    sucursales_totales: int
    empleados_activos: int
    productos_activos: int
    ventas_pagadas_cantidad: int
    ventas_pagadas_monto: Decimal
    reservas_totales: int


class EmpresaResumenOut(BaseModel):
    """Vista resumida de una empresa para el listado de supervisión."""

    model_config = ConfigDict(from_attributes=True)

    id_tenant: int
    codigo: str
    nombre: str
    correo_contacto: Optional[str] = None
    telefono: Optional[str] = None
    estado: str
    creado_en: datetime
    suscripcion_actual: Optional[SuscripcionResumenEmpresaOut] = None
    indicadores: IndicadoresEmpresaOut


class EmpresaDetalleOut(EmpresaResumenOut):
    """Detalle completo de la empresa con datos de su administrador principal."""

    admin_email: Optional[str] = None
    admin_nombre: Optional[str] = None


class MetricasPorEmpresaItem(BaseModel):
    """Fila de indicadores consolidados por empresa para el tablero de plataforma."""

    id_tenant: int
    codigo: str
    nombre: str
    estado_empresa: str
    nombre_plan: Optional[str] = None
    estado_suscripcion: Optional[str] = None
    sucursales_activas: int
    empleados_activos: int
    productos_activos: int
    ventas_pagadas_cantidad: int
    ventas_pagadas_monto: Decimal


class MetricasPlataformaOut(BaseModel):
    """Métricas globales del SaaS (CU05 paso 8)."""

    empresas_totales: int
    empresas_activas: int
    empresas_suspendidas: int
    empresas_baja: int
    suscripciones_vigentes: int
    suscripciones_vencidas_o_suspendidas: int
    sucursales_activas_totales: int
    empleados_activos_totales: int
    ventas_pagadas_totales: int
    monto_ventas_pagadas_total: Decimal
    desglose_empresas: list[MetricasPorEmpresaItem]


class BitacoraPlataformaItemOut(BaseModel):
    """Evento de bitácora enriquecido con información de la empresa originadora."""

    id_bitacora: int
    id_tenant: Optional[int] = None
    codigo_empresa: Optional[str] = None
    nombre_empresa: Optional[str] = None
    id_usuario: Optional[int] = None
    usuario_nombre: Optional[str] = None
    accion: str
    tabla_modulo: str
    direccion_ip: Optional[str] = None
    severidad: str
    tiene_payload: bool
    payload_anterior: Optional[dict[str, Any]] = None
    payload_nuevo: Optional[dict[str, Any]] = None
    creado_en: datetime


class BitacoraPlataformaListadoOut(BaseModel):
    """Respuesta paginada de la bitácora global de plataforma."""

    items: list[BitacoraPlataformaItemOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int

