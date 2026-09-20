"""Modelos ORM de SQLAlchemy 2.0 para el paquete autenticacion_seguridad.

Mapea las tablas `fashionstore.usuarios` y `fashionstore.clientes` con fidelidad
al esquema de base de datos definido en SI2-Parcial1.md.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

rol_usuario_enum = PG_ENUM(
    "cliente",
    "administrador",
    "encargado_sucursal",
    "cajero",
    "proveedor",
    name="rol_usuario",
    schema="fashionstore",
    create_type=False,
)


class UsuarioORM(Base):
    """Entidad ORM que mapea la tabla `fashionstore.usuarios`."""

    __tablename__ = "usuarios"
    __table_args__ = {"schema": "fashionstore"}

    id_usuario: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    rol: Mapped[str] = mapped_column(rol_usuario_enum, nullable=False, default="cliente", index=True)
    id_sucursal: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relacion 1:1 con ClienteORM
    cliente: Mapped[Optional["ClienteORM"]] = relationship(
        "ClienteORM",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )


class ClienteORM(Base):
    """Entidad ORM que mapea la tabla `fashionstore.clientes`."""

    __tablename__ = "clientes"
    __table_args__ = {"schema": "fashionstore"}

    id_cliente: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.usuarios.id_usuario", ondelete="CASCADE"),
        primary_key=True,
    )
    fecha_nacimiento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    genero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    talla_preferida: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ciudad_preferida: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    acepta_marketing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relacion inversa con UsuarioORM
    usuario: Mapped["UsuarioORM"] = relationship(
        "UsuarioORM",
        back_populates="cliente",
    )


class CodigoRecuperacionORM(Base):
    """Entidad ORM que mapea la tabla `fashionstore.codigos_recuperacion` para códigos OTP."""

    __tablename__ = "codigos_recuperacion"
    __table_args__ = {"schema": "fashionstore"}

    id_codigo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ip_solicitante: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relacion con UsuarioORM
    usuario: Mapped["UsuarioORM"] = relationship("UsuarioORM")

