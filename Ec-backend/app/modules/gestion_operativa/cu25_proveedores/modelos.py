"""Modelos ORM de SQLAlchemy 2.0 para CU25: Gestionar Proveedores.

Mapeo relacional de la tabla fashionstore.proveedores para administracion
de talleres textiles, fabricantes y confeccionistas en la cadena de abastecimiento.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ProveedorORM(Base):
    """Mapeo de la tabla `fashionstore.proveedores`."""

    __tablename__ = "proveedores"
    __table_args__ = (
        UniqueConstraint("nit_rut", name="uq_proveedores_nit_rut"),
        UniqueConstraint("razon_social", name="uq_proveedores_razon_social"),
        CheckConstraint("length(trim(razon_social)) >= 3", name="chk_proveedores_razon_social_len"),
        CheckConstraint("length(trim(nit_rut)) >= 5", name="chk_proveedores_nit_rut_len"),
        CheckConstraint("length(trim(contacto_nombre)) >= 3", name="chk_proveedores_contacto_len"),
        {"schema": "fashionstore", "extend_existing": True},
    )

    id_proveedor: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.usuarios.id_usuario"),
        nullable=True,
        index=True,
    )
    razon_social: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    nit_rut: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    contacto_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    rubro: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    estado_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
