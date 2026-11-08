"""Servicio de dominio transaccional para CU02: Iniciar Sesion (Login)."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.errors import AuthenticationError, AuthorizationError
from core.security import create_access_token, verify_password
from core.tenant import buscar_tenant, contexto, exigir_activa, fijar_contexto, tenant_actual
from modules.autenticacion_seguridad.cu02_iniciar_sesion.esquemas import (
    LoginIn,
    LoginOut,
    TenantSesionOut,
)
from modules.plataforma.servicio_tenants import TenantServicio
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class ServicioAutenticarLogin:
    """Gestiona la logica de autenticacion, validacion criptografica y emision de JWT."""

    def autenticar_usuario(
        self,
        db: Session,
        datos: LoginIn,
        direccion_ip: Optional[str] = None,
    ) -> LoginOut:
        """Autentica las credenciales de un usuario y emite un token de acceso JWT.

        Args:
            db: Sesion activa de base de datos SQLAlchemy.
            datos: Credenciales proporcionadas por el usuario (email, password, recordar_dispositivo).
            direccion_ip: Direccion IP del cliente para bitacora de seguridad.

        Returns:
            LoginOut con el token de acceso JWT y los datos esenciales del usuario.

        Raises:
            AuthenticationError: Si el correo no existe o la contrasena no coincide (HTTP 401).
            AuthorizationError: Si la cuenta del usuario se encuentra inactiva/suspendida (HTTP 403).
        """
        # 1. Normalizar correo y buscar usuario (P2-CU13, F7 y F8)
        email_normalizado = str(datos.email).strip().lower()
        usuario = self._buscar_usuario(db, email_normalizado, datos.codigo_empresa)

        # 2. Verificacion contra ataques de enumeracion (mismo mensaje y codigo)
        if usuario is None:
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=None,
                usuario_nombre=email_normalizado,
                accion="LOGIN_FALLIDO",
                tabla_modulo="autenticacion",
                direccion_ip=direccion_ip,
                severidad="WARN",
                payload_anterior=None,
                payload_nuevo={"email": email_normalizado, "motivo": "Usuario inexistente"},
                db=db,
            )
            raise AuthenticationError(
                message="Credenciales incorrectas",
                code="CREDENCIALES_INVALIDAS",
            )

        # 3. Verificacion criptografica con Argon2id
        if not verify_password(datos.password, usuario.password_hash):
            nombre_desc = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=usuario.id_usuario,
                usuario_nombre=nombre_desc,
                accion="LOGIN_FALLIDO",
                tabla_modulo="autenticacion",
                direccion_ip=direccion_ip,
                severidad="WARN",
                payload_anterior=None,
                payload_nuevo={"email": email_normalizado, "motivo": "Password incorrecto"},
                db=db,
            )
            raise AuthenticationError(
                message="Credenciales incorrectas",
                code="CREDENCIALES_INVALIDAS",
            )

        # 4. Verificacion de estado activo de la cuenta
        if not usuario.activo:
            nombre_desc = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=usuario.id_usuario,
                usuario_nombre=nombre_desc,
                accion="LOGIN_FALLIDO",
                tabla_modulo="autenticacion",
                direccion_ip=direccion_ip,
                severidad="WARN",
                payload_anterior=None,
                payload_nuevo={"email": email_normalizado, "motivo": "Cuenta inactiva"},
                db=db,
            )
            raise AuthorizationError(
                message="La cuenta se encuentra inactiva o suspendida.",
                code="CUENTA_INACTIVA",
            )

        # 5. Actualizar fecha de ultimo acceso de forma atomica
        usuario.ultimo_acceso = datetime.now(timezone.utc)
        db.commit()
        db.refresh(usuario)

        # 6. Calcular expiracion y emitir token JWT con la empresa de la sesión (P2-CU13)
        id_tenant = TenantServicio.empresa_del_token(db, usuario)
        TenantServicio.exigir_empresa_activa(db, id_tenant)
        expires_delta = timedelta(days=7) if datos.recordar_dispositivo else None
        payload_token = {
            "sub": str(usuario.id_usuario),
            "email": usuario.email,
            "rol": str(usuario.rol),
            "id_tenant": id_tenant,
        }
        access_token = create_access_token(data=payload_token, expires_delta=expires_delta)

        # 6.5 Registrar evento exitoso en bitacora de auditoria
        nombre_desc = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_desc,
            accion="LOGIN_EXITOSO",
            tabla_modulo="autenticacion",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_anterior=None,
            payload_nuevo={"email": usuario.email, "rol": str(usuario.rol)},
            db=db,
        )

        # 7. Construir respuesta estandarizada
        return LoginOut(
            access_token=access_token,
            token_type="bearer",
            id_usuario=usuario.id_usuario,
            email=usuario.email,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            rol=str(usuario.rol),
            tenant=self._tenant_out(db, id_tenant),
        )

    @staticmethod
    def _buscar_usuario(db: Session, email: str, codigo_empresa: Optional[str]) -> Optional[UsuarioORM]:
        """Empleado de la empresa indicada o, sin código, cliente/super administrador (cuenta global)
        y, en el modo de transición, empleado de la empresa por defecto (spec §1.3)."""
        if codigo_empresa:
            tenant = buscar_tenant(db, codigo_empresa) if contexto(db) is not None else None
            if contexto(db) is not None:
                if tenant is None:
                    return None  # mismo error genérico que unas credenciales incorrectas
                exigir_activa(tenant)
                fijar_contexto(db, tenant.id_tenant)
            stmt = select(UsuarioORM).where(
                UsuarioORM.email == email, UsuarioORM.id_tenant == tenant_actual(db)
            ) if contexto(db) is not None else select(UsuarioORM).where(UsuarioORM.email == email)
            return db.scalars(stmt).first()

        global_ = db.scalars(
            select(UsuarioORM).where(UsuarioORM.email == email, UsuarioORM.id_tenant.is_(None))
        ).first()
        if global_ is not None or contexto(db) is None:
            return global_
        actual = tenant_actual(db)
        if actual is None:
            return None
        return db.scalars(
            select(UsuarioORM).where(UsuarioORM.email == email, UsuarioORM.id_tenant == actual)
        ).first()

    @staticmethod
    def _tenant_out(db: Session, id_tenant: Optional[int]) -> Optional[TenantSesionOut]:
        tenant = TenantServicio.datos_publicos(db, id_tenant)
        return TenantSesionOut(codigo=tenant.codigo, nombre=tenant.nombre) if tenant else None
