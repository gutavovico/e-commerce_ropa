"""Generador de reportes en formato Excel (.xlsx) con openpyxl.

Aplica la paleta institucional Atelier (Obsidian #111111 y Camel #AD8C63),
auto-ancho de celdas, formatos monetarios y formulas de totalizacion.
"""

from datetime import datetime
import io
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


class GeneradorExcel:
    """Generador binario de planillas ejecutivas en formato Microsoft Excel (.xlsx)."""

    COLOR_OBSIDIAN = "111111"
    COLOR_CAMEL = "AD8C63"
    COLOR_FONDO_CLARO = "F8F7F5"
    COLOR_BORDE = "D5D2CD"

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
        """Construye un libro de calculo Excel estricto y retorna el flujo binario en bytes.

        Args:
            titulo: Titulo principal institucional.
            subtitulo: Detalle del modulo y periodo temporal.
            columnas: Lista de nombres de columnas.
            filas: Matriz de valores correspondientes a cada fila.
            totales: Diccionario opcional de totales o resumen al pie.
            metadatos: Informacion de operador, fecha y sucursal.

        Returns:
            bytes con el contenido del archivo .xlsx generado en memoria.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte Ejecutivo"
        ws.views.sheetView[0].showGridLines = True

        # Tipografias institucionales
        fuente_titulo = Font(name="Arial", size=14, bold=True, color="FFFFFF")
        fuente_subtitulo = Font(name="Arial", size=10, italic=True, color="333333")
        fuente_meta = Font(name="Arial", size=9, bold=False, color="666666")
        fuente_header = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        fuente_datos = Font(name="Arial", size=9, color="111111")
        fuente_totales = Font(name="Arial", size=10, bold=True, color="111111")

        # Rellenos
        fill_titulo = PatternFill(start_color=cls.COLOR_OBSIDIAN, end_color=cls.COLOR_OBSIDIAN, fill_type="solid")
        fill_header = PatternFill(start_color=cls.COLOR_OBSIDIAN, end_color=cls.COLOR_OBSIDIAN, fill_type="solid")
        fill_header_accent = PatternFill(start_color=cls.COLOR_CAMEL, end_color=cls.COLOR_CAMEL, fill_type="solid")
        fill_zebra = PatternFill(start_color=cls.COLOR_FONDO_CLARO, end_color=cls.COLOR_FONDO_CLARO, fill_type="solid")
        fill_totales = PatternFill(start_color="EFECE6", end_color="EFECE6", fill_type="solid")

        # Bordes
        borde_fino = Border(
            left=Side(style="thin", color=cls.COLOR_BORDE),
            right=Side(style="thin", color=cls.COLOR_BORDE),
            top=Side(style="thin", color=cls.COLOR_BORDE),
            bottom=Side(style="thin", color=cls.COLOR_BORDE),
        )
        borde_totales = Border(
            top=Side(style="thin", color=cls.COLOR_OBSIDIAN),
            bottom=Side(style="double", color=cls.COLOR_OBSIDIAN),
        )

        num_columnas = max(len(columnas), 1)

        # 1. Encabezado Institucional (Filas 1 a 3)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_columnas)
        celda_titulo = ws.cell(row=1, column=1, value=titulo.upper())
        celda_titulo.font = fuente_titulo
        celda_titulo.fill = fill_titulo
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 36

        ws.cell(row=2, column=1, value=f"Reporte: {subtitulo}").font = fuente_subtitulo
        ws.row_dimensions[2].height = 20

        # Metadatos en Fila 3
        texto_meta = f"Emision: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if metadatos:
            detalles = [f"{k}: {v}" for k, v in metadatos.items()]
            texto_meta += " | " + " | ".join(detalles)
        ws.cell(row=3, column=1, value=texto_meta).font = fuente_meta
        ws.row_dimensions[3].height = 18

        # 2. Fila de Cabecera de Columnas (Fila 5)
        fila_header = 5
        ws.row_dimensions[fila_header].height = 24
        for col_idx, col_nombre in enumerate(columnas, start=1):
            celda = ws.cell(row=fila_header, column=col_idx, value=col_nombre)
            celda.font = fuente_header
            celda.fill = fill_header if col_idx < num_columnas else fill_header_accent
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.border = borde_fino

        # 3. Datos
        fila_actual = 6
        for fila_idx, fila_datos in enumerate(filas):
            ws.row_dimensions[fila_actual].height = 20
            usar_zebra = (fila_idx % 2 == 1)
            for col_idx, valor in enumerate(fila_datos, start=1):
                celda = ws.cell(row=fila_actual, column=col_idx)

                # Formateo segun tipo de dato
                if isinstance(valor, (int, float)):
                    celda.value = valor
                    if isinstance(valor, float):
                        celda.number_format = "#,##0.00"
                    celda.alignment = Alignment(horizontal="right", vertical="center")
                elif isinstance(valor, datetime):
                    celda.value = valor.strftime("%Y-%m-%d %H:%M")
                    celda.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    celda.value = str(valor) if valor is not None else "-"
                    celda.alignment = Alignment(horizontal="left", vertical="center")

                celda.font = fuente_datos
                if usar_zebra:
                    celda.fill = fill_zebra
                celda.border = borde_fino

            fila_actual += 1

        # 4. Fila de Totales o Resumen (si aplica)
        if totales:
            ws.row_dimensions[fila_actual].height = 24
            celda_tot_label = ws.cell(row=fila_actual, column=1, value="TOTALES / RESUMEN")
            celda_tot_label.font = fuente_totales
            celda_tot_label.fill = fill_totales
            celda_tot_label.alignment = Alignment(horizontal="left", vertical="center")
            celda_tot_label.border = borde_totales

            for col_idx, col_nombre in enumerate(columnas[1:], start=2):
                celda_tot = ws.cell(row=fila_actual, column=col_idx)
                if col_nombre in totales:
                    val_tot = totales[col_nombre]
                    celda_tot.value = val_tot
                    if isinstance(val_tot, (int, float)):
                        celda_tot.number_format = "#,##0.00" if isinstance(val_tot, float) else "#,##0"
                    celda_tot.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    celda_tot.value = ""
                celda_tot.font = fuente_totales
                celda_tot.fill = fill_totales
                celda_tot.border = borde_totales

        # 5. Ajuste dinamico de ancho de columnas
        for col in ws.columns:
            longitud_max = 0
            col_letter = get_column_letter(col[0].column)
            for celda in col:
                if celda.row > 4 and celda.value is not None:
                    longitud_max = max(longitud_max, len(str(celda.value)))
            ancho_ajustado = max(longitud_max + 4, 14)
            ws.column_dimensions[col_letter].width = min(ancho_ajustado, 45)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
