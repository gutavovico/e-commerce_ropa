"""Modelo ORM para CU10: Utilizar Vestidor Virtual (Dos Motores: Local e IA Decart).

Mapea la tabla `fashionstore.sesiones_vestidor_virtual` conforme al esquema en PostgreSQL.
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class SesionVestidorORM(Base):
    """Mapeo de la tabla `fashionstore.sesiones_vestidor_virtual`."""

    __tablename__ = "sesiones_vestidor_virtual"
    __table_args__ = (
        CheckConstraint("motor IN ('local', 'ia')", name="chk_sesiones_ar_motor"),
        CheckConstraint(
            "duracion_segundos IS NULL OR duracion_segundos >= 0",
            name="chk_sesiones_ar_duracion",
        ),
        {"schema": "fashionstore", "extend_existing": True},
    )

    id_sesion_ar: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_cliente: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.clientes.id_cliente", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    id_producto: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.productos.id_producto", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    dispositivo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    motor: Mapped[str] = mapped_column(String(10), nullable=False, default="local")
    duracion_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resultado_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    genero_interes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relaciones de dominio
    cliente = relationship("ClienteORM", foreign_keys=[id_cliente], lazy="joined")
    producto = relationship("ProductoORM", foreign_keys=[id_producto], lazy="joined")

