"""Dependencia de FastAPI para exigir una funcionalidad del plan en un endpoint (P2-CU12)."""

from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_optional_current_user
from modules.plataforma.cu12_validar_suscripcion.servicio import FUNCIONALIDADES, SuscripcionServicio


def requiere_funcionalidad(funcionalidad: str) -> Callable[..., None]:
    """Uso: `@router.post(..., dependencies=[Depends(requiere_funcionalidad("ventas"))])`.

    FastAPI resuelve las `dependencies` del decorador antes que los parámetros del endpoint, así que
    esta dependencia resuelve ella misma el token (`get_optional_current_user`): la validación usa la
    empresa del token y no la de la cabecera. La autenticación obligatoria sigue a cargo del endpoint.
    """
    if funcionalidad not in FUNCIONALIDADES:
        raise ValueError(f"Funcionalidad desconocida: {funcionalidad}")

    def _verificar(
        db: Session = Depends(get_db),
        usuario=Depends(get_optional_current_user),
    ) -> None:
        # Sin usuario no se valida aquí: el endpoint responde 401 con su propia autenticación
        # (comprobar el plan antes daría un 403 engañoso a quien solo olvidó iniciar sesión).
        if usuario is None:
            return
        SuscripcionServicio.validar(db, funcionalidad=funcionalidad)

    _verificar.__name__ = f"requiere_funcionalidad_{funcionalidad}"
    return _verificar
