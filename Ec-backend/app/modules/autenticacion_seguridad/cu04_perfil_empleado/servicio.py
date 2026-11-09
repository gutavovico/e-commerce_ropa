"""Servicio del perfil del empleado.

- La empresa sale de `TenantServicio.datos_publicos` (nombre y moneda de la cuenta del empleado).
- Las sucursales, de `SucursalesEmpleadoServicio` (RN07): el administrador opera en todas.
- Cambiar la contraseña exige la actual; nunca se registra en la bitácora.
"""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.errors import DomainError
from core.security import hash_password, verify_password
from core.tenant import contexto
from modules.autenticacion_seguridad.cu04_perfil_empleado.esquemas import (
    CambioContrasenaIn,
    EmpresaPerfilOut,
    PerfilEmpleadoActualizarIn,
    PerfilEmpleadoOut,
    SucursalPerfilOut,
)
from modules.gestion_operativa.modelos import SucursalORM
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio
from modules.plataforma.servicio_tenants import TenantServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


def _rol(usuario: Any) -> str:
    return str(getattr(usuario.rol, "value", usuario.rol))


def _registrar(db: Session, usuario: Any, accion: str, ip: Optional[str], **payloads) -> None:
    ServicioBitacoraAuditoria.registrar_evento_seguro(
        id_usuario=usuario.id_usuario,
        usuario_nombre=f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email,
        accion=accion,
        tabla_modulo="usuarios",
        direccion_ip=ip,
        severidad="INFO",
        db=db,
        **payloads,
    )


class PerfilEmpleadoServicio:
    @staticmethod
    def obtener(db: Session, usuario: Any) -> PerfilEmpleadoOut:
        tenant = TenantServicio.datos_publicos(db, usuario.id_tenant)
        empresa = (
            EmpresaPerfilOut(codigo=tenant.codigo, nombre=tenant.nombre, moneda=tenant.moneda) if tenant else None
        )

        todas = SucursalesEmpleadoServicio.autorizadas(usuario) is None
        sucursales: list[SucursalPerfilOut] = []
        if not todas:
            pares = SucursalesEmpleadoServicio.de_empleado(db, usuario.id_usuario)
            if not pares and usuario.id_sucursal:
                pares = [(usuario.id_sucursal, True)]
            if pares:
                nombres = {}
                if contexto(db) is not None:  # con una sesión simulada, sin nombres
                    nombres = dict(db.execute(
                        select(SucursalORM.id_sucursal, SucursalORM.nombre).where(
                            SucursalORM.id_sucursal.in_([p[0] for p in pares])
                        )
                    ).all())
                sucursales = [
                    SucursalPerfilOut(id_sucursal=id_suc, nombre=nombres.get(id_suc), es_principal=principal)
                    for id_suc, principal in pares
                ]

        return PerfilEmpleadoOut(
            id_usuario=usuario.id_usuario,
            email=usuario.email,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            telefono=usuario.telefono,
            rol=_rol(usuario),
            empresa=empresa,
            todas_las_sucursales=todas,
            sucursales=sucursales,
            ultimo_acceso=usuario.ultimo_acceso,
        )

    @staticmethod
    def actualizar(
        db: Session, usuario: Any, datos: PerfilEmpleadoActualizarIn, ip: Optional[str] = None
    ) -> PerfilEmpleadoOut:
        anterior, nuevo = {}, {}
        for campo in ("nombres", "apellidos", "telefono"):
            if campo not in datos.model_fields_set:
                continue
            valor = getattr(datos, campo)
            if campo != "telefono" and valor is None:
                continue
            if getattr(usuario, campo) != valor:
                anterior[campo], nuevo[campo] = getattr(usuario, campo), valor
                setattr(usuario, campo, valor)
        if nuevo:
            db.commit()
            db.refresh(usuario)
            _registrar(db, usuario, "PERFIL_EMPLEADO_MODIFICADO", ip, payload_anterior=anterior, payload_nuevo=nuevo)
        return PerfilEmpleadoServicio.obtener(db, usuario)

    @staticmethod
    def cambiar_contrasena(db: Session, usuario: Any, datos: CambioContrasenaIn, ip: Optional[str] = None) -> None:
        if not verify_password(datos.contrasena_actual, usuario.password_hash):
            raise DomainError("La contraseña actual no es correcta.", code="CONTRASENA_ACTUAL_INCORRECTA")
        if datos.contrasena_actual == datos.contrasena_nueva:
            raise DomainError("La contraseña nueva debe ser distinta de la actual.", code="CONTRASENA_REPETIDA")
        usuario.password_hash = hash_password(datos.contrasena_nueva)
        db.commit()
        _registrar(db, usuario, "CONTRASENA_CAMBIADA", ip, payload_nuevo={"id_usuario": usuario.id_usuario})
