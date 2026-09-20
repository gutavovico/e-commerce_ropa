"""Servicio de lista negra de tokens (Token Blacklist) para revocación de JWT (CU03).

Permite invalidar tokens antes de su tiempo de expiración natural (logout seguro).
Implementa almacenamiento en memoria seguro para hilos con limpieza automática de expirados.
"""

from datetime import datetime, timezone
import hashlib
import threading
from typing import Dict, Optional


class TokenBlacklistService:
    """Gestiona la revocación e invalidación de tokens JWT en el servidor."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Mapeo: hash_token -> exp_timestamp (segundos epoch)
        self._revocados: Dict[str, float] = {}

    def _hash_token(self, token: str) -> str:
        """Calcula un hash SHA-256 del token para optimizar memoria."""
        return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

    def revocar_token(self, token: str, exp_timestamp: Optional[float] = None) -> None:
        """Registra un token en la lista negra hasta su fecha de expiración.

        Args:
            token: Cadena en texto del JWT.
            exp_timestamp: Timestamp Unix (segundos) de expiración. Si es None,
                           se asigna 24 horas por defecto.
        """
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc).timestamp()

        if exp_timestamp is None:
            # 24 horas por defecto
            exp_timestamp = now + 86400.0

        with self._lock:
            self._limpiar_expirados_interno(now)
            self._revocados[token_hash] = exp_timestamp

    def esta_revocado(self, token: str) -> bool:
        """Comprueba si un token ha sido revocado y su revocación sigue vigente."""
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc).timestamp()

        with self._lock:
            exp = self._revocados.get(token_hash)
            if exp is None:
                return False

            if exp <= now:
                # Ya expiró naturalmente, se retira de la lista negra
                del self._revocados[token_hash]
                return False

            return True

    def _limpiar_expirados_interno(self, now: float) -> None:
        """Elimina tokens cuya expiración ya ocurrió en el tiempo actual."""
        expirados = [th for th, exp in self._revocados.items() if exp <= now]
        for th in expirados:
            del self._revocados[th]

    def limpiar_expirados(self) -> None:
        """Ejecuta la purga explícita de tokens expirados."""
        now = datetime.now(timezone.utc).timestamp()
        with self._lock:
            self._limpiar_expirados_interno(now)

    def reiniciar(self) -> None:
        """Limpia todos los tokens revocados (utilizado en testing)."""
        with self._lock:
            self._revocados.clear()


# Instancia singleton para la aplicación
token_blacklist = TokenBlacklistService()
