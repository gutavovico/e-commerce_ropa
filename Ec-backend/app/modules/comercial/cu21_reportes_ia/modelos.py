"""Modelo ORM de SQLAlchemy 2.0 para solicitudes de reportes con IA (P2-CU21)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import FetchedValue

from core.database import Base


class SolicitudReporteIaORM(Base):
    """Mapeo de la tabla `fashionstore.solicitudes_reporte_ia` (aislada por `id_tenant`)."""

    __tablename__ = "solicitudes_reporte_ia"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_solicitud: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=FetchedValue()
    )
    id_usuario: Mapped[int] = mapped_column(BigInteger, nullable=False)
    comando_voz_texto: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_reporte: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resultado_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="completada"
    )
    interpretacion: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    formato_visualizacion: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="ambos"
    )
    mensaje_estado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exportaciones: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

