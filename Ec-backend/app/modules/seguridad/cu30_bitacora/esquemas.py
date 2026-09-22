"""Esquemas Pydantic v2 para CU30: Consultar bitacora.

Define contratos de transferencia de datos para filtros, resumen, detalle y metricas de auditoria.
"""

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SeveridadEnum = Literal["INFO", "WARN", "ERROR", "CRITICAL"]
OrdenarPorBitacora = Literal["creado_en_desc", "creado_en_asc", "severidad_desc", "accion_asc"]


class BitacoraFiltrosParametros(BaseModel):
    """Parametros de consulta y filtrado para la bitacora de auditoria."""

    model_config = ConfigDict(extra="forbid")

    fecha_inicio: Optional[date] = Field(
        None,
        description="Fecha inicial de busqueda (inclusive, en formato YYYY-MM-DD)",
    )
    fecha_fin: Optional[date] = Field(
        None,
        description="Fecha final de busqueda (inclusive, en formato YYYY-MM-DD)",
    )
    severidad: Optional[SeveridadEnum] = Field(
        None,
        description="Nivel de severidad requerido",
    )
    tabla_modulo: Optional[str] = Field(
        None,
        description="Filtrar por nombre del modulo o tabla afectada",
    )
    accion: Optional[str] = Field(
        None,
        description="Filtrar por accion ejecutada (ej: CREACION, MODIFICACION, ELIMINACION)",
    )
    q: Optional[str] = Field(
        None,
        description="Termino de busqueda en usuario, accion, modulo o direccion IP",
    )
    ordenar_por: OrdenarPorBitacora = Field(
        default="creado_en_desc",
        description="Criterio de ordenacion de los eventos",
    )
    pagina: int = Field(default=1, ge=1, description="Numero de pagina")
    limite: int = Field(default=20, ge=1, le=100, description="Tamano de pagina")


class BitacoraEventoResumen(BaseModel):
    """Resumen de un evento de auditoria para presentacion en tabla cronologica."""

    model_config = ConfigDict(from_attributes=True)

    id_bitacora: int = Field(..., description="ID unico del evento")
    id_usuario: Optional[int] = Field(None, description="ID del usuario operador")
    usuario_nombre: Optional[str] = Field(None, description="Nombre o correo del operador")
    accion: str = Field(..., description="Accion formal ejecutada")
    tabla_modulo: str = Field(..., description="Modulo o recurso impactado")
    direccion_ip: Optional[str] = Field(None, description="Direccion IP de origen")
    severidad: str = Field(..., description="Severidad: INFO, WARN, ERROR o CRITICAL")
    tiene_payload: bool = Field(..., description="Indica si el evento contiene payload anterior o nuevo")
    creado_en: datetime = Field(..., description="Marca de tiempo UTC de creacion")


class BitacoraEventoDetalle(BitacoraEventoResumen):
    """Detalle exhaustivo de un evento incluyendo payloads serializados."""

    payload_anterior: Optional[dict[str, Any]] = Field(
        None,
        description="Snapshot del estado anterior en formato JSON",
    )
    payload_nuevo: Optional[dict[str, Any]] = Field(
        None,
        description="Snapshot del nuevo estado resultante en formato JSON",
    )


class BitacoraMetricas(BaseModel):
    """Metricas consolidadas de auditoria en el periodo consultado."""

    total_eventos: int = Field(0, description="Total general de eventos registrados")
    eventos_criticos: int = Field(0, description="Total de eventos con severidad CRITICAL")
    advertencias_errores: int = Field(0, description="Total de eventos con severidad WARN o ERROR")
    usuarios_activos: int = Field(0, description="Cantidad de operadores unicos con registros")


class BitacoraListadoRespuesta(BaseModel):
    """Respuesta paginada completa con lista de eventos y metricas ejecutivas."""

    items: list[BitacoraEventoResumen] = Field(default_factory=list, description="Listado de eventos de la pagina")
    total: int = Field(0, description="Total de eventos coincidentes con los filtros")
    pagina: int = Field(1, description="Pagina actual")
    limite: int = Field(20, description="Cantidad de elementos por pagina")
    total_paginas: int = Field(1, description="Total de paginas disponibles")
    metricas: BitacoraMetricas = Field(default_factory=BitacoraMetricas, description="Metricas agregadas")


class RegistrarEventoBitacoraIn(BaseModel):
    """Esquema interno para registro programatico de nuevos eventos de bitacora."""

    id_usuario: Optional[int] = None
    usuario_nombre: Optional[str] = None
    accion: str
    tabla_modulo: str
    direccion_ip: Optional[str] = None
    severidad: SeveridadEnum = "INFO"
    payload_anterior: Optional[dict[str, Any]] = None
    payload_nuevo: Optional[dict[str, Any]] = None
