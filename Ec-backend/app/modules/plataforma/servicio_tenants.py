"""Operaciones de empresa (tenant) que usan otros paquetes — P2-CU13.

Punto único de acceso al modelo multitenant desde autenticación (CU01, CU02) y usuarios (CU20):
la regla de arquitectura exige pasar por el servicio del otro paquete, nunca por sus modelos.
"""

from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from core.errors import AuthorizationError
from core.tenant import TenantInfo, buscar_tenant_por_id, contexto, exigir_activa, tenant_actual
from modules.plataforma.modelos import ClienteTenantORM, EmpleadoSucursalORM

#: Roles que no pertenecen a ninguna empresa (RN04, F1).
ROLES_SIN_EMPRESA = ("cliente", "super_administrador")


def es_rol_sin_empresa(rol: Any) -> bool:
    return str(getattr(rol, "value", rol)) in ROLES_SIN_EMPRESA


class TenantServicio:
    @staticmethod
    def empresa_para_rol(db: Any, rol: Any) -> Optional[int]:
        """`usuarios.id_tenant` que corresponde a un rol: la empresa de la sesión para los empleados,
        ninguna para clientes y super administradores (CHECK `chk_usuarios_tenant_segun_rol`)."""
        return None if es_rol_sin_empresa(rol) else tenant_actual(db)

    @staticmethod
    def cliente_registrado(db: Session, id_cliente: int, id_tenant: int) -> bool:
        if contexto(db) is None:
            return False
        stmt = select(ClienteTenantORM.id_cliente).where(
            ClienteTenantORM.id_tenant == id_tenant,
            ClienteTenantORM.id_cliente == id_cliente,
            ClienteTenantORM.activo.is_(True),
        )
        return db.execute(stmt).first() is not None

    @staticmethod
    def registrar_cliente(db: Any, id_cliente: int, id_tenant: Optional[int] = None) -> Optional[int]:
        """Registra al cliente en la empresa indicada o en la de la sesión (F9). Idempotente.

        Devuelve la empresa en la que quedó registrado, o None si la sesión no tiene empresa.
        """
        if contexto(db) is None:
            return None
        destino = id_tenant if id_tenant is not None else tenant_actual(db)
        if destino is None:
            return None
        if not TenantServicio.cliente_registrado(db, id_cliente, destino):
            db.add(ClienteTenantORM(id_tenant=destino, id_cliente=id_cliente))
            db.flush()
        return destino

    @staticmethod
    def empresa_del_token(db: Any, usuario: Any) -> Optional[int]:
        """Empresa que viaja en el JWT (F4): la del empleado; la de la sesión para un cliente
        registrado en ella; ninguna para el super administrador o un cliente no registrado."""
        if not es_rol_sin_empresa(usuario.rol):
            return getattr(usuario, "id_tenant", None)
        if str(usuario.rol) != "cliente":
            return None
        actual = tenant_actual(db)
        if actual is not None and TenantServicio.cliente_registrado(db, usuario.id_usuario, actual):
            return actual
        return None

    @staticmethod
    def datos_publicos(db: Any, id_tenant: Optional[int]) -> Optional[TenantInfo]:
        """Código y nombre de la empresa para la respuesta del login (solo con sesión real)."""
        if id_tenant is None or contexto(db) is None:
            return None
        return buscar_tenant_por_id(db, id_tenant)

    @staticmethod
    def exigir_cliente_en_tenant(db: Any, usuario: Any) -> None:
        """Antes de crear un carrito o una reserva (FK compuesta hacia `cliente_tenant`).

        - Cliente: debe estar registrado en la empresa de la sesión (decisión D-B); si no,
          403 CLIENTE_NO_REGISTRADO en lugar de un error de base de datos.
        - Empleado en su propia empresa: se registra su ficha de cliente, como funcionaba antes de
          la fundación multitenant (el personal podía comprar en su tienda).
        """
        if contexto(db) is None:
            return
        actual = tenant_actual(db)
        if actual is None:
            raise AuthorizationError("La operación requiere una empresa identificada.", code="TENANT_REQUERIDO")
        if TenantServicio.cliente_registrado(db, usuario.id_usuario, actual):
            return
        if not es_rol_sin_empresa(usuario.rol) and getattr(usuario, "id_tenant", None) == actual:
            TenantServicio.registrar_cliente(db, usuario.id_usuario, actual)
            return
        raise AuthorizationError(
            "Para comprar o reservar en esta tienda primero debes registrarte en ella.",
            code="CLIENTE_NO_REGISTRADO",
        )

    @staticmethod
    def sincronizar_sucursal_principal(db: Any, id_empleado: int, id_sucursal: Optional[int]) -> None:
        """F10: `usuarios.id_sucursal` sigue siendo la sucursal principal; `empleado_sucursal` la refleja.

        Se llama después de `asegurar_ficha_empleado` (la FK compuesta exige la fila de `empleados`).
        """
        if contexto(db) is None:
            return
        db.execute(
            update(EmpleadoSucursalORM)
            .where(EmpleadoSucursalORM.id_empleado == id_empleado, EmpleadoSucursalORM.es_principal.is_(True))
            .values(es_principal=False)
        )
        if id_sucursal is None:
            return
        existente = db.execute(
            select(EmpleadoSucursalORM).where(
                EmpleadoSucursalORM.id_empleado == id_empleado,
                EmpleadoSucursalORM.id_sucursal == id_sucursal,
            )
        ).scalar_one_or_none()
        if existente is not None:
            existente.es_principal = True
        else:
            db.add(EmpleadoSucursalORM(id_empleado=id_empleado, id_sucursal=id_sucursal, es_principal=True))
        db.flush()

    @staticmethod
    def exigir_empresa_activa(db: Any, id_tenant: Optional[int]) -> None:
        tenant = TenantServicio.datos_publicos(db, id_tenant)
        if tenant is not None:
            exigir_activa(tenant)
