"""Hora de la empresa — fix de P2-CU11 (decisiones M4 y M5).

Spec: `.specs/finalized/P2-CU11-fix-moneda-zona-bolivia/spec.md` §1.

Todas las empresas operan en `America/La_Paz` (CHECK `chk_config_zona`), así que «hoy» y el inicio
del día se calculan con esa zona, no con la del servidor (Render corre en UTC). Los instantes se
guardan igual que antes, en `TIMESTAMPTZ`. PostgreSQL usa la misma zona en cada transacción
(`core.tenant`), de modo que `current_date` y `date_trunc` coinciden con estas funciones.

Si algún día se admite otra zona, hay que leerla de la configuración de la empresa en lugar de usar
esta constante.
"""

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

ZONA_EMPRESA = "America/La_Paz"
_ZONA = ZoneInfo(ZONA_EMPRESA)


def ahora() -> datetime:
    """Instante actual, con zona UTC (para guardar y comparar con columnas `TIMESTAMPTZ`)."""
    return datetime.now(timezone.utc)


def ahora_local() -> datetime:
    """Instante actual en la hora de Bolivia (para mostrar o nombrar archivos)."""
    return datetime.now(_ZONA)


def hoy() -> date:
    """Fecha de hoy en Bolivia."""
    return ahora_local().date()


def inicio_del_dia(dia: date | None = None) -> datetime:
    """Medianoche de Bolivia del día indicado (hoy por defecto), con zona."""
    return datetime.combine(dia or hoy(), time.min, tzinfo=_ZONA)
