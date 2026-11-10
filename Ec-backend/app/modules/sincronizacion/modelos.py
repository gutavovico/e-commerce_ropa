"""ORM de la operación sin conexión (migración 0020).

Spec: `.specs/finalized/P2-CU14-CU15-CU19-CU20-sin-conexion/plan.md` §4. Todas son tablas de empresa:
`id_tenant` se mapea con `FetchedValue()` y PostgreSQL lo toma del contexto de la transacción.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import FetchedValue

from core.database import Base

ESQUEMA = {"schema": "fashionstore"}

PLATAFORMAS = ("pwa", "flutter")
TIPOS_OPERACION = ("reserva", "compra_interrumpida")
ESTADOS_OPERACION = ("confirmada", "rechazada", "en_conflicto")
TIPOS_CONFLICTO = (
    "stock_insuficiente",
    "precio_modificado",
    "producto_inactivo",
    "sucursal_inactiva",
    "suscripcion_no_vigente",
    # Compra cobrada que supera `dias_antiguedad_offline` (RN41): también se reembolsa.
    "antiguedad_excedida",
)
ESTADOS_CONFLICTO = ("pendiente", "reembolso_pendiente", "resuelto")
TIPOS_AVISO = ("reserva_cancelada", "reembolso_aceptado", "reembolso_procesado")


class DispositivoORM(Base):
    __tablename__ = "dispositivos"
    __table_args__ = ESQUEMA

    id_dispositivo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    identificador: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    id_cliente: Mapped[int] = mapped_column(BigInteger, nullable=False)
    plataforma: Mapped[str] = mapped_column(String(10), nullable=False)
    codigo_corto: Mapped[str] = mapped_column(String(4), nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ultima_descarga_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ultima_sincronizacion_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    token_push: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class OperacionSyncORM(Base):
    __tablename__ = "operaciones_sync"
    __table_args__ = ESQUEMA

    id_operacion_sync: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    uuid_operacion: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    id_dispositivo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_sucursal: Mapped[Optional[int]] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(25), nullable=False)
    estado: Mapped[str] = mapped_column(String(15), nullable=False)
    codigo_provisional: Mapped[Optional[str]] = mapped_column(String(24))
    registrada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recibida_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    datos: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resultado: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    motivo: Mapped[Optional[str]] = mapped_column(String(40))
    id_reserva: Mapped[Optional[int]] = mapped_column(BigInteger)
    id_venta: Mapped[Optional[int]] = mapped_column(BigInteger)


class ConflictoSyncORM(Base):
    __tablename__ = "conflictos_sync"
    __table_args__ = ESQUEMA

    id_conflicto: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    id_operacion_sync: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_venta: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_pago: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_sucursal: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    detalle: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    estado: Mapped[str] = mapped_column(String(25), nullable=False, default="pendiente")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    aceptado_por: Mapped[Optional[int]] = mapped_column(BigInteger)
    aceptado_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resuelto_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    referencia_reembolso: Mapped[Optional[str]] = mapped_column(String(150))
    intentos_reembolso: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultimo_error: Mapped[Optional[str]] = mapped_column(Text)


class SyncLogORM(Base):
    __tablename__ = "sync_log"
    __table_args__ = ESQUEMA

    id_sync_log: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    id_dispositivo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(String(15), nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finalizado_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resultado: Mapped[str] = mapped_column(String(10), nullable=False)
    enviadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rechazadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    en_conflicto: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mensaje: Mapped[Optional[str]] = mapped_column(String(500))


class AvisoClienteORM(Base):
    __tablename__ = "avisos_cliente"
    __table_args__ = ESQUEMA

    id_aviso: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    id_cliente: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(String(25), nullable=False)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(500), nullable=False)
    id_reserva: Mapped[Optional[int]] = mapped_column(BigInteger)
    id_venta: Mapped[Optional[int]] = mapped_column(BigInteger)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    leido_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
