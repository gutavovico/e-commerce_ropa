"""Servicios transaccionales para CU24: Gestionar temporadas y colecciones."""

from datetime import datetime, timezone
from typing import Dict
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from modules.catalogo.cu24_temporadas_colecciones.errores import (
    ColeccionDuplicadaError,
    ColeccionNoEncontradaError,
    TemporadaDuplicadaError,
    TemporadaFechasInvalidasError,
    TemporadaInactivaParaColeccionError,
    TemporadaNoEncontradaError,
)
from modules.catalogo.cu24_temporadas_colecciones.esquemas import (
    ColeccionActualizarIn,
    ColeccionCrearIn,
    ColeccionFiltrosIn,
    ColeccionItemOut,
    ListaPaginadaColeccionesOut,
    ListaPaginadaTemporadasOut,
    TemporadaActualizarIn,
    TemporadaCrearIn,
    TemporadaFiltrosIn,
    TemporadaItemOut,
)
from modules.catalogo.cu24_temporadas_colecciones.modelos import ColeccionORM, TemporadaORM
from modules.catalogo.modelos import ProductoORM


class ServicioGestionTemporadas:
    """Capa de servicio de dominio para la administracion de temporadas de moda."""

    @staticmethod
    def listar_temporadas(db: Session, filtros: TemporadaFiltrosIn) -> ListaPaginadaTemporadasOut:
        query = select(TemporadaORM)

        # Filtros opcionales
        if filtros.q:
            query = query.where(TemporadaORM.nombre.ilike(f"%{filtros.q.strip()}%"))

        if filtros.anio:
            query = query.where(TemporadaORM.anio == filtros.anio)

        if filtros.estado_activo == "activas":
            query = query.where(TemporadaORM.estado_activo.is_(True))
        elif filtros.estado_activo == "inactivas":
            query = query.where(TemporadaORM.estado_activo.is_(False))

        # Conteo total con subquery
        conteo_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(conteo_stmt) or 0

        # Criterios de ordenacion
        if filtros.ordenar_por == "anio_asc":
            query = query.order_by(TemporadaORM.anio.asc(), TemporadaORM.id_temporada.asc())
        elif filtros.ordenar_por == "nombre_asc":
            query = query.order_by(TemporadaORM.nombre.asc())
        elif filtros.ordenar_por == "nombre_desc":
            query = query.order_by(TemporadaORM.nombre.desc())
        elif filtros.ordenar_por == "fecha_desc":
            query = query.order_by(TemporadaORM.fecha_inicio.desc(), TemporadaORM.id_temporada.desc())
        else:  # anio_desc por defecto
            query = query.order_by(TemporadaORM.anio.desc(), TemporadaORM.id_temporada.desc())

        # Paginacion
        offset = (filtros.pagina - 1) * filtros.limite
        query = query.offset(offset).limit(filtros.limite)
        temporadas = list(db.scalars(query).all())

        # Conteo de colecciones asociadas para los items de la pagina
        ids_temporadas = [t.id_temporada for t in temporadas]
        conteos_map: Dict[int, int] = {}
        if ids_temporadas:
            stmt_conteos = (
                select(ColeccionORM.id_temporada, func.count(ColeccionORM.id_coleccion))
                .where(ColeccionORM.id_temporada.in_(ids_temporadas))
                .group_by(ColeccionORM.id_temporada)
            )
            for id_temp, c in db.execute(stmt_conteos):
                conteos_map[id_temp] = c

        items = [
            TemporadaItemOut(
                id_temporada=t.id_temporada,
                nombre=t.nombre,
                anio=t.anio,
                fecha_inicio=t.fecha_inicio,
                fecha_fin=t.fecha_fin,
                estado_activo=t.estado_activo,
                total_colecciones=conteos_map.get(t.id_temporada, 0),
                creado_en=t.creado_en,
                actualizado_en=t.actualizado_en,
            )
            for t in temporadas
        ]

        total_paginas = (total + filtros.limite - 1) // filtros.limite if total > 0 else 1

        return ListaPaginadaTemporadasOut(
            items=items,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )

    @staticmethod
    def obtener_temporada_por_id(db: Session, id_temporada: int) -> TemporadaItemOut:
        temporada = db.scalar(select(TemporadaORM).where(TemporadaORM.id_temporada == id_temporada))
        if not temporada:
            raise TemporadaNoEncontradaError(id_temporada)

        total_cols = (
            db.scalar(
                select(func.count(ColeccionORM.id_coleccion)).where(
                    ColeccionORM.id_temporada == id_temporada
                )
            )
            or 0
        )

        return TemporadaItemOut(
            id_temporada=temporada.id_temporada,
            nombre=temporada.nombre,
            anio=temporada.anio,
            fecha_inicio=temporada.fecha_inicio,
            fecha_fin=temporada.fecha_fin,
            estado_activo=temporada.estado_activo,
            total_colecciones=total_cols,
            creado_en=temporada.creado_en,
            actualizado_en=temporada.actualizado_en,
        )

    @staticmethod
    def crear_temporada(db: Session, payload: TemporadaCrearIn) -> TemporadaItemOut:
        # 1. Validacion de fechas ya validada en Pydantic pero verificada defensivamente
        if payload.fecha_fin <= payload.fecha_inicio:
            raise TemporadaFechasInvalidasError()

        nombre_limpio = payload.nombre.strip()

        # 2. Validacion de unicidad de nombre (LOWER)
        existe = db.scalar(
            select(TemporadaORM.id_temporada).where(
                func.lower(func.trim(TemporadaORM.nombre)) == nombre_limpio.lower()
            )
        )
        if existe:
            raise TemporadaDuplicadaError(nombre_limpio)

        # 3. Creacion de entidad
        ahora = datetime.now(timezone.utc)
        nueva = TemporadaORM(
            nombre=nombre_limpio,
            anio=payload.anio,
            fecha_inicio=payload.fecha_inicio,
            fecha_fin=payload.fecha_fin,
            estado_activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        return TemporadaItemOut(
            id_temporada=nueva.id_temporada,
            nombre=nueva.nombre,
            anio=nueva.anio,
            fecha_inicio=nueva.fecha_inicio,
            fecha_fin=nueva.fecha_fin,
            estado_activo=nueva.estado_activo,
            total_colecciones=0,
            creado_en=nueva.creado_en,
            actualizado_en=nueva.actualizado_en,
        )

    @staticmethod
    def actualizar_temporada(
        db: Session, id_temporada: int, payload: TemporadaActualizarIn
    ) -> TemporadaItemOut:
        temporada = db.scalar(select(TemporadaORM).where(TemporadaORM.id_temporada == id_temporada))
        if not temporada:
            raise TemporadaNoEncontradaError(id_temporada)

        # Validacion de unicidad si se modifica el nombre
        if payload.nombre is not None:
            nombre_limpio = payload.nombre.strip()
            existe = db.scalar(
                select(TemporadaORM.id_temporada).where(
                    func.lower(func.trim(TemporadaORM.nombre)) == nombre_limpio.lower(),
                    TemporadaORM.id_temporada != id_temporada,
                )
            )
            if existe:
                raise TemporadaDuplicadaError(nombre_limpio)
            temporada.nombre = nombre_limpio

        if payload.anio is not None:
            temporada.anio = payload.anio

        # Validacion cruzada de fechas
        fecha_ini = payload.fecha_inicio if payload.fecha_inicio is not None else temporada.fecha_inicio
        fecha_fin = payload.fecha_fin if payload.fecha_fin is not None else temporada.fecha_fin
        if fecha_fin <= fecha_ini:
            raise TemporadaFechasInvalidasError()

        if payload.fecha_inicio is not None:
            temporada.fecha_inicio = payload.fecha_inicio
        if payload.fecha_fin is not None:
            temporada.fecha_fin = payload.fecha_fin

        temporada.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(temporada)

        total_cols = (
            db.scalar(
                select(func.count(ColeccionORM.id_coleccion)).where(
                    ColeccionORM.id_temporada == id_temporada
                )
            )
            or 0
        )

        return TemporadaItemOut(
            id_temporada=temporada.id_temporada,
            nombre=temporada.nombre,
            anio=temporada.anio,
            fecha_inicio=temporada.fecha_inicio,
            fecha_fin=temporada.fecha_fin,
            estado_activo=temporada.estado_activo,
            total_colecciones=total_cols,
            creado_en=temporada.creado_en,
            actualizado_en=temporada.actualizado_en,
        )

    @staticmethod
    def conmutar_estado_temporada(
        db: Session, id_temporada: int, estado_activo: bool
    ) -> TemporadaItemOut:
        temporada = db.scalar(select(TemporadaORM).where(TemporadaORM.id_temporada == id_temporada))
        if not temporada:
            raise TemporadaNoEncontradaError(id_temporada)

        temporada.estado_activo = estado_activo
        temporada.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(temporada)

        total_cols = (
            db.scalar(
                select(func.count(ColeccionORM.id_coleccion)).where(
                    ColeccionORM.id_temporada == id_temporada
                )
            )
            or 0
        )

        return TemporadaItemOut(
            id_temporada=temporada.id_temporada,
            nombre=temporada.nombre,
            anio=temporada.anio,
            fecha_inicio=temporada.fecha_inicio,
            fecha_fin=temporada.fecha_fin,
            estado_activo=temporada.estado_activo,
            total_colecciones=total_cols,
            creado_en=temporada.creado_en,
            actualizado_en=temporada.actualizado_en,
        )


class ServicioGestionColecciones:
    """Capa de servicio de dominio para la administracion de colecciones y capsulas."""

    @staticmethod
    def listar_colecciones(db: Session, filtros: ColeccionFiltrosIn) -> ListaPaginadaColeccionesOut:
        query = (
            select(ColeccionORM, TemporadaORM.nombre.label("temp_nombre"), TemporadaORM.anio.label("temp_anio"))
            .join(TemporadaORM, ColeccionORM.id_temporada == TemporadaORM.id_temporada)
        )

        if filtros.q:
            q_clean = filtros.q.strip()
            query = query.where(
                or_(
                    ColeccionORM.nombre.ilike(f"%{q_clean}%"),
                    ColeccionORM.descripcion.ilike(f"%{q_clean}%"),
                )
            )

        if filtros.id_temporada:
            query = query.where(ColeccionORM.id_temporada == filtros.id_temporada)

        if filtros.estado_activo == "activas":
            query = query.where(ColeccionORM.estado_activo.is_(True))
        elif filtros.estado_activo == "inactivas":
            query = query.where(ColeccionORM.estado_activo.is_(False))

        conteo_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(conteo_stmt) or 0

        offset = (filtros.pagina - 1) * filtros.limite
        query = query.order_by(ColeccionORM.id_coleccion.desc()).offset(offset).limit(filtros.limite)
        resultados = db.execute(query).all()

        ids_colecciones = [row[0].id_coleccion for row in resultados]
        conteos_prod_map: Dict[int, int] = {}
        if ids_colecciones:
            stmt_prods = (
                select(ProductoORM.id_coleccion, func.count(ProductoORM.id_producto))
                .where(ProductoORM.id_coleccion.in_(ids_colecciones))
                .group_by(ProductoORM.id_coleccion)
            )
            for id_col, cp in db.execute(stmt_prods):
                if id_col is not None:
                    conteos_prod_map[id_col] = cp

        items = [
            ColeccionItemOut(
                id_coleccion=row[0].id_coleccion,
                id_temporada=row[0].id_temporada,
                temporada_nombre=row[1],
                temporada_anio=row[2],
                nombre=row[0].nombre,
                descripcion=row[0].descripcion,
                estado_activo=row[0].estado_activo,
                total_productos=conteos_prod_map.get(row[0].id_coleccion, 0),
                creado_en=row[0].creado_en,
                actualizado_en=row[0].actualizado_en,
            )
            for row in resultados
        ]

        total_paginas = (total + filtros.limite - 1) // filtros.limite if total > 0 else 1

        return ListaPaginadaColeccionesOut(
            items=items,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )

    @staticmethod
    def obtener_coleccion_por_id(db: Session, id_coleccion: int) -> ColeccionItemOut:
        row = db.execute(
            select(ColeccionORM, TemporadaORM.nombre, TemporadaORM.anio)
            .join(TemporadaORM, ColeccionORM.id_temporada == TemporadaORM.id_temporada)
            .where(ColeccionORM.id_coleccion == id_coleccion)
        ).first()

        if not row:
            raise ColeccionNoEncontradaError(id_coleccion)

        col, temp_nombre, temp_anio = row
        total_prods = (
            db.scalar(
                select(func.count(ProductoORM.id_producto)).where(
                    ProductoORM.id_coleccion == id_coleccion
                )
            )
            or 0
        )

        return ColeccionItemOut(
            id_coleccion=col.id_coleccion,
            id_temporada=col.id_temporada,
            temporada_nombre=temp_nombre,
            temporada_anio=temp_anio,
            nombre=col.nombre,
            descripcion=col.descripcion,
            estado_activo=col.estado_activo,
            total_productos=total_prods,
            creado_en=col.creado_en,
            actualizado_en=col.actualizado_en,
        )

    @staticmethod
    def crear_coleccion(db: Session, payload: ColeccionCrearIn) -> ColeccionItemOut:
        temporada = db.scalar(
            select(TemporadaORM).where(TemporadaORM.id_temporada == payload.id_temporada)
        )
        if not temporada:
            raise TemporadaNoEncontradaError(payload.id_temporada)

        if not temporada.estado_activo:
            raise TemporadaInactivaParaColeccionError()

        nombre_limpio = payload.nombre.strip()

        # Validacion de unicidad de coleccion dentro de la misma temporada
        existe = db.scalar(
            select(ColeccionORM.id_coleccion).where(
                ColeccionORM.id_temporada == payload.id_temporada,
                func.lower(func.trim(ColeccionORM.nombre)) == nombre_limpio.lower(),
            )
        )
        if existe:
            raise ColeccionDuplicadaError(nombre_limpio, temporada.nombre)

        ahora = datetime.now(timezone.utc)
        nueva = ColeccionORM(
            id_temporada=payload.id_temporada,
            nombre=nombre_limpio,
            descripcion=payload.descripcion.strip() if payload.descripcion else None,
            estado_activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        return ColeccionItemOut(
            id_coleccion=nueva.id_coleccion,
            id_temporada=nueva.id_temporada,
            temporada_nombre=temporada.nombre,
            temporada_anio=temporada.anio,
            nombre=nueva.nombre,
            descripcion=nueva.descripcion,
            estado_activo=nueva.estado_activo,
            total_productos=0,
            creado_en=nueva.creado_en,
            actualizado_en=nueva.actualizado_en,
        )

    @staticmethod
    def actualizar_coleccion(
        db: Session, id_coleccion: int, payload: ColeccionActualizarIn
    ) -> ColeccionItemOut:
        coleccion = db.scalar(select(ColeccionORM).where(ColeccionORM.id_coleccion == id_coleccion))
        if not coleccion:
            raise ColeccionNoEncontradaError(id_coleccion)

        target_temp_id = payload.id_temporada if payload.id_temporada is not None else coleccion.id_temporada
        target_nombre = payload.nombre.strip() if payload.nombre is not None else coleccion.nombre

        temporada = db.scalar(select(TemporadaORM).where(TemporadaORM.id_temporada == target_temp_id))
        if not temporada:
            raise TemporadaNoEncontradaError(target_temp_id)

        # Si se cambia a una temporada inactiva, rechazar
        if payload.id_temporada is not None and payload.id_temporada != coleccion.id_temporada:
            if not temporada.estado_activo:
                raise TemporadaInactivaParaColeccionError()

        # Validacion de unicidad
        existe = db.scalar(
            select(ColeccionORM.id_coleccion).where(
                ColeccionORM.id_temporada == target_temp_id,
                func.lower(func.trim(ColeccionORM.nombre)) == target_nombre.lower(),
                ColeccionORM.id_coleccion != id_coleccion,
            )
        )
        if existe:
            raise ColeccionDuplicadaError(target_nombre, temporada.nombre)

        if payload.id_temporada is not None:
            coleccion.id_temporada = payload.id_temporada
        if payload.nombre is not None:
            coleccion.nombre = target_nombre
        if payload.descripcion is not None:
            coleccion.descripcion = payload.descripcion.strip() if payload.descripcion else None

        coleccion.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(coleccion)

        total_prods = (
            db.scalar(
                select(func.count(ProductoORM.id_producto)).where(
                    ProductoORM.id_coleccion == id_coleccion
                )
            )
            or 0
        )

        return ColeccionItemOut(
            id_coleccion=coleccion.id_coleccion,
            id_temporada=coleccion.id_temporada,
            temporada_nombre=temporada.nombre,
            temporada_anio=temporada.anio,
            nombre=coleccion.nombre,
            descripcion=coleccion.descripcion,
            estado_activo=coleccion.estado_activo,
            total_productos=total_prods,
            creado_en=coleccion.creado_en,
            actualizado_en=coleccion.actualizado_en,
        )

    @staticmethod
    def conmutar_estado_coleccion(
        db: Session, id_coleccion: int, estado_activo: bool
    ) -> ColeccionItemOut:
        coleccion = db.scalar(select(ColeccionORM).where(ColeccionORM.id_coleccion == id_coleccion))
        if not coleccion:
            raise ColeccionNoEncontradaError(id_coleccion)

        coleccion.estado_activo = estado_activo
        coleccion.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(coleccion)

        temporada = db.scalar(
            select(TemporadaORM).where(TemporadaORM.id_temporada == coleccion.id_temporada)
        )
        temp_nombre = temporada.nombre if temporada else ""
        temp_anio = temporada.anio if temporada else 2026

        total_prods = (
            db.scalar(
                select(func.count(ProductoORM.id_producto)).where(
                    ProductoORM.id_coleccion == id_coleccion
                )
            )
            or 0
        )

        return ColeccionItemOut(
            id_coleccion=coleccion.id_coleccion,
            id_temporada=coleccion.id_temporada,
            temporada_nombre=temp_nombre,
            temporada_anio=temp_anio,
            nombre=coleccion.nombre,
            descripcion=coleccion.descripcion,
            estado_activo=coleccion.estado_activo,
            total_productos=total_prods,
            creado_en=coleccion.creado_en,
            actualizado_en=coleccion.actualizado_en,
        )
