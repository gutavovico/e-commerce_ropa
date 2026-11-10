"""Servicio de Notificaciones Push con Firebase Cloud Messaging (FCM · RF37).

Spec: `P2-cierre-sesion-respaldos-push` (Parte C).
- AC-C3: Las notificaciones push se envían DESPUÉS del commit de la transacción;
         si la transacción hace rollback, no se envía ningún push.
- AC-C4: Si Firebase no está configurado (FIREBASE_CREDENCIALES vacía o ausente) o la llamada a FCM falla,
         la operación de negocio termina con éxito (el push es de mejor esfuerzo) y se registra en log.
- AC-C6: Los tokens push pertenecen a una empresa; una notificación jamás deberá enviarse
         al dispositivo de otra empresa (garantizado por el filtro RLS de id_tenant en fashionstore.dispositivos).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy import event, select
from sqlalchemy.orm import Session

from core.config import settings

logger = logging.getLogger("fashionstore.fcm")

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _FIREBASE_SDK_DISPONIBLE = True
except ImportError:
    firebase_admin = None  # type: ignore
    credentials = None  # type: ignore
    messaging = None  # type: ignore
    _FIREBASE_SDK_DISPONIBLE = False

_app_firebase = None
_inicializacion_intentada = False

# Historial en memoria para pruebas automáticas
_historial_envios_pruebas: List[Dict[str, Any]] = []


def _obtener_app_firebase():
    global _app_firebase, _inicializacion_intentada
    if _inicializacion_intentada:
        return _app_firebase

    _inicializacion_intentada = True
    cred_val = (settings.FIREBASE_CREDENCIALES or "").strip()
    if not cred_val or not _FIREBASE_SDK_DISPONIBLE:
        logger.info("Firebase FCM no configurado o SDK ausente; se operará en modo simulador (mejor esfuerzo).")
        return None

    try:
        # Verificar si ya existe una app de Firebase por defecto
        try:
            _app_firebase = firebase_admin.get_app()
            return _app_firebase
        except ValueError:
            pass

        # Puede ser ruta a archivo JSON o JSON en texto crudo
        if os.path.exists(cred_val):
            cred = credentials.Certificate(cred_val)
        else:
            try:
                cred_dict = json.loads(cred_val)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                logger.warning("No se pudo parsear FIREBASE_CREDENCIALES como JSON ni encontrar archivo: %s", e)
                return None

        _app_firebase = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin inicializado correctamente.")
        return _app_firebase
    except Exception as exc:
        logger.warning("Fallo al inicializar Firebase Admin SDK: %s", exc)
        return None


def enviar_push(
    token: str,
    titulo: str,
    cuerpo: str,
    datos: Optional[Dict[str, str]] = None,
) -> bool:
    """Envía una notificación push directa a un token FCM (AC-C4: nunca lanza excepciones)."""
    if not token or not token.strip():
        return False

    datos_limpios = {str(k): str(v) for k, v in (datos or {}).items()}
    registro_prueba = {
        "token": token,
        "titulo": titulo,
        "cuerpo": cuerpo,
        "datos": datos_limpios,
    }
    _historial_envios_pruebas.append(registro_prueba)

    app = _obtener_app_firebase()
    if app is None:
        logger.info(
            "[SIMULADOR FCM] Push emitido a token '%s...': '%s' - '%s' | datos: %s",
            token[:10],
            titulo,
            cuerpo,
            datos_limpios,
        )
        return True

    try:
        mensaje = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=cuerpo,
            ),
            data=datos_limpios,
            token=token,
        )
        respuesta = messaging.send(mensaje, app=app)
        logger.info("FCM push enviado con éxito. Message ID: %s", respuesta)
        return True
    except Exception as exc:
        logger.warning("Fallo al despachar notificación push FCM al token '%s...': %s", token[:10], exc)
        return False


def programar_push(
    db: Session,
    token: str,
    titulo: str,
    cuerpo: str,
    datos: Optional[Dict[str, str]] = None,
) -> None:
    """Encola un push para ser enviado estrictamente DESPUÉS del commit de la sesión (AC-C3)."""
    if not token or not token.strip():
        return

    pendientes = db.info.setdefault("_push_pendientes", [])
    pendientes.append((token, titulo, cuerpo, datos or {}))


def notificar_cliente(
    db: Session,
    id_cliente: int,
    titulo: str,
    cuerpo: str,
    datos: Optional[Dict[str, str]] = None,
) -> int:
    """Programa una notificación push a todos los dispositivos registrados del cliente en el tenant activo (AC-C6)."""
    try:
        from modules.sincronizacion.modelos import DispositivoORM

        stmt = select(DispositivoORM).where(
            DispositivoORM.id_cliente == id_cliente,
            DispositivoORM.token_push.isnot(None),
            DispositivoORM.token_push != "",
        )
        res = db.execute(stmt)
        dispositivos = res.scalars().all() if hasattr(res, "scalars") else []
    except Exception as exc:
        logger.debug("No se pudieron consultar dispositivos para push: %s", exc)
        return 0

    count = 0
    for dev in dispositivos:
        token = getattr(dev, "token_push", None)
        if token:
            programar_push(db, token, titulo, cuerpo, datos)
            count += 1
    return count


# --- Hooks de SQLAlchemy para garantizar AC-C3 ---

@event.listens_for(Session, "after_commit")
def _al_confirmar_transaccion(session: Session) -> None:
    pendientes = session.info.pop("_push_pendientes", [])
    for token, titulo, cuerpo, datos in pendientes:
        try:
            enviar_push(token, titulo, cuerpo, datos)
        except Exception as exc:
            logger.warning("Error despachando push tras commit: %s", exc)


@event.listens_for(Session, "after_rollback")
def _al_revertir_transaccion(session: Session) -> None:
    # Si la transacción hace rollback, se desechan todos los pushes programados
    session.info.pop("_push_pendientes", None)


def obtener_historial_pruebas() -> List[Dict[str, Any]]:
    return list(_historial_envios_pruebas)


def limpiar_historial_pruebas() -> None:
    _historial_envios_pruebas.clear()
