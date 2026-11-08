"""ORM del modelo multitenant (migraciones 0012 y 0013).

Spec: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.1. Las columnas `id_tenant` de las
tablas de una empresa se mapean con `FetchedValue()`: si el código no las indica, PostgreSQL toma la
empresa del contexto de la transacción (F2).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import FetchedValue

from core.database import Base

ESQUEMA = {"schema": "fashionstore"}


class TenantORM(Base):
    __tablename__ = "tenants"
    __table_args__ = ESQUEMA

    id_tenant: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo_contacto: Mapped[Optional[str]] = mapped_column(String(255))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="activa")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FuncionalidadORM(Base):
    __tablename__ = "funcionalidades"
    __table_args__ = ESQUEMA

    codigo: Mapped[str] = mapped_column(String(50), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String)


class PlanORM(Base):
    __tablename__ = "planes"
    __table_args__ = ESQUEMA

    id_plan: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    precio_mensual: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    max_sucursales_activas: Mapped[int] = mapped_column(Integer, nullable=False)
    #: None = sin límite (F14)
    max_empleados: Mapped[Optional[int]] = mapped_column(Integer)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PlanFuncionalidadORM(Base):
    __tablename__ = "plan_funcionalidades"
    __table_args__ = ESQUEMA

    id_plan: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.planes.id_plan", ondelete="CASCADE"), primary_key=True
    )
    codigo_funcionalidad: Mapped[str] = mapped_column(
        String(50), ForeignKey("fashionstore.funcionalidades.codigo"), primary_key=True
    )


class SuscripcionORM(Base):
    __tablename__ = "suscripciones"
    __table_args__ = ESQUEMA

    id_suscripcion: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_tenant: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.tenants.id_tenant"), nullable=False, server_default=FetchedValue()
    )
    id_plan: Mapped[int] = mapped_column(BigInteger, ForeignKey("fashionstore.planes.id_plan"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class HistorialSuscripcionORM(Base):
    __tablename__ = "historial_suscripcion"
    __table_args__ = ESQUEMA

    id_historial: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    id_suscripcion: Mapped[int] = mapped_column(BigInteger, nullable=False)
    evento: Mapped[str] = mapped_column(String(30), nullable=False)
    detalle: Mapped[Optional[dict]] = mapped_column(JSONB)
    id_usuario: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.usuarios.id_usuario", ondelete="SET NULL")
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ConfiguracionTenantORM(Base):
    __tablename__ = "configuracion_tenant"
    __table_args__ = ESQUEMA

    id_tenant: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.tenants.id_tenant", ondelete="CASCADE"),
        primary_key=True, server_default=FetchedValue(),
    )
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, server_default="EUR")
    zona_horaria: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Europe/Madrid")
    horas_vencimiento_reserva: Mapped[int] = mapped_column(Integer, nullable=False, server_default="24")
    dias_cambio_prenda: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
    operacion_offline_habilitada: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    dias_antiguedad_offline: Mapped[int] = mapped_column(Integer, nullable=False, server_default="7")
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ClienteTenantORM(Base):
    """F9: registro de un cliente (cuenta global) en una empresa."""

    __tablename__ = "cliente_tenant"
    __table_args__ = ESQUEMA

    id_tenant: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.tenants.id_tenant"), primary_key=True, server_default=FetchedValue()
    )
    id_cliente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.clientes.id_cliente", ondelete="CASCADE"), primary_key=True
    )
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class EmpleadoSucursalORM(Base):
    """F10 / RN07: sucursales autorizadas de un empleado; una de ellas es la principal."""

    __tablename__ = "empleado_sucursal"
    __table_args__ = ESQUEMA

    id_tenant: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=FetchedValue())
    id_empleado: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True)
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
