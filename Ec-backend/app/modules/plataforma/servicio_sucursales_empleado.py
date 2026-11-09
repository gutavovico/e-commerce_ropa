"""Sucursales autorizadas de un empleado (RN07) — P2-CU03.

Spec: `.specs/finalized/P2-CU03-CU04-usuarios-sucursales/spec.md` §2 (B3, B4, B5).

- El **administrador** opera en todas las sucursales de su empresa: `autorizadas()` devuelve `None`.
- **Encargado y cajero** operan en las filas de `empleado_sucursal`; `usuarios.id_sucursal` es la
  principal y cuenta siempre como autorizada.
- Los servicios que aplican RN07 reciben solo el usuario autenticado: las sucursales se leen con la
  sesión a la que pertenece (`object_session`) y se guardan en el propio objeto durante la petición.
  Un usuario simulado de las pruebas unitarias (sin sesión) se limita a su `id_sucursal`.
"""

from typing import Any, Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import object_session
from sqlalchemy.orm.exc import UnmappedInstanceError

from core.tenant import contexto
from modules.plataforma.modelos import EmpleadoSucursalORM

#: Roles que operan en todas las sucursales de su empresa.
ROLES_TODAS_LAS_SUCURSALES = ("administrador", "admin")

_CACHE = "_sucursales_autorizadas"


def _rol(usuario: Any) -> str:
    rol = getattr(usuario, "rol", None)
    return str(getattr(rol, "value", rol) or "").lower().strip()


def _sesion_de(usuario: Any) -> Any:
    try:
        return object_session(usuario)
    except (UnmappedInstanceError, NoInspectionAvailable):
        return None


class SucursalesEmpleadoServicio:
    @staticmethod
    def autorizadas(usuario: Any) -> Optional[frozenset[int]]:
        """`None` = todas (administrador). Para el resto, el conjunto de sucursales autorizadas."""
        if _rol(usuario) in ROLES_TODAS_LAS_SUCURSALES:
            return None
        cache = getattr(usuario, "__dict__", {}).get(_CACHE)
        if cache is not None:
            return cache

        ids: set[int] = set()
        db = _sesion_de(usuario)
        if db is not None and contexto(db) is not None:
            ids.update(
                db.execute(
                    select(EmpleadoSucursalORM.id_sucursal).where(
                        EmpleadoSucursalORM.id_empleado == usuario.id_usuario
                    )
                ).scalars()
            )
        principal = getattr(usuario, "id_sucursal", None)
        if principal:
            ids.add(principal)

        resultado = frozenset(ids)
        if db is not None:
            usuario.__dict__[_CACHE] = resultado
        return resultado

    @staticmethod
    def autoriza(usuario: Any, id_sucursal: Optional[int]) -> bool:
        if id_sucursal is None:
            return False
        autorizadas = SucursalesEmpleadoServicio.autorizadas(usuario)
        return autorizadas is None or id_sucursal in autorizadas

    @staticmethod
    def empleados_de_sucursal(id_sucursal: int):
        """Subconsulta con los empleados autorizados en una sucursal (para filtros y conteos)."""
        return select(EmpleadoSucursalORM.id_empleado).where(EmpleadoSucursalORM.id_sucursal == id_sucursal)

    @staticmethod
    def de_empleado(db: Any, id_empleado: int) -> list[tuple[int, bool]]:
        """`[(id_sucursal, es_principal)]` de un empleado, la principal primero."""
        if contexto(db) is None:
            return []
        filas = db.execute(
            select(EmpleadoSucursalORM.id_sucursal, EmpleadoSucursalORM.es_principal)
            .where(EmpleadoSucursalORM.id_empleado == id_empleado)
            .order_by(EmpleadoSucursalORM.es_principal.desc(), EmpleadoSucursalORM.id_sucursal)
        ).all()
        return [(int(fila[0]), bool(fila[1])) for fila in filas]

    @staticmethod
    def reemplazar(db: Any, id_empleado: int, ids: Iterable[int], principal: Optional[int]) -> None:
        """Deja exactamente `ids` como sucursales autorizadas, con `principal` marcada.

        Se llama después de `asegurar_ficha_empleado` (la FK compuesta exige la fila de `empleados`).
        Con una lista vacía, el empleado se queda sin sucursales (administrador).
        """
        if contexto(db) is None:
            return
        deseadas = set(ids)
        db.execute(
            delete(EmpleadoSucursalORM).where(EmpleadoSucursalORM.id_empleado == id_empleado)
        )
        db.flush()
        for id_sucursal in sorted(deseadas):
            db.add(EmpleadoSucursalORM(
                id_empleado=id_empleado,
                id_sucursal=id_sucursal,
                es_principal=id_sucursal == principal,
            ))
        db.flush()
