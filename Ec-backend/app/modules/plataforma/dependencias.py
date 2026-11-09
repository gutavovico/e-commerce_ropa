"""Dependencias de autorización y contexto para el panel del Super Administrador SaaS (P2-CU05 a P2-CU08).

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` (decisiones S2 y S3).
"""

import hashlib

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from core.errors import AuthorizationError
from core.tenant import fijar_contexto
from modules.autenticacion_seguridad.modelos import UsuarioORM

# Digests SHA-256 irreversibles de contraseñas y hashes Argon2 expuestos en historial previo.
# Prohibidos permanentemente tanto al aprovisionar/rotar cuentas como al autenticar en plataforma.
CONTRASENAS_SUPERADMIN_BLOQUEADAS_SHA256: frozenset[str] = frozenset(
    {
        "4a7372bd055b0d93fbd42915bd03a7d6a58c81f9e0be5ac9fe8f57c2b5c359b5",
    }
)

HASHES_SUPERADMIN_REVOCADOS_SHA256: frozenset[str] = frozenset(
    {
        "a64ab3309bfd41cb1b4505ff5d6dad17e3cea4162da8becbb33f4a5f94dc9e47",
    }
)


def validar_contrasena_superadmin_segura(password: str) -> None:
    """Valida que la contraseña de un `super_administrador` sea robusta y nunca haya sido expuesta.

    Raises:
        ValueError: si la contraseña está en la lista de revocación por exposición en Git
            o no cumple los requisitos mínimos de seguridad (12+ caracteres, mayúscula,
            minúscula, dígito y símbolo).
    """
    limpia = (password or "").strip()
    digest = hashlib.sha256(limpia.encode("utf-8")).hexdigest()
    if digest in CONTRASENAS_SUPERADMIN_BLOQUEADAS_SHA256:
        raise ValueError(
            "La contraseña indicada fue expuesta previamente en el historial de Git "
            "y está bloqueada permanentemente. Elija una contraseña nueva y privada."
        )
    if len(limpia) < 12:
        raise ValueError("La contraseña del super administrador debe tener al menos 12 caracteres.")
    tiene_mayus = any(c.isupper() for c in limpia)
    tiene_minus = any(c.islower() for c in limpia)
    tiene_digito = any(c.isdigit() for c in limpia)
    tiene_simbolo = any(not c.isalnum() for c in limpia)
    if not (tiene_mayus and tiene_minus and tiene_digito and tiene_simbolo):
        raise ValueError(
            "La contraseña del super administrador debe incluir mayúsculas, minúsculas, números y símbolos."
        )


def exigir_super_administrador(
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsuarioORM:
    """Verifica que el usuario autenticado tenga el rol `super_administrador` y activa `modo_plataforma`.

    Raises:
        AuthorizationError: HTTP 403 `ACCESO_DENEGADO` si el rol no es `super_administrador`
            o `CREDENCIAL_REVOCADA` si la cuenta conserva un hash revocado.
    """
    rol = str(getattr(usuario, "rol", "") or "").strip()
    if rol != "super_administrador":
        raise AuthorizationError(
            "Acceso restringido al Super Administrador de la plataforma.",
            code="ACCESO_DENEGADO",
        )
    password_hash = str(getattr(usuario, "password_hash", "") or "").strip()
    if password_hash:
        hash_digest = hashlib.sha256(password_hash.encode("utf-8")).hexdigest()
        if hash_digest in HASHES_SUPERADMIN_REVOCADOS_SHA256:
            raise AuthorizationError(
                "La credencial del Super Administrador pertenece a una semilla revocada. "
                "Debe rotarse fuera de banda con scripts/crear_superadmin.py.",
                code="CREDENCIAL_REVOCADA",
            )
    fijar_contexto(db, None, id_usuario=usuario.id_usuario, plataforma=True)
    return usuario
