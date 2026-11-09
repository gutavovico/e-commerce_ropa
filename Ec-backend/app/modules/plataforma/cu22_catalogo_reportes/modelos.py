"""Modelo ORM de SQLAlchemy 2.0 para el catálogo de reportes permitidos por la IA (P2-CU22)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CatalogoReporteIaORM(Base):
    """Mapeo de la tabla global `fashionstore.catalogo_reportes_ia`."""

    __tablename__ = "catalogo_reportes_ia"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_reporte_catalogo: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    codigo: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vista_origen: Mapped[str] = mapped_column(String(80), nullable=False)
    metricas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dimensiones: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    filtros_permitidos: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tipos_grafico: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ejemplos_consulta: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

