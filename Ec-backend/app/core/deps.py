"""Dependencias de FastAPI para autenticacion y autorizacion (CU01-CU04).

Provee la extraccion segura de credenciales desde tokens Bearer JWT,
resolucion de identidad en la base de datos PostgreSQL, y validacion de roles.
"""

from collections.abc import Callable
from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.errors import AuthenticationError, AuthorizationError
from core.security import decode_access_token
from core.token_blacklist import token_blacklist
from modules.autenticacion_seguridad.modelos import UsuarioORM

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/autenticacion/login",
    auto_error=False,
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioORM:
    """Extrae y valida el usuario activo a partir del token Bearer JWT.

    Raises:
        AuthenticationError: si el token es ausente, invalido, expirado o revocado (HTTP 401).
        AuthorizationError: si la cuenta de usuario se encuentra inactiva (HTTP 403).
    """
    if not token:
        raise AuthenticationError("Token de acceso no proporcionado", code="TOKEN_INVALIDO")

    if token_blacklist.esta_revocado(token):
        raise AuthenticationError(
            "La sesión ha sido finalizada. Inicie sesión nuevamente.",
            code="TOKEN_REVOCADO",
        )

    try:
        payload = decode_access_token(token)
    except AuthenticationError:
        raise AuthenticationError("Token de acceso invalido o expirado", code="TOKEN_INVALIDO")

    sub = payload.get("sub")
    if not sub:
        raise AuthenticationError("Token sin identificador de usuario", code="TOKEN_INVALIDO")

    try:
        id_usuario = int(sub)
    except (ValueError, TypeError):
        raise AuthenticationError("Identificador de usuario invalido en token", code="TOKEN_INVALIDO")

    stmt = (
        select(UsuarioORM)
        .options(joinedload(UsuarioORM.cliente))
        .where(UsuarioORM.id_usuario == id_usuario)
    )
    usuario = db.execute(stmt).scalar_one_or_none()

    if not usuario:
        raise AuthenticationError("Usuario no encontrado en el sistema", code="USUARIO_NO_ENCONTRADO")

    if not usuario.activo:
        raise AuthorizationError("La cuenta se encuentra inactiva o suspendida", code="CUENTA_INACTIVA")

    return usuario


def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioORM | None:
    """Extrae el usuario autenticado si existe un token Bearer válido; de lo contrario retorna None.

    No lanza excepciones si no se provee token o si el token es inválido/expirado,
    permitiendo la navegación elegante a visitantes o clientes no autenticados.
    """
    if not token:
        return None

    if token_blacklist.esta_revocado(token):
        return None

    try:
        payload = decode_access_token(token)
    except Exception:
        return None

    sub = payload.get("sub")
    if not sub:
        return None

    try:
        id_usuario = int(sub)
    except (ValueError, TypeError):
        return None

    stmt = (
        select(UsuarioORM)
        .options(joinedload(UsuarioORM.cliente))
        .where(UsuarioORM.id_usuario == id_usuario)
    )
    usuario = db.execute(stmt).scalar_one_or_none()
    if not usuario or not usuario.activo:
        return None

    return usuario



def require_roles(roles_permitidos: list[str]) -> Callable[..., UsuarioORM]:
    """Fabrica de dependencias para verificar que el usuario posea uno de los roles permitidos."""

    def _role_checker(usuario: UsuarioORM = Depends(get_current_user)) -> UsuarioORM:
        if str(usuario.rol) not in roles_permitidos:
            raise AuthorizationError(
                f"Acceso restringido. Se requiere uno de los siguientes roles: {', '.join(roles_permitidos)}",
                code="ACCESO_DENEGADO",
            )
        return usuario

    return _role_checker

