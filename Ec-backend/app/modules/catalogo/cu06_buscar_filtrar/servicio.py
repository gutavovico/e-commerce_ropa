"""Servicio de dominio para CU06 - Buscar y Filtrar Productos.

Implementa la construcción de consultas dinámicas en SQLAlchemy 2.0,
coincidencia difusa textual (pg_trgm / ILIKE), filtros combinados,
ordenamiento y paginación determinista de alto rendimiento.
"""

from decimal import Decimal
from math import ceil
from typing import Any, Dict, List, Optional, Set
import unicodedata

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from core.errors import DomainError
from modules.catalogo.cu06_buscar_filtrar.esquemas import (
    CriterioOrdenamiento,
    FiltrosDisponiblesOut,
    OpcionFiltroItem,
    PaginacionMetaOut,
    ProductoItemOut,
    ProductoPaginadoOut,
    VarianteResumenOut,
)
from modules.catalogo.modelos import (
    CategoriaORM,
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    TallaORM,
    TemporadaORM,
    VarianteProductoORM,
)


class FiltroInvalidoError(DomainError):
    """Excepción lanzada cuando los parámetros de filtrado son inconsistentes."""

    def __init__(self, mensaje: str):
        super().__init__(message=mensaje, code="FILTRO_INVALIDO")


# Palabras vacías en español a omitir en búsquedas multi-término
_STOP_WORDS: Set[str] = {
    "de", "del", "la", "el", "los", "las", "un", "una", "y", "e", "o", "u",
    "con", "en", "para", "por", "a", "al", "sobre"
}

# Diccionario de sinónimos de alta costura y categorías omnicanal
_SINONIMOS_MODA: Dict[str, List[str]] = {
    "vestido": ["vestido", "vestidos", "traje", "gala"],
    "vestidos": ["vestido", "vestidos", "traje", "gala"],
    "falda": ["falda", "faldas", "midi", "plisada"],
    "faldas": ["falda", "faldas", "midi", "plisada"],
    "pantalon": ["pantalon", "pantalón", "pantalones", "palazzo", "tiro alto"],
    "pantalones": ["pantalon", "pantalón", "pantalones", "palazzo", "tiro alto"],
    "blusa": ["blusa", "blusas", "camisa", "camisas"],
    "blusas": ["blusa", "blusas", "camisa", "camisas"],
    "camisa": ["camisa", "camisas", "blusa", "blusas"],
    "camisas": ["camisa", "camisas", "blusa", "blusas"],
    "chaqueta": ["chaqueta", "chaquetas", "blazer", "blazers", "trench", "abrigo", "smoking", "esmoquin"],
    "chaquetas": ["chaqueta", "chaquetas", "blazer", "blazers", "trench", "abrigo", "smoking", "esmoquin"],
    "blazer": ["blazer", "blazers", "chaqueta", "chaquetas", "smoking"],
    "blazers": ["blazer", "blazers", "chaqueta", "chaquetas", "smoking"],
    "trench": ["trench", "abrigo", "chaqueta", "chaquetas"],
    "rojo": ["rojo", "roja", "rojos", "rojas", "carmin", "carmín", "granate", "vino", "borgoña", "borgona"],
    "roja": ["rojo", "roja", "rojos", "rojas", "carmin", "carmín"],
    "seda": ["seda", "sedas", "saten", "satén"],
    "saten": ["saten", "satén", "seda"],
    "satén": ["saten", "satén", "seda"],
}

# Mapeo de tildes fonéticas comunes del catálogo
_MAPA_TILDES: Dict[str, str] = {
    "pantalon": "pantalón",
    "saten": "satén",
    "ebano": "ébano",
    "carmin": "carmín",
    "sastreria": "sastrería",
    "otono": "otoño",
    "edicion": "edición",
    "fluido": "fluído",
    "unica": "única",
    "algodon": "algodón",
    "crepe": "crepé",
}


def _normalizar_texto(texto: str) -> str:
    """Elimina diacríticos (tildes) y convierte a minúsculas limpias."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()


def _expandir_termino(palabra: str) -> Set[str]:
    """Genera formas morfológicas (singular/plural, tildes, sinónimos) para un término de búsqueda."""
    limpia = _normalizar_texto(palabra)
    if not limpia or len(limpia) < 2:
        return set()

    variantes: Set[str] = {limpia, palabra.lower()}

    # Resolver correspondencias con tildes
    if limpia in _MAPA_TILDES:
        variantes.add(_MAPA_TILDES[limpia])
    for k, v in _MAPA_TILDES.items():
        if v == palabra.lower():
            variantes.add(k)

    # Inferencia morfológica de número (singular <-> plural)
    if limpia.endswith("es") and len(limpia) > 3:
        sing = limpia[:-2]
        variantes.add(sing)
        if sing in _MAPA_TILDES:
            variantes.add(_MAPA_TILDES[sing])
    elif limpia.endswith("s") and len(limpia) > 2:
        sing = limpia[:-1]
        variantes.add(sing)
        if sing in _MAPA_TILDES:
            variantes.add(_MAPA_TILDES[sing])
    else:
        variantes.add(limpia + "s")
        variantes.add(limpia + "es")

    # Inclusión de sinónimos de moda
    if limpia in _SINONIMOS_MODA:
        for syn in _SINONIMOS_MODA[limpia]:
            variantes.add(syn.lower())
            syn_norm = _normalizar_texto(syn)
            variantes.add(syn_norm)
            if syn_norm in _MAPA_TILDES:
                variantes.add(_MAPA_TILDES[syn_norm])

    return {v for v in variantes if v and len(v) >= 2}


class ServicioBuscarFiltro:
    """Servicio que encapsula la lógica de búsqueda y filtrado de catálogo."""

    @staticmethod
    def _derivar_badge_editorial(producto: ProductoORM) -> Optional[str]:
        """Asigna el badge de alta costura según la colección o características del producto."""
        if not producto.coleccion:
            return None
        nombre_col = producto.coleccion.nombre.lower()
        if "edición limitada" in nombre_col or "capsula" in nombre_col or "alta costura" in nombre_col:
            return "ED. LIMITADA 12/50"
        if "serrano" in nombre_col or "atelier" in nombre_col:
            return "EN SERRANO"
        if "seda" in nombre_col:
            return "SEDA PURA"
        if "lana" in nombre_col:
            return "LANA & SEDA"
        return "NUEVA COLECCIÓN"

    @staticmethod
    def _derivar_subtitulo_atelier(producto: ProductoORM) -> str:
        """Asigna la línea atelier en mayúsculas."""
        if producto.coleccion:
            nombre = producto.coleccion.nombre.upper()
            if "ALTA COSTURA" in nombre:
                return "ALTA COSTURA"
            if "SASTRERÍA" in nombre or "ATELIER" in nombre:
                return "SASTRERÍA ATELIER"
            if "ESENCIALES" in nombre:
                return "BÁSICOS DE LUJO"
            return nombre
        return (producto.categoria.nombre if producto.categoria else "FASHION STORE").upper()

    @classmethod
    def mapear_a_item_out(cls, producto: ProductoORM) -> ProductoItemOut:
        """Transforma una entidad ProductoORM en el esquema ProductoItemOut enriquecido."""
        variantes_out: List[VarianteResumenOut] = []
        talla_sugerida: Optional[str] = None
        color_sugerido: Optional[str] = None

        for idx, var in enumerate(producto.variantes):
            # Sumar stock total en todas las sucursales
            stock_total = sum(inv.cantidad_disponible for inv in var.inventarios) if var.inventarios else 0
            esta_disp = stock_total > 0

            variantes_out.append(
                VarianteResumenOut(
                    id_variante=var.id_variante,
                    sku=var.sku,
                    talla=var.talla.codigo if var.talla else "",
                    id_talla=var.id_talla,
                    color=var.color.nombre if var.color else "",
                    id_color=var.id_color,
                    codigo_hex=var.color.codigo_hex if var.color else None,
                    precio_extra=var.precio_extra,
                    disponible=esta_disp,
                    cantidad_disponible=stock_total,
                )
            )
            if idx == 0:
                talla_sugerida = f"Talla {var.talla.codigo}" if var.talla else None
                color_sugerido = var.color.nombre if var.color else None

        coleccion_nombre = producto.coleccion.nombre if producto.coleccion else None
        temporada_nombre = (
            producto.coleccion.temporada.nombre
            if producto.coleccion and producto.coleccion.temporada
            else None
        )
        id_temporada = (
            producto.coleccion.id_temporada if producto.coleccion else None
        )

        return ProductoItemOut(
            id_producto=producto.id_producto,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria.nombre if producto.categoria else "General",
            id_categoria=producto.id_categoria,
            coleccion=coleccion_nombre,
            id_coleccion=producto.id_coleccion,
            temporada=temporada_nombre,
            id_temporada=id_temporada,
            precio_base=producto.precio_base,
            imagen_url=producto.imagen_url,
            modelo_ar_url=producto.modelo_ar_url,
            activo=producto.activo,
            badge_editorial=cls._derivar_badge_editorial(producto),
            subtitulo_atelier=cls._derivar_subtitulo_atelier(producto),
            talla_sugerida=talla_sugerida,
            color_sugerido=color_sugerido,
            variantes=variantes_out,
        )

    @classmethod
    def buscar_productos(
        cls,
        session: Session,
        q: Optional[str] = None,
        categoria_id: Optional[int] = None,
        coleccion_id: Optional[int] = None,
        temporada_id: Optional[int] = None,
        id_talla: Optional[int] = None,
        talla: Optional[str] = None,
        id_color: Optional[int] = None,
        color: Optional[str] = None,
        precio_min: Optional[Decimal] = None,
        precio_max: Optional[Decimal] = None,
        solo_en_stock: bool = True,
        ordenar_por: str = "recientes",
        pagina: int = 1,
        limite: int = 12,
    ) -> ProductoPaginadoOut:
        """Ejecuta la búsqueda y filtrado multicriterio de prendas con paginación."""
        if precio_min is not None and precio_max is not None and precio_max < precio_min:
            raise FiltroInvalidoError("El precio_max no puede ser menor que precio_min.")

        condiciones = [ProductoORM.activo == True]

        # 1. Filtro por Categoría (incluye subcategorías si aplica)
        if categoria_id is not None:
            subcats = session.scalars(
                select(CategoriaORM.id_categoria).where(
                    CategoriaORM.id_categoria_padre == categoria_id
                )
            ).all()
            cats_ids = [categoria_id] + list(subcats)
            condiciones.append(ProductoORM.id_categoria.in_(cats_ids))

        # 2. Filtro por Colección
        if coleccion_id is not None:
            condiciones.append(ProductoORM.id_coleccion == coleccion_id)

        # 3. Filtro por Temporada
        if temporada_id is not None:
            condiciones.append(
                exists(
                    select(1)
                    .select_from(ColeccionORM)
                    .where(
                        and_(
                            ColeccionORM.id_coleccion == ProductoORM.id_coleccion,
                            ColeccionORM.id_temporada == temporada_id,
                        )
                    )
                )
            )

        # 4. Búsqueda semántica, morfológica y por palabras sueltas (nombre, categoría, colección, temporada, color, descripción)
        clean_q = q.strip() if q else ""
        if clean_q:
            palabras = [w for w in clean_q.split() if _normalizar_texto(w) not in _STOP_WORDS]
            if not palabras:
                palabras = [clean_q]

            condiciones_palabras = []
            for palabra in palabras:
                variantes = _expandir_termino(palabra)
                conds_variante = []
                for var in variantes:
                    pattern = f"%{var}%"
                    conds_variante.append(func.lower(ProductoORM.nombre).like(pattern))
                    conds_variante.append(func.lower(func.coalesce(ProductoORM.descripcion, "")).like(pattern))
                    conds_variante.append(
                        exists(
                            select(1)
                            .select_from(CategoriaORM)
                            .where(
                                and_(
                                    CategoriaORM.id_categoria == ProductoORM.id_categoria,
                                    func.lower(CategoriaORM.nombre).like(pattern),
                                )
                            )
                        )
                    )
                    conds_variante.append(
                        exists(
                            select(1)
                            .select_from(ColeccionORM)
                            .where(
                                and_(
                                    ColeccionORM.id_coleccion == ProductoORM.id_coleccion,
                                    func.lower(ColeccionORM.nombre).like(pattern),
                                )
                            )
                        )
                    )
                    conds_variante.append(
                        exists(
                            select(1)
                            .select_from(ColeccionORM)
                            .join(TemporadaORM, ColeccionORM.id_temporada == TemporadaORM.id_temporada)
                            .where(
                                and_(
                                    ColeccionORM.id_coleccion == ProductoORM.id_coleccion,
                                    func.lower(TemporadaORM.nombre).like(pattern),
                                )
                            )
                        )
                    )
                    conds_variante.append(
                        exists(
                            select(1)
                            .select_from(VarianteProductoORM)
                            .join(ColorORM, VarianteProductoORM.id_color == ColorORM.id_color)
                            .where(
                                and_(
                                    VarianteProductoORM.id_producto == ProductoORM.id_producto,
                                    func.lower(ColorORM.nombre).like(pattern),
                                )
                            )
                        )
                    )
                if conds_variante:
                    condiciones_palabras.append(or_(*conds_variante))

            if condiciones_palabras:
                condiciones.append(and_(*condiciones_palabras))

        # 5. Filtro por Rango de Precios
        if precio_min is not None:
            condiciones.append(ProductoORM.precio_base >= precio_min)
        if precio_max is not None:
            condiciones.append(ProductoORM.precio_base <= precio_max)

        # 6. Filtro por Variantes (Talla, Color y/o Stock disponible)
        if (
            id_talla is not None
            or talla
            or id_color is not None
            or color
            or solo_en_stock
        ):
            var_conds = [VarianteProductoORM.id_producto == ProductoORM.id_producto]

            if id_talla is not None:
                var_conds.append(VarianteProductoORM.id_talla == id_talla)
            elif talla:
                talla_clean = talla.strip()
                var_conds.append(
                    exists(
                        select(1)
                        .select_from(TallaORM)
                        .where(
                            and_(
                                TallaORM.id_talla == VarianteProductoORM.id_talla,
                                func.lower(TallaORM.codigo) == talla_clean.lower(),
                            )
                        )
                    )
                )

            if id_color is not None:
                var_conds.append(VarianteProductoORM.id_color == id_color)
            elif color:
                color_clean = color.strip()
                var_conds.append(
                    exists(
                        select(1)
                        .select_from(ColorORM)
                        .where(
                            and_(
                                ColorORM.id_color == VarianteProductoORM.id_color,
                                func.lower(ColorORM.nombre) == color_clean.lower(),
                            )
                        )
                    )
                )

            if solo_en_stock:
                var_conds.append(
                    exists(
                        select(1)
                        .select_from(InventarioSucursalORM)
                        .where(
                            and_(
                                InventarioSucursalORM.id_variante == VarianteProductoORM.id_variante,
                                InventarioSucursalORM.cantidad_disponible > 0,
                            )
                        )
                    )
                )

            condiciones.append(
                exists(
                    select(1)
                    .select_from(VarianteProductoORM)
                    .where(and_(*var_conds))
                )
            )

        # Conteo total de registros coincidentes
        stmt_count = select(func.count(ProductoORM.id_producto)).where(and_(*condiciones))
        total_registros = session.scalar(stmt_count) or 0

        # Ordenamiento
        orden = CriterioOrdenamiento(ordenar_por) if ordenar_por in [c.value for c in CriterioOrdenamiento] else CriterioOrdenamiento.RECIENTES
        if orden == CriterioOrdenamiento.PRECIO_ASC:
            order_clause = ProductoORM.precio_base.asc()
        elif orden == CriterioOrdenamiento.PRECIO_DESC:
            order_clause = ProductoORM.precio_base.desc()
        elif orden == CriterioOrdenamiento.NOMBRE_ASC:
            order_clause = ProductoORM.nombre.asc()
        elif orden == CriterioOrdenamiento.RELEVANCIA and clean_q:
            order_clause = func.similarity(ProductoORM.nombre, clean_q).desc()
        else:
            order_clause = ProductoORM.creado_en.desc()

        # Paginación
        total_paginas = ceil(total_registros / limite) if total_registros > 0 else 0
        offset = (pagina - 1) * limite

        # Consulta final con carga impaciente (eager loading) de relaciones
        stmt_items = (
            select(ProductoORM)
            .where(and_(*condiciones))
            .options(
                selectinload(ProductoORM.categoria),
                selectinload(ProductoORM.coleccion).selectinload(ColeccionORM.temporada),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.talla),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.color),
                selectinload(ProductoORM.variantes).selectinload(VarianteProductoORM.inventarios),
            )
            .order_by(order_clause, ProductoORM.id_producto.desc())
            .offset(offset)
            .limit(limite)
        )

        productos_orm = session.scalars(stmt_items).all()
        items = [cls.mapear_a_item_out(p) for p in productos_orm]

        filtros_dict: Dict[str, Any] = {}
        if clean_q:
            filtros_dict["q"] = clean_q
        if categoria_id is not None:
            filtros_dict["categoria_id"] = categoria_id
        if coleccion_id is not None:
            filtros_dict["coleccion_id"] = coleccion_id
        if temporada_id is not None:
            filtros_dict["temporada_id"] = temporada_id
        if talla or id_talla:
            filtros_dict["talla"] = talla or id_talla
        if color or id_color:
            filtros_dict["color"] = color or id_color
        if precio_min is not None:
            filtros_dict["precio_min"] = float(precio_min)
        if precio_max is not None:
            filtros_dict["precio_max"] = float(precio_max)
        filtros_dict["solo_en_stock"] = solo_en_stock
        filtros_dict["ordenar_por"] = orden.value

        return ProductoPaginadoOut(
            items=items,
            paginacion=PaginacionMetaOut(
                total_registros=total_registros,
                pagina_actual=pagina,
                limite=limite,
                total_paginas=total_paginas,
                tiene_siguiente=pagina < total_paginas,
                tiene_anterior=pagina > 1,
            ),
            filtros_aplicados=filtros_dict,
        )

    @classmethod
    def obtener_filtros_disponibles(cls, session: Session) -> FiltrosDisponiblesOut:
        """Obtiene las dimensiones de filtro disponibles en la base de datos."""
        # 1. Temporadas activas
        temporadas_orm = session.scalars(
            select(TemporadaORM).where(TemporadaORM.activa == True).order_by(TemporadaORM.fecha_inicio.desc())
        ).all()
        temporadas = [
            OpcionFiltroItem(id=t.id_temporada, nombre=t.nombre, extra=t.tipo)
            for t in temporadas_orm
        ]

        # 2. Colecciones con conteo de productos activos
        stmt_col = (
            select(
                ColeccionORM.id_coleccion,
                ColeccionORM.nombre,
                func.count(ProductoORM.id_producto).label("conteo"),
            )
            .outerjoin(
                ProductoORM,
                and_(
                    ProductoORM.id_coleccion == ColeccionORM.id_coleccion,
                    ProductoORM.activo == True,
                ),
            )
            .group_by(ColeccionORM.id_coleccion, ColeccionORM.nombre)
            .order_by(ColeccionORM.nombre.asc())
        )
        colecciones = [
            OpcionFiltroItem(id=row[0], nombre=row[1], conteo=row[2])
            for row in session.execute(stmt_col).all()
        ]

        # 3. Categorías con conteo
        stmt_cat = (
            select(
                CategoriaORM.id_categoria,
                CategoriaORM.nombre,
                func.count(ProductoORM.id_producto).label("conteo"),
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
        categorias = [
            OpcionFiltroItem(id=row[0], nombre=row[1], conteo=row[2])
            for row in session.execute(stmt_cat).all()
        ]

        # 4. Tallas
        tallas_orm = session.scalars(select(TallaORM).order_by(TallaORM.orden.asc())).all()
        tallas = [
            OpcionFiltroItem(id=t.id_talla, codigo=t.codigo, nombre=t.codigo)
            for t in tallas_orm
        ]

        # 5. Colores
        colores_orm = session.scalars(select(ColorORM).order_by(ColorORM.nombre.asc())).all()
        colores = [
            OpcionFiltroItem(id=c.id_color, nombre=c.nombre, extra=c.codigo_hex)
            for c in colores_orm
        ]

        # 6. Rango de Precios
        stmt_precios = select(
            func.coalesce(func.min(ProductoORM.precio_base), Decimal("0.00")),
            func.coalesce(func.max(ProductoORM.precio_base), Decimal("1500.00")),
        ).where(ProductoORM.activo == True)
        min_p, max_p = session.execute(stmt_precios).one()

        return FiltrosDisponiblesOut(
            temporadas=temporadas,
            colecciones=colecciones,
            categorias=categorias,
            tallas=tallas,
            colores=colores,
            precio_min_global=min_p,
            precio_max_global=max_p,
        )
