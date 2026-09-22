"""Repositorio de acceso a datos para CU05: Consultar Catálogo de Productos."""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from modules.catalogo.modelos import (
    CategoriaORM,
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    PromocionORM,
    PromocionProductoORM,
    TallaORM,
    VarianteProductoORM,
)


class CatalogoRepositorio:
    """Acceso optimizado a datos del catálogo de prendas con carga impaciente."""

    @staticmethod
    def obtener_resumen_categorias(db: Session) -> List[Tuple[int, str, int]]:
        """Obtiene la lista de categorías con el conteo de prendas activas asociadas.
        
        Retorna:
            Lista de tuplas (id_categoria, nombre, total_prendas).
        """
        stmt = (
            select(
                CategoriaORM.id_categoria,
                CategoriaORM.nombre,
                func.count(ProductoORM.id_producto).label("total_prendas"),
            )
            .outerjoin(
                ProductoORM,
                and_(
                    ProductoORM.id_categoria == CategoriaORM.id_categoria,
                    ProductoORM.activo == True,
                ),
            )
            .group_by(CategoriaORM.id_categoria, CategoriaORM.nombre)
            .order_by(CategoriaORM.nombre.asc())
        )
        resultados = db.execute(stmt).all()
        return [(row[0], row[1], int(row[2])) for row in resultados]

    @staticmethod
    def contar_total_prendas_activas(
        db: Session, categoria_id: Optional[int] = None
    ) -> int:
        """Calcula el número total de prendas activas para el filtro de categoría dado."""
        condiciones = [ProductoORM.activo == True]

        if categoria_id is not None:
            subcats_stmt = select(CategoriaORM.id_categoria).where(
                or_(
                    CategoriaORM.id_categoria == categoria_id,
                    CategoriaORM.id_categoria_padre == categoria_id,
                )
            )
            condiciones.append(ProductoORM.id_categoria.in_(subcats_stmt))

        stmt = select(func.count(ProductoORM.id_producto)).where(and_(*condiciones))
        return int(db.scalar(stmt) or 0)

    @staticmethod
    def consultar_productos_paginados(
        db: Session,
        categoria_id: Optional[int] = None,
        ordenar_por: str = "recientes",
        pagina: int = 1,
        limite: int = 8,
    ) -> Tuple[List[ProductoORM], int]:
        """Consulta productos activos de forma paginada con carga impaciente de variantes y stock.
        
        Retorna:
            Tupla con (lista de ProductoORM, total de artículos coincidentes).
        """
        condiciones = [ProductoORM.activo == True]

        if categoria_id is not None:
            subcats_stmt = select(CategoriaORM.id_categoria).where(
                or_(
                    CategoriaORM.id_categoria == categoria_id,
                    CategoriaORM.id_categoria_padre == categoria_id,
                )
            )
            condiciones.append(ProductoORM.id_categoria.in_(subcats_stmt))

        # Conteo total para paginación
        stmt_count = select(func.count(ProductoORM.id_producto)).where(and_(*condiciones))
        total_articulos = int(db.scalar(stmt_count) or 0)

        if total_articulos == 0:
            return [], 0

        # Criterio de ordenamiento
        if ordenar_por == "precio_asc":
            order_clause = ProductoORM.precio_base.asc()
        elif ordenar_por == "precio_desc":
            order_clause = ProductoORM.precio_base.desc()
        elif ordenar_por == "nombre_asc":
            order_clause = ProductoORM.nombre.asc()
        else:
            # "recientes" y default
            order_clause = ProductoORM.creado_en.desc()

        offset = max(0, (pagina - 1) * limite)

        stmt = (
            select(ProductoORM)
            .where(and_(*condiciones))
            .options(
                selectinload(ProductoORM.categoria),
                selectinload(ProductoORM.coleccion),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.talla),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.color),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.inventarios),
            )
            .order_by(order_clause, ProductoORM.id_producto.desc())
            .offset(offset)
            .limit(limite)
        )

        productos = list(db.scalars(stmt).all())
        return productos, total_articulos

    @staticmethod
    def obtener_promociones_activas_para_productos(
        db: Session, ids_productos: List[int]
    ) -> Dict[int, Tuple[Decimal, str]]:
        """Obtiene la promoción activa con mayor descuento para cada producto de la lista.
        
        Retorna:
            Diccionario {id_producto: (porcentaje_descuento, nombre_promocion)}.
        """
        if not ids_productos:
            return {}

        hoy = date.today()
        stmt = (
            select(
                PromocionProductoORM.id_producto,
                PromocionORM.porcentaje_descuento,
                PromocionORM.nombre,
            )
            .join(PromocionORM, PromocionORM.id_promocion == PromocionProductoORM.id_promocion)
            .where(
                and_(
                    PromocionProductoORM.id_producto.in_(ids_productos),
                    PromocionORM.activa == True,
                    PromocionORM.fecha_inicio <= hoy,
                    PromocionORM.fecha_fin >= hoy,
                    PromocionORM.porcentaje_descuento.is_not(None),
                    PromocionORM.porcentaje_descuento > 0,
                )
            )
        )

        filas = db.execute(stmt).all()
        promociones_map: Dict[int, Tuple[Decimal, str]] = {}
        for fila in filas:
            prod_id = fila[0]
            pct = fila[1]
            nombre = fila[2]
            # Si hay varias promociones, mantener la de mayor descuento
            if prod_id not in promociones_map or pct > promociones_map[prod_id][0]:
                promociones_map[prod_id] = (pct, nombre)

        return promociones_map
