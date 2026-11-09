"""Comprobante de venta presencial en PDF (CU32, D8 ampliada).

Ticket de 80 mm de ancho y alto ajustado al contenido, generado en memoria con `reportlab` (ya en
`requirements.txt`). Recibe la misma `VentaPosOut` que pinta la web: el PDF y el ticket impreso no
pueden contar cosas distintas.
"""

import io
from decimal import Decimal
from typing import List, Tuple

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from core.moneda import formatear_importe
from modules.compras_pagos.cu31_cu32_punto_venta.esquemas import VentaPosOut

ANCHO = 80 * mm
MARGEN = 5 * mm
INTERLINEA = 4.2 * mm

METODOS = {
    "efectivo": "Efectivo",
    "tarjeta_debito": "Tarjeta de débito",
    "tarjeta_credito": "Tarjeta de crédito",
    "qr": "QR",
    "transferencia": "Transferencia",
}


def _recortar(texto: str, maximo: int) -> str:
    return texto if len(texto) <= maximo else texto[: maximo - 1] + "…"


def _renglones(venta: VentaPosOut, moneda: str) -> List[Tuple[str, str, str]]:
    """(estilo, izquierda, derecha). Estilos: titulo, centro, texto, negrita, linea, espacio.
    Importes en la moneda de la empresa (fix de P2-CU11, M8)."""

    def _importe(valor: Decimal) -> str:
        return formatear_importe(valor, moneda)

    filas: List[Tuple[str, str, str]] = [
        ("titulo", "FASHION STORE", ""),
        ("centro", venta.nombre_sucursal, ""),
    ]
    if venta.direccion_sucursal:
        filas.append(("centro", _recortar(venta.direccion_sucursal, 46), ""))
    filas += [
        ("linea", "", ""),
        ("negrita", "Comprobante", venta.numero_comprobante),
        ("texto", "Fecha", venta.fecha_venta.strftime("%d/%m/%Y %H:%M")),
    ]
    if venta.cajero_nombre:
        filas.append(("texto", "Cajero", _recortar(venta.cajero_nombre, 30)))
    cliente = f"{venta.cliente.nombres} {venta.cliente.apellidos}".strip() if venta.cliente else "Sin registro"
    filas.append(("texto", "Cliente", _recortar(cliente, 30)))
    if venta.reserva_codigo:
        filas.append(("texto", "Reserva", venta.reserva_codigo))
    if venta.estado == "anulada":
        filas += [("espacio", "", ""), ("titulo", "*** ANULADA ***", "")]
    filas.append(("linea", "", ""))

    for linea in venta.lineas:
        filas.append(("negrita", _recortar(linea.nombre_producto, 44), ""))
        filas.append((
            "texto",
            f"  {linea.talla_codigo} · {_recortar(linea.color_nombre, 14)} · {linea.cantidad} x {_importe(linea.precio_unitario)}",
            _importe(linea.subtotal_linea),
        ))

    filas += [
        ("linea", "", ""),
        ("texto", "Subtotal", _importe(venta.subtotal)),
        ("texto", "Descuento", f"-{_importe(venta.descuento)}"),
    ]
    if venta.cupon_aplicado:
        filas.append(("texto", "Cupón", venta.cupon_aplicado))
    filas += [
        ("negrita", "TOTAL", _importe(venta.total)),
        ("texto", "IVA (13 %) incluido", _importe(venta.iva_incluido)),
    ]

    confirmados = [p for p in venta.pagos if p.estado == "confirmado"]
    if confirmados:
        pago = confirmados[-1]
        filas += [("linea", "", ""), ("texto", "Pago", METODOS.get(pago.metodo_pago, pago.metodo_pago))]
        if pago.monto_recibido is not None:
            filas.append(("texto", "Recibido", _importe(pago.monto_recibido)))
            filas.append(("texto", "Cambio", _importe(pago.cambio or Decimal("0"))))
        if pago.referencia:
            filas.append(("texto", "Referencia", _recortar(pago.referencia, 28)))

    filas += [("linea", "", ""), ("centro", "Gracias por su visita", ""), ("centro", "Comprobante no fiscal", "")]
    return filas


def generar_comprobante_pdf(venta: VentaPosOut, moneda: str = "BOB") -> bytes:
    filas = _renglones(venta, moneda)
    alto = 2 * MARGEN + len(filas) * INTERLINEA + 6 * mm
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(ANCHO, alto))
    pdf.setTitle(f"Comprobante {venta.numero_comprobante}")
    pdf.setAuthor("FASHION STORE")

    y = alto - MARGEN - INTERLINEA
    for estilo, izquierda, derecha in filas:
        if estilo == "linea":
            pdf.setDash(1, 2)
            pdf.line(MARGEN, y + 1.5 * mm, ANCHO - MARGEN, y + 1.5 * mm)
            pdf.setDash()
        elif estilo == "titulo":
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawCentredString(ANCHO / 2, y, izquierda)
        elif estilo == "centro":
            pdf.setFont("Helvetica", 7.5)
            pdf.drawCentredString(ANCHO / 2, y, izquierda)
        elif estilo in ("texto", "negrita"):
            pdf.setFont("Helvetica-Bold" if estilo == "negrita" else "Helvetica", 7.5)
            pdf.drawString(MARGEN, y, izquierda)
            if derecha:
                pdf.drawRightString(ANCHO - MARGEN, y, derecha)
        y -= INTERLINEA

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
