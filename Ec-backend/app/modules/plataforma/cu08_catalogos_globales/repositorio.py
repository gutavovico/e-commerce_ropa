"""Repositorio de datos para P2-CU08: Gestionar catálogos globales (ciudades, tallas, colores).

Opera mediante expresiones SQLAlchemy Core sobre `fashionstore.ciudades`, `fashionstore.tallas`
y `fashionstore.colores` sin modificar los modelos ORM de `gestion_operativa` ni `catalogo`.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, SmallInteger, String, column, delete, func, insert, select, table, update
from sqlalchemy.orm import Session

_t_ciudades = table(
    "ciudades",
    column("id_ciudad", Integer),
    column("nombre", String(100)),
    column("pais", String(100)),
    column("activo", Boolean),
    column("creado_en", DateTime(timezone=True)),
    schema="fashionstore",
)

_t_tallas = table(
    "tallas",
    column("id_talla", Integer),
    column("codigo", String(10)),
    column("orden", SmallInteger),
    column("activo", Boolean),
    schema="fashionstore",
)

_t_colores = table(
    "colores",
    column("id_color", Integer),
    column("nombre", String(50)),
    column("codigo_hex", String(7)),
    column("activo", Boolean),
    schema="fashionstore",
)

_t_sucursales = table(
    "sucursales",
    column("id_sucursal", Integer),
    column("id_ciudad", Integer),
    schema="fashionstore",
)

_t_variantes = table(
    "variantes_producto",
    column("id_variante", Integer),
    column("id_talla", Integer),
    column("id_color", Integer),
    schema="fashionstore",
)


class CatalogosGlobalesRepositorio:
    """Persistencia y conteo de referencias para ciudades, tallas y colores globales."""

    # --- Ciudades ---

    @staticmethod
    def listar_ciudades(db: Session, *, solo_activas: bool = False) -> list[dict[str, Any]]:
        stmt = select(
            _t_ciudades.c.id_ciudad,
            _t_ciudades.c.nombre,
            _t_ciudades.c.pais,
            _t_ciudades.c.activo,
            _t_ciudades.c.creado_en,
            func.count(_t_sucursales.c.id_sucursal).label("sucursales_asociadas"),
        ).outerjoin(_t_sucursales, _t_sucursales.c.id_ciudad == _t_ciudades.c.id_ciudad)
        if solo_activas:
            stmt = stmt.where(_t_ciudades.c.activo.is_(True))
        stmt = stmt.group_by(
            _t_ciudades.c.id_ciudad,
            _t_ciudades.c.nombre,
            _t_ciudades.c.pais,
            _t_ciudades.c.activo,
            _t_ciudades.c.creado_en,
        ).order_by(_t_ciudades.c.nombre.asc())
        return [dict(r._mapping) for r in db.execute(stmt).all()]

    @staticmethod
    def obtener_ciudad(db: Session, id_ciudad: int) -> Optional[dict[str, Any]]:
        stmt = (
            select(
                _t_ciudades.c.id_ciudad,
                _t_ciudades.c.nombre,
                _t_ciudades.c.pais,
                _t_ciudades.c.activo,
                _t_ciudades.c.creado_en,
                func.count(_t_sucursales.c.id_sucursal).label("sucursales_asociadas"),
            )
            .outerjoin(_t_sucursales, _t_sucursales.c.id_ciudad == _t_ciudades.c.id_ciudad)
            .where(_t_ciudades.c.id_ciudad == id_ciudad)
            .group_by(
                _t_ciudades.c.id_ciudad,
                _t_ciudades.c.nombre,
                _t_ciudades.c.pais,
                _t_ciudades.c.activo,
                _t_ciudades.c.creado_en,
            )
        )
        fila = db.execute(stmt).first()
        return dict(fila._mapping) if fila else None

    @staticmethod
    def buscar_ciudad_por_nombre(
        db: Session, nombre: str, *, excluir_id: Optional[int] = None
    ) -> Optional[int]:
        stmt = select(_t_ciudades.c.id_ciudad).where(
            func.lower(_t_ciudades.c.nombre) == nombre.strip().lower()
        )
        if excluir_id is not None:
            stmt = stmt.where(_t_ciudades.c.id_ciudad != excluir_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def crear_ciudad(db: Session, *, nombre: str, pais: str) -> dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        stmt = (
            insert(_t_ciudades)
            .values(nombre=nombre, pais=pais, activo=True, creado_en=now_utc)
            .returning(
                _t_ciudades.c.id_ciudad,
                _t_ciudades.c.nombre,
                _t_ciudades.c.pais,
                _t_ciudades.c.activo,
                _t_ciudades.c.creado_en,
            )
        )
        fila = db.execute(stmt).first()
        db.commit()
        res = dict(fila._mapping)
        res["sucursales_asociadas"] = 0
        return res

    @staticmethod
    def actualizar_ciudad(
        db: Session, id_ciudad: int, *, nombre: str, pais: str
    ) -> dict[str, Any]:
        db.execute(
            update(_t_ciudades)
            .where(_t_ciudades.c.id_ciudad == id_ciudad)
            .values(nombre=nombre, pais=pais)
        )
        db.commit()
        return CatalogosGlobalesRepositorio.obtener_ciudad(db, id_ciudad)  # type: ignore[return-value]

    @staticmethod
    def cambiar_estado_ciudad(db: Session, id_ciudad: int, *, activo: bool) -> dict[str, Any]:
        db.execute(
            update(_t_ciudades)
            .where(_t_ciudades.c.id_ciudad == id_ciudad)
            .values(activo=activo)
        )
        db.commit()
        return CatalogosGlobalesRepositorio.obtener_ciudad(db, id_ciudad)  # type: ignore[return-value]

    @staticmethod
    def eliminar_ciudad(db: Session, id_ciudad: int) -> None:
        db.execute(delete(_t_ciudades).where(_t_ciudades.c.id_ciudad == id_ciudad))
        db.commit()

    # --- Tallas ---

    @staticmethod
    def listar_tallas(db: Session, *, solo_activas: bool = False) -> list[dict[str, Any]]:
        stmt = select(
            _t_tallas.c.id_talla,
            _t_tallas.c.codigo,
            _t_tallas.c.orden,
            _t_tallas.c.activo,
            func.count(_t_variantes.c.id_variante).label("variantes_asociadas"),
        ).outerjoin(_t_variantes, _t_variantes.c.id_talla == _t_tallas.c.id_talla)
        if solo_activas:
            stmt = stmt.where(_t_tallas.c.activo.is_(True))
        stmt = stmt.group_by(
            _t_tallas.c.id_talla,
            _t_tallas.c.codigo,
            _t_tallas.c.orden,
            _t_tallas.c.activo,
        ).order_by(_t_tallas.c.orden.asc(), _t_tallas.c.id_talla.asc())
        return [dict(r._mapping) for r in db.execute(stmt).all()]

    @staticmethod
    def obtener_talla(db: Session, id_talla: int) -> Optional[dict[str, Any]]:
        stmt = (
            select(
                _t_tallas.c.id_talla,
                _t_tallas.c.codigo,
                _t_tallas.c.orden,
                _t_tallas.c.activo,
                func.count(_t_variantes.c.id_variante).label("variantes_asociadas"),
            )
            .outerjoin(_t_variantes, _t_variantes.c.id_talla == _t_tallas.c.id_talla)
            .where(_t_tallas.c.id_talla == id_talla)
            .group_by(
                _t_tallas.c.id_talla,
                _t_tallas.c.codigo,
                _t_tallas.c.orden,
                _t_tallas.c.activo,
            )
        )
        fila = db.execute(stmt).first()
        return dict(fila._mapping) if fila else None

    @staticmethod
    def buscar_talla_por_codigo(
        db: Session, codigo: str, *, excluir_id: Optional[int] = None
    ) -> Optional[int]:
        stmt = select(_t_tallas.c.id_talla).where(
            func.lower(_t_tallas.c.codigo) == codigo.strip().lower()
        )
        if excluir_id is not None:
            stmt = stmt.where(_t_tallas.c.id_talla != excluir_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def crear_talla(db: Session, *, codigo: str, orden: int) -> dict[str, Any]:
        stmt = (
            insert(_t_tallas)
            .values(codigo=codigo, orden=orden, activo=True)
            .returning(
                _t_tallas.c.id_talla,
                _t_tallas.c.codigo,
                _t_tallas.c.orden,
                _t_tallas.c.activo,
            )
        )
        fila = db.execute(stmt).first()
        db.commit()
        res = dict(fila._mapping)
        res["variantes_asociadas"] = 0
        return res

    @staticmethod
    def actualizar_talla(
        db: Session, id_talla: int, *, codigo: str, orden: int
    ) -> dict[str, Any]:
        db.execute(
            update(_t_tallas)
            .where(_t_tallas.c.id_talla == id_talla)
            .values(codigo=codigo, orden=orden)
        )
        db.commit()
        return CatalogosGlobalesRepositorio.obtener_talla(db, id_talla)  # type: ignore[return-value]

    @staticmethod
    def cambiar_estado_talla(db: Session, id_talla: int, *, activo: bool) -> dict[str, Any]:
        db.execute(
            update(_t_tallas)
            .where(_t_tallas.c.id_talla == id_talla)
            .values(activo=activo)
        )
        db.commit()
        return CatalogosGlobalesRepositorio.obtener_talla(db, id_talla)  # type: ignore[return-value]

    @staticmethod
    def eliminar_talla(db: Session, id_talla: int) -> None:
        db.execute(delete(_t_tallas).where(_t_tallas.c.id_talla == id_talla))
        db.commit()

    # --- Colores ---

    @staticmethod
    def listar_colores(db: Session, *, solo_activos: bool = False) -> list[dict[str, Any]]:
        stmt = select(
            _t_colores.c.id_color,
            _t_colores.c.nombre,
            _t_colores.c.codigo_hex,
            _t_colores.c.activo,
            func.count(_t_variantes.c.id_variante).label("variantes_asociadas"),
        ).outerjoin(_t_variantes, _t_variantes.c.id_color == _t_colores.c.id_color)
        if solo_activos:
            stmt = stmt.where(_t_colores.c.activo.is_(True))
        stmt = stmt.group_by(
            _t_colores.c.id_color,
            _t_colores.c.nombre,
            _t_colores.c.codigo_hex,
            _t_colores.c.activo,
        ).order_by(_t_colores.c.nombre.asc())
        return [dict(r._mapping) for r in db.execute(stmt).all()]

    @staticmethod
    def obtener_color(db: Session, id_color: int) -> Optional[dict[str, Any]]:
        stmt = (
            select(
                _t_colores.c.id_color,
                _t_colores.c.nombre,
                _t_colores.c.codigo_hex,
                _t_colores.c.activo,
                func.count(_t_variantes.c.id_variante).label("variantes_asociadas"),
            )
            .outerjoin(_t_variantes, _t_variantes.c.id_color == _t_colores.c.id_color)
            .where(_t_colores.c.id_color == id_color)
            .group_by(
                _t_colores.c.id_color,
                _t_colores.c.nombre,
                _t_colores.c.codigo_hex,
                _t_colores.c.activo,
            )
        )
        fila = db.execute(stmt).first()
        return dict(fila._mapping) if fila else None

    @staticmethod
    def buscar_color_por_nombre(
        db: Session, nombre: str, *, excluir_id: Optional[int] = None
    ) -> Optional[int]:
        stmt = select(_t_colores.c.id_color).where(
            func.lower(_t_colores.c.nombre) == nombre.strip().lower()
        )
        if excluir_id is not None:
            stmt = stmt.where(_t_colores.c.id_color != excluir_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def crear_color(db: Session, *, nombre: str, codigo_hex: str) -> dict[str, Any]:
        stmt = (
            insert(_t_colores)
            .values(nombre=nombre, codigo_hex=codigo_hex, activo=True)
            .returning(
                _t_colores.c.id_color,
                _t_colores.c.nombre,
                _t_colores.c.codigo_hex,
                _t_colores.c.activo,
            )
        )
        fila = db.execute(stmt).first()
        db.commit()
        res = dict(fila._mapping)
        res["variantes_asociadas"] = 0
        return res

    @staticmethod
    def actualizar_color(
        db: Session, id_color: int, *, nombre: str, codigo_hex: str
    ) -> dict[str, Any]:
        db.execute(
            update(_t_colores)
            .where(_t_colores.c.id_color == id_color)
            .values(nombre=nombre, codigo_hex=codigo_hex)
        )
        db.commit()
        return CatalogosGlobalesRepositorio.obtener_color(db, id_color)  # type: ignore[return-value]

    @staticmethod
    def cambiar_estado_color(db: Session, id_color: int, *, activo: bool) -> dict[str, Any]:
        db.execute(
            update(_t_colores)
            .where(_t_colores.c.id_color == id_color)
            .values(activo=activo)
        )
        db.commit()
        return CatalogosGlobalesRepositorio.obtener_color(db, id_color)  # type: ignore[return-value]

    @staticmethod
    def eliminar_color(db: Session, id_color: int) -> None:
        db.execute(delete(_t_colores).where(_t_colores.c.id_color == id_color))
        db.commit()

