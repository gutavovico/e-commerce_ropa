"""Servicio de dominio analitico para CU26: Consultar inventario global.

Implementa la agregacion multi-sucursal de existencias, calculo de balances de red,
metricas cuantitativas consolidadas y semaforizacion de inventario sobre PostgreSQL Neon.
"""

from math import ceil
from typing import Dict, List, Optional
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from modules.catalogo.modelos import (
    CategoriaORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    TallaORM,
    VarianteProductoORM,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM
from .esquemas import (
    ExistenciaSucursalItemOut,
    InventarioGlobalFiltrosIn,
    InventarioGlobalItemOut,
    MetricasInventarioGlobalOut,
    RespuestaInventarioGlobalOut,
)
from .errores import CategoriaInvalidaConsultaError, SucursalInvalidaConsultaError


class ServicioInventarioGlobal:
    """Logica analitica de negocio para la consulta consolidada de inventario en red."""

    @staticmethod
    def calcular_estado_stock(total_disponible: int) -> str:
        """Clasifica el estado cuantitativo segun los umbrales de red."""
        if total_disponible <= 0:
            return "agotado"
        if total_disponible <= 5:
            return "alerta_baja"
        return "optimo"

    @classmethod
    def consultar_inventario_global(
        cls,
        db: Session,
        filtros: InventarioGlobalFiltrosIn,
    ) -> RespuestaInventarioGlobalOut:
        """Ejecuta la agregacion analitica de inventario multi-sucursal aplicando filtros."""
        # 1. Validacion defensiva previa de filtros de sucursal y categoria
        if filtros.id_sucursal is not None:
            suc_valida = db.execute(
                select(SucursalORM.id_sucursal).where(
                    SucursalORM.id_sucursal == filtros.id_sucursal,
                    SucursalORM.activa.is_(True),
                )
            ).scalar_one_or_none()
            if not suc_valida:
                raise SucursalInvalidaConsultaError(filtros.id_sucursal)

        if filtros.id_categoria is not None:
            cat_valida = db.execute(
                select(CategoriaORM.id_categoria).where(
                    CategoriaORM.id_categoria == filtros.id_categoria
                )
            ).scalar_one_or_none()
            if not cat_valida:
                raise CategoriaInvalidaConsultaError(filtros.id_categoria)

        # 2. Carga de todas las sucursales activas con datos logisticos
        sucursales_activas = db.execute(
            select(
                SucursalORM.id_sucursal,
                SucursalORM.nombre,
                SucursalORM.direccion,
                SucursalORM.telefono,
                CiudadORM.nombre.label("ciudad_nombre"),
            )
            .join(CiudadORM, SucursalORM.id_ciudad == CiudadORM.id_ciudad)
            .where(SucursalORM.activa.is_(True))
            .order_by(SucursalORM.nombre.asc())
        ).all()
        sedes_activas_count = len(sucursales_activas)

        # 3. Expresiones de agregacion de existencias filtrando sedes activas
        total_disp_expr = func.coalesce(
            func.sum(
                case(
                    (SucursalORM.activa.is_(True), InventarioSucursalORM.cantidad_disponible),
                    else_=0,
                )
            ),
            0,
        ).label("total_disponible")

        total_res_expr = func.coalesce(
            func.sum(
                case(
                    (SucursalORM.activa.is_(True), InventarioSucursalORM.cantidad_reservada),
                    else_=0,
                )
            ),
            0,
        ).label("total_reservado")

        # 4. Construccion de consulta sobre variantes y productos activos
        stmt = (
            select(
                VarianteProductoORM.id_variante,
                VarianteProductoORM.id_producto,
                ProductoORM.nombre.label("nombre_producto"),
                VarianteProductoORM.sku,
                CategoriaORM.nombre.label("categoria_nombre"),
                TallaORM.codigo.label("talla_codigo"),
                ColorORM.nombre.label("color_nombre"),
                ColorORM.codigo_hex.label("swatches_hex"),
                total_disp_expr,
                total_res_expr,
            )
            .join(ProductoORM, VarianteProductoORM.id_producto == ProductoORM.id_producto)
            .join(CategoriaORM, ProductoORM.id_categoria == CategoriaORM.id_categoria)
            .join(TallaORM, VarianteProductoORM.id_talla == TallaORM.id_talla)
            .join(ColorORM, VarianteProductoORM.id_color == ColorORM.id_color)
            .outerjoin(InventarioSucursalORM, VarianteProductoORM.id_variante == InventarioSucursalORM.id_variante)
            .outerjoin(SucursalORM, InventarioSucursalORM.id_sucursal == SucursalORM.id_sucursal)
            .where(
                ProductoORM.activo.is_(True),
                VarianteProductoORM.activo.is_(True),
            )
            .group_by(
                VarianteProductoORM.id_variante,
                VarianteProductoORM.id_producto,
                ProductoORM.nombre,
                VarianteProductoORM.sku,
                CategoriaORM.nombre,
                TallaORM.codigo,
                ColorORM.nombre,
                ColorORM.codigo_hex,
            )
        )

        # Filtro textual (nombre o SKU)
        if filtros.q:
            patron = f"%{filtros.q.strip()}%"
            stmt = stmt.where(
                or_(
                    ProductoORM.nombre.ilike(patron),
                    VarianteProductoORM.sku.ilike(patron),
                )
            )

        # Filtro por categoria
        if filtros.id_categoria is not None:
            stmt = stmt.where(ProductoORM.id_categoria == filtros.id_categoria)

        # Filtro por sucursal
        if filtros.id_sucursal is not None:
            stmt = stmt.where(InventarioSucursalORM.id_sucursal == filtros.id_sucursal)

        # Filtro por estado de stock en clausula HAVING
        if filtros.estado_stock and filtros.estado_stock != "todos":
            if filtros.estado_stock == "agotado":
                stmt = stmt.having(total_disp_expr == 0)
            elif filtros.estado_stock == "alerta_baja":
                stmt = stmt.having(and_(total_disp_expr > 0, total_disp_expr <= 5))
            elif filtros.estado_stock == "optimo":
                stmt = stmt.having(total_disp_expr > 5)

        # Ordenamiento determinista
        if filtros.ordenar_por == "stock_asc":
            stmt = stmt.order_by(total_disp_expr.asc(), ProductoORM.nombre.asc())
        elif filtros.ordenar_por == "stock_desc":
            stmt = stmt.order_by(total_disp_expr.desc(), ProductoORM.nombre.asc())
        elif filtros.ordenar_por == "nombre_desc":
            stmt = stmt.order_by(ProductoORM.nombre.desc(), VarianteProductoORM.sku.asc())
        elif filtros.ordenar_por == "sku_asc":
            stmt = stmt.order_by(VarianteProductoORM.sku.asc())
        else:
            stmt = stmt.order_by(ProductoORM.nombre.asc(), VarianteProductoORM.sku.asc())

        # Conteo total de coincidencias mediante subconsulta
        conteo_subquery = stmt.order_by(None).subquery("conteo_subquery")
        total_registros = db.execute(
            select(func.count()).select_from(conteo_subquery)
        ).scalar_one() or 0

        total_paginas = max(1, ceil(total_registros / filtros.limite))
        offset = (filtros.pagina - 1) * filtros.limite

        # Consulta paginada
        filas_pagina = db.execute(stmt.offset(offset).limit(filtros.limite)).all()
        ids_variantes_pagina = [f.id_variante for f in filas_pagina]

        # 5. Carga del desglose de existencias por sucursal activa para las variantes de la pagina
        desglose_por_variante: Dict[int, List[ExistenciaSucursalItemOut]] = {
            v_id: [] for v_id in ids_variantes_pagina
        }

        if ids_variantes_pagina and sucursales_activas:
            existencias_db = db.execute(
                select(
                    InventarioSucursalORM.id_variante,
                    InventarioSucursalORM.id_sucursal,
                    InventarioSucursalORM.cantidad_disponible,
                    InventarioSucursalORM.cantidad_reservada,
                )
                .join(SucursalORM, InventarioSucursalORM.id_sucursal == SucursalORM.id_sucursal)
                .where(
                    InventarioSucursalORM.id_variante.in_(ids_variantes_pagina),
                    SucursalORM.activa.is_(True),
                )
            ).all()

            mapa_existencias = {
                (e.id_variante, e.id_sucursal): (e.cantidad_disponible, e.cantidad_reservada)
                for e in existencias_db
            }

            for v_id in ids_variantes_pagina:
                for suc in sucursales_activas:
                    disp, res = mapa_existencias.get((v_id, suc.id_sucursal), (0, 0))
                    desglose_por_variante[v_id].append(
                        ExistenciaSucursalItemOut(
                            id_sucursal=suc.id_sucursal,
                            nombre_sucursal=suc.nombre,
                            ciudad=suc.ciudad_nombre,
                            direccion=suc.direccion,
                            telefono=suc.telefono,
                            cantidad_disponible=disp,
                            cantidad_reservada=res,
                        )
                    )

        # 6. Construccion de items de respuesta
        items_out: List[InventarioGlobalItemOut] = []
        for f in filas_pagina:
            disp = int(f.total_disponible or 0)
            res = int(f.total_reservado or 0)
            estado = cls.calcular_estado_stock(disp)

            items_out.append(
                InventarioGlobalItemOut(
                    id_variante=f.id_variante,
                    id_producto=f.id_producto,
                    nombre_producto=f.nombre_producto,
                    sku=f.sku,
                    categoria=f.categoria_nombre,
                    talla=f.talla_codigo,
                    color=f.color_nombre,
                    swatches_hex=f.swatches_hex,
                    total_disponible=disp,
                    total_reservado=res,
                    total_fisico=disp + res,
                    estado_stock=estado,
                    desglose_sucursales=desglose_por_variante.get(f.id_variante, []),
                )
            )

        # 7. Computo de metricas cuantitativas de red
        total_unidades = db.execute(
            select(
                func.coalesce(
                    func.sum(InventarioSucursalORM.cantidad_disponible),
                    0,
                )
            )
            .select_from(InventarioSucursalORM)
            .join(VarianteProductoORM, InventarioSucursalORM.id_variante == VarianteProductoORM.id_variante)
            .join(ProductoORM, VarianteProductoORM.id_producto == ProductoORM.id_producto)
            .join(SucursalORM, InventarioSucursalORM.id_sucursal == SucursalORM.id_sucursal)
            .where(
                ProductoORM.activo.is_(True),
                VarianteProductoORM.activo.is_(True),
                SucursalORM.activa.is_(True),
            )
        ).scalar_one() or 0

        total_variantes = db.execute(
            select(func.count(VarianteProductoORM.id_variante))
            .select_from(VarianteProductoORM)
            .join(ProductoORM, VarianteProductoORM.id_producto == ProductoORM.id_producto)
            .where(
                ProductoORM.activo.is_(True),
                VarianteProductoORM.activo.is_(True),
            )
        ).scalar_one() or 0

        subq_alerta = (
            select(
                VarianteProductoORM.id_variante,
                func.coalesce(
                    func.sum(
                        case(
                            (SucursalORM.activa.is_(True), InventarioSucursalORM.cantidad_disponible),
                            else_=0,
                        )
                    ),
                    0,
                ).label("disp"),
            )
            .select_from(VarianteProductoORM)
            .join(ProductoORM, VarianteProductoORM.id_producto == ProductoORM.id_producto)
            .outerjoin(InventarioSucursalORM, VarianteProductoORM.id_variante == InventarioSucursalORM.id_variante)
            .outerjoin(SucursalORM, InventarioSucursalORM.id_sucursal == SucursalORM.id_sucursal)
            .where(
                ProductoORM.activo.is_(True),
                VarianteProductoORM.activo.is_(True),
            )
            .group_by(VarianteProductoORM.id_variante)
            .having(
                and_(
                    func.coalesce(func.sum(case((SucursalORM.activa.is_(True), InventarioSucursalORM.cantidad_disponible), else_=0)), 0) > 0,
                    func.coalesce(func.sum(case((SucursalORM.activa.is_(True), InventarioSucursalORM.cantidad_disponible), else_=0)), 0) <= 5,
                )
            )
            .subquery("subq_alerta")
        )
        total_alertas = db.execute(select(func.count()).select_from(subq_alerta)).scalar_one() or 0

        metricas_out = MetricasInventarioGlobalOut(
            total_unidades_red=int(total_unidades),
            variantes_monitoreadas=int(total_variantes),
            alertas_stock_bajo=int(total_alertas),
            sedes_activas=sedes_activas_count,
        )

        return RespuestaInventarioGlobalOut(
            items=items_out,
            metricas=metricas_out,
            total=total_registros,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )
