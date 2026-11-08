"""Servicio de integración con Decart Lucy VTON para CU10: Vestidor Virtual.

Solicita tokens efímeros de cliente (~60 s de ventana de conexión) hacia la API de Decart
sin exponer la clave API maestra permanente del backend a la aplicación móvil.
Si la clave está ausente, la API externa no responde o los créditos se encuentran agotados,
lanza ServiceUnavailableError (HTTP 503) para activar el fallback automático al Motor 1 (Local).
"""

import json
import logging
import secrets
import urllib.error
import urllib.request
from typing import Any, Optional

from core.config import settings
from core.errors import ServiceUnavailableError

logger = logging.getLogger("fashionstore.decart_service")

# Medido contra Decart: 0,9–1,4 s en caliente, 4,55 s en la primera petición (arranque en frío del
# TLS/DNS). Con el límite anterior de 4 s ese primer token fallaba con DECART_TIMEOUT y la app
# conmutaba al Motor 1 sin que Decart estuviera caído.
TIMEOUT_TOKEN_SEGUNDOS = 10.0


class DecartService:
    """Cliente desacoplado para la emisión de tokens de cliente de Decart."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: float = TIMEOUT_TOKEN_SEGUNDOS,
    ):
        self.api_key = api_key if api_key is not None else settings.DECART_API_KEY
        self.api_url = (api_url if api_url is not None else settings.DECART_API_URL).rstrip("/")
        self.timeout = timeout

    def generar_token_cliente(self, restringir_origenes: bool = True) -> dict[str, Any]:
        """Solicita un token efímero a Decart para la sesión de streaming Lucy VTON.

        Args:
            restringir_origenes: con `True` (web) el token solo vale desde los orígenes de
                `CORS_ORIGINS`. La app móvil pasa `False`: su WebView carga la página de Decart
                como asset local (`file://`), cuyo `Origin` es `null`, y Decart rechazaría el
                token con «Origin not allowed». La restricción de origen solo protege navegadores;
                el token sigue limitado a 60 s, al modelo VTON y a 60 s de sesión.

        Returns:
            dict con token, expira_en_segundos y servicio.

        Raises:
            ServiceUnavailableError: si la clave no está configurada, falla la red o
                                      Decart retorna error (créditos agotados o servicio caído).
        """
        clave = (self.api_key if self.api_key is not None else settings.DECART_API_KEY or "").strip()
        if not clave:
            logger.info("DECART_API_KEY no configurada. Denegando token para conmutar a Motor 1.")
            raise ServiceUnavailableError(
                "Servicio de vestidor con IA Decart no configurado o no disponible.",
                code="DECART_NO_DISPONIBLE",
            )

        # Entorno de pruebas o clave simulada para tests locales sin red
        if clave.startswith("mock_") or clave.startswith("test_") or clave == "simulador":
            return {
                "token": f"decart_client_token_{secrets.token_hex(16)}",
                "expira_en_segundos": 60,
                "servicio": "decart_lucy_vton_720p",
            }

        # Extraer orígenes válidos para restricción en el token de cliente
        raw_origins = settings.CORS_ORIGINS
        if isinstance(raw_origins, str):
            raw_origins = raw_origins.split(",")
        allowed_origins = [
            str(orig).strip()
            for orig in (raw_origins or [])
            if str(orig).strip() and not str(orig).strip().startswith("*")
        ]
        if not allowed_origins:
            allowed_origins = ["http://localhost:4200", "http://127.0.0.1:4200"]

        endpoint = f"{self.api_url}/v1/client/tokens"
        headers = {
            "x-api-key": clave,
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
            "User-Agent": "FashionStore-Backend/1.0",
        }
        payload_dict = {
            "expiresIn": 60,
            "allowedModels": ["lucy-vton-3.6"],
            **({"allowedOrigins": allowed_origins} if restringir_origenes else {}),
            "constraints": {
                "realtime": {
                    "maxSessionDuration": 60,
                }
            },
        }
        payload = json.dumps(payload_dict).encode("utf-8")

        req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status in (200, 201):
                    body = json.loads(response.read().decode("utf-8"))
                    token_val = (
                        body.get("apiKey")
                        or body.get("token")
                        or body.get("client_token")
                        or body.get("id")
                    )
                    if not token_val:
                        raise ServiceUnavailableError(
                            "Respuesta inválida de Decart API.",
                            code="DECART_RESPUESTA_INVALIDA",
                        )
                    return {
                        "token": str(token_val),
                        "expira_en_segundos": int(body.get("expira_en_segundos", 60)),
                        "servicio": body.get("servicio", "decart_lucy_vton_3.6"),
                    }
                raise ServiceUnavailableError(
                    f"Respuesta no exitosa de Decart (HTTP {response.status}).",
                    code="DECART_NO_DISPONIBLE",
                )
        except urllib.error.HTTPError as exc:
            logger.warning(
                "Error HTTP al invocar Decart API: %s - %s",
                exc.code,
                exc.reason,
            )
            # 401/403/402 (créditos) / 500 / 503 conmutan limpiamente a 503
            raise ServiceUnavailableError(
                "El servicio externo Decart no está disponible o carece de saldo de créditos.",
                code="DECART_NO_DISPONIBLE",
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            logger.warning("Fallo de red o timeout conectando con Decart: %s", exc)
            raise ServiceUnavailableError(
                "Tiempo de espera agotado al conectar con el servicio de IA de Decart.",
                code="DECART_TIMEOUT",
            ) from exc
        except Exception as exc:
            logger.exception("Error imprevisto en DecartService: %s", exc)
            raise ServiceUnavailableError(
                "Error técnico en la integración con Decart.",
                code="DECART_ERROR_TECNICO",
            ) from exc


decart_service = DecartService()

