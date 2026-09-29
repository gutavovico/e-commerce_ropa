"""Utilidades compartidas entre los casos de uso del paquete `reservas`."""

from datetime import datetime


def formatear_codigo_reserva(id_reserva: int, creado_en: datetime) -> str:
    """Código legible de una reserva: `RES-{año}-{id con 4 dígitos}`.

    Único punto de esta regla: antes vivía duplicada dentro de
    `cu12_reservar_prendas.servicio.ReservaServicio.crear_reserva_presencial`.
    """
    return f"RES-{creado_en.year}-{id_reserva:04d}"
