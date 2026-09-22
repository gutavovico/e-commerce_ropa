"""Modelos ORM de SQLAlchemy 2.0 para el paquete de Gestion Operativa.

Mapea las tablas de infraestructura territorial del esquema `fashionstore`:
- ciudades
- sucursales
"""

from datetime import datetime, time, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class CiudadORM(Base):
    """Mapeo de la tabla `fashionstore.ciudades`."""

    __tablename__ = "ciudades"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_ciudad: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    pais: Mapped[str] = mapped_column(String(100), nullable=False, default="Bolivia")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sucursales: Mapped[List["SucursalORM"]] = relationship(
        "SucursalORM",
        back_populates="ciudad",
        cascade="all, delete-orphan",
    )


class SucursalORM(Base):
    """Mapeo de la tabla `fashionstore.sucursales`."""

    __tablename__ = "sucursales"
    __table_args__ = (
        UniqueConstraint("id_ciudad", "nombre", name="uq_sucursales_ciudad_nombre"),
        {"schema": "fashionstore", "extend_existing": True},
    )

    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_ciudad: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fashionstore.ciudades.id_ciudad"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    horario_apertura: Mapped[time] = mapped_column(Time, nullable=False, default=time(9, 0))
    horario_cierre: Mapped[time] = mapped_column(Time, nullable=False, default=time(20, 0))
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ciudad: Mapped["CiudadORM"] = relationship("CiudadORM", back_populates="sucursales")
