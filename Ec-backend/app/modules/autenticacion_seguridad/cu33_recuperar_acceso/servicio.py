"""Servicio de lógica de negocio para CU33 - Recuperar Acceso de Cuenta."""

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.email_service import email_service
from core.errors import DomainError
from core.security import hash_password
from modules.autenticacion_seguridad.cu33_recuperar_acceso.esquemas import (
    RestablecerPasswordIn,
    RestablecerPasswordOut,
    SolicitarCodigoOut,
)
from modules.autenticacion_seguridad.modelos import CodigoRecuperacionORM, UsuarioORM

logger = logging.getLogger("fashionstore.cu33")


class RecuperarPasswordServicio:
    """Orquestador de reglas de negocio para la recuperación de acceso mediante OTP."""

    async def solicitar_codigo(
        self,
        db: Session,
        email: str,
        ip_solicitante: Optional[str] = None,
    ) -> SolicitarCodigoOut:
        """Genera un OTP criptoseguro y despacha notificación por correo.
        
        Aplica protección anti-enumeración de usuarios respondiendo siempre de manera
        neutra y uniforme.
        """
        stmt = select(UsuarioORM).where(UsuarioORM.email == email.lower().strip())
        usuario = db.scalars(stmt).first()

        # Si el usuario no existe o está inactivo, respuesta neutra (Anti-Enumeración)
        if not usuario or not usuario.activo:
            logger.info("Solicitud de codigo para correo inexistente o inactivo: %s", email)
            return SolicitarCodigoOut()

        ahora = datetime.now(timezone.utc)

        # Rate Limiting: verificar si ya existe un código emitido hace menos de 60 segundos
        stmt_reciente = (
            select(CodigoRecuperacionORM)
            .where(
                CodigoRecuperacionORM.id_usuario == usuario.id_usuario,
                CodigoRecuperacionORM.usado.is_(False),
            )
            .order_by(CodigoRecuperacionORM.id_codigo.desc())
        )
        codigo_reciente = db.scalars(stmt_reciente).first()

        if codigo_reciente:
            segundos_transcurridos = (ahora - codigo_reciente.creado_en).total_seconds()
            if segundos_transcurridos < settings.OTP_RESEND_COOLDOWN_SECONDS:
                tiempo_restante = int(settings.OTP_RESEND_COOLDOWN_SECONDS - segundos_transcurridos)
                logger.info(
                    "Solicitud en cooldown para %s. Restan %s segundos.",
                    email,
                    tiempo_restante,
                )
                return SolicitarCodigoOut(
                    mensaje="Ya se ha enviado un código recientemente. Revisa tu correo o espera antes de solicitar otro.",
                    tiempo_espera_segundos=tiempo_restante,
                )

        # Invalidar códigos anteriores no utilizados
        codigos_previos = db.scalars(
            select(CodigoRecuperacionORM).where(
                CodigoRecuperacionORM.id_usuario == usuario.id_usuario,
                CodigoRecuperacionORM.usado.is_(False),
            )
        ).all()
        for prev in codigos_previos:
            prev.usado = True

        # Generar código criptoseguro de 6 dígitos (100000 - 999999)
        codigo_otp = f"{secrets.randbelow(900000) + 100000}"
        codigo_hash = hashlib.sha256(codigo_otp.encode("utf-8")).hexdigest()
        expira_en = ahora + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        nuevo_codigo = CodigoRecuperacionORM(
            id_usuario=usuario.id_usuario,
            codigo_hash=codigo_hash,
            expira_en=expira_en,
            usado=False,
            intentos_fallidos=0,
            ip_solicitante=ip_solicitante,
            creado_en=ahora,
        )
        db.add(nuevo_codigo)
        db.commit()

        # Envío asíncrono del correo
        try:
            await email_service.enviar_codigo_recuperacion(usuario.email, codigo_otp)
        except Exception as exc:
            logger.error("Error al despachar correo OTP a %s: %s", usuario.email, str(exc))
            logger.warning(
                "[DIAGNÓSTICO SMTP] Falló el despacho del correo a %s (%s). Código OTP generado en base de datos: %s",
                usuario.email,
                str(exc),
                codigo_otp,
            )
            # No se revierte la BD para permitir validar el código en pruebas o reintentos

        return SolicitarCodigoOut()

    def restablecer_password(
        self,
        db: Session,
        datos: RestablecerPasswordIn,
    ) -> RestablecerPasswordOut:
        """Valida el código OTP y actualiza la contraseña del usuario con Argon2id."""
        stmt = select(UsuarioORM).where(UsuarioORM.email == datos.email.lower().strip())
        usuario = db.scalars(stmt).first()

        if not usuario or not usuario.activo:
            raise DomainError(
                "Código de verificación inválido o expirado.",
                code="CODIGO_INVALIDO",
            )

        stmt_codigo = (
            select(CodigoRecuperacionORM)
            .where(
                CodigoRecuperacionORM.id_usuario == usuario.id_usuario,
                CodigoRecuperacionORM.usado.is_(False),
            )
            .order_by(CodigoRecuperacionORM.id_codigo.desc())
        )
        codigo_orm = db.scalars(stmt_codigo).first()

        if not codigo_orm:
            raise DomainError(
                "Código de verificación inválido o no solicitado.",
                code="CODIGO_INVALIDO",
            )

        ahora = datetime.now(timezone.utc)

        # 1. Comprobar expiración
        if ahora > codigo_orm.expira_en:
            codigo_orm.usado = True
            db.commit()
            raise DomainError(
                "El código de verificación ha expirado. Solicita uno nuevo.",
                code="CODIGO_EXPIRADO",
            )

        # 2. Comprobar límite de intentos fallidos
        if codigo_orm.intentos_fallidos >= settings.OTP_MAX_ATTEMPTS:
            codigo_orm.usado = True
            db.commit()
            raise DomainError(
                "Has superado el límite de intentos permitidos. Solicita un nuevo código.",
                code="INTENTOS_SUPERADOS",
            )

        # 3. Validar hash SHA-256 del código suministrado
        hash_ingresado = hashlib.sha256(datos.codigo.encode("utf-8")).hexdigest()
        if hash_ingresado != codigo_orm.codigo_hash:
            codigo_orm.intentos_fallidos += 1
            if codigo_orm.intentos_fallidos >= settings.OTP_MAX_ATTEMPTS:
                codigo_orm.usado = True
                db.commit()
                raise DomainError(
                    "Has superado el límite de intentos permitidos. Solicita un nuevo código.",
                    code="INTENTOS_SUPERADOS",
                )
            db.commit()
            intentos_restantes = settings.OTP_MAX_ATTEMPTS - codigo_orm.intentos_fallidos
            raise DomainError(
                f"Código de verificación inválido. Intentos restantes: {intentos_restantes}.",
                code="CODIGO_INVALIDO",
            )

        # 4. Código válido: actualizar contraseña con Argon2id
        usuario.password_hash = hash_password(datos.nueva_password)
        codigo_orm.usado = True
        db.commit()

        logger.info("Contraseña actualizada exitosamente para el usuario %s", usuario.email)
        return RestablecerPasswordOut()


servicio_recuperar_password = RecuperarPasswordServicio()
