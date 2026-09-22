"""Utilidades y algoritmos corporativos para CU22: Gestionar Prendas, Productos y Variantes (SKUs)."""

import re
import unicodedata
from typing import Optional


def slugify_text(texto: str, max_len: int = 16) -> str:
    """Convierte texto en un slug alfanumerico en mayusculas sin tildes ni caracteres especiales."""
    if not texto:
        return ""
    # Descomposicion Unicode para purgar tildes y diacriticos
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_texto = nfkd.encode("ASCII", "ignore").decode("utf-8")
    # Conservar unicamente alfanumericos y reemplazar espacios/simbolos por guiones
    limpio = re.sub(r"[^A-Za-z0-9]+", "-", ascii_texto).strip("-").upper()
    return limpio[:max_len].strip("-")


def generar_sku_corporativo(
    nombre_producto: str,
    codigo_talla: str,
    nombre_color: str,
    id_producto: Optional[int] = None,
) -> str:
    """Genera un SKU estandarizado con el formato FS-[SLUG_PRODUCTO]-[COD_TALLA]-[SLUG_COLOR].
    
    Garantiza una cadena alfanumerica en mayusculas, sin caracteres especiales ni tildes,
    con longitud maxima acotada a 50 caracteres para compatibilidad absoluta con la base de datos.
    """
    slug_prod = slugify_text(nombre_producto, max_len=18)
    slug_talla = slugify_text(codigo_talla, max_len=8)
    slug_color = slugify_text(nombre_color, max_len=10)

    if not slug_prod:
        slug_prod = f"PROD{id_producto}" if id_producto else "PROD"
    if not slug_talla:
        slug_talla = "STD"
    if not slug_color:
        slug_color = "UNI"

    sku_candidato = f"FS-{slug_prod}-{slug_talla}-{slug_color}"
    return sku_candidato[:50].strip("-")
