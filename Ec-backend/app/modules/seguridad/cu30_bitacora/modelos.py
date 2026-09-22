"""Modelos ORM para CU30: Consultar bitacora.

Mapea la tabla de auditoria inmutable fashionstore.bitacora.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Bitacora(Base):
    """Entidad inmutable de registro de eventos de auditoria y trazabilidad."""

    __tablename__ = "bitacora"
    __table_args__ = {"schema": "fashionstore"}

    id_bitacora: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Identificador secuencial unico del evento de auditoria",
    )
    id_usuario: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("fashionstore.usuarios.id_usuario", ondelete="SET NULL"),
        nullable=True,
        comment="Operador o usuario que origino el evento (nulo para procesos del sistema)",
    )
    usuario_nombre: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nombre descriptivo o correo del operador capturado en el momento del evento",
    )
    accion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Accion operativa ejecutada (ej: CREACION, MODIFICACION, ELIMINACION, LOGIN)",
    )
    tabla_modulo: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Modulo o entidad afectada por la transaccion",
    )
    direccion_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Direccion IPv4 o IPv6 desde la cual se origino la peticion",
    )
    severidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INFO",
        comment="Nivel de criticidad: INFO, WARN, ERROR, CRITICAL",
    )
    payload_anterior: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Estado previo de la entidad antes de la mutacion",
    )
    payload_nuevo: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Estado resultante de la entidad tras la mutacion",
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Marca temporal inmutable de ocurrencia del evento",
    )
