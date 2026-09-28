"""Integración con Stripe en modo test para CU16 (Realizar Pago Electrónico).

Sigue el mismo patrón que `GeminiService`: si `STRIPE_SECRET_KEY` está configurada con una clave
utilizable, cobra contra la API de Stripe en entorno de pruebas; si no lo está, conmuta a un
simulador determinista que reproduce el contrato de Stripe sin salir a la red.

Esa conmutación no es una comodidad: la suite de pruebas debe ejecutarse con 0 ms de latencia y
sin dependencias externas, y el entorno de desarrollo tiene hoy un marcador de 32 caracteres en
lugar de una clave real (`sk_test_...` de Stripe ronda los 107). Un fallo de red o una clave
ausente no pueden dejar el checkout inoperante.

**El backend nunca recibe el PAN ni el CVV** (revisado el 2026-09-28). El flujo es de dos pasos:

1. `crear_intento` abre un `PaymentIntent` en Stripe (`automatic_payment_methods` habilitado, sin
   `confirm`) y devuelve su `client_secret`. La tarjeta se recolecta y el cobro se confirma en el
   navegador/app con Stripe.js o el SDK de Flutter, directamente contra Stripe: este servidor no
   participa de esa confirmación ni ve el número de la tarjeta.
2. `verificar_intento` recupera el `PaymentIntent` por su id y decide `aprobado` según lo que
   Stripe diga que pasó — nunca según lo que el cliente afirme. Es la aplicación de la misma
   regla que ya rige los importes de la orden: el servidor jamás confía en el cliente para el
   desenlace de un cobro.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

from core.config import settings

logger = logging.getLogger("fashionstore.stripe_service")

# Una clave real de Stripe es sustancialmente más larga; por debajo de este umbral se asume
# marcador de configuración y se usa el simulador.
LONGITUD_MINIMA_CLAVE_REAL = 40

#: Desenlaces deterministas que el simulador puede forzar en `verificar_intento`, para que las
#: pruebas no dependan del azar. Con Stripe real este parámetro se ignora: el desenlace lo decide
#: la pasarela, nunca el cliente.
ESCENARIOS_PRUEBA = {
    "rechazado": ("card_declined", "La entidad emisora ha rechazado la tarjeta."),
    "fondos_insuficientes": ("insufficient_funds", "La tarjeta no dispone de fondos suficientes."),
}


class ErrorPasarela(Exception):
    """Fallo técnico de la pasarela: red, credenciales o error interno de Stripe.

    Se distingue de un rechazo de tarjeta: aquí el cargo no llegó a evaluarse, de modo que la
    orden no debe registrarse como rechazada sino tratarse como error del servicio.
    """


@dataclass
class IntentoPago:
    """Desenlace de la apertura de un `PaymentIntent`, ya normalizado para el servicio."""

    referencia: str
    client_secret: Optional[str]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoPasarela:
    """Desenlace de la verificación de un intento de cobro, ya normalizado para el dominio."""

    aprobado: bool
    referencia: Optional[str]
    codigo_respuesta: str
    mensaje: str
    marca: Optional[str] = None
    ultimos_digitos: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)


class PasarelaPagos:
    """Contrato que consume `PagoServicio`.

    Existe para que las pruebas puedan inyectar un doble sin red ni latencia, y para aislar el
    dominio de la biblioteca concreta de la pasarela, conforme a la regla de integraciones
    externas de la constitución de backend.
    """

    def crear_intento(
        self,
        monto: Decimal,
        metodo_pago: str,
        descripcion: str = "",
        metadatos: Optional[dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> IntentoPago:
        raise NotImplementedError

    def recuperar_client_secret(self, referencia: str) -> Optional[str]:
        raise NotImplementedError

    def verificar_intento(
        self, referencia: str, escenario_prueba: Optional[str] = None
    ) -> ResultadoPasarela:
        raise NotImplementedError


class StripeService(PasarelaPagos):
    """Cliente de Stripe con conmutación automática a simulador determinista."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        latencia_simulada_ms: int = 400,
    ):
        self.api_key = api_key if api_key is not None else settings.STRIPE_SECRET_KEY
        self.latencia_simulada_ms = latencia_simulada_ms

    @property
    def usa_stripe_real(self) -> bool:
        """True solo si hay una clave de test con longitud plausible y el SDK disponible."""
        if not self.api_key or len(self.api_key) < LONGITUD_MINIMA_CLAVE_REAL:
            return False
        try:
            import stripe  # noqa: F401
        except ImportError:
            logger.warning("El SDK de Stripe no está instalado; se usará el simulador.")
            return False
        return True

    @staticmethod
    def a_centimos(monto: Decimal) -> int:
        """Convierte un importe a la unidad mínima entera que exige la API de Stripe."""
        return int((monto * 100).quantize(Decimal("1")))

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def crear_intento(
        self,
        monto: Decimal,
        metodo_pago: str,
        descripcion: str = "",
        metadatos: Optional[dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> IntentoPago:
        if self.usa_stripe_real:
            return self._crear_intento_stripe(monto, descripcion, metadatos, idempotency_key)
        return self._crear_intento_simulado(monto, metodo_pago, descripcion)

    def recuperar_client_secret(self, referencia: str) -> Optional[str]:
        """Recupera el `client_secret` de un intento ya abierto, para un reenvío idempotente."""
        if self.usa_stripe_real:
            import stripe

            stripe.api_key = self.api_key
            try:
                intento = stripe.PaymentIntent.retrieve(referencia)
            except Exception as exc:  # noqa: BLE001 - fallo técnico, no de tarjeta
                logger.exception("Fallo técnico al recuperar el intento en Stripe", exc_info=exc)
                raise ErrorPasarela(
                    "No fue posible recuperar el cobro en curso. Inténtalo de nuevo."
                ) from exc
            return intento.get("client_secret")
        return f"{referencia}_secret_sbx"

    def verificar_intento(
        self, referencia: str, escenario_prueba: Optional[str] = None
    ) -> ResultadoPasarela:
        if self.usa_stripe_real:
            return self._verificar_intento_stripe(referencia)
        return self._verificar_intento_simulado(referencia, escenario_prueba)

    # ------------------------------------------------------------------
    # Stripe real (modo test)
    # ------------------------------------------------------------------

    def _crear_intento_stripe(
        self,
        monto: Decimal,
        descripcion: str,
        metadatos: Optional[dict[str, Any]],
        idempotency_key: Optional[str],
    ) -> IntentoPago:
        import stripe

        stripe.api_key = self.api_key

        try:
            intento = stripe.PaymentIntent.create(
                amount=self.a_centimos(monto),
                currency="eur",
                description=descripcion or "FashionStore Atelier",
                metadata=metadatos or {},
                automatic_payment_methods={"enabled": True},
                idempotency_key=idempotency_key or None,
            )
        except Exception as exc:  # noqa: BLE001 - cualquier fallo aquí es técnico, no de tarjeta
            logger.exception("Fallo técnico al abrir el intento en Stripe", exc_info=exc)
            raise ErrorPasarela(
                "No fue posible iniciar el cobro con la pasarela. Inténtalo de nuevo."
            ) from exc

        return IntentoPago(
            referencia=intento["id"],
            client_secret=intento.get("client_secret"),
            payload=self._sanear(dict(intento)),
        )

    def _verificar_intento_stripe(self, referencia: str) -> ResultadoPasarela:
        import stripe

        stripe.api_key = self.api_key

        try:
            intento = stripe.PaymentIntent.retrieve(referencia, expand=["payment_method"])
        except Exception as exc:  # noqa: BLE001 - cualquier fallo aquí es técnico, no de tarjeta
            logger.exception("Fallo técnico al verificar el intento en Stripe", exc_info=exc)
            raise ErrorPasarela(
                "No fue posible confirmar el cobro con la pasarela. Inténtalo de nuevo."
            ) from exc

        aprobado = intento.get("status") == "succeeded"
        metodo_pago = intento.get("payment_method")
        tarjeta = (
            metodo_pago.get("card") if isinstance(metodo_pago, dict) else None
        )

        return ResultadoPasarela(
            aprobado=aprobado,
            referencia=intento.get("id"),
            codigo_respuesta=intento.get("status", "desconocido"),
            mensaje=(
                "Pago confirmado por la pasarela."
                if aprobado
                else "La pasarela no pudo completar el cargo."
            ),
            marca=tarjeta.get("brand", "").upper() if tarjeta else None,
            ultimos_digitos=tarjeta.get("last4") if tarjeta else None,
            payload=self._sanear(dict(intento)),
        )

    @staticmethod
    def _sanear(payload: dict[str, Any]) -> dict[str, Any]:
        """Elimina cualquier rastro de datos sensibles antes de persistir el payload.

        Stripe no devuelve el PAN completo, pero el saneado es explícito y no confiado: lo que
        se guarda en `pagos.payload_respuesta` queda en la base de datos para siempre.
        """
        prohibidas = {"number", "cvc", "cvv", "card_number", "client_secret"}

        def limpiar(valor: Any) -> Any:
            if isinstance(valor, dict):
                return {
                    k: ("[REDACTADO]" if k in prohibidas else limpiar(v))
                    for k, v in valor.items()
                }
            if isinstance(valor, list):
                return [limpiar(v) for v in valor]
            return valor

        return limpiar(payload)

    # ------------------------------------------------------------------
    # Simulador determinista
    # ------------------------------------------------------------------

    def _crear_intento_simulado(
        self, monto: Decimal, metodo_pago: str, descripcion: str
    ) -> IntentoPago:
        referencia = f"pi_sbx_{random.randint(10**9, 10**10 - 1)}"
        return IntentoPago(
            referencia=referencia,
            client_secret=f"{referencia}_secret_sbx",
            payload={
                "simulado": True,
                "id": referencia,
                "status": "requires_payment_method",
                "amount": self.a_centimos(monto),
                "currency": "eur",
                "description": descripcion,
                "metodo_pago": metodo_pago,
            },
        )

    def _verificar_intento_simulado(
        self, referencia: str, escenario_prueba: Optional[str]
    ) -> ResultadoPasarela:
        """Reproduce el contrato de Stripe sin salir a la red.

        El desenlace es **determinista**: lo fija `escenario_prueba`, que el simulador es el
        único que consulta — con Stripe real este parámetro no existe en la API y se ignora.
        """
        if self.latencia_simulada_ms > 0:
            time.sleep(self.latencia_simulada_ms / 1000)

        motivo = ESCENARIOS_PRUEBA.get(escenario_prueba or "")
        if motivo:
            codigo, mensaje = motivo
            return ResultadoPasarela(
                aprobado=False,
                referencia=referencia,
                codigo_respuesta=codigo,
                mensaje=mensaje,
                payload={
                    "simulado": True,
                    "id": referencia,
                    "status": "requires_payment_method",
                    "error": {"code": codigo, "message": mensaje},
                },
            )

        return ResultadoPasarela(
            aprobado=True,
            referencia=referencia,
            codigo_respuesta="succeeded",
            mensaje="Pago confirmado por la pasarela.",
            marca="VISA",
            ultimos_digitos="4242",
            payload={
                "simulado": True,
                "id": referencia,
                "status": "succeeded",
            },
        )
