"""Modelos ORM de SQLAlchemy 2.0 para CU23: Gestionar Categorias, Tallas y Colores.

Re-exporta las entidades persistentes mapeadas sobre el esquema fashionstore en PostgreSQL:
- CategoriaORM: Jerarquia taxonomica auto-referencial (id_categoria_padre).
- TallaORM: Codigo comercial con orden secuencial (orden).
- ColorORM: Denominacion textil con codigo hexadecimal estandar (codigo_hex).
"""

from modules.catalogo.modelos import (
    CategoriaORM,
    ColorORM,
    ProductoORM,
    TallaORM,
    VarianteProductoORM,
)

__all__ = [
    "CategoriaORM",
    "TallaORM",
    "ColorORM",
    "ProductoORM",
    "VarianteProductoORM",
]
