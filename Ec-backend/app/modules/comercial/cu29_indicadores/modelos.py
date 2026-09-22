"""Modelos y dependencias relacionales de SQLAlchemy 2.0 para CU29.
Nomenclatura oficial: Visualizar indicadores empresariales

Reutiliza y consolida las entidades del esquema `fashionstore` requeridas
para consultas analiticas de ingresos, transacciones y rankings:
- fashionstore.ventas
- fashionstore.venta_detalle
- fashionstore.variantes_producto
- fashionstore.productos
- fashionstore.categorias
- fashionstore.sucursales
"""

from modules.catalogo.modelos import (
    CategoriaORM,
    ProductoORM,
    VarianteProductoORM,
)
from modules.comercial.cu28_ventas_reservas.modelos import (
    VentaDetalleORM,
    VentaORM,
)
from modules.gestion_operativa.modelos import (
    CiudadORM,
    SucursalORM,
)

__all__ = [
    "VentaORM",
    "VentaDetalleORM",
    "VarianteProductoORM",
    "ProductoORM",
    "CategoriaORM",
    "SucursalORM",
    "CiudadORM",
]
