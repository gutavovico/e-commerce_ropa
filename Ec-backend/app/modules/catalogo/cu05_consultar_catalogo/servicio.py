"""Servicio de dominio para CU05: Consultar Catálogo de Productos."""

from decimal import Decimal
from math import ceil
from typing import List, Optional

from sqlalchemy.orm import Session

from modules.catalogo.cu05_consultar_catalogo.esquemas import (
    CatalogoOut,
    CategoriaResumenOut,
    ColorItemOut,
    ProductoCatalogoOut,
)
from modules.catalogo.cu05_consultar_catalogo.repositorio import CatalogoRepositorio
from modules.catalogo.modelos import ProductoORM


class CatalogoServicio:
    """Lógica de negocio y transformación editorial para el catálogo de FashionStore."""

    @classmethod
    def consultar_catalogo(
        cls,
        db: Session,
        categoria_id: Optional[int] = None,
        ordenar_por: str = "recientes",
        pagina: int = 1,
        limite: int = 8,
    ) -> CatalogoOut:
        """Obtiene el catálogo paginado enriquecido con categorías, promociones y variantes."""
        # 1. Obtener resumen de categorías con unidades disponibles para los chips
        categorias_raw = CatalogoRepositorio.obtener_resumen_categorias(db)
        resumen_categorias = [
            CategoriaResumenOut(
                id_categoria=cat_id,
                nombre=cat_nombre,
                total_prendas=total,
            )
            for cat_id, cat_nombre, total in categorias_raw
        ]

        # 2. Consultar productos paginados con precarga optimizada
        productos_orm, total_articulos = CatalogoRepositorio.consultar_productos_paginados(
            db=db,
            categoria_id=categoria_id,
            ordenar_por=ordenar_por,
            pagina=pagina,
            limite=limite,
        )

        # 3. Obtener promociones activas para los productos en pantalla
        ids_productos = [p.id_producto for p in productos_orm]
        promociones_map = CatalogoRepositorio.obtener_promociones_activas_para_productos(
            db=db, ids_productos=ids_productos
        )

        # 4. Mapear entidades ORM a esquemas enriquecidos
        items: List[ProductoCatalogoOut] = [
            cls._mapear_producto(p, promociones_map.get(p.id_producto))
            for p in productos_orm
        ]

        # 5. Metadatos de paginación
        total_paginas = ceil(total_articulos / limite) if total_articulos > 0 else 0
        tiene_siguiente = pagina < total_paginas
        tiene_anterior = pagina > 1 and total_paginas > 0

        return CatalogoOut(
            resumen_categorias=resumen_categorias,
            total_articulos=total_articulos,
            pagina_actual=pagina,
            limite=limite,
            total_paginas=total_paginas,
            tiene_siguiente=tiene_siguiente,
            tiene_anterior=tiene_anterior,
            categoria_seleccionada_id=categoria_id,
            items=items,
        )

    @classmethod
    def _mapear_producto(
        cls, p: ProductoORM, promo_info: Optional[tuple] = None
    ) -> ProductoCatalogoOut:
        """Transforma una entidad ProductoORM en el DTO de tarjeta de alta costura."""
        # Recolectar tallas ordenadas y únicas
        tallas_dict = {}
        for var in p.variantes or []:
            if var.talla and var.talla.codigo:
                tallas_dict[var.talla.codigo] = var.talla.orden or 0
        tallas_disponibles = sorted(tallas_dict.keys(), key=lambda t: tallas_dict[t])

        # Recolectar colores únicos
        colores_vistos = set()
        colores_disponibles: List[ColorItemOut] = []
        for var in p.variantes or []:
            if var.color and var.color.id_color not in colores_vistos:
                colores_vistos.add(var.color.id_color)
                colores_disponibles.append(
                    ColorItemOut(
                        id_color=var.color.id_color,
                        nombre=var.color.nombre,
                        codigo_hex=var.color.codigo_hex or "#1A1A1A",
                    )
                )

        # Calcular stock total disponible sumando todas las sucursales
        stock_total = 0
        for var in p.variantes or []:
            for inv in var.inventarios or []:
                stock_total += max(0, inv.cantidad_disponible)

        tiene_stock = stock_total > 0

        # Cálculo de promociones y descuentos
        precio_base = Decimal(str(p.precio_base))
        tiene_descuento = False
        porcentaje_descuento: Optional[int] = None
        precio_final = precio_base

        if promo_info:
            pct_raw, _ = promo_info
            pct: Optional[Decimal] = None
            try:
                if pct_raw is not None:
                    pct = Decimal(str(pct_raw))
            except Exception:
                pct = None

            if pct is not None and pct > 0:
                tiene_descuento = True
                porcentaje_descuento = int(pct)
                descuento = (precio_base * pct / Decimal("100")).quantize(Decimal("0.01"))
                precio_final = (precio_base - descuento).quantize(Decimal("0.01"))

        # Determinar subtítulo de atelier según categoría / línea
        categoria_nombre = p.categoria.nombre if p.categoria else "Prendas"
        cat_lower = categoria_nombre.lower()
        if "sastrer" in cat_lower or "traje" in cat_lower or "blazer" in cat_lower:
            subtitulo_atelier = "SASTRERÍA ATELIER"
        elif "vestido" in cat_lower or "gala" in cat_lower or "noche" in cat_lower:
            subtitulo_atelier = "ALTA COSTURA"
        elif "abrigo" in cat_lower or "chaqueta" in cat_lower or "trench" in cat_lower:
            subtitulo_atelier = "ABRIGOS DE AUTOR"
        elif "blusa" in cat_lower or "top" in cat_lower or "camisa" in cat_lower:
            subtitulo_atelier = "BÁSICOS DE LUJO"
        elif "punto" in cat_lower or "cashmere" in cat_lower:
            subtitulo_atelier = "PUNTO & CASHMERE"
        else:
            subtitulo_atelier = "EDICIÓN ATELIER"

        # Asignar badge editorial contextual
        if tiene_descuento:
            etiqueta_badge = f"-{porcentaje_descuento}% ATELIER"
        elif stock_total > 0 and stock_total <= 5:
            etiqueta_badge = "ÚLTIMAS UNIDADES"
        elif not tiene_stock:
            etiqueta_badge = "PRÓXIMO INGRESO"
        else:
            # Determinación editorial según ID de producto para variedad estética
            badges_editoriales = [
                "EDICIÓN LIMITADA",
                "EN SERRANO",
                "NOVEDAD",
                "DISPONIBLE",
                "SEDA PURA",
                "LANA & SEDA",
            ]
            etiqueta_badge = badges_editoriales[p.id_producto % len(badges_editoriales)]

        return ProductoCatalogoOut(
            id_producto=p.id_producto,
            nombre=p.nombre,
            descripcion=p.descripcion,
            precio_base=precio_base,
            precio_final=precio_final,
            tiene_descuento=tiene_descuento,
            porcentaje_descuento=porcentaje_descuento,
            imagen_url=p.imagen_url,
            categoria_id=p.id_categoria,
            categoria_nombre=categoria_nombre,
            subtitulo_atelier=subtitulo_atelier,
            etiqueta_badge=etiqueta_badge,
            rating_promedio=4.9,
            tallas_disponibles=tallas_disponibles,
            colores_disponibles=colores_disponibles,
            stock_total_disponible=stock_total,
            tiene_stock=tiene_stock,
            es_favorito=False,
        )
