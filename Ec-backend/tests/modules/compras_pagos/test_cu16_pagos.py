"""Pruebas de CU16: Realizar Pago Electrónico.

Cada prueba cita el escenario Gherkin que verifica, definido en
`.specs/changes/CU16-realizar-pago-electronico/spec.md`, sección A.5. Las pruebas de pago en
efectivo en sucursal citan las secciones §1.5.2/§1.6 del mismo documento.

**El backend nunca recibe datos de tarjeta** (revisado el 2026-09-28): el cobro digital se abre
con `iniciar_pago` (crea un `PaymentIntent` y devuelve su `client_secret`, sin PAN ni CVV) y se
cierra con `confirmar_pago` (verifica el desenlace contra la pasarela, nunca contra lo que el
cliente reporte). La pasarela se inyecta siempre como doble: la suite no sale a la red ni espera
latencia.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from core.errors import ConflictError, NotFoundError, PaymentRequiredError
from integrations.stripe_service import (
    ErrorPasarela,
    IntentoPago,
    PasarelaPagos,
    ResultadoPasarela,
    StripeService,
)
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import SucursalORM, VentaDetalleORM, VentaORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu16_realizar_pago.esquemas import PagoIniciarIn
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.compras_pagos.modelos import PagoORM
from modules.reservas.modelos import MovimientoInventarioORM

PAGO_INICIAR_TARJETA = {"id_venta": 1, "metodo_pago": "tarjeta_credito"}


# ---------------------------------------------------------------------------
# Dobles
# ---------------------------------------------------------------------------


class PasarelaFalsa(PasarelaPagos):
    """Pasarela determinista para pruebas: sin red, sin latencia."""

    def __init__(self, aprobado: bool = True, error_tecnico: bool = False, error_en: str = "verificar"):
        self.aprobado = aprobado
        self.error_tecnico = error_tecnico
        self.error_en = error_en  # "crear" o "verificar": en qué paso falla la pasarela
        self.llamadas_crear = 0
        self.llamadas_verificar = 0
        self.ultimo_monto = None
        self.ultima_idempotency_key = None

    def crear_intento(
        self, monto, metodo_pago, descripcion="", metadatos=None, idempotency_key=None
    ) -> IntentoPago:
        self.llamadas_crear += 1
        self.ultimo_monto = monto
        self.ultima_idempotency_key = idempotency_key
        if self.error_tecnico and self.error_en == "crear":
            raise ErrorPasarela("La pasarela no responde.")
        return IntentoPago(
            referencia="pi_test_123456789",
            client_secret="pi_test_123456789_secret_test",
            payload={"id": "pi_test_123456789", "status": "requires_payment_method"},
        )

    def recuperar_client_secret(self, referencia):
        return f"{referencia}_secret_test"

    def verificar_intento(self, referencia, escenario_prueba=None) -> ResultadoPasarela:
        self.llamadas_verificar += 1
        if self.error_tecnico and self.error_en == "verificar":
            raise ErrorPasarela("La pasarela no responde.")

        if self.aprobado:
            return ResultadoPasarela(
                aprobado=True,
                referencia=referencia,
                codigo_respuesta="succeeded",
                mensaje="Pago confirmado por la pasarela.",
                marca="VISA",
                ultimos_digitos="1111",
                payload={"id": referencia, "status": "succeeded"},
            )

        return ResultadoPasarela(
            aprobado=False,
            referencia=referencia,
            codigo_respuesta="card_declined",
            mensaje="La entidad emisora ha rechazado la tarjeta.",
            payload={"error": {"code": "card_declined"}},
        )


def crear_venta(estado: str = "pendiente", minutos_antiguedad: int = 1) -> VentaORM:
    """Orden con una línea, en el estado y antigüedad indicados."""
    venta = VentaORM(
        id_venta=1,
        numero_comprobante="FS-2026-000001",
        id_cliente=10,
        id_sucursal=1,
        tipo_venta="digital_web",
        estado=estado,
        subtotal=Decimal("2100.00"),
        descuento=Decimal("160.00"),
        total=Decimal("1940.00"),
        fecha_venta=datetime.now(timezone.utc) - timedelta(minutes=minutos_antiguedad),
        tipo_entrega="domicilio",
        direccion_envio="Calle de Claudio Coello 48, 28001 Madrid",
    )
    venta.detalles = [
        VentaDetalleORM(
            id_venta_detalle=1,
            id_venta=1,
            id_variante=3,
            cantidad=3,
            precio_unitario=Decimal("646.67"),
            id_sucursal=1,
        )
    ]
    venta.sucursal_retiro = None
    return venta


def crear_venta_recogida(
    estado: str = "pendiente", minutos_antiguedad: int = 1, id_sucursal_retiro: int = 5
) -> VentaORM:
    """Orden con recogida en boutique: la única modalidad que admite pago en efectivo (§1.6)."""
    venta = crear_venta(estado=estado, minutos_antiguedad=minutos_antiguedad)
    venta.tipo_entrega = "recogida_boutique"
    venta.id_sucursal_retiro = id_sucursal_retiro
    venta.direccion_envio = None
    venta.sucursal_retiro = SucursalORM(
        id_sucursal=id_sucursal_retiro,
        id_ciudad=1,
        nombre="Atelier Serrano - Madrid",
        direccion="Calle Serrano 48",
        activa=True,
    )
    return venta


PAGO_EFECTIVO = {"id_venta": 1}


def usuario_caja(rol: str, id_sucursal: int | None = None, id_usuario: int = 50) -> UsuarioORM:
    """Cajero, encargado de sucursal o administrador que confirma/cancela en mostrador."""
    return UsuarioORM(
        id_usuario=id_usuario,
        email=f"{rol}@fashionstore.com",
        rol=rol,
        nombres="Nombre",
        apellidos="Apellido",
        activo=True,
        id_sucursal=id_sucursal,
    )


def pago_pendiente_digital(
    id_pago: int = 99,
    id_venta: int = 1,
    metodo_pago: str = "tarjeta_credito",
    monto: Decimal = Decimal("1940.00"),
    escenario_prueba: str | None = None,
    clave_idempotencia: str | None = None,
) -> PagoORM:
    """Pago digital `pendiente` con su `PaymentIntent` ya abierto, listo para `confirmar_pago`."""
    return PagoORM(
        id_pago=id_pago,
        id_venta=id_venta,
        metodo_pago=metodo_pago,
        monto=monto,
        estado="pendiente",
        referencia_pasarela="pi_test_123456789",
        payload_respuesta={
            "clave_idempotencia": clave_idempotencia,
            "metodo_pago": metodo_pago,
            "escenario_prueba": escenario_prueba,
            "pasarela": {"id": "pi_test_123456789", "status": "requires_payment_method"},
        },
    )


def preparar_admin(pago: PagoORM, venta: VentaORM, bolsa_real: bool = False):
    """Sustituye la carga del pago en efectivo y su venta por los dobles de la prueba.

    `bolsa_real=True` deja correr el retiro de la bolsa de verdad, para las pruebas que
    verifican a quién se le retiran las prendas al confirmar el efectivo.
    """
    pago.venta = venta
    dobles = {
        "_cargar_pago_efectivo_para_caja": staticmethod(
            lambda db, id_pago, bloquear=False: (pago, venta)
        ),
    }
    if not bolsa_real:
        dobles["_retirar_de_la_bolsa"] = staticmethod(lambda db, venta_: None)
    return patch.multiple(PagoServicio, **dobles)


def espiar_bolsa(registro: dict, id_carrito: int = 77):
    """Doble de la bolsa que anota de qué cliente se retiran prendas, y cuáles.

    Permite afirmar la regla: la bolsa solo se toca cuando el cobro queda confirmado.
    """
    carrito = SimpleNamespace(id_carrito=id_carrito)

    def buscar(db, id_cliente):
        registro["cliente_consultado"] = id_cliente
        return carrito

    def retirar(db, id_carrito_, detalles):
        registro.setdefault("retiradas", []).append((id_carrito_, list(detalles)))
        return len(list(detalles))

    return patch.multiple(
        CarritoRepositorio,
        buscar_carrito=staticmethod(buscar),
        retirar_lineas_compradas=staticmethod(retirar),
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sesion_autenticada(db, usuario):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db_con_ids(db):
    """Asigna identificadores como haría PostgreSQL en el flush."""
    contador = {"pago": 0}

    def asignar(objeto):
        if isinstance(objeto, PagoORM) and objeto.id_pago is None:
            contador["pago"] += 1
            objeto.id_pago = contador["pago"]

    db.add.side_effect = asignar
    db.refresh.side_effect = lambda obj: None
    return db


def agregados(db, tipo):
    return [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], tipo)]


def preparar(venta, inventario, bolsa_real: bool = False):
    """Sustituye la carga de venta y de inventario por los dobles de la prueba.

    `bolsa_real=True` deja correr el retiro de la bolsa de verdad; por defecto se neutraliza,
    porque la sesión simulada no puede resolver las consultas del carrito.
    """
    dobles = {
        "_cargar_venta": staticmethod(lambda db, id_venta, bloquear=False: venta),
        "_buscar_pago_idempotente": staticmethod(lambda db, id_venta, clave: None),
        "_buscar_pago_efectivo_pendiente": staticmethod(lambda db, id_venta: None),
    }
    if not bolsa_real:
        dobles["_retirar_de_la_bolsa"] = staticmethod(lambda db, venta_: None)

    return patch.multiple(PagoServicio, **dobles), patch.object(
        CarritoRepositorio,
        "obtener_inventario",
        staticmethod(lambda db, v, s, cantidad=1, bloquear=False: inventario),
    )


def preparar_confirmar(pago, venta, inventario, bolsa_real: bool = False):
    """Sustituye la carga del pago digital y de la venta por los dobles de la prueba."""
    dobles = {
        "_cargar_pago_digital": staticmethod(lambda db, id_pago, bloquear=False: pago),
        "_cargar_venta": staticmethod(lambda db, id_venta, bloquear=False: venta),
        "_buscar_pago_efectivo_pendiente": staticmethod(lambda db, id_venta: None),
    }
    if not bolsa_real:
        dobles["_retirar_de_la_bolsa"] = staticmethod(lambda db, venta_: None)

    return patch.multiple(PagoServicio, **dobles), patch.object(
        CarritoRepositorio,
        "obtener_inventario",
        staticmethod(lambda db, v, s, cantidad=0, bloquear=False: inventario),
    )


# ===========================================================================
# Escenario: Iniciar un cobro digital (nunca recibe datos de tarjeta)
# ===========================================================================


def test_iniciar_pago_abre_intento_y_devuelve_client_secret(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Iniciar cobro digital»: 201 y `client_secret`, sin dato alguno de tarjeta."""
    venta = crear_venta()
    pasarela = PasarelaFalsa()

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA)

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["client_secret"] == "pi_test_123456789_secret_test"
    assert datos["ya_confirmado"] is False
    assert pasarela.llamadas_crear == 1

    pagos = agregados(db_con_ids, PagoORM)
    assert len(pagos) == 1
    assert pagos[0].estado == "pendiente"
    assert pagos[0].referencia_pasarela == "pi_test_123456789"
    # Nunca se persiste el `client_secret`: es de un solo uso, para el cliente.
    assert "client_secret" not in str(pagos[0].payload_respuesta)


def test_esquema_de_iniciar_pago_no_admite_ningun_dato_de_tarjeta():
    """`PagoIniciarIn` no declara ningún campo de tarjeta: el backend no puede recibir el PAN."""
    campos = set(PagoIniciarIn.model_fields)
    assert not campos & {"tarjeta", "numero", "cvv", "cvc"}


def test_iniciar_pago_rechaza_metodo_efectivo(client, sesion_autenticada):
    """`efectivo` no abre ningún `PaymentIntent`: tiene su propio endpoint."""
    respuesta = client.post(
        "/api/v1/pagos/intentos", json={"id_venta": 1, "metodo_pago": "efectivo"}
    )
    assert respuesta.status_code == 422


def test_iniciar_pago_orden_ya_pagada_responde_409_sin_abrir_intento(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Orden ya liquidada»: 409 y ningún efecto secundario."""
    venta = crear_venta(estado="pagada")
    pasarela = PasarelaFalsa()

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "VENTA_YA_LIQUIDADA"
    assert agregados(db_con_ids, PagoORM) == []
    assert pasarela.llamadas_crear == 0


def test_iniciar_pago_orden_anulada_responde_409(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Una orden anulada tampoco admite pago."""
    venta = crear_venta(estado="anulada")

    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "VENTA_ANULADA"


def test_iniciar_pago_orden_expirada_responde_409_y_libera_existencias(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Ventana expirada»: 409, orden anulada y stock devuelto, sin abrir intento."""
    # Tramitada hace 40 minutos: la ventana es de 25.
    venta = crear_venta(minutos_antiguedad=40)
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12
    pasarela = PasarelaFalsa()

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ), patch.object(
        __import__(
            "modules.compras_pagos.cu15_comprar_plataforma.servicio",
            fromlist=["CheckoutServicio"],
        ).CheckoutServicio,
        "_cargar_venta_para_liberar",
        create=True,
    ):
        respuesta = client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "ORDEN_EXPIRADA"
    assert pasarela.llamadas_crear == 0
    assert agregados(db_con_ids, PagoORM) == []


def test_iniciar_pago_orden_de_otro_cliente_responde_403(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Orden de otro cliente»: 403 VENTA_AJENA, no 404: el recurso existe pero es ajeno."""
    venta = crear_venta()
    venta.id_cliente = 999

    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA)

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "VENTA_AJENA"


def test_iniciar_pago_requiere_autenticacion(client):
    """Sin sesión válida, abrir un cobro responde 401."""
    assert client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA).status_code == 401


def test_iniciar_pago_ignora_el_importe_enviado_por_el_cliente(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """El importe lo fija la orden congelada; el enviado por el cliente se ignora."""
    venta = crear_venta()
    pasarela = PasarelaFalsa()

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post(
            "/api/v1/pagos/intentos",
            json={**PAGO_INICIAR_TARJETA, "monto": "1.00", "total": "1.00"},
        )

    assert respuesta.status_code == 201
    # La pasarela abrió el intento por el importe real de la orden.
    assert pasarela.ultimo_monto == Decimal("1940.00")


def test_iniciar_pago_pasa_la_clave_de_idempotencia_a_la_pasarela(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """La clave de idempotencia también viaja a Stripe, como defensa adicional."""
    venta = crear_venta()
    pasarela = PasarelaFalsa()

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        client.post(
            "/api/v1/pagos/intentos",
            json={**PAGO_INICIAR_TARJETA, "clave_idempotencia": "idem-tarjeta-1"},
        )

    assert pasarela.ultima_idempotency_key == "idem-tarjeta-1"


def test_iniciar_pago_fallo_tecnico_de_pasarela_no_registra_pago(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Un fallo de red al abrir el intento no debe ensuciar el historial de pagos."""
    venta = crear_venta()
    pasarela = PasarelaFalsa(error_tecnico=True, error_en="crear")

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/intentos", json=PAGO_INICIAR_TARJETA)

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "PASARELA_NO_DISPONIBLE"
    assert agregados(db_con_ids, PagoORM) == []
    assert venta.estado == "pendiente"


def test_iniciar_pago_idempotente_pendiente_reutiliza_el_intento_abierto(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Reenviar la misma clave no abre un segundo `PaymentIntent`."""
    venta = crear_venta()
    previo = pago_pendiente_digital(id_pago=5, clave_idempotencia="idem-tarjeta-1")
    pasarela = PasarelaFalsa()

    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta),
        _buscar_pago_idempotente=staticmethod(
            lambda db, id_venta, clave: previo if clave == "idem-tarjeta-1" else None
        ),
    ), patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post(
            "/api/v1/pagos/intentos",
            json={**PAGO_INICIAR_TARJETA, "clave_idempotencia": "idem-tarjeta-1"},
        )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id_pago"] == 5
    assert datos["client_secret"] == "pi_test_123456789_secret_test"
    assert datos["ya_confirmado"] is False
    assert pasarela.llamadas_crear == 0
    assert agregados(db_con_ids, PagoORM) == []


def test_iniciar_pago_idempotente_confirmado_devuelve_la_confirmacion_sin_nuevo_intento(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Si el cobro ya se cerró, reenviar la clave devuelve esa confirmación, no un intento nuevo."""
    venta = crear_venta(estado="pagada")
    previo = pago_pendiente_digital(id_pago=5, clave_idempotencia="idem-tarjeta-1")
    previo.estado = "confirmado"
    previo.confirmado_en = datetime.now(timezone.utc)
    pasarela = PasarelaFalsa()

    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta),
        _buscar_pago_idempotente=staticmethod(
            lambda db, id_venta, clave: previo if clave == "idem-tarjeta-1" else None
        ),
    ), patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post(
            "/api/v1/pagos/intentos",
            json={**PAGO_INICIAR_TARJETA, "clave_idempotencia": "idem-tarjeta-1"},
        )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["ya_confirmado"] is True
    assert datos["client_secret"] is None
    assert datos["confirmacion"]["estado_pago"] == "confirmado"
    assert pasarela.llamadas_crear == 0
    assert agregados(db_con_ids, PagoORM) == []


# ===========================================================================
# Escenario: Confirmar un cobro digital (el servidor nunca confía en el cliente)
# ===========================================================================


def test_confirmar_pago_aprobado_confirma_venta_y_consolida_stock(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Pago exitoso»: 200, venta pagada y existencias consolidadas."""
    venta = crear_venta()
    inventario.cantidad_disponible = 12
    inventario.cantidad_reservada = 3
    pago = pago_pendiente_digital()
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 200
    datos = respuesta.json()

    assert datos["estado_pago"] == "confirmado"
    assert datos["estado_venta"] == "pagada"
    assert datos["numero_comprobante"] == "FS-2026-000001"
    assert datos["referencia_pasarela"] == "pi_test_123456789"
    assert datos["monto"] == "1940.00"
    # De la tarjeta solo sobreviven marca y últimos cuatro dígitos, y solo porque Stripe los
    # devuelve al recuperar el `PaymentIntent`: el backend nunca los recibió directamente.
    assert datos["marca_tarjeta"] == "VISA"
    assert datos["ultimos_digitos"] == "1111"

    assert venta.estado == "pagada"
    assert pago.estado == "confirmado"
    assert pago.confirmado_en is not None

    auditoria = pago.payload_respuesta
    assert auditoria["ultimos_digitos"] == "1111"
    assert not {"numero", "cvv", "cvc", "card_number"} & set(auditoria)


def test_confirmar_pago_descuenta_reservado_sin_devolver_a_disponible(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """La prenda vendida abandona el almacén: no vuelve a estar disponible."""
    venta = crear_venta()
    inventario.cantidad_disponible = 12
    inventario.cantidad_reservada = 3
    pago = pago_pendiente_digital()
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 200
    assert inventario.cantidad_reservada == 0
    assert inventario.cantidad_disponible == 12


def test_confirmar_pago_audita_movimiento_con_saldos_reales(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin: movimiento `venta_confirmada` con responsable y saldos reales."""
    venta = crear_venta()
    inventario.cantidad_reservada = 3
    pago = pago_pendiente_digital()
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        client.post("/api/v1/pagos/99/confirmar")

    movimientos = agregados(db_con_ids, MovimientoInventarioORM)
    assert len(movimientos) == 1
    mov = movimientos[0]
    assert mov.tipo_movimiento == "venta_confirmada"
    assert mov.cantidad == -3
    assert mov.id_usuario_responsable == usuario.id_usuario
    assert mov.referencia_documento == "VENTA-1"
    assert mov.saldo_anterior == 3
    assert mov.saldo_nuevo == 0


def test_confirmar_pago_rechazado_responde_402_y_deja_la_orden_viva(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Tarjeta denegada»: 402, venta pendiente e inventario intacto."""
    venta = crear_venta()
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12
    pago = pago_pendiente_digital()
    pasarela = PasarelaFalsa(aprobado=False)

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 402
    assert respuesta.json()["code"] == "PAGO_RECHAZADO"
    assert "rechazado" in respuesta.json()["detail"].lower()

    assert pago.estado == "rechazado"
    assert venta.estado == "pendiente"
    assert inventario.cantidad_reservada == 3
    assert inventario.cantidad_disponible == 12
    assert agregados(db_con_ids, MovimientoInventarioORM) == []


def test_confirmar_pago_fallo_tecnico_de_pasarela_no_se_registra_como_rechazo(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Un fallo de red no es un rechazo de tarjeta: no debe ensuciar el historial de pagos."""
    venta = crear_venta()
    pago = pago_pendiente_digital()
    pasarela = PasarelaFalsa(error_tecnico=True, error_en="verificar")

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "PASARELA_NO_DISPONIBLE"
    assert pago.estado == "pendiente"
    assert venta.estado == "pendiente"


def test_confirmar_pago_ya_confirmado_es_idempotente_y_no_repite_la_verificacion(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Un doble clic (o un reintento de red) no debe volver a llamar a la pasarela."""
    venta = crear_venta()
    pago = pago_pendiente_digital()
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        primera = client.post("/api/v1/pagos/99/confirmar")
        segunda = client.post("/api/v1/pagos/99/confirmar")

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert primera.json()["confirmado_en"] == segunda.json()["confirmado_en"]
    assert pasarela.llamadas_verificar == 1


def test_confirmar_pago_ya_rechazado_no_admite_reconfirmarse(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Un pago que ya se resolvió como rechazado no vuelve a evaluarse: hace falta un intento nuevo."""
    venta = crear_venta()
    pago = pago_pendiente_digital()
    pago.estado = "rechazado"
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "PAGO_NO_PENDIENTE"
    assert pasarela.llamadas_verificar == 0


def test_confirmar_pago_de_otro_cliente_responde_403(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Confirmar el pago de una orden ajena responde 403, no 404."""
    venta = crear_venta()
    venta.id_cliente = 999
    pago = pago_pendiente_digital()

    p1, p2 = preparar_confirmar(pago, venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "VENTA_AJENA"


def test_confirmar_pago_requiere_autenticacion(client):
    """Sin sesión válida, confirmar un pago responde 401."""
    assert client.post("/api/v1/pagos/99/confirmar").status_code == 401


def test_cargar_pago_digital_no_encontrado_responde_404():
    """Un `id_pago` inexistente no se confunde con uno ajeno: es un 404 limpio."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = None

    with pytest.raises(NotFoundError):
        PagoServicio._cargar_pago_digital(db, 999)


def test_cargar_pago_digital_rechaza_un_pago_en_efectivo():
    """Un pago en efectivo nunca abrió un `PaymentIntent`: no tiene sentido verificarlo aquí."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = PagoORM(
        id_pago=1, id_venta=1, metodo_pago="efectivo", monto=Decimal("10.00"), estado="pendiente"
    )

    with pytest.raises(ConflictError):
        PagoServicio._cargar_pago_digital(db, 1)


def test_escenario_de_prueba_declarado_al_iniciar_determina_el_desenlace_al_confirmar(
    db_con_ids, usuario, inventario
):
    """El simulador real (sin doble de prueba) respeta `escenario_prueba` de extremo a extremo."""
    venta = crear_venta()
    servicio_stripe = StripeService(api_key="", latencia_simulada_ms=0)

    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        intento = PagoServicio.iniciar_pago(
            db_con_ids,
            usuario,
            PagoIniciarIn(id_venta=1, metodo_pago="tarjeta_credito", escenario_prueba="rechazado"),
            pasarela=servicio_stripe,
        )

    pago = agregados(db_con_ids, PagoORM)[0]
    assert pago.id_pago == intento.id_pago

    p3, p4 = preparar_confirmar(pago, venta, inventario)
    with p3, p4:
        with pytest.raises(PaymentRequiredError):
            PagoServicio.confirmar_pago(db_con_ids, usuario, pago.id_pago, pasarela=servicio_stripe)

    assert pago.estado == "rechazado"


# ===========================================================================
# Resumen de pago
# ===========================================================================


def test_resumen_pago_devuelve_orden_congelada(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Resumen de pago»: total, líneas y segundos restantes del servidor."""
    venta = crear_venta(minutos_antiguedad=5)

    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta),
        _buscar_pago_efectivo_pendiente=staticmethod(lambda db, id_venta: None),
    ):
        respuesta = client.get("/api/v1/ventas/1/resumen-pago")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["numero_comprobante"] == "FS-2026-000001"
    assert datos["total"] == "1940.00"
    assert datos["subtotal"] == "2100.00"
    assert datos["descuento"] == "160.00"
    assert Decimal(datos["subtotal"]) - Decimal(datos["descuento"]) == Decimal(datos["total"])
    assert datos["tipo_entrega"] == "domicilio"
    assert datos["direccion_envio"].startswith("Calle de Claudio Coello")
    # Tramitada hace 5 min sobre una ventana de 25: quedan unos 20.
    assert 1100 < datos["segundos_restantes"] <= 1200


def test_resumen_de_orden_pagada_responde_409(client, sesion_autenticada, usuario):
    """Una orden ya liquidada no tiene resumen de pago que mostrar."""
    venta = crear_venta(estado="pagada")

    with patch.object(
        PagoServicio, "_cargar_venta", staticmethod(lambda db, id_venta, bloquear=False: venta)
    ):
        respuesta = client.get("/api/v1/ventas/1/resumen-pago")

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "VENTA_NO_PAGABLE"


# ===========================================================================
# Pago en efectivo en sucursal (§1.5.2/§1.6 de la especificación)
# ===========================================================================


def test_efectivo_con_entrega_domicilio_responde_422(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """El pago en efectivo solo está disponible con recogida en boutique."""
    venta = crear_venta()  # tipo_entrega "domicilio" por defecto
    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/efectivo", json=PAGO_EFECTIVO)

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "METODO_NO_SOPORTADO"
    assert venta.estado == "pendiente"
    assert agregados(db_con_ids, PagoORM) == []


def test_efectivo_registra_pago_pendiente_sin_liquidar_la_venta(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Con recogida en boutique, el pago queda `pendiente` y la venta no se toca todavía."""
    venta = crear_venta_recogida()
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12

    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/efectivo", json=PAGO_EFECTIVO)

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado_pago"] == "pendiente"
    assert datos["estado_venta"] == "pendiente"
    assert datos["confirmado_en"] is None
    assert "24 horas" in datos["mensaje_confirmacion"]
    assert "Atelier Serrano - Madrid" in datos["mensaje_confirmacion"]

    assert venta.estado == "pendiente"
    pagos = agregados(db_con_ids, PagoORM)
    assert len(pagos) == 1
    assert pagos[0].estado == "pendiente"
    assert pagos[0].metodo_pago == "efectivo"
    assert inventario.cantidad_reservada == 3
    assert inventario.cantidad_disponible == 12
    assert agregados(db_con_ids, MovimientoInventarioORM) == []


def test_efectivo_idempotente_no_duplica_el_registro(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Reenviar la misma clave de idempotencia devuelve el pago pendiente ya registrado."""
    venta = crear_venta_recogida()
    payload = {**PAGO_EFECTIVO, "clave_idempotencia": "idem-efectivo-1"}
    pago_previo = PagoORM(
        id_pago=5,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        payload_respuesta={"clave_idempotencia": "idem-efectivo-1"},
    )

    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta),
        _buscar_pago_idempotente=staticmethod(
            lambda db, id_venta, clave: pago_previo if clave == "idem-efectivo-1" else None
        ),
    ):
        respuesta = client.post("/api/v1/pagos/efectivo", json=payload)

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id_pago"] == 5
    assert datos["estado_pago"] == "pendiente"
    assert agregados(db_con_ids, PagoORM) == []


def test_resumen_pago_metodos_disponibles_incluye_efectivo_solo_con_recogida_boutique(
    client, sesion_autenticada, usuario
):
    """`metodos_disponibles` solo lista `efectivo` cuando la venta se recoge en boutique."""
    venta_domicilio = crear_venta()
    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta_domicilio),
        _buscar_pago_efectivo_pendiente=staticmethod(lambda db, id_venta: None),
    ):
        datos = client.get("/api/v1/ventas/1/resumen-pago").json()
    assert "efectivo" not in datos["metodos_disponibles"]

    venta_recogida = crear_venta_recogida()
    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta_recogida),
        _buscar_pago_efectivo_pendiente=staticmethod(lambda db, id_venta: None),
    ):
        datos = client.get("/api/v1/ventas/1/resumen-pago").json()
    assert "efectivo" in datos["metodos_disponibles"]


def test_resumen_pago_usa_ventana_de_24h_si_hay_pago_efectivo_pendiente(
    client, sesion_autenticada, usuario
):
    """Con un pago en efectivo pendiente, la cuenta atrás deja de regirse por los 25 min de CU15."""
    # Tramitada hace 40 minutos: ya superó los 25 minutos de la bolsa, pero el pago en
    # efectivo se registró hace apenas 1 hora de las 24 que tiene de plazo.
    venta = crear_venta_recogida(minutos_antiguedad=40)
    pago_pendiente = PagoORM(
        id_pago=99,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    with patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta),
        _buscar_pago_efectivo_pendiente=staticmethod(lambda db, id_venta: pago_pendiente),
    ):
        respuesta = client.get("/api/v1/ventas/1/resumen-pago")

    assert respuesta.status_code == 200
    # Quedan unas 23h de las 24 desde que se registró el pago hace 1h.
    assert respuesta.json()["segundos_restantes"] > 22 * 3600


def test_confirmar_pago_efectivo_administrador_consolida_inventario(
    client, db_con_ids, inventario
):
    """El administrador confirma sin restricción de sucursal; la venta pasa a pagada."""
    venta = crear_venta_recogida()
    pago = PagoORM(
        id_pago=7,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    admin = usuario_caja("administrador")

    app.dependency_overrides[get_db] = lambda: db_con_ids
    app.dependency_overrides[get_current_user] = lambda: admin
    try:
        with preparar_admin(pago, venta), patch.object(
            CarritoRepositorio,
            "obtener_inventario",
            staticmethod(lambda db, v, s, cantidad=0, bloquear=True: inventario),
        ):
            respuesta = client.post("/api/v1/admin/pagos/7/confirmar-efectivo")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estado_pago"] == "confirmado"
    assert datos["estado_venta"] == "pagada"
    assert datos["confirmado_en"] is not None

    assert pago.estado == "confirmado"
    assert venta.estado == "pagada"
    movimientos = agregados(db_con_ids, MovimientoInventarioORM)
    assert len(movimientos) == 1
    assert movimientos[0].tipo_movimiento == "venta_confirmada"


def test_confirmar_pago_efectivo_encargado_de_su_propia_sucursal_ok(
    client, db_con_ids, inventario
):
    """`encargado_sucursal` puede confirmar pagos de la boutique que tiene asignada."""
    venta = crear_venta_recogida(id_sucursal_retiro=5)
    pago = PagoORM(
        id_pago=7,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc),
    )
    encargado = usuario_caja("encargado_sucursal", id_sucursal=5)

    app.dependency_overrides[get_db] = lambda: db_con_ids
    app.dependency_overrides[get_current_user] = lambda: encargado
    try:
        with preparar_admin(pago, venta), patch.object(
            CarritoRepositorio,
            "obtener_inventario",
            staticmethod(lambda db, v, s, cantidad=0, bloquear=True: inventario),
        ):
            respuesta = client.post("/api/v1/admin/pagos/7/confirmar-efectivo")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    assert venta.estado == "pagada"


def test_confirmar_pago_efectivo_encargado_de_otra_sucursal_responde_403(
    client, db_con_ids, inventario
):
    """`encargado_sucursal`/`cajero` no pueden tocar pagos de una boutique ajena."""
    venta = crear_venta_recogida(id_sucursal_retiro=5)
    pago = PagoORM(
        id_pago=7,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc),
    )
    cajero_ajeno = usuario_caja("cajero", id_sucursal=9)

    app.dependency_overrides[get_db] = lambda: db_con_ids
    app.dependency_overrides[get_current_user] = lambda: cajero_ajeno
    try:
        with preparar_admin(pago, venta):
            respuesta = client.post("/api/v1/admin/pagos/7/confirmar-efectivo")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SUCURSAL_AJENA"
    assert venta.estado == "pendiente"
    assert pago.estado == "pendiente"


def test_confirmar_pago_efectivo_expirado_libera_existencias_y_responde_409(
    client, db_con_ids, inventario
):
    """Pasadas las 24h sin confirmar, el intento de confirmarlo libera el stock (§1.6)."""
    venta = crear_venta_recogida()
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12
    pago = PagoORM(
        id_pago=7,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc) - timedelta(hours=25),
    )
    admin = usuario_caja("administrador")

    app.dependency_overrides[get_db] = lambda: db_con_ids
    app.dependency_overrides[get_current_user] = lambda: admin
    try:
        with preparar_admin(pago, venta), patch.object(
            CarritoRepositorio,
            "obtener_inventario",
            staticmethod(lambda db, v, s, cantidad=0, bloquear=True: inventario),
        ):
            respuesta = client.post("/api/v1/admin/pagos/7/confirmar-efectivo")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "PAGO_EFECTIVO_EXPIRADO"
    assert pago.estado == "rechazado"
    assert venta.estado == "anulada"
    assert inventario.cantidad_disponible == 15
    assert inventario.cantidad_reservada == 0


def test_cancelar_pago_efectivo_libera_existencias_y_anula_venta(
    client, db_con_ids, inventario
):
    """Cancelación manual en mostrador antes de las 24h: libera el stock de inmediato."""
    venta = crear_venta_recogida()
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12
    pago = PagoORM(
        id_pago=7,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc),
    )
    admin = usuario_caja("administrador")

    app.dependency_overrides[get_db] = lambda: db_con_ids
    app.dependency_overrides[get_current_user] = lambda: admin
    try:
        with preparar_admin(pago, venta), patch.object(
            CarritoRepositorio,
            "obtener_inventario",
            staticmethod(lambda db, v, s, cantidad=0, bloquear=True: inventario),
        ):
            respuesta = client.post("/api/v1/admin/pagos/7/cancelar-efectivo")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estado"] == "anulada"
    assert datos["unidades_liberadas"] == 3
    assert pago.estado == "rechazado"
    assert venta.estado == "anulada"
    assert inventario.cantidad_disponible == 15
    assert inventario.cantidad_reservada == 0


def test_confirmar_pago_efectivo_requiere_rol_de_caja(client, sesion_autenticada):
    """Un cliente autenticado no puede confirmar pagos en efectivo en mostrador."""
    respuesta = client.post("/api/v1/admin/pagos/7/confirmar-efectivo")
    assert respuesta.status_code == 403


# ===========================================================================
# La bolsa solo se vacía cuando el cobro queda confirmado
# ===========================================================================


def test_confirmar_pago_aprobado_retira_las_prendas_de_la_bolsa(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Con la pasarela confirmando el cobro, las prendas compradas salen de la bolsa."""
    venta = crear_venta()
    pago = pago_pendiente_digital()
    registro: dict = {}
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar_confirmar(pago, venta, inventario, bolsa_real=True)
    with p1, p2, espiar_bolsa(registro), patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 200
    # Se retira de la bolsa del titular de la orden, y solo las líneas de esa venta.
    assert registro["cliente_consultado"] == venta.id_cliente
    assert registro["retiradas"] == [(77, venta.detalles)]


def test_confirmar_pago_rechazado_conserva_la_bolsa_intacta(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Un 402 no puede costarle al cliente su selección: la bolsa queda como estaba."""
    venta = crear_venta()
    pago = pago_pendiente_digital()
    registro: dict = {}
    pasarela = PasarelaFalsa(aprobado=False)

    p1, p2 = preparar_confirmar(pago, venta, inventario, bolsa_real=True)
    with p1, p2, espiar_bolsa(registro), patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/99/confirmar")

    assert respuesta.status_code == 402
    assert "retiradas" not in registro


def test_efectivo_pendiente_conserva_la_bolsa_hasta_que_el_cajero_confirme(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Registrar el pago en efectivo no vacía nada: el cobro aún no ha ocurrido."""
    venta = crear_venta_recogida()
    registro: dict = {}

    p1, p2 = preparar(venta, inventario, bolsa_real=True)
    with p1, p2, espiar_bolsa(registro):
        respuesta = client.post("/api/v1/pagos/efectivo", json=PAGO_EFECTIVO)

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_pago"] == "pendiente"
    assert "retiradas" not in registro


def test_confirmar_pago_efectivo_retira_las_prendas_de_la_bolsa_del_cliente(
    client, db_con_ids, inventario
):
    """Al dar por cobrado el efectivo, la bolsa que se toca es la del comprador, no la del cajero."""
    venta = crear_venta_recogida()
    pago = PagoORM(
        id_pago=7,
        id_venta=1,
        metodo_pago="efectivo",
        monto=venta.total,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc),
    )
    cajero = usuario_caja("cajero", id_sucursal=5, id_usuario=999)
    registro: dict = {}

    app.dependency_overrides[get_db] = lambda: db_con_ids
    app.dependency_overrides[get_current_user] = lambda: cajero
    try:
        with preparar_admin(pago, venta, bolsa_real=True), espiar_bolsa(registro), patch.object(
            CarritoRepositorio,
            "obtener_inventario",
            staticmethod(lambda db, v, s, cantidad=0, bloquear=True: inventario),
        ):
            respuesta = client.post("/api/v1/admin/pagos/7/confirmar-efectivo")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    # El cajero es el usuario 999; la bolsa vaciada es la del cliente de la venta.
    assert registro["cliente_consultado"] == venta.id_cliente
    assert registro["cliente_consultado"] != cajero.id_usuario
    assert registro["retiradas"] == [(77, venta.detalles)]


# ===========================================================================
# Pasarela: conversión, conmutación y saneado
# ===========================================================================


def test_conversion_a_centimos_para_la_api_de_stripe():
    assert StripeService.a_centimos(Decimal("19.99")) == 1999
    assert StripeService.a_centimos(Decimal("100.00")) == 10000


def test_sin_clave_configurada_se_usa_el_simulador():
    servicio = StripeService(api_key="", latencia_simulada_ms=0)
    assert servicio.usa_stripe_real is False


def test_clave_marcador_de_32_caracteres_usa_el_simulador():
    """El `.env` de desarrollo trae un marcador de 32 caracteres, no una clave real de Stripe."""
    servicio = StripeService(api_key="sk_test_placeholder_fashionstore", latencia_simulada_ms=0)
    assert servicio.usa_stripe_real is False


def test_simulador_crea_intento_con_client_secret_determinista():
    servicio = StripeService(api_key="", latencia_simulada_ms=0)
    intento = servicio.crear_intento(Decimal("100.00"), "tarjeta_credito")
    assert intento.referencia.startswith("pi_sbx_")
    assert intento.client_secret == f"{intento.referencia}_secret_sbx"


def test_simulador_verifica_aprobado_por_defecto():
    servicio = StripeService(api_key="", latencia_simulada_ms=0)
    resultado = servicio.verificar_intento("pi_sbx_1")
    assert resultado.aprobado is True
    assert resultado.codigo_respuesta == "succeeded"


def test_simulador_es_determinista_por_escenario_de_prueba():
    """El desenlace del simulador lo fija `escenario_prueba`, no el azar."""
    servicio = StripeService(api_key="", latencia_simulada_ms=0)

    rechazado = servicio.verificar_intento("pi_sbx_1", escenario_prueba="rechazado")
    assert rechazado.aprobado is False
    assert rechazado.codigo_respuesta == "card_declined"

    sin_fondos = servicio.verificar_intento("pi_sbx_1", escenario_prueba="fondos_insuficientes")
    assert sin_fondos.aprobado is False
    assert sin_fondos.codigo_respuesta == "insufficient_funds"


def test_saneado_elimina_datos_sensibles_del_payload():
    sucio = {
        "number": "4111111111111111",
        "cvc": "123",
        "client_secret": "pi_test_123_secret_abc",
        "status": "succeeded",
    }
    limpio = StripeService._sanear(sucio)
    assert limpio["number"] == "[REDACTADO]"
    assert limpio["cvc"] == "[REDACTADO]"
    assert limpio["client_secret"] == "[REDACTADO]"
    assert limpio["status"] == "succeeded"
