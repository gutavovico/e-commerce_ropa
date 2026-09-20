"""Servicio de dominio para el caso de uso CU03: Cerrar Sesión (Logout)."""

from typing import Optional
from core.security import decode_access_token
from core.token_blacklist import token_blacklist
from modules.autenticacion_seguridad.cu03_cerrar_sesion.esquemas import LogoutOut
from modules.autenticacion_seguridad.modelos import UsuarioORM


class ServicioLogout:
    """Coordina la revocación criptográfica y la finalización de sesión activa."""

    @staticmethod
    def cerrar_sesion(
        token: str,
        usuario: UsuarioORM,
    ) -> LogoutOut:
        """Invalida el token Bearer en el servidor impidiendo futuras peticiones.

        Args:
            token: Token JWT activo recibido en la cabecera Authorization.
            usuario: Instancia del usuario autenticado resuelta por la dependencia.

        Returns:
            LogoutOut: DTO confirmando la revocación exitosa.
        """
        exp_timestamp: Optional[float] = None
        try:
            payload = decode_access_token(token)
            exp_val = payload.get("exp")
            if exp_val and isinstance(exp_val, (int, float)):
                exp_timestamp = float(exp_val)
        except Exception:
            # Si falla la decodificación, revocar con el valor por defecto
            exp_timestamp = None

        token_blacklist.revocar_token(token, exp_timestamp)

        return LogoutOut(
            mensaje=f"Sesión finalizada exitosamente para {usuario.email}.",
            revocado=True,
            codigo="SESION_FINALIZADA",
        )
