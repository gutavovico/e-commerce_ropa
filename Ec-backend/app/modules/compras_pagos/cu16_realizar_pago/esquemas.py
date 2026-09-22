"""Esquemas Pydantic para CU16: Realizar Pago Electrónico."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from integrations.stripe_service import validar_luhn

# Métodos que el checkout digital admite. `efectivo` y `transferencia` existen en el enum de
# PostgreSQL para la venta presencial, pero no tienen sentido en una pasarela en línea.
METODOS_DIGITALES = ("tarjeta_credito", "tarjeta_debito", "qr", "pasarela_digital")
METODOS_CON_TARJETA = ("tarjeta_credito", "tarjeta_debito")


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
    metodos_disponibles: List[str] = Field(default_factory=lambda: list(METODOS_DIGITALES))


# ---------------------------------------------------------------------------
# Escritura: procesamiento del pago
# ---------------------------------------------------------------------------


class TarjetaIn(BaseModel):
    """Datos de tarjeta en tránsito.

    **No se persisten.** Se usan para validar y cobrar, y se descartan; de la tarjeta solo
    sobreviven la marca y los últimos cuatro dígitos. El CVV no se guarda ni se registra.
    """

    numero: str = Field(..., min_length=12, max_length=23)
    titular: str = Field(..., min_length=2, max_length=150)
    mes_expiracion: int = Field(..., ge=1, le=12)
    anio_expiracion: int = Field(..., ge=2024, le=2099)
    cvv: str = Field(..., min_length=3, max_length=4)

    @field_validator("numero", mode="before")
    @classmethod
    def _normalizar_numero(cls, valor: str) -> str:
        """Admite el PAN con espacios o guiones, como lo teclea cualquier persona."""
        return "".join(c for c in str(valor) if c.isdigit())

    @field_validator("numero")
    @classmethod
    def _validar_luhn(cls, valor: str) -> str:
        if not validar_luhn(valor):
            raise ValueError("El número de tarjeta no supera la verificación de Luhn.")
        return valor

    @field_validator("cvv")
    @classmethod
    def _validar_cvv(cls, valor: str) -> str:
        if not valor.isdigit():
            raise ValueError("El código CVV debe contener solo dígitos.")
        return valor

    @model_validator(mode="after")
    def _validar_expiracion(self) -> "TarjetaIn":
        """La tarjeta caduca el último día de su mes de expiración."""
        hoy = date.today()
        ultimo_dia_valido = date(self.anio_expiracion, self.mes_expiracion, 1)
        if (ultimo_dia_valido.year, ultimo_dia_valido.month) < (hoy.year, hoy.month):
            raise ValueError("La tarjeta está caducada.")
        return self


class PagoProcesarIn(BaseModel):
    """Payload de cobro.

    Deliberadamente **no admite importes**: el servidor los toma de la orden ya congelada. Una
    cifra enviada por el cliente se ignora por completo.

    Tampoco admite `guardar_tarjeta`: sin un token reutilizable de pasarela, guardar un medio de
    pago exigiría almacenar el PAN, lo que queda descartado (decisión §1.2 de la especificación).
    """

    id_venta: int
    metodo_pago: Literal["tarjeta_credito", "tarjeta_debito", "qr", "pasarela_digital"]

    tarjeta: Optional[TarjetaIn] = Field(
        None, description="Obligatoria para métodos con tarjeta, salvo que se aporte un token"
    )
    token_pasarela: Optional[str] = Field(
        None,
        max_length=120,
        description="Token de prueba de Stripe (tok_visa, tok_chargeDeclined…), alternativo a la tarjeta",
    )

    clave_idempotencia: Optional[str] = Field(
        None,
        max_length=64,
        description=(
            "Identificador único del intento. Reenviar la misma clave devuelve el pago ya "
            "confirmado en lugar de cobrar dos veces."
        ),
    )

    @model_validator(mode="after")
    def _validar_datos_del_metodo(self) -> "PagoProcesarIn":
        if self.metodo_pago in METODOS_CON_TARJETA and not (self.tarjeta or self.token_pasarela):
            raise ValueError(
                "Los pagos con tarjeta requieren los datos de la tarjeta o un token de pasarela."
            )
        return self


class PagoConfirmadoOut(BaseModel):
    """Confirmación del cobro y del cierre del ciclo de compra."""

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

    confirmado_en: datetime
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
