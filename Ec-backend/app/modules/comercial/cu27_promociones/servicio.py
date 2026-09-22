"""Capa de servicio transaccional para CU27: Gestionar promociones."""

from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from typing import Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from modules.catalogo.modelos import CategoriaORM, ProductoORM
from modules.comercial.cu27_promociones.errores import (
    AlcancePromocionInvalidoError,
    CodigoCuponDuplicadoError,
    FechasPromocionInvalidasError,
    PromocionNoEncontradaError,
    ValorDescuentoInvalidoError,
)
from modules.comercial.cu27_promociones.esquemas import (
    AlcancePromocionEnum,
    FiltrosPromocionIn,
    ListaPaginadaPromocionesOut,
    MetricasPromocionesOut,
    PromocionActualizarIn,
    PromocionCrearIn,
    PromocionItemOut,
    TipoDescuentoEnum,
)
from modules.comercial.cu27_promociones.modelos import PromocionORM


class ServicioGestionPromociones:
    """Servicio de logica de negocio y persistencia transaccional para promociones."""

    def _mapear_item_out(self, p: PromocionORM, now_utc: datetime) -> PromocionItemOut:
        esta_vigente = bool(p.estado_activo and (p.fecha_inicio <= now_utc <= p.fecha_fin))
        return PromocionItemOut(
            id_promocion=p.id_promocion,
            nombre=p.nombre,
            descripcion=p.descripcion,
            codigo_cupon=p.codigo_cupon,
            tipo_descuento=p.tipo_descuento,
            valor_descuento=p.valor_descuento,
            fecha_inicio=p.fecha_inicio,
            fecha_fin=p.fecha_fin,
            tope_descuento=p.tope_descuento,
            limite_usos=p.limite_usos,
            usos_actuales=p.usos_actuales,
            alcance=p.alcance,
            id_categoria=p.id_categoria,
            nombre_categoria=p.categoria.nombre if p.categoria else None,
            id_producto=p.id_producto,
            nombre_producto=p.producto.nombre if p.producto else None,
            estado_activo=p.estado_activo,
            creado_en=p.creado_en,
            actualizado_en=p.actualizado_en,
            esta_vigente=esta_vigente,
        )

    def listar_promociones(
        self, db: Session, filtros: FiltrosPromocionIn
    ) -> ListaPaginadaPromocionesOut:
        """Retorna el listado paginado de promociones con filtros multicriterio y metricas."""
        now_utc = datetime.now(timezone.utc)
        query = select(PromocionORM).options(
            joinedload(PromocionORM.categoria),
            joinedload(PromocionORM.producto),
        )

        condiciones = []

        # Filtro busqueda textual
        if filtros.q and filtros.q.strip():
            termino = f"%{filtros.q.strip()}%"
            condiciones.append(
                or_(
                    PromocionORM.nombre.ilike(termino),
                    PromocionORM.codigo_cupon.ilike(termino),
                )
            )

        # Filtro tipo de descuento
        if filtros.tipo_descuento and filtros.tipo_descuento != "todos":
            condiciones.append(PromocionORM.tipo_descuento == filtros.tipo_descuento)

        # Filtro estado activo
        if filtros.estado_activo == "activas":
            condiciones.append(PromocionORM.estado_activo.is_(True))
        elif filtros.estado_activo == "inactivas":
            condiciones.append(PromocionORM.estado_activo.is_(False))

        # Filtro alcance
        if filtros.alcance and filtros.alcance != "todos":
            condiciones.append(PromocionORM.alcance == filtros.alcance)

        if condiciones:
            query = query.where(and_(*condiciones))

        # Conteo total con subquery determinista
        conteo_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = db.execute(conteo_query).scalar() or 0

        # Criterio de ordenacion
        if filtros.ordenar_por == "fecha_fin_asc":
            query = query.order_by(PromocionORM.fecha_fin.asc(), PromocionORM.id_promocion.desc())
        elif filtros.ordenar_por == "nombre_asc":
            query = query.order_by(PromocionORM.nombre.asc(), PromocionORM.id_promocion.desc())
        elif filtros.ordenar_por == "valor_desc":
            query = query.order_by(PromocionORM.valor_descuento.desc(), PromocionORM.id_promocion.desc())
        elif filtros.ordenar_por == "usos_desc":
            query = query.order_by(PromocionORM.usos_actuales.desc(), PromocionORM.id_promocion.desc())
        elif filtros.ordenar_por == "creado_en_asc":
            query = query.order_by(PromocionORM.creado_en.asc(), PromocionORM.id_promocion.desc())
        elif filtros.ordenar_por == "fecha_inicio_desc":
            query = query.order_by(PromocionORM.fecha_inicio.desc(), PromocionORM.id_promocion.desc())
        else:
            # Por defecto: creado_en_desc
            query = query.order_by(PromocionORM.creado_en.desc(), PromocionORM.id_promocion.desc())

        # Paginacion
        offset = (filtros.pagina - 1) * filtros.limite
        items_orm = db.execute(query.offset(offset).limit(filtros.limite)).unique().scalars().all()

        items = [self._mapear_item_out(p, now_utc) for p in items_orm]
        metricas = self.obtener_metricas(db)
        total_paginas = max(1, ceil(total / filtros.limite)) if total > 0 else 1

        return ListaPaginadaPromocionesOut(
            items=items,
            metricas=metricas,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )

    def obtener_promocion_por_id(self, db: Session, id_promocion: int) -> PromocionItemOut:
        """Obtiene el detalle completo de una promocion comercial por ID."""
        now_utc = datetime.now(timezone.utc)
        stmt = (
            select(PromocionORM)
            .options(
                joinedload(PromocionORM.categoria),
                joinedload(PromocionORM.producto),
            )
            .where(PromocionORM.id_promocion == id_promocion)
        )
        promocion = db.execute(stmt).unique().scalar_one_or_none()
        if not promocion:
            raise PromocionNoEncontradaError(id_promocion)

        return self._mapear_item_out(promocion, now_utc)

    def crear_promocion(self, db: Session, datos: PromocionCrearIn) -> PromocionItemOut:
        """Crea una nueva promocion o cupon de descuento con validaciones semanticas."""
        # 1. Validacion de fechas
        if datos.fecha_fin <= datos.fecha_inicio:
            raise FechasPromocionInvalidasError()

        # 2. Validacion de porcentajes
        if datos.tipo_descuento == TipoDescuentoEnum.PORCENTAJE:
            if datos.valor_descuento < Decimal("1.00") or datos.valor_descuento > Decimal("100.00"):
                raise ValorDescuentoInvalidoError(
                    "El porcentaje de descuento debe situarse entre 1.00% y 100.00%."
                )

        # 3. Validacion de unicidad de cupon (insensible a mayusculas)
        codigo_normalizado: Optional[str] = None
        if datos.codigo_cupon:
            codigo_normalizado = datos.codigo_cupon.strip().upper()
            existente = db.execute(
                select(PromocionORM).where(
                    func.lower(func.trim(PromocionORM.codigo_cupon)) == codigo_normalizado.lower()
                )
            ).scalar_one_or_none()
            if existente:
                raise CodigoCuponDuplicadoError(codigo_normalizado)

        # 4. Validacion de entidad asociada segun alcance
        id_categoria_final: Optional[int] = None
        id_producto_final: Optional[int] = None

        if datos.alcance == AlcancePromocionEnum.CATEGORIA:
            if not datos.id_categoria:
                raise AlcancePromocionInvalidoError(
                    "Debe seleccionar una categoria para promociones con alcance de categoria."
                )
            cat = db.execute(
                select(CategoriaORM).where(CategoriaORM.id_categoria == datos.id_categoria)
            ).scalar_one_or_none()
            if not cat:
                raise AlcancePromocionInvalidoError(
                    f"La categoria con ID {datos.id_categoria} no existe."
                )
            id_categoria_final = datos.id_categoria

        elif datos.alcance == AlcancePromocionEnum.PRODUCTO:
            if not datos.id_producto:
                raise AlcancePromocionInvalidoError(
                    "Debe seleccionar una prenda o producto para promociones con alcance especifico."
                )
            prod = db.execute(
                select(ProductoORM).where(ProductoORM.id_producto == datos.id_producto)
            ).scalar_one_or_none()
            if not prod:
                raise AlcancePromocionInvalidoError(
                    f"El producto con ID {datos.id_producto} no existe."
                )
            id_producto_final = datos.id_producto

        # 5. Instanciar y persistir
        ahora = datetime.now(timezone.utc)
        nueva_promocion = PromocionORM(
            nombre=datos.nombre.strip(),
            descripcion=datos.descripcion.strip() if datos.descripcion else None,
            codigo_cupon=codigo_normalizado,
            tipo_descuento=datos.tipo_descuento.value,
            valor_descuento=datos.valor_descuento,
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=datos.fecha_fin,
            tope_descuento=datos.tope_descuento,
            limite_usos=datos.limite_usos,
            usos_actuales=0,
            alcance=datos.alcance.value,
            id_categoria=id_categoria_final,
            id_producto=id_producto_final,
            estado_activo=datos.estado_activo,
            creado_en=ahora,
            actualizado_en=ahora,
        )

        db.add(nueva_promocion)
        db.commit()
        db.refresh(nueva_promocion)

        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            accion="CREAR_PROMOCION",
            tabla_modulo="promociones",
            severidad="INFO",
            payload_anterior=None,
            payload_nuevo={
                "id_promocion": nueva_promocion.id_promocion,
                "nombre": nueva_promocion.nombre,
                "codigo_cupon": nueva_promocion.codigo_cupon,
                "tipo_descuento": nueva_promocion.tipo_descuento,
            },
            db=db,
        )

        return self.obtener_promocion_por_id(db, nueva_promocion.id_promocion)

    def actualizar_promocion(
        self, db: Session, id_promocion: int, datos: PromocionActualizarIn
    ) -> PromocionItemOut:
        """Actualiza integralmente una promocion existente."""
        promocion = db.execute(
            select(PromocionORM).where(PromocionORM.id_promocion == id_promocion)
        ).scalar_one_or_none()
        if not promocion:
            raise PromocionNoEncontradaError(id_promocion)

        # 1. Validacion de fechas
        if datos.fecha_fin <= datos.fecha_inicio:
            raise FechasPromocionInvalidasError()

        # 2. Validacion de porcentajes
        if datos.tipo_descuento == TipoDescuentoEnum.PORCENTAJE:
            if datos.valor_descuento < Decimal("1.00") or datos.valor_descuento > Decimal("100.00"):
                raise ValorDescuentoInvalidoError(
                    "El porcentaje de descuento debe situarse entre 1.00% y 100.00%."
                )

        # 3. Validacion de unicidad de cupon si se modifica
        codigo_normalizado: Optional[str] = None
        if datos.codigo_cupon:
            codigo_normalizado = datos.codigo_cupon.strip().upper()
            existente = db.execute(
                select(PromocionORM).where(
                    func.lower(func.trim(PromocionORM.codigo_cupon)) == codigo_normalizado.lower(),
                    PromocionORM.id_promocion != id_promocion,
                )
            ).scalar_one_or_none()
            if existente:
                raise CodigoCuponDuplicadoError(codigo_normalizado)

        # 4. Validacion de alcance
        id_categoria_final: Optional[int] = None
        id_producto_final: Optional[int] = None

        if datos.alcance == AlcancePromocionEnum.CATEGORIA:
            if not datos.id_categoria:
                raise AlcancePromocionInvalidoError(
                    "Debe seleccionar una categoria para promociones con alcance de categoria."
                )
            cat = db.execute(
                select(CategoriaORM).where(CategoriaORM.id_categoria == datos.id_categoria)
            ).scalar_one_or_none()
            if not cat:
                raise AlcancePromocionInvalidoError(
                    f"La categoria con ID {datos.id_categoria} no existe."
                )
            id_categoria_final = datos.id_categoria

        elif datos.alcance == AlcancePromocionEnum.PRODUCTO:
            if not datos.id_producto:
                raise AlcancePromocionInvalidoError(
                    "Debe seleccionar una prenda o producto para promociones con alcance especifico."
                )
            prod = db.execute(
                select(ProductoORM).where(ProductoORM.id_producto == datos.id_producto)
            ).scalar_one_or_none()
            if not prod:
                raise AlcancePromocionInvalidoError(
                    f"El producto con ID {datos.id_producto} no existe."
                )
            id_producto_final = datos.id_producto

        # 5. Mutacion de campos
        payload_ant = {
            "nombre": promocion.nombre,
            "codigo_cupon": promocion.codigo_cupon,
            "tipo_descuento": promocion.tipo_descuento,
            "valor_descuento": float(promocion.valor_descuento) if promocion.valor_descuento else None,
        }

        promocion.nombre = datos.nombre.strip()
        promocion.descripcion = datos.descripcion.strip() if datos.descripcion else None
        promocion.codigo_cupon = codigo_normalizado
        promocion.tipo_descuento = datos.tipo_descuento.value
        promocion.valor_descuento = datos.valor_descuento
        promocion.fecha_inicio = datos.fecha_inicio
        promocion.fecha_fin = datos.fecha_fin
        promocion.tope_descuento = datos.tope_descuento
        promocion.limite_usos = datos.limite_usos
        promocion.alcance = datos.alcance.value
        promocion.id_categoria = id_categoria_final
        promocion.id_producto = id_producto_final
        promocion.estado_activo = datos.estado_activo
        promocion.actualizado_en = datetime.now(timezone.utc)

        db.commit()
        db.refresh(promocion)

        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            accion="ACTUALIZAR_PROMOCION",
            tabla_modulo="promociones",
            severidad="INFO",
            payload_anterior=payload_ant,
            payload_nuevo={
                "id_promocion": promocion.id_promocion,
                "nombre": promocion.nombre,
                "codigo_cupon": promocion.codigo_cupon,
            },
            db=db,
        )

        return self.obtener_promocion_por_id(db, promocion.id_promocion)

    def conmutar_estado(
        self, db: Session, id_promocion: int, estado_activo: bool
    ) -> PromocionItemOut:
        """Conmuta el estado operativo de la promocion (baja logica o reactivacion)."""
        promocion = db.execute(
            select(PromocionORM).where(PromocionORM.id_promocion == id_promocion)
        ).scalar_one_or_none()
        if not promocion:
            raise PromocionNoEncontradaError(id_promocion)

        estado_anterior = promocion.estado_activo
        promocion.estado_activo = estado_activo
        promocion.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(promocion)

        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            accion="CONMUTAR_ESTADO_PROMOCION",
            tabla_modulo="promociones",
            severidad="INFO",
            payload_anterior={"estado_activo": estado_anterior},
            payload_nuevo={"id_promocion": id_promocion, "estado_activo": estado_activo},
            db=db,
        )

        return self.obtener_promocion_por_id(db, promocion.id_promocion)

    def obtener_metricas(self, db: Session) -> MetricasPromocionesOut:
        """Computa los indicadores agregados del panel de promociones."""
        now_utc = datetime.now(timezone.utc)

        # 1. Promociones activas
        promociones_activas = db.execute(
            select(func.count(PromocionORM.id_promocion)).where(
                PromocionORM.estado_activo.is_(True)
            )
        ).scalar() or 0

        # 2. Cupones vigentes (con codigo, activos y en fecha)
        cupones_vigentes = db.execute(
            select(func.count(PromocionORM.id_promocion)).where(
                PromocionORM.estado_activo.is_(True),
                PromocionORM.codigo_cupon.isnot(None),
                PromocionORM.fecha_inicio <= now_utc,
                PromocionORM.fecha_fin >= now_utc,
            )
        ).scalar() or 0

        # 3. Descuento promedio entre promociones activas
        descuento_promedio_val = db.execute(
            select(func.coalesce(func.avg(PromocionORM.valor_descuento), Decimal("0.00"))).where(
                PromocionORM.estado_activo.is_(True)
            )
        ).scalar() or Decimal("0.00")

        # 4. Usos totales acumulados
        usos_totales = db.execute(
            select(func.coalesce(func.sum(PromocionORM.usos_actuales), 0))
        ).scalar() or 0

        return MetricasPromocionesOut(
            promociones_activas=promociones_activas,
            cupones_vigentes=cupones_vigentes,
            descuento_promedio=Decimal(str(round(float(descuento_promedio_val), 2))),
            usos_totales=usos_totales,
        )
