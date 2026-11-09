"""Operaciones de empresa (tenant) que usan otros paquetes — P2-CU13.

Punto único de acceso al modelo multitenant desde autenticación (CU01, CU02) y usuarios (CU20):
la regla de arquitectura exige pasar por el servicio del otro paquete, nunca por sus modelos.
"""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.errors import AuthorizationError, DomainError
from core.tenant import (
    CLAVE_TENANT_CABECERA,
    TenantInfo,
    buscar_tenant_por_id,
    contexto,
    empresas_disponibles,
    exigir_activa,
    tenant_actual,
)
from modules.plataforma.modelos import ClienteTenantORM

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
        """Empresa que viaja en el JWT (F4): la del empleado. Los clientes navegan en la empresa de
        la cabecera `X-Tenant` y el super administrador no tiene empresa (P2-CU02 A10)."""
        if not es_rol_sin_empresa(usuario.rol):
            return getattr(usuario, "id_tenant", None)
        return None

    @staticmethod
    def empresas_del_cliente(db: Any, usuario: Any) -> list[TenantInfo]:
        """Tiendas disponibles en las que el cliente está registrado (P2-CU02 A15). Vacía si no es cliente.

        La política de `cliente_tenant` deja ver al cliente todos sus registros (`app.id_usuario`).
        """
        if str(usuario.rol) != "cliente" or contexto(db) is None:
            return []
        registradas = set(db.execute(
            select(ClienteTenantORM.id_tenant).where(
                ClienteTenantORM.id_cliente == usuario.id_usuario,
                ClienteTenantORM.activo.is_(True),
            )
        ).scalars().all())
        return [t for t in empresas_disponibles(db) if t.id_tenant in registradas]

    @staticmethod
    def empresa_del_portal(db: Any) -> Optional[int]:
        """Empresa pedida con la cabecera `X-Tenant` (portal web o tienda elegida en el móvil).

        Si la hay, debe estar disponible: activa y con suscripción vigente (CU01 A6) → si no, 403
        TENANT_INACTIVO. Devuelve None si la petición no indica empresa o la sesión es simulada.
        """
        info = contexto(db)
        if info is None:
            return None
        pedido = info.get(CLAVE_TENANT_CABECERA)
        if pedido is None:
            return None
        if not any(t.id_tenant == pedido for t in empresas_disponibles(db)):
            raise AuthorizationError("Esta tienda no está disponible en este momento.", code="TENANT_INACTIVO")
        return pedido

    @staticmethod
    def registrar_en_tienda(db: Session, usuario: Any) -> bool:
        """«Registrarme en esta tienda» (P2-CU02 A8): registra al cliente en la empresa del portal.

        Devuelve True si se registró y False si ya lo estaba. Idempotente.
        """
        if str(usuario.rol) != "cliente":
            raise AuthorizationError(
                "Solo los clientes se registran en una tienda; las cuentas de empleado pertenecen a su empresa.",
                code="SOLO_CLIENTES",
            )
        if contexto(db) is None:
            return False
        destino = TenantServicio.empresa_del_portal(db)
        if destino is None:
            raise DomainError("Indique la tienda en la que desea registrarse.", code="TENANT_REQUERIDO")
        existente = db.execute(
            select(ClienteTenantORM).where(
                ClienteTenantORM.id_tenant == destino,
                ClienteTenantORM.id_cliente == usuario.id_usuario,
            )
        ).scalar_one_or_none()
        if existente is not None:
            if not existente.activo:
                raise AuthorizationError(
                    "Tu registro en esta tienda está desactivado. Contacta con la tienda.",
                    code="CLIENTE_DESACTIVADO",
                )
            return False
        db.add(ClienteTenantORM(id_tenant=destino, id_cliente=usuario.id_usuario))
        db.flush()
        return True

    @staticmethod
    def empresa_disponible(db: Any, codigo: str) -> Optional[TenantInfo]:
        """Empresa activa y con suscripción vigente con ese código, o None (A12)."""
        codigo = codigo.strip().lower()
        return next((t for t in empresas_disponibles(db) if t.codigo == codigo), None)

    @staticmethod
    def datos_publicos(db: Any, id_tenant: Optional[int]) -> Optional[TenantInfo]:
        """Código, nombre y moneda de la empresa para la respuesta del login (solo con sesión real).

        La moneda la trae `empresas_disponibles` (fix de P2-CU11, M6); una empresa no disponible
        se devuelve con la moneda por defecto.
        """
        if id_tenant is None or contexto(db) is None:
            return None
        disponible = next((t for t in empresas_disponibles(db) if t.id_tenant == id_tenant), None)
        return disponible or buscar_tenant_por_id(db, id_tenant)

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
    def exigir_empresa_activa(db: Any, id_tenant: Optional[int]) -> None:
        tenant = TenantServicio.datos_publicos(db, id_tenant)
        if tenant is not None:
            exigir_activa(tenant)
