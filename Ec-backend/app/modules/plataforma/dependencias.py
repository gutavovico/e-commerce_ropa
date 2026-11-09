"""Dependencias de autorización y contexto para el panel del Super Administrador SaaS (P2-CU05 a P2-CU08).

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` (decisión S3).
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from core.errors import AuthorizationError
from core.tenant import fijar_contexto
from modules.autenticacion_seguridad.modelos import UsuarioORM


def exigir_super_administrador(
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsuarioORM:
    """Verifica que el usuario autenticado tenga el rol `super_administrador` y activa `modo_plataforma`.

    Raises:
        AuthorizationError: HTTP 403 `ACCESO_DENEGADO` si el rol no es `super_administrador`.
    """
    rol = str(getattr(usuario, "rol", "") or "").strip()
    if rol != "super_administrador":
        raise AuthorizationError(
            "Acceso restringido al Super Administrador de la plataforma.",
            code="ACCESO_DENEGADO",
        )
    fijar_contexto(db, None, id_usuario=usuario.id_usuario, plataforma=True)
    return usuario

