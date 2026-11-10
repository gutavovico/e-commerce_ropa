"""Apoyo común del paquete de operación sin conexión."""

from typing import Any, Optional

from modules.plataforma.servicio_tenants import TenantServicio


def nombre_usuario(usuario: Any) -> str:
    nombre = f"{getattr(usuario, 'nombres', '') or ''} {getattr(usuario, 'apellidos', '') or ''}".strip()
    return nombre or getattr(usuario, "email", "") or "Usuario"


def exigir_cliente(db: Any, usuario: Any) -> int:
    """El cliente debe estar registrado en la empresa del portal (403 `CLIENTE_NO_REGISTRADO`).
    Devuelve su `id_cliente` (= `id_usuario`)."""
    TenantServicio.exigir_cliente_en_tenant(db, usuario)
    return usuario.id_usuario


def texto(valor: Optional[Any]) -> Optional[str]:
    return None if valor is None else str(valor)
