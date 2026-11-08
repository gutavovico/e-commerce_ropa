"""Correo único en toda la plataforma (P2-CU02, RN05 y decisión A2).

Lo usan el registro de clientes (CU01) y la gestión de usuarios (CU20). Con una sesión real se consulta
`fashionstore.cuenta_por_email`, que ve las cuentas de todas las empresas (la RLS de `usuarios` oculta
a los empleados de las demás). Las sesiones simuladas de los tests unitarios usan la consulta ORM.
"""

from typing import Any, Optional

from sqlalchemy import func, select

from core.tenant import contexto, localizar_cuenta
from modules.autenticacion_seguridad.modelos import UsuarioORM


def correo_ocupado(db: Any, email: str, excluir_id: Optional[int] = None) -> bool:
    """True si otra cuenta (de cualquier rol y empresa) ya usa ese correo."""
    email_norm = email.strip().lower()
    if contexto(db) is not None:
        cuenta = localizar_cuenta(db, email_norm)
        return cuenta is not None and cuenta.id_usuario != excluir_id
    stmt = select(UsuarioORM).where(func.lower(UsuarioORM.email) == email_norm)
    if excluir_id is not None:
        stmt = stmt.where(UsuarioORM.id_usuario != excluir_id)
    return db.scalars(stmt).first() is not None
