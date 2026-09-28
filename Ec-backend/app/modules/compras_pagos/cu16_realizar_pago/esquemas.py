"""Esquemas Pydantic para CU16: Realizar Pago Electrónico."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Métodos que el checkout digital admite contra la pasarela sandbox. `transferencia` existe en
# el enum de PostgreSQL para la venta presencial, pero no tiene sentido aquí.
METODOS_DIGITALES = ("tarjeta_credito", "tarjeta_debito", "qr", "pasarela_digital")
METODOS_CON_TARJETA = ("tarjeta_credito", "tarjeta_debito")

# `efectivo` no pasa por la pasarela: se registra como pago `pendiente` hasta que un cajero lo
# confirma en la boutique de recogida (§1.5.2/§1.6 de la especificación). Solo se ofrece cuando
# `ventas.tipo_entrega == 'recogida_boutique'`.
METODO_EFECTIVO = "efectivo"


# ---------------------------------------------------------------------------
# Lectura: resumen previo al pago
# ---------------------------------------------------------------------------


class PagoItemOut(BaseModel):
    """Línea de la orden con el precio ya congelado por CU15."""

    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    imagen_url: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal_linea: Decimal
    nombre_sucursal: Optional[str] = None


class ResumenPagoOut(BaseModel):
    """Datos necesarios para inicializar la pasarela sobre una orden pendiente."""

    id_venta: int
    numero_comprobante: str
    estado: str

    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    iva_incluido: Decimal = Field(
        ..., description="IVA contenido en el total (21%). Informativo: no se persiste"
    )
    moneda: str = "EUR"
    total_prendas: int

    items: List[PagoItemOut] = Field(default_factory=list)

    tipo_entrega: str
    direccion_envio: Optional[str] = None
    nombre_sucursal_retiro: Optional[str] = None
    nombre_cliente: Optional[str] = None

    fecha_venta: datetime
    expira_en: datetime
    segundos_restantes: int = Field(
        ...,
        description=(
            "Tiempo restante de la retención, calculado en el servidor. El cliente no debe "
            "derivarlo de su propio reloj, que puede ir desfasado."
        ),
    )
    metodos_disponibles: List[str] = Field(
        default_factory=lambda: list(METODOS_DIGITALES),
        description=(
            "Incluye 'efectivo' únicamente si tipo_entrega es 'recogida_boutique'; lo resuelve "
            "el servicio, no este valor por defecto."
        ),
    )


# ---------------------------------------------------------------------------
# Escritura: procesamiento del pago
# ---------------------------------------------------------------------------


class PagoEfectivoIn(BaseModel):
    """Payload para registrar la intención de pago en efectivo en sucursal.

    Deliberadamente **no admite importes**: el servidor los toma de la orden ya congelada.
    """

    id_venta: int

    clave_idempotencia: Optional[str] = Field(
        None,
        max_length=64,
        description=(
            "Identificador único del intento. Reenviar la misma clave devuelve el registro ya "
            "creado en lugar de duplicarlo."
        ),
    )


class PagoIniciarIn(BaseModel):
    """Payload para abrir un cobro digital contra Stripe.

    **No lleva ningún dato de tarjeta.** El backend nunca recibe el PAN ni el CVV: crea un
    `PaymentIntent` en Stripe y devuelve su `client_secret`, que el cliente usa con Stripe.js
    (Web) o el SDK de Flutter (Mobile) para recolectar la tarjeta y confirmar el cobro
    directamente contra Stripe, sin pasar por este servidor. Ver «Renombrado a confirmación por
    tokens» en `spec.md` de CU16.
    """

    id_venta: int
    metodo_pago: Literal["tarjeta_credito", "tarjeta_debito", "qr", "pasarela_digital"]

    clave_idempotencia: Optional[str] = Field(
        None,
        max_length=64,
        description=(
            "Identificador único del intento. Reenviar la misma clave devuelve el mismo "
            "`PaymentIntent` en lugar de crear otro."
        ),
    )

    escenario_prueba: Optional[Literal["aprobado", "rechazado", "fondos_insuficientes"]] = Field(
        None,
        description=(
            "Solo tiene efecto cuando el simulador está activo (sin clave real de Stripe "
            "configurada): fuerza el desenlace de la verificación para que las pruebas sean "
            "deterministas. Con Stripe real se ignora; el desenlace lo decide la pasarela."
        ),
    )


class PagoIntentoOut(BaseModel):
    """Respuesta a la apertura de un cobro digital.

    `client_secret` es lo único que el cliente necesita para confirmar el `PaymentIntent` con
    Stripe.js/el SDK de Flutter. Si la orden ya estaba pagada (reenvío idempotente de un cobro ya
    confirmado), `ya_confirmado` viene en `True` y `confirmacion` trae el resultado sin abrir un
    intento nuevo.
    """

    id_pago: int
    client_secret: Optional[str] = None
    ya_confirmado: bool = False
    confirmacion: Optional["PagoConfirmadoOut"] = None


class PagoConfirmadoOut(BaseModel):
    """Confirmación del cobro, o del registro pendiente si el método es `efectivo`.

    Para tarjeta/Bizum/PayPal, `estado_pago` llega siempre `confirmado` y `confirmado_en`
    resuelto. Para `efectivo`, el pago queda `pendiente` (`confirmado_en=None`) hasta que un
    cajero lo confirme en la boutique de recogida (§1.5.2/§1.6 de la especificación) — la venta
    permanece `pendiente`, no `pagada`, y el mensaje explica el siguiente paso al cliente.
    """

    id_pago: int
    id_venta: int
    numero_comprobante: str
    estado_pago: str = "confirmado"
    estado_venta: str = "pagada"
    metodo_pago: str

    referencia_pasarela: Optional[str] = None
    monto: Decimal
    moneda: str = "EUR"

    marca_tarjeta: Optional[str] = None
    ultimos_digitos: Optional[str] = None

    confirmado_en: Optional[datetime] = None
    mensaje_confirmacion: str = (
        "Pago confirmado. Tu orden entra en preparación en el atelier."
    )


class PagoRechazadoOut(BaseModel):
    """Detalle del rechazo, devuelto con HTTP 402.

    Acompaña al código `PAGO_RECHAZADO` para que el cliente sepa que puede reintentar: la orden
    sigue viva y con sus existencias retenidas.
    """

    id_pago: int
    id_venta: int
    estado_pago: str = "rechazado"
    codigo_rechazo: str
    motivo: str
    puede_reintentar: bool = True
