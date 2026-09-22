"""Integración con Stripe en modo test para CU16 (Realizar Pago Electrónico).

Sigue el mismo patrón que `GeminiService`: si `STRIPE_SECRET_KEY` está configurada con una clave
utilizable, cobra contra la API de Stripe en entorno de pruebas; si no lo está, conmuta a un
simulador determinista que reproduce el contrato de Stripe sin salir a la red.

Esa conmutación no es una comodidad: la suite de pruebas debe ejecutarse con 0 ms de latencia y
sin dependencias externas, y el entorno de desarrollo tiene hoy un marcador de 32 caracteres en
lugar de una clave real (`sk_test_...` de Stripe ronda los 107). Un fallo de red o una clave
ausente no pueden dejar el checkout inoperante.

Ningún método de este módulo recibe, devuelve ni registra el PAN completo ni el CVV: solo la
marca y los últimos cuatro dígitos, que es lo único que puede persistirse.
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

# Sufijos de PAN que fuerzan un resultado concreto, al estilo de las tarjetas de prueba de
# Stripe. Hacen que el escenario de tarjeta denegada sea reproducible en vez de aleatorio.
#
# IMPORTANTE: un PAN de prueba debe superar además la verificación de Luhn, porque `TarjetaIn`
# la aplica antes de que el pago llegue a la pasarela. Los valores de `PANES_PRUEBA` cumplen
# ambas condiciones; usar cualquier otro número terminado en estos sufijos puede ser rechazado
# antes por el validador y no llegar nunca a ejercitar este simulador.
SUFIJO_RECHAZO_GENERICO = "0000"
SUFIJO_FONDOS_INSUFICIENTES = "9995"

#: PAN de prueba válidos según Luhn, para pruebas y documentación de la API.
PANES_PRUEBA = {
    "aprobado": "4111111111111111",
    "rechazado": "4100000050000000",
    "fondos_insuficientes": "4000000000009995",
}

# Tokens de prueba de Stripe admitidos por el simulador.
TOKENS_RECHAZO = {"tok_chargeDeclined", "tok_chargeDeclinedInsufficientFunds"}


class ErrorPasarela(Exception):
    """Fallo técnico de la pasarela: red, credenciales o error interno de Stripe.

    Se distingue de un rechazo de tarjeta: aquí el cargo no llegó a evaluarse, de modo que la
    orden no debe registrarse como rechazada sino tratarse como error del servicio.
    """


@dataclass(frozen=True)
class DatosTarjeta:
    """Datos de tarjeta en tránsito. Nunca se persisten ni se registran en logs."""

    numero: str
    titular: str
    mes_expiracion: int
    anio_expiracion: int
    cvv: str

    @property
    def ultimos_digitos(self) -> str:
        return self.numero[-4:] if len(self.numero) >= 4 else self.numero

    @property
    def marca(self) -> str:
        """Deduce la marca por el prefijo del PAN, como hace cualquier pasarela."""
        if self.numero.startswith("4"):
            return "VISA"
        if self.numero[:2] in {"51", "52", "53", "54", "55"} or self.numero[:4] == "2221":
            return "MASTERCARD"
        if self.numero[:2] in {"34", "37"}:
            return "AMEX"
        return "DESCONOCIDA"


@dataclass
class ResultadoPasarela:
    """Desenlace de un intento de cobro, ya normalizado para el servicio de dominio."""

    aprobado: bool
    referencia: Optional[str]
    codigo_respuesta: str
    mensaje: str
    marca: Optional[str] = None
    ultimos_digitos: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)


def validar_luhn(numero: str) -> bool:
    """Comprueba el dígito verificador de un PAN mediante el algoritmo de Luhn."""
    digitos = [int(c) for c in numero if c.isdigit()]
    if len(digitos) < 12:
        return False

    suma = 0
    # Se recorre de derecha a izquierda duplicando uno de cada dos dígitos.
    for indice, digito in enumerate(reversed(digitos)):
        if indice % 2 == 1:
            digito *= 2
            if digito > 9:
                digito -= 9
        suma += digito
    return suma % 10 == 0


class PasarelaPagos:
    """Contrato que consume `PagoServicio`.

    Existe para que las pruebas puedan inyectar un doble sin red ni latencia, y para aislar el
    dominio de la biblioteca concreta de la pasarela, conforme a la regla de integraciones
    externas de la constitución de backend.
    """

    def procesar_cargo(
        self,
        monto: Decimal,
        metodo_pago: str,
        tarjeta: Optional[DatosTarjeta] = None,
        token: Optional[str] = None,
        descripcion: str = "",
        metadatos: Optional[dict[str, Any]] = None,
    ) -> ResultadoPasarela:
        raise NotImplementedError


class StripeService(PasarelaPagos):
    """Cliente de Stripe con conmutación automática a simulador determinista."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        latencia_simulada_ms: int = 800,
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

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def procesar_cargo(
        self,
        monto: Decimal,
        metodo_pago: str,
        tarjeta: Optional[DatosTarjeta] = None,
        token: Optional[str] = None,
        descripcion: str = "",
        metadatos: Optional[dict[str, Any]] = None,
    ) -> ResultadoPasarela:
        """Cobra `monto` y devuelve el desenlace normalizado.

        `monto` viaja como `Decimal` y solo se convierte a céntimos enteros en el borde de la
        llamada a Stripe, que es la unidad que su API exige. El importe exacto que se persiste
        en `pagos.monto` sigue siendo el `Decimal` original.
        """
        if self.usa_stripe_real:
            return self._cobrar_con_stripe(monto, metodo_pago, tarjeta, token, descripcion, metadatos)
        return self._cobrar_simulado(monto, metodo_pago, tarjeta, token, descripcion)

    @staticmethod
    def a_centimos(monto: Decimal) -> int:
        """Convierte un importe a la unidad mínima entera que exige la API de Stripe."""
        return int((monto * 100).quantize(Decimal("1")))

    # ------------------------------------------------------------------
    # Stripe real (modo test)
    # ------------------------------------------------------------------

    def _cobrar_con_stripe(
        self,
        monto: Decimal,
        metodo_pago: str,
        tarjeta: Optional[DatosTarjeta],
        token: Optional[str],
        descripcion: str,
        metadatos: Optional[dict[str, Any]],
    ) -> ResultadoPasarela:
        import stripe

        stripe.api_key = self.api_key

        try:
            intento = stripe.PaymentIntent.create(
                amount=self.a_centimos(monto),
                currency="eur",
                description=descripcion or "FashionStore Atelier",
                metadata=metadatos or {},
                payment_method_data=self._construir_metodo_pago(tarjeta, token),
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )

            aprobado = intento.get("status") == "succeeded"
            return ResultadoPasarela(
                aprobado=aprobado,
                referencia=intento.get("id"),
                codigo_respuesta=intento.get("status", "desconocido"),
                mensaje=(
                    "Pago confirmado por la pasarela."
                    if aprobado
                    else "La pasarela no pudo completar el cargo."
                ),
                marca=tarjeta.marca if tarjeta else None,
                ultimos_digitos=tarjeta.ultimos_digitos if tarjeta else None,
                payload=self._sanear(dict(intento)),
            )

        except stripe.CardError as exc:  # type: ignore[attr-defined]
            # Rechazo legítimo: la tarjeta fue evaluada y denegada.
            cuerpo = getattr(exc, "json_body", None) or {}
            error = cuerpo.get("error", {})
            return ResultadoPasarela(
                aprobado=False,
                referencia=error.get("charge") or error.get("payment_intent", {}).get("id"),
                codigo_respuesta=error.get("decline_code") or error.get("code", "card_declined"),
                mensaje=error.get("message") or str(exc),
                marca=tarjeta.marca if tarjeta else None,
                ultimos_digitos=tarjeta.ultimos_digitos if tarjeta else None,
                payload=self._sanear(cuerpo),
            )

        except Exception as exc:  # noqa: BLE001 - cualquier otro fallo es técnico, no de tarjeta
            logger.exception("Fallo técnico al contactar con Stripe", exc_info=exc)
            raise ErrorPasarela(
                "No fue posible contactar con la pasarela de pagos. Inténtalo de nuevo."
            ) from exc

    @staticmethod
    def _construir_metodo_pago(
        tarjeta: Optional[DatosTarjeta], token: Optional[str]
    ) -> dict[str, Any]:
        if token:
            return {"type": "card", "card": {"token": token}}
        if tarjeta:
            return {
                "type": "card",
                "card": {
                    "number": tarjeta.numero,
                    "exp_month": tarjeta.mes_expiracion,
                    "exp_year": tarjeta.anio_expiracion,
                    "cvc": tarjeta.cvv,
                },
            }
        raise ErrorPasarela("No se aportaron datos de tarjeta ni token de pasarela.")

    @staticmethod
    def _sanear(payload: dict[str, Any]) -> dict[str, Any]:
        """Elimina cualquier rastro de datos sensibles antes de persistir el payload.

        Stripe no devuelve el PAN completo, pero el saneado es explícito y no confiado: lo que
        se guarda en `pagos.payload_respuesta` queda en la base de datos para siempre.
        """
        prohibidas = {"number", "cvc", "cvv", "card_number"}

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

    def _cobrar_simulado(
        self,
        monto: Decimal,
        metodo_pago: str,
        tarjeta: Optional[DatosTarjeta],
        token: Optional[str],
        descripcion: str,
    ) -> ResultadoPasarela:
        """Reproduce el contrato de Stripe sin salir a la red.

        El desenlace es **determinista**: lo fija el sufijo del PAN o el token de prueba. Una
        prueba que dependiera del azar sería intermitente y acabaría desactivada.
        """
        if self.latencia_simulada_ms > 0:
            time.sleep(self.latencia_simulada_ms / 1000)

        referencia = f"pi_sbx_{random.randint(10**9, 10**10 - 1)}"

        motivo_rechazo = self._motivo_rechazo(tarjeta, token)
        if motivo_rechazo:
            codigo, mensaje = motivo_rechazo
            return ResultadoPasarela(
                aprobado=False,
                referencia=referencia,
                codigo_respuesta=codigo,
                mensaje=mensaje,
                marca=tarjeta.marca if tarjeta else None,
                ultimos_digitos=tarjeta.ultimos_digitos if tarjeta else None,
                payload={
                    "simulado": True,
                    "id": referencia,
                    "status": "requires_payment_method",
                    "error": {"code": codigo, "message": mensaje},
                    "amount": self.a_centimos(monto),
                    "currency": "eur",
                    "metodo_pago": metodo_pago,
                },
            )

        return ResultadoPasarela(
            aprobado=True,
            referencia=referencia,
            codigo_respuesta="succeeded",
            mensaje="Pago confirmado por la pasarela.",
            marca=tarjeta.marca if tarjeta else None,
            ultimos_digitos=tarjeta.ultimos_digitos if tarjeta else None,
            payload={
                "simulado": True,
                "id": referencia,
                "status": "succeeded",
                "amount": self.a_centimos(monto),
                "currency": "eur",
                "description": descripcion,
                "metodo_pago": metodo_pago,
                "ultimos_digitos": tarjeta.ultimos_digitos if tarjeta else None,
                "marca": tarjeta.marca if tarjeta else None,
            },
        )

    @staticmethod
    def _motivo_rechazo(
        tarjeta: Optional[DatosTarjeta], token: Optional[str]
    ) -> Optional[tuple[str, str]]:
        """Decide si el cargo simulado debe rechazarse y por qué motivo."""
        if token in TOKENS_RECHAZO:
            if token == "tok_chargeDeclinedInsufficientFunds":
                return ("insufficient_funds", "La tarjeta no dispone de fondos suficientes.")
            return ("card_declined", "La entidad emisora ha rechazado la tarjeta.")

        if tarjeta is None:
            return None

        if tarjeta.numero.endswith(SUFIJO_FONDOS_INSUFICIENTES):
            return ("insufficient_funds", "La tarjeta no dispone de fondos suficientes.")
        if tarjeta.numero.endswith(SUFIJO_RECHAZO_GENERICO):
            return ("card_declined", "La entidad emisora ha rechazado la tarjeta.")
        return None
