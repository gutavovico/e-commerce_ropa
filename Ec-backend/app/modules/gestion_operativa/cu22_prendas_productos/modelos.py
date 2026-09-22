"""Modelos ORM de SQLAlchemy 2.0 para CU22: Gestionar Prendas, Productos y Variantes (SKUs).

Re-exporta y mapea las entidades sobre el esquema fashionstore en PostgreSQL:
- ProductoORM: Prenda con clasificacion taxonomica, precio base y estado activo.
- VarianteProductoORM: Instancia comercial con SKU, talla, color, precio_extra y activo.
- CategoriaORM, TallaORM, ColorORM, ColeccionORM, InventarioSucursalORM.
"""

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

__all__ = [
    "CategoriaORM",
    "ColeccionORM",
    "ColorORM",
    "InventarioSucursalORM",
    "ProductoORM",
    "TallaORM",
    "TemporadaORM",
    "VarianteProductoORM",
]
