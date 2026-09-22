"""Modelos ORM para CU24: Gestionar temporadas y colecciones.

Re-exporta las entidades persistentes mapeadas sobre el esquema fashionstore en PostgreSQL:
- TemporadaORM: Mapeo de la tabla fashionstore.temporadas.
- ColeccionORM: Mapeo de la tabla fashionstore.colecciones.
- ProductoORM: Mapeo de la tabla fashionstore.productos para verificacion de integridad referencial.
"""

from modules.catalogo.modelos import ColeccionORM, ProductoORM, TemporadaORM

__all__ = [
    "TemporadaORM",
    "ColeccionORM",
    "ProductoORM",
]
