"""Repositorio de acceso a datos para P2-CU22: Gestionar catálogo de reportes permitidos."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.plataforma.cu22_catalogo_reportes.modelos import CatalogoReporteIaORM


class CatalogoReportesRepositorio:
    """Operaciones CRUD sobre `fashionstore.catalogo_reportes_ia`."""

    @staticmethod
    def listar(db: Session, *, solo_activos: bool = False) -> list[CatalogoReporteIaORM]:
        stmt = select(CatalogoReporteIaORM).order_by(
            CatalogoReporteIaORM.id_reporte_catalogo.asc()
        )
        if solo_activos:
            stmt = stmt.where(CatalogoReporteIaORM.activo.is_(True))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener_por_id(db: Session, id_reporte: int) -> Optional[CatalogoReporteIaORM]:
        return db.get(CatalogoReporteIaORM, id_reporte)

    @staticmethod
    def obtener_por_codigo(db: Session, codigo: str) -> Optional[CatalogoReporteIaORM]:
        stmt = select(CatalogoReporteIaORM).where(
            func.lower(CatalogoReporteIaORM.codigo) == codigo.strip().lower()
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def crear(db: Session, datos: dict) -> CatalogoReporteIaORM:
        ahora = datetime.now(timezone.utc)
        item = CatalogoReporteIaORM(
            codigo=datos["codigo"],
            nombre=datos["nombre"],
            descripcion=datos.get("descripcion"),
            vista_origen=datos["vista_origen"],
            metricas=datos["metricas"],
            dimensiones=datos["dimensiones"],
            filtros_permitidos=datos.get("filtros_permitidos", []),
            tipos_grafico=datos["tipos_grafico"],
            ejemplos_consulta=datos.get("ejemplos_consulta", []),
            activo=datos.get("activo", True),
            creado_en=ahora,
            actualizado_en=ahora,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def actualizar(
        db: Session, item: CatalogoReporteIaORM, datos: dict
    ) -> CatalogoReporteIaORM:
        item.codigo = datos["codigo"]
        item.nombre = datos["nombre"]
        item.descripcion = datos.get("descripcion")
        item.vista_origen = datos["vista_origen"]
        item.metricas = datos["metricas"]
        item.dimensiones = datos["dimensiones"]
        item.filtros_permitidos = datos.get("filtros_permitidos", [])
        item.tipos_grafico = datos["tipos_grafico"]
        item.ejemplos_consulta = datos.get("ejemplos_consulta", [])
        item.activo = datos.get("activo", item.activo)
        item.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def cambiar_estado(
        db: Session, item: CatalogoReporteIaORM, activo: bool
    ) -> CatalogoReporteIaORM:
        item.activo = activo
        item.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item

