"""Servicio de dominio para CU36: Consultar Colecciones.

Implementa la lógica de negocio para:
- Resolución de temporada comercial activa y colecciones vigentes.
- Cálculo de precio de entrada ('Desde X €'), total de prendas activas y piezas clave.
- Listado de prendas exclusivas por colección específica.
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from modules.catalogo.modelos import (
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    ProveedorORM,
    TallaORM,
    TemporadaORM,
    VarianteProductoORM,
)
from modules.catalogo.cu36_colecciones.esquemas import (
    ColeccionDetalleOut,
    ColeccionResumenOut,
    ColeccionesActivasResponseOut,
    ProductoColeccionItemOut,
    VarianteColeccionOut,
)


class ColeccionNoEncontradaError(Exception):
    """Excepción lanzada cuando una colección no existe."""

    def __init__(self, mensaje: str = "Colección no encontrada"):
        self.mensaje = mensaje
        super().__init__(mensaje)


class ColeccionesService:
    """Servicio de negocio para consulta y exploración editorial de colecciones."""

    # Mapeo de metadatos editoriales de alta costura para fidelidad visual
    METADATOS_EDITORIALES: Dict[str, Dict[str, str]] = {
        "sastrería en lana virgen & seda natural": {
            "taller": "Molinos Históricos de Biella y Lyon",
            "edicion": "EDICIÓN VIGENTE",
            "disponibilidad": "DISPONIBLE",
        },
        "edición milano: punto & lino": {
            "taller": "Molinos de Biella & Como",
            "edicion": "EDICIÓN SS24 MILANO",
            "disponibilidad": "DISPONIBLE",
        },
        "abrigos en alpaca & lana": {
            "taller": "Alpaca Suri de los Andes",
            "edicion": "EDICIÓN Nº 03 INVIERNO",
            "disponibilidad": "ÚLTIMAS UNIDADES",
        },
        "seda & plisados de lyon": {
            "taller": "Hilatura Francesa 100%",
            "edicion": "EDICIÓN LYON",
            "disponibilidad": "DISPONIBLE",
        },
        "sastrería & gabardinas giza": {
            "taller": "Algodón Egipcio ELS",
            "edicion": "ESENCIALES ATEMPORALES",
            "disponibilidad": "PIEZAS ICÓNICAS",
        },
    }

    @classmethod
    def _derivar_metadatos_coleccion(
        cls, nombre: str, proveedor: Optional[ProveedorORM]
    ) -> Dict[str, str]:
        """Deriva el taller de origen y badges editoriales según la colección."""
        nombre_lower = nombre.lower().strip()
        for clave, meta in cls.METADATOS_EDITORIALES.items():
            if clave in nombre_lower:
                return meta

        taller = proveedor.razon_social if proveedor else "Atelier Central Serrano"
        return {
            "taller": taller,
            "edicion": "EDICIÓN CÁPSULA",
            "disponibilidad": "DISPONIBLE",
        }

    @classmethod
    def _derivar_badge_producto(cls, prod: ProductoORM, idx: int = 0) -> str:
        """Deriva una etiqueta editorial de alta costura según el producto."""
        nombre_lower = prod.nombre.lower()
        if "vestido" in nombre_lower or "plisado" in nombre_lower:
            return "COLECCIÓN 07"
        if "blazer" in nombre_lower or "saco" in nombre_lower:
            return "EN SERRANO"
        if "blusa" in nombre_lower or "camisa" in nombre_lower or "satén" in nombre_lower:
            return "BÁSICO DE LUJO"
        if "pantalón" in nombre_lower or "sastre" in nombre_lower:
            return "SASTRERÍA ATELIER"
        badges_rotativos = ["DISPONIBLE", "EDICIÓN LIMITADA", "EN SERRANO", "PIEZA CLAVE"]
        return badges_rotativos[idx % len(badges_rotativos)]

    @classmethod
    def _derivar_subtitulo_textil(cls, prod: ProductoORM) -> str:
        """Deriva el subtítulo de composición textil."""
        nombre_lower = prod.nombre.lower()
        if "seda" in nombre_lower or "vestido" in nombre_lower:
            return "SEDA LYON · ALTA COSTURA"
        if "lana" in nombre_lower or "blazer" in nombre_lower:
            return "BIELLA 380G · SASTRERÍA ATELIER"
        if "satén" in nombre_lower or "blusa" in nombre_lower:
            return "SATÉN 100% · SEDA 22 MOMME"
        if "pantalón" in nombre_lower or "tiro alto" in nombre_lower:
            return "LANA FINA · ÉBANO"
        if "lino" in nombre_lower:
            return "LINO BELGA · HILATURA PURA"
        if "alpaca" in nombre_lower or "abrigo" in nombre_lower:
            return "BABY ALPACA 100% · SURI"
        return "CONFECCIÓN ARTESANAL · MAISON"

    @classmethod
    def _mapear_producto_a_item_out(
        cls, prod: ProductoORM, idx: int = 0
    ) -> ProductoColeccionItemOut:
        """Mapea una entidad ProductoORM a su esquema de salida Pydantic."""
        colores_set = set()
        variantes_out: List[VarianteColeccionOut] = []
        stock_total = 0

        for v in prod.variantes:
            color_nombre = v.color.nombre if v.color else "Tono Atelier"
            colores_set.add(color_nombre)
            hex_color = v.color.codigo_hex if v.color else None

            # Calcular existencias físicas de la variante
            stock_var = sum(
                inv.cantidad_disponible
                for inv in v.inventarios
                if inv.estado == "disponible" and inv.cantidad_disponible > 0
            )
            stock_total += stock_var

            variantes_out.append(
                VarianteColeccionOut(
                    id_variante=v.id_variante,
                    talla=v.talla.codigo if v.talla else "U",
                    color=color_nombre,
                    codigo_hex=hex_color,
                    sku=v.sku,
                    precio_final=prod.precio_base + (v.precio_extra or Decimal("0.00")),
                    stock_disponible=stock_var,
                )
            )

        categoria_nombre = prod.categoria.nombre if prod.categoria else "Alta Costura"

        return ProductoColeccionItemOut(
            id_producto=prod.id_producto,
            nombre=prod.nombre,
            descripcion=prod.descripcion,
            precio_base=prod.precio_base,
            imagen_url=prod.imagen_url,
            badge_editorial=cls._derivar_badge_producto(prod, idx),
            subtitulo_textil=cls._derivar_subtitulo_textil(prod),
            categoria=categoria_nombre,
            colores_disponibles=list(colores_set),
            stock_total_disponible=stock_total,
            tiene_stock=stock_total > 0,
            variantes=variantes_out,
        )

    @classmethod
    def obtener_temporada_activa(cls, db: Session) -> Optional[TemporadaORM]:
        """Resuelve la temporada comercial activa por rango de fecha o flag activa."""
        hoy = date.today()

        # 1. Intentar por fecha vigente dentro de temporadas activas
        stmt = (
            select(TemporadaORM)
            .where(
                TemporadaORM.activa.is_(True),
                TemporadaORM.fecha_inicio <= hoy,
                TemporadaORM.fecha_fin >= hoy,
            )
            .order_by(TemporadaORM.fecha_fin.desc())
        )
        temporada = db.execute(stmt).scalars().first()

        # 2. Fallback a la temporada activa más reciente si no hay coincidencia exacta de fechas
        if not temporada:
            stmt_fallback = (
                select(TemporadaORM)
                .where(TemporadaORM.activa.is_(True))
                .order_by(TemporadaORM.fecha_fin.desc())
            )
            temporada = db.execute(stmt_fallback).scalars().first()

        # 3. Fallback a la última temporada registrada en el sistema
        if not temporada:
            stmt_ultima = select(TemporadaORM).order_by(TemporadaORM.id_temporada.desc())
            temporada = db.execute(stmt_ultima).scalars().first()

        return temporada

    @classmethod
    def obtener_colecciones_activas(
        cls, db: Session, limite_piezas_clave: int = 4
    ) -> ColeccionesActivasResponseOut:
        """Recupera las colecciones activas, destacando la principal con piezas clave."""
        temporada = cls.obtener_temporada_activa(db)

        if not temporada:
            return ColeccionesActivasResponseOut(
                temporada_activa_id=None,
                temporada_activa_nombre=None,
                temporada_activa_tipo=None,
                coleccion_destacada=None,
                otras_colecciones=[],
                total_colecciones=0,
            )

        # Consultar colecciones de la temporada activa y colecciones complementarias
        stmt_colecciones = (
            select(ColeccionORM)
            .where(ColeccionORM.id_temporada == temporada.id_temporada)
            .options(
                joinedload(ColeccionORM.temporada),
                joinedload(ColeccionORM.proveedor),
                selectinload(ColeccionORM.productos)
                .joinedload(ProductoORM.categoria),
                selectinload(ColeccionORM.productos)
                .selectinload(ProductoORM.variantes)
                .joinedload(VarianteProductoORM.color),
                selectinload(ColeccionORM.productos)
                .selectinload(ProductoORM.variantes)
                .joinedload(VarianteProductoORM.talla),
                selectinload(ColeccionORM.productos)
                .selectinload(ProductoORM.variantes)
                .selectinload(VarianteProductoORM.inventarios),
            )
            .order_by(ColeccionORM.id_coleccion.asc())
        )
        colecciones = list(db.execute(stmt_colecciones).scalars().all())

        # Si hay pocas colecciones en la temporada activa, incorporar colecciones de temporadas anteriores
        if len(colecciones) < 4:
            ids_existentes = {c.id_coleccion for c in colecciones}
            stmt_otras = (
                select(ColeccionORM)
                .where(
                    ColeccionORM.id_temporada != temporada.id_temporada,
                    ColeccionORM.id_coleccion.not_in(ids_existentes) if ids_existentes else True,
                )
                .options(
                    joinedload(ColeccionORM.temporada),
                    joinedload(ColeccionORM.proveedor),
                    selectinload(ColeccionORM.productos)
                    .joinedload(ProductoORM.categoria),
                    selectinload(ColeccionORM.productos)
                    .selectinload(ProductoORM.variantes)
                    .joinedload(VarianteProductoORM.color),
                    selectinload(ColeccionORM.productos)
                    .selectinload(ProductoORM.variantes)
                    .joinedload(VarianteProductoORM.talla),
                    selectinload(ColeccionORM.productos)
                    .selectinload(ProductoORM.variantes)
                    .selectinload(VarianteProductoORM.inventarios),
                )
                .order_by(ColeccionORM.id_coleccion.desc())
                .limit(6 - len(colecciones))
            )
            colecciones_extra = [
                c for c in db.execute(stmt_otras).scalars().all()
                if c.id_coleccion not in ids_existentes
            ]
            colecciones.extend(colecciones_extra)

        if not colecciones:
            return ColeccionesActivasResponseOut(
                temporada_activa_id=temporada.id_temporada,
                temporada_activa_nombre=temporada.nombre,
                temporada_activa_tipo=str(temporada.tipo),
                coleccion_destacada=None,
                otras_colecciones=[],
                total_colecciones=0,
            )

        # Determinar colección destacada (aquella con más productos o la primera)
        coleccion_destacada_orm = max(
            colecciones,
            key=lambda c: len([p for p in c.productos if p.activo]),
        )

        resúmenes: List[ColeccionResumenOut] = []

        for col in colecciones:
            es_destacada = col.id_coleccion == coleccion_destacada_orm.id_coleccion
            prendas_activas = sorted([p for p in col.productos if p.activo], key=lambda p: p.id_producto)
            total_prendas = len(prendas_activas)

            # Cálculo de precio de entrada 'Desde X €'
            if prendas_activas:
                precio_desde = min(p.precio_base for p in prendas_activas)
                portada = next((p.imagen_url for p in prendas_activas if p.imagen_url), None)
            else:
                precio_desde = Decimal("0.00")
                portada = None

            metadatos = cls._derivar_metadatos_coleccion(col.nombre, col.proveedor)

            # Si es la destacada, precargar hasta limite_piezas_clave
            piezas_clave: List[ProductoColeccionItemOut] = []
            if es_destacada:
                piezas_clave = [
                    cls._mapear_producto_a_item_out(p, idx)
                    for idx, p in enumerate(prendas_activas[:limite_piezas_clave])
                ]

            temporada_col = col.temporada or temporada

            resúmenes.append(
                ColeccionResumenOut(
                    id_coleccion=col.id_coleccion,
                    nombre=col.nombre,
                    descripcion=col.descripcion,
                    temporada_id=temporada_col.id_temporada,
                    temporada_nombre=temporada_col.nombre,
                    temporada_tipo=str(temporada_col.tipo),
                    proveedor_nombre=col.proveedor.razon_social if col.proveedor else None,
                    taller_origen=metadatos["taller"],
                    precio_desde=precio_desde,
                    total_prendas=total_prendas,
                    es_destacada=es_destacada,
                    badge_edicion=metadatos["edicion"],
                    badge_disponibilidad=metadatos["disponibilidad"],
                    imagen_portada=portada,
                    piezas_clave=piezas_clave,
                )
            )

        destacada_out = next((r for r in resúmenes if r.es_destacada), resúmenes[0])
        otras_out = [r for r in resúmenes if not r.es_destacada]

        return ColeccionesActivasResponseOut(
            temporada_activa_id=temporada.id_temporada,
            temporada_activa_nombre=temporada.nombre,
            temporada_activa_tipo=str(temporada.tipo),
            coleccion_destacada=destacada_out,
            otras_colecciones=otras_out,
            total_colecciones=len(resúmenes),
        )

    @classmethod
    def obtener_prendas_por_coleccion(
        cls, db: Session, id_coleccion: int
    ) -> ColeccionDetalleOut:
        """Recupera la información editorial de una colección y sus prendas activas."""
        stmt = (
            select(ColeccionORM)
            .where(ColeccionORM.id_coleccion == id_coleccion)
            .options(
                joinedload(ColeccionORM.temporada),
                joinedload(ColeccionORM.proveedor),
                selectinload(ColeccionORM.productos)
                .joinedload(ProductoORM.categoria),
                selectinload(ColeccionORM.productos)
                .selectinload(ProductoORM.variantes)
                .joinedload(VarianteProductoORM.color),
                selectinload(ColeccionORM.productos)
                .selectinload(ProductoORM.variantes)
                .joinedload(VarianteProductoORM.talla),
                selectinload(ColeccionORM.productos)
                .selectinload(ProductoORM.variantes)
                .selectinload(VarianteProductoORM.inventarios),
            )
        )
        col = db.execute(stmt).scalars().first()

        if not col:
            raise ColeccionNoEncontradaError(
                f"Colección con id {id_coleccion} no encontrada en el catálogo"
            )

        prendas_activas = sorted([p for p in col.productos if p.activo], key=lambda p: p.id_producto)
        total_prendas = len(prendas_activas)

        metadatos = cls._derivar_metadatos_coleccion(col.nombre, col.proveedor)

        items_out = [
            cls._mapear_producto_a_item_out(p, idx)
            for idx, p in enumerate(prendas_activas)
        ]

        empty_state = None
        if total_prendas == 0:
            empty_state = (
                "Próximo lanzamiento: las piezas de esta colección están en proceso de "
                "confección artesanal y estarán disponibles en las boutiques próximamente."
            )

        temporada_nombre = col.temporada.nombre if col.temporada else "Temporada Permanente"
        temporada_tipo = str(col.temporada.tipo) if col.temporada else "permanente"
        temporada_id = col.temporada.id_temporada if col.temporada else 0

        return ColeccionDetalleOut(
            id_coleccion=col.id_coleccion,
            nombre=col.nombre,
            descripcion=col.descripcion,
            temporada_id=temporada_id,
            temporada_nombre=temporada_nombre,
            temporada_tipo=temporada_tipo,
            proveedor_nombre=col.proveedor.razon_social if col.proveedor else None,
            taller_origen=metadatos["taller"],
            total_prendas=total_prendas,
            mensaje_empty_state=empty_state,
            productos=items_out,
        )
