"""Generador de reportes en formato PDF institucional con reportlab.

Aplica maquetacion vectorial Letter horizontal, cabecera editorial Atelier
(Obsidian #111111 y Camel #AD8C63), tablas estructuradas paginadas y pie de pagina numerado.
"""

from datetime import datetime
import io
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class CanvasNumerado(canvas.Canvas):
    """Canvas de ReportLab de dos pasadas para calcular el total de paginas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_paginas = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.dibujar_pie(num_paginas)
            super().showPage()
        super().save()

    def dibujar_pie(self, total_paginas: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))

        # Linea divisoria superior del pie
        self.setStrokeColor(colors.HexColor("#D5D2CD"))
        self.setLineWidth(0.5)
        self.line(40, 32, self._pagesize[0] - 40, 32)

        # Textos de pie de pagina
        texto_confidencial = "FASHION STORE - DOCUMENTO CONFIDENCIAL DE GESTION CORPORATIVA"
        texto_pagina = f"Pagina {self._pageNumber} de {total_paginas}"

        self.drawString(40, 20, texto_confidencial)
        self.drawRightString(self._pagesize[0] - 40, 20, texto_pagina)
        self.restoreState()


class GeneradorPDF:
    """Generador binario de reportes institucionales en formato PDF."""

    COLOR_OBSIDIAN = colors.HexColor("#111111")
    COLOR_CAMEL = colors.HexColor("#AD8C63")
    COLOR_FONDO_CLARO = colors.HexColor("#F8F7F5")
    COLOR_BORDE = colors.HexColor("#D5D2CD")

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
        """Construye un documento PDF institucional paginado y retorna sus bytes.

        Args:
            titulo: Titulo principal de la compania o modulo.
            subtitulo: Criterio temporal y descripcion del reporte.
            columnas: Lista de nombres de columnas.
            filas: Matriz de valores.
            totales: Resumen numerico consolidado.
            metadatos: Diccionario de datos operativos (sucursal, operador, fecha).

        Returns:
            bytes del archivo PDF compilado.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=50,
        )

        estilos = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            name="ReporteTitulo",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=cls.COLOR_OBSIDIAN,
            spaceAfter=4,
        )
        estilo_subtitulo = ParagraphStyle(
            name="ReporteSubtitulo",
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=13,
            textColor=cls.COLOR_CAMEL,
            spaceAfter=6,
        )
        estilo_meta = ParagraphStyle(
            name="ReporteMeta",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12,
        )
        estilo_celda = ParagraphStyle(
            name="ReporteCelda",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#111111"),
        )
        estilo_header = ParagraphStyle(
            name="ReporteHeader",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=1,  # Centrado
        )

        elementos = []

        # 1. Cabecera Institucional
        elementos.append(Paragraph(titulo.upper(), estilo_titulo))
        elementos.append(Paragraph(f"Reporte Ejecutivo: {subtitulo}", estilo_subtitulo))

        detalles_meta = [f"Fecha de Emision: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        if metadatos:
            for k, v in metadatos.items():
                detalles_meta.append(f"{k}: {v}")
        elementos.append(Paragraph(" | ".join(detalles_meta), estilo_meta))
        elementos.append(Spacer(1, 8))

        # 2. Construccion de la Tabla
        datos_tabla = []

        # Fila de Cabecera
        fila_cabecera = [Paragraph(col, estilo_header) for col in columnas]
        datos_tabla.append(fila_cabecera)

        # Filas de Datos
        for fila in filas:
            fila_p = []
            for val in fila:
                if isinstance(val, float):
                    txt = f"{val:,.2f}"
                elif isinstance(val, int):
                    txt = f"{val:,}"
                elif isinstance(val, datetime):
                    txt = val.strftime("%Y-%m-%d %H:%M")
                else:
                    txt = str(val) if val is not None else "-"
                fila_p.append(Paragraph(txt, estilo_celda))
            datos_tabla.append(fila_p)

        # Fila de Totales (si aplica)
        tiene_totales = False
        if totales:
            tiene_totales = True
            fila_totales = [Paragraph("<b>TOTALES</b>", estilo_celda)]
            for col in columnas[1:]:
                if col in totales:
                    v = totales[col]
                    txt = f"<b>{v:,.2f}</b>" if isinstance(v, float) else f"<b>{v}</b>"
                else:
                    txt = ""
                fila_totales.append(Paragraph(txt, estilo_celda))
            datos_tabla.append(fila_totales)

        # Estilo de la Tabla
        estilo_t = [
            ("BACKGROUND", (0, 0), (-1, 0), cls.COLOR_OBSIDIAN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, cls.COLOR_BORDE),
            ("BOX", (0, 0), (-1, -1), 0.8, cls.COLOR_OBSIDIAN),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]

        # Filas alternadas (Zebra)
        total_filas_datos = len(filas)
        for i in range(1, total_filas_datos + 1):
            if i % 2 == 0:
                estilo_t.append(("BACKGROUND", (0, i), (-1, i), cls.COLOR_FONDO_CLARO))

        # Fila de totales
        if tiene_totales:
            idx_tot = len(datos_tabla) - 1
            estilo_t.append(("BACKGROUND", (0, idx_tot), (-1, idx_tot), colors.HexColor("#EAE7E1")))
            estilo_t.append(("LINEABOVE", (0, idx_tot), (-1, idx_tot), 1.2, cls.COLOR_OBSIDIAN))
            estilo_t.append(("LINEBELOW", (0, idx_tot), (-1, idx_tot), 1.5, cls.COLOR_OBSIDIAN))

        tabla = Table(datos_tabla, repeatRows=1)
        tabla.setStyle(TableStyle(estilo_t))
        elementos.append(tabla)

        # Compilar documento
        doc.build(elementos, canvasmaker=CanvasNumerado)
        buffer.seek(0)
        return buffer.getvalue()
