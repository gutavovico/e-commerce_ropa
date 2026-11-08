"""Contexto de empresa (tenant) por petición y por transacción — P2-CU13.

Spec: `.specs/changes/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.4 (decisiones F2–F6).

Cómo llega la empresa a PostgreSQL:
1. `preparar_sesion()` (llamada desde `get_db`) resuelve la empresa de la petición: cabecera
   `X-Tenant: <codigo>` o, si no la hay, `TENANT_POR_DEFECTO` (modo de transición, §1.3).
2. `get_current_user()` la sustituye por la del token, que siempre manda (F4).
3. El contexto se guarda en `session.info` y un listener `after_begin` lo aplica con
   `set_config(..., true)` al comenzar **cada** transacción. Equivale a `SET LOCAL`: compatible con
   PgBouncer en modo transacción y sin fugas entre peticiones, aunque un servicio haga varios commits.

Sin empresa, la RLS no deja ver ni escribir nada (F5). Las sesiones simuladas de los tests
(`MagicMock`) no tienen un `info` de tipo `dict` y se ignoran.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.errors import AuthorizationError, NotFoundError

logger = logging.getLogger("fashionstore.tenant")

CABECERA_TENANT = "X-Tenant"

#: Claves de `session.info`.
CLAVE_TENANT = "id_tenant"
CLAVE_USUARIO = "id_usuario"
CLAVE_PLATAFORMA = "modo_plataforma"
#: Empresa pedida explícitamente con la cabecera (para detectar TENANT_NO_COINCIDE).
CLAVE_TENANT_CABECERA = "id_tenant_cabecera"
CLAVE_TENANT_INFO = "tenant"

_SQL_CONTEXTO = text(
    "SELECT set_config('app.id_tenant', :t, true), "
    "set_config('app.id_usuario', :u, true), "
    "set_config('app.modo_plataforma', :p, true)"
)


@dataclass(frozen=True)
class TenantInfo:
    id_tenant: int
    codigo: str
    nombre: str
    estado: str

    @property
    def activa(self) -> bool:
        return self.estado == "activa"


def _info(db: Any) -> Optional[dict]:
    """`session.info` si es una sesión real; None para dobles de prueba."""
    info = getattr(db, "info", None)
    return info if isinstance(info, dict) else None


def contexto(db: Any) -> Optional[dict]:
    """Contexto de empresa de la sesión, o None si es una sesión simulada."""
    return _info(db)


def tenant_actual(db: Any) -> Optional[int]:
    info = _info(db)
    return info.get(CLAVE_TENANT) if info else None


def _parametros(info: dict) -> dict:
    tenant = info.get(CLAVE_TENANT)
    usuario = info.get(CLAVE_USUARIO)
    return {
        "t": str(tenant) if tenant is not None else "",
        "u": str(usuario) if usuario is not None else "",
        "p": "on" if info.get(CLAVE_PLATAFORMA) else "",
    }


@event.listens_for(Session, "after_begin")
def _aplicar_contexto(session: Session, _transaction, connection) -> None:
    """Fija el contexto al inicio de cada transacción (también si está vacío: nunca se hereda)."""
    connection.execute(_SQL_CONTEXTO, _parametros(session.info))


def fijar_contexto(
    db: Any,
    id_tenant: Optional[int],
    *,
    id_usuario: Optional[int] = None,
    plataforma: bool = False,
) -> None:
    """Fija la empresa (y opcionalmente el usuario y el modo plataforma) de la sesión.

    Si la transacción ya está abierta, lo aplica también de inmediato.
    """
    info = _info(db)
    if info is None:
        return
    info[CLAVE_TENANT] = id_tenant
    info[CLAVE_USUARIO] = id_usuario
    info[CLAVE_PLATAFORMA] = plataforma
    if db.in_transaction():
        db.execute(_SQL_CONTEXTO, _parametros(info))


# -------------------------------------------------------------------------------------------
# Catálogo de empresas (tabla `tenants`, sin RLS) con caché corta en memoria
# -------------------------------------------------------------------------------------------

_TTL_SEGUNDOS = 60.0
_cache: dict[str, tuple[float, Optional[TenantInfo]]] = {}
_cache_lock = threading.Lock()


def limpiar_cache_tenants() -> None:
    with _cache_lock:
        _cache.clear()


def buscar_tenant(db: Session, codigo: str) -> Optional[TenantInfo]:
    """Empresa por su código (RN03), con caché de 60 s."""
    clave = codigo.strip().lower()
    ahora = time.monotonic()
    with _cache_lock:
        guardado = _cache.get(clave)
        if guardado and ahora - guardado[0] < _TTL_SEGUNDOS:
            return guardado[1]
    fila = db.execute(
        text("SELECT id_tenant, codigo, nombre, estado FROM fashionstore.tenants WHERE codigo = :c"),
        {"c": clave},
    ).first()
    tenant = TenantInfo(int(fila[0]), fila[1], fila[2], fila[3]) if fila else None
    with _cache_lock:
        _cache[clave] = (ahora, tenant)
    return tenant


def buscar_tenant_por_id(db: Session, id_tenant: int) -> Optional[TenantInfo]:
    fila = db.execute(
        text("SELECT id_tenant, codigo, nombre, estado FROM fashionstore.tenants WHERE id_tenant = :i"),
        {"i": id_tenant},
    ).first()
    return TenantInfo(int(fila[0]), fila[1], fila[2], fila[3]) if fila else None


def exigir_activa(tenant: TenantInfo) -> None:
    """RN08: una empresa suspendida o dada de baja no opera."""
    if not tenant.activa:
        raise AuthorizationError(
            f"La empresa «{tenant.nombre}» no está activa.", code="TENANT_INACTIVO"
        )


def preparar_sesion(db: Session, codigo_cabecera: Optional[str], codigo_por_defecto: str) -> None:
    """Resuelve la empresa de la petición antes de cualquier consulta (F4: cabecera → por defecto).

    - Cabecera con un código inexistente → 404 TENANT_NO_ENCONTRADO; empresa inactiva → 403.
    - Sin cabecera: empresa por defecto (transición). Si no existe o la tabla aún no está migrada,
      la sesión queda sin empresa y la RLS no deja ver nada.
    """
    info = _info(db)
    if info is None:
        return
    codigo = (codigo_cabecera or "").strip()
    if codigo:
        tenant = buscar_tenant(db, codigo)
        if tenant is None:
            raise NotFoundError(f"No existe la empresa «{codigo}».", code="TENANT_NO_ENCONTRADO")
        exigir_activa(tenant)
        info[CLAVE_TENANT_CABECERA] = tenant.id_tenant
    else:
        tenant = None
        if codigo_por_defecto:
            try:
                tenant = buscar_tenant(db, codigo_por_defecto)
            except SQLAlchemyError as exc:  # base sin migrar a 0012
                db.rollback()
                logger.warning("No se pudo resolver la empresa por defecto: %s", exc.__class__.__name__)
                tenant = None
        if tenant is not None and not tenant.activa:
            tenant = None
    info[CLAVE_TENANT_INFO] = tenant
    fijar_contexto(db, tenant.id_tenant if tenant else None)


def aplicar_tenant_del_token(db: Any, id_tenant_token: Optional[int], id_usuario: int) -> None:
    """El token manda (F4). Si la cabecera pidió otra empresa → 403 TENANT_NO_COINCIDE."""
    info = _info(db)
    if info is None:
        return
    pedido = info.get(CLAVE_TENANT_CABECERA)
    if id_tenant_token is not None:
        if pedido is not None and pedido != id_tenant_token:
            raise AuthorizationError(
                "El token pertenece a otra empresa.", code="TENANT_NO_COINCIDE"
            )
        fijar_contexto(db, id_tenant_token, id_usuario=id_usuario)
    else:
        # Clientes sin empresa en el token y super administrador: conservan la de la petición.
        fijar_contexto(db, info.get(CLAVE_TENANT), id_usuario=id_usuario)
