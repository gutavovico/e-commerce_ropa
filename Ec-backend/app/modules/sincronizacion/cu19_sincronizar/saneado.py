"""Saneado de `operaciones_sync.datos` (RN43, AC-19.12).

Lista blanca por tipo de operación: lo que no está aquí no se guarda. Así nunca llegan a la base
un token, una contraseña, un `client_secret` ni datos de tarjeta, aunque la app los enviara.
"""

from typing import Any

_ITEM_RESERVA = ("id_variante", "cantidad")
_CAMPOS = {
    "reserva": ("fecha_hora_atencion", "observacion"),
    "compra_interrumpida": ("id_venta", "id_pago"),
}
MAX_OBSERVACION = 500


def sanear(tipo: str, datos: Any) -> dict[str, Any]:
    if not isinstance(datos, dict):
        return {}
    limpio: dict[str, Any] = {}
    for campo in _CAMPOS.get(tipo, ()):
        if campo in datos and isinstance(datos[campo], (str, int, float)) and not isinstance(datos[campo], bool):
            valor = datos[campo]
            limpio[campo] = valor[:MAX_OBSERVACION] if isinstance(valor, str) else valor
    if tipo == "reserva" and isinstance(datos.get("items"), list):
        limpio["items"] = [
            {k: item[k] for k in _ITEM_RESERVA if isinstance(item.get(k), int)}
            for item in datos["items"][:20]
            if isinstance(item, dict)
        ]
    return limpio
