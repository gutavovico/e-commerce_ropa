"""Modelos ORM SQLAlchemy 2.0 para P2-CU23, P2-CU24 y P2-CU25 (Aprendizaje Automático)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class DatasetMlORM(Base):
    """Conjunto de datos de aprendizaje automático por empresa (`fashionstore.datasets_ml`, P2-CU23)."""

    __tablename__ = "datasets_ml"
    __table_args__ = {"schema": "fashionstore"}

    id_dataset: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(140), nullable=False)
    origen: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad_registros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    variables_seleccionadas: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    parametros_generacion: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    resumen_preprocesamiento: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    muestra_datos: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    creado_por: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ModeloMlORM(Base):
    """Modelo supervisado o no supervisado entrenado por empresa (`fashionstore.modelos_ml`, P2-CU23)."""

    __tablename__ = "modelos_ml"
    __table_args__ = {"schema": "fashionstore"}

    id_modelo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    id_dataset: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(String(140), nullable=False)
    tipo_modelo: Mapped[str] = mapped_column(String(25), nullable=False)
    algoritmo: Mapped[str] = mapped_column(String(80), nullable=False)
    variable_objetivo: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    variables_entrada: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    origen_datos: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(25), nullable=False, default="evaluado")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    motivo_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metricas_entrenamiento: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    metricas_validacion: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    metricas_prueba: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    creado_por: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PrediccionMlORM(Base):
    """Predicción generada por un modelo supervisado (`fashionstore.predicciones_ml`, P2-CU24, RN50)."""

    __tablename__ = "predicciones_ml"
    __table_args__ = {"schema": "fashionstore"}

    id_prediccion: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    id_modelo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_producto: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    nombre_producto: Mapped[str] = mapped_column(String(150), nullable=False)
    id_sucursal: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    nombre_sucursal: Mapped[str] = mapped_column(String(120), nullable=False)
    periodo: Mapped[str] = mapped_column(String(40), nullable=False)
    demanda_esperada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ingresos_esperados_bob: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    probabilidad: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0.5000")
    )
    nivel_confianza: Mapped[str] = mapped_column(String(25), nullable=False, default="ALTA")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SegmentoClienteMlORM(Base):
    """Grupo de clientes detectado por un modelo no supervisado (`fashionstore.segmentos_clientes_ml`, P2-CU25)."""

    __tablename__ = "segmentos_clientes_ml"
    __table_args__ = {"schema": "fashionstore"}

    id_segmento: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_tenant: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    id_modelo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    codigo_grupo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre_grupo: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    cantidad_clientes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    caracteristicas: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    clientes_muestra: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

