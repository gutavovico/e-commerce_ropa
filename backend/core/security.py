"""Utilidades de seguridad: hash de contrasenas (argon2) y JWT (PyJWT).

Esqueleto funcional sin logica de login ni roles.
Las dependencias de auth (get_current_user, require_roles) se implementan
con CU01-CU04 en core/deps.py.
"""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from core.config import settings
from core.errors import AuthenticationError

_ph = PasswordHasher()

_JWT_ALGORITHM = "HS256"


# --- Hash de contrasenas ---


def hash_password(plain: str) -> str:
    """Genera un hash argon2 de la contrasena en texto plano."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contrasena contra su hash argon2.

    Retorna False si no coincide (no lanza excepcion).
    """
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


# --- JSON Web Tokens ---


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un JWT firmado con HS256.

    Args:
        data: payload del token (tipicamente {"sub": user_id}).
        expires_delta: duracion del token. Si es None, usa JWT_EXPIRE_MINUTES de settings.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT.

    Raises:
        AuthenticationError: si el token es invalido, expirado o mal firmado.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Token invalido o expirado") from exc
