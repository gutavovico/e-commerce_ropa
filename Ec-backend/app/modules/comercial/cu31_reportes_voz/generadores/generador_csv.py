"""Generador de reportes en formato CSV plano con compatibilidad UTF-8 BOM."""

import csv
from datetime import datetime
import io
from typing import Any, Dict, List, Optional


class GeneradorCSV:
    """Generador binario de datos tabulares delimitados por comas (.csv)."""

    @classmethod
    def generar(
        cls,
        titulo: str,
        subtitulo: str,
        columnas: List[str],
        filas: List[List[Any]],
        totales: Optional[Dict[str, Any]] = None,
        metadatos: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Genera un archivo CSV con prefijo BOM UTF-8 y retorna sus bytes.

        Args:
            titulo: Titulo del reporte.
            subtitulo: Subtitulo o rango temporal.
            columnas: Encabezados de columnas.
            filas: Matriz de valores por fila.
            totales: Resumen de totales al pie.
            metadatos: Informacion complementaria de emision.

        Returns:
            bytes codificados en UTF-8 con BOM.
        """
        string_io = io.StringIO()
        # Inyectar BOM para compatibilidad directa con Microsoft Excel en Windows
        string_io.write("\ufeff")

        writer = csv.writer(string_io, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        # 1. Cabecera Informativa
        writer.writerow([f"# {titulo.upper()} - REPORTE EJECUTIVO"])
        writer.writerow([f"# Criterio: {subtitulo}"])
        texto_meta = f"# Emision: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if metadatos:
            texto_meta += " | " + " | ".join([f"{k}: {v}" for k, v in metadatos.items()])
        writer.writerow([texto_meta])
        writer.writerow([])  # Linea en blanco

        # 2. Encabezados de Columnas
        writer.writerow(columnas)

        # 3. Filas de Datos
        for fila in filas:
            fila_formateada = []
            for val in fila:
                if isinstance(val, datetime):
                    fila_formateada.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                elif isinstance(val, float):
                    fila_formateada.append(f"{val:.2f}")
                elif val is None:
                    fila_formateada.append("")
                else:
                    fila_formateada.append(str(val))
            writer.writerow(fila_formateada)

        # 4. Fila de Totales
        if totales:
            fila_totales = ["TOTALES"]
            for col in columnas[1:]:
                if col in totales:
                    v = totales[col]
                    fila_totales.append(f"{v:.2f}" if isinstance(v, float) else str(v))
                else:
                    fila_totales.append("")
            writer.writerow(fila_totales)

        return string_io.getvalue().encode("utf-8")
