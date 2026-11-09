"""Monedas de la empresa e IVA — fix de P2-CU11 (decisiones M1, M8 y M9).

Spec: `.specs/finalized/P2-CU11-fix-moneda-zona-bolivia/spec.md` §1.

- Monedas admitidas: boliviano (BOB) y dólar (USD); CHECK `chk_config_moneda` en la base.
- Formato boliviano: `Bs 1.234,50` y `US$ 1.234,50`.
- IVA de Bolivia (13 %), incluido en el precio; solo se desglosa para mostrarlo.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

Moneda = Literal["BOB", "USD"]
MONEDAS: tuple[str, ...] = ("BOB", "USD")
MONEDA_POR_DEFECTO = "BOB"
SIMBOLOS = {"BOB": "Bs", "USD": "US$"}

#: M9: IVA de Bolivia, contenido en el precio.
TASA_IVA = Decimal("0.13")


def formatear_importe(valor: Decimal | int | float | str, moneda: str = MONEDA_POR_DEFECTO) -> str:
    """`Bs 1.234,50` / `US$ 1.234,50` (dos decimales, separadores de Bolivia)."""
    importe = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    texto = f"{importe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{SIMBOLOS.get(moneda, moneda)} {texto}"
