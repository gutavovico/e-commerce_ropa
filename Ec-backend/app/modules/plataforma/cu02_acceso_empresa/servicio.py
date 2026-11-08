"""Servicio de P2-CU02 · Acceso por empresa.

Spec: `.specs/changes/P2-CU02-CU01-acceso-por-empresa/spec.md` §A.2 (decisiones A4, A8, A12 y A15).
"""

from typing import Any, List

from sqlalchemy.orm import Session

from core.errors import AuthorizationError, NotFoundError
from core.tenant import CLAVE_TENANT_CABECERA, buscar_tenant, contexto, empresas_disponibles
from modules.plataforma.cu02_acceso_empresa.esquemas import EmpresaOut, RegistroEnTiendaOut
from modules.plataforma.servicio_tenants import TenantServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


def _out(tenant: Any) -> EmpresaOut:
    return EmpresaOut(codigo=tenant.codigo, nombre=tenant.nombre)


class AccesoEmpresaServicio:
    @staticmethod
    def directorio(db: Session) -> List[EmpresaOut]:
        """A4: empresas activas con suscripción vigente."""
        return [_out(t) for t in empresas_disponibles(db)]

    @staticmethod
    def portal(db: Session, codigo: str) -> EmpresaOut:
        """Datos del portal `/{codigo}`. 404 si no existe; 403 si no está disponible."""
        tenant = buscar_tenant(db, codigo)
        if tenant is None:
            raise NotFoundError(f"No existe la tienda «{codigo}».", code="TENANT_NO_ENCONTRADO")
        disponible = TenantServicio.empresa_disponible(db, tenant.codigo)
        if disponible is None:
            raise AuthorizationError("Esta tienda no está disponible en este momento.", code="TENANT_INACTIVO")
        return _out(disponible)

    @staticmethod
    def mis_empresas(db: Session, usuario: Any) -> List[EmpresaOut]:
        if str(usuario.rol) != "cliente":
            raise AuthorizationError("Solo los clientes tienen tiendas registradas.", code="SOLO_CLIENTES")
        return [_out(t) for t in TenantServicio.empresas_del_cliente(db, usuario)]

    @staticmethod
    def registrarse_en_tienda(db: Session, usuario: Any, direccion_ip: str | None = None) -> RegistroEnTiendaOut:
        """A8: el cliente se registra en la empresa del portal sin crear otra cuenta (CU01 A1)."""
        registrado_ahora = TenantServicio.registrar_en_tienda(db, usuario)
        info = contexto(db)
        id_tenant = info.get(CLAVE_TENANT_CABECERA) if info else None
        tenant = TenantServicio.datos_publicos(db, id_tenant)
        if registrado_ahora:
            db.commit()
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=usuario.id_usuario,
                usuario_nombre=f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email,
                accion="REGISTRO_EN_TIENDA",
                tabla_modulo="cliente_tenant",
                direccion_ip=direccion_ip,
                severidad="INFO",
                payload_nuevo={"tienda": tenant.codigo if tenant else None},
                db=db,
            )
        return RegistroEnTiendaOut(
            empresa=_out(tenant) if tenant else EmpresaOut(codigo="", nombre=""),
            registrado_ahora=registrado_ahora,
        )
