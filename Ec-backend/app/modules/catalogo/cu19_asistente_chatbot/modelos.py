"""Modelo ORM para el CU19: Asistente Inteligente / Chatbot.

Mapea la tabla `fashionstore.interacciones_chatbot` conforme al esquema en PostgreSQL.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from modules.reservas.modelos import canal_origen_enum


class InteraccionChatbotORM(Base):
    """Mapeo de la tabla `fashionstore.interacciones_chatbot`."""

    __tablename__ = "interacciones_chatbot"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_interaccion: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_cliente: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.clientes.id_cliente", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    mensaje_usuario: Mapped[str] = mapped_column(Text, nullable=False)
    respuesta_ia: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    canal: Mapped[str] = mapped_column(canal_origen_enum, nullable=False, default="web")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relación opcional con cliente
    cliente = relationship(
        "ClienteORM",
        foreign_keys=[id_cliente],
        lazy="joined",
    )

