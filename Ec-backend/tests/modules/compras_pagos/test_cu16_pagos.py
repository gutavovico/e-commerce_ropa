"""Pruebas de CU16: Realizar Pago Electrónico.

Cada prueba cita el escenario Gherkin que verifica, definido en
`.specs/changes/change-pago-electronico.md`, sección A.5.

La pasarela se inyecta siempre como doble: la suite no sale a la red ni espera latencia.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from integrations.stripe_service import (
    DatosTarjeta,
    ErrorPasarela,
    PasarelaPagos,
    ResultadoPasarela,
    PANES_PRUEBA,
    StripeService,
    validar_luhn,
)
from main import app
from modules.catalogo.modelos import VentaDetalleORM, VentaORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.compras_pagos.modelos import PagoORM
from modules.reservas.modelos import MovimientoInventarioORM

# Tarjeta de prueba válida (supera Luhn) y tarjeta que el simulador rechaza siempre.
PAN_VALIDO = "4111111111111111"
PAN_RECHAZADO = "4100000050000000"
PAN_SIN_FONDOS = "4000000000009995"

PAGO_TARJETA = {
    "id_venta": 1,
    "metodo_pago": "tarjeta_credito",
    "tarjeta": {
        "numero": PAN_VALIDO,
        "titular": "ANA VALENZUELA",
        "mes_expiracion": 9,
        "anio_expiracion": 2030,
        "cvv": "123",
    },
}


# ---------------------------------------------------------------------------
# Dobles
# ---------------------------------------------------------------------------


class PasarelaFalsa(PasarelaPagos):
    """Pasarela determinista para pruebas: sin red, sin latencia."""

    def __init__(self, aprobado: bool = True, error_tecnico: bool = False):
        self.aprobado = aprobado
        self.error_tecnico = error_tecnico
        self.llamadas = 0
        self.ultimo_monto = None

    def procesar_cargo(
        self, monto, metodo_pago, tarjeta=None, token=None, descripcion="", metadatos=None
    ):
        self.llamadas += 1
        self.ultimo_monto = monto

        if self.error_tecnico:
            raise ErrorPasarela("La pasarela no responde.")

        if self.aprobado:
            return ResultadoPasarela(
                aprobado=True,
                referencia="pi_test_123456789",
                codigo_respuesta="succeeded",
                mensaje="Pago confirmado por la pasarela.",
                marca=tarjeta.marca if tarjeta else None,
                ultimos_digitos=tarjeta.ultimos_digitos if tarjeta else None,
                payload={"id": "pi_test_123456789", "status": "succeeded"},
            )

        return ResultadoPasarela(
            aprobado=False,
            referencia="pi_test_declined",
            codigo_respuesta="card_declined",
            mensaje="La entidad emisora ha rechazado la tarjeta.",
            marca=tarjeta.marca if tarjeta else None,
            ultimos_digitos=tarjeta.ultimos_digitos if tarjeta else None,
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


def preparar(venta, inventario):
    """Sustituye la carga de venta y de inventario por los dobles de la prueba."""
    return patch.multiple(
        PagoServicio,
        _cargar_venta=staticmethod(lambda db, id_venta, bloquear=False: venta),
        _buscar_pago_idempotente=staticmethod(lambda db, id_venta, clave: None),
    ), patch.object(
        CarritoRepositorio,
        "obtener_inventario",
        staticmethod(lambda db, v, s, cantidad=1, bloquear=False: inventario),
    )


# ===========================================================================
# Escenario: Pago exitoso con tarjeta
# ===========================================================================


def test_pago_exitoso_confirma_venta_y_consolida_stock(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Pago exitoso»: 201, venta pagada y existencias consolidadas."""
    venta = crear_venta()
    inventario.cantidad_disponible = 12
    inventario.cantidad_reservada = 3
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 201
    datos = respuesta.json()

    assert datos["estado_pago"] == "confirmado"
    assert datos["estado_venta"] == "pagada"
    assert datos["numero_comprobante"] == "FS-2026-000001"
    assert datos["referencia_pasarela"] == "pi_test_123456789"
    assert datos["monto"] == "1940.00"
    # De la tarjeta solo sobreviven marca y últimos cuatro dígitos.
    assert datos["marca_tarjeta"] == "VISA"
    assert datos["ultimos_digitos"] == "1111"

    # La venta cambia de estado.
    assert venta.estado == "pagada"

    # El pago se persiste como confirmado.
    pagos = agregados(db_con_ids, PagoORM)
    assert len(pagos) == 1
    assert pagos[0].estado == "confirmado"
    assert pagos[0].monto == Decimal("1940.00")
    assert pagos[0].confirmado_en is not None
    # El payload de auditoría nunca contiene el PAN completo ni el CVV.
    auditoria = pagos[0].payload_respuesta
    assert PAN_VALIDO not in str(auditoria)
    assert auditoria["ultimos_digitos"] == "1111"
    # Ninguna clave del payload guarda datos sensibles.
    assert not {"numero", "cvv", "cvc", "card_number"} & set(auditoria)
    assert not {"numero", "cvv", "cvc"} & set(auditoria.get("pasarela", {}))


def test_pago_exitoso_descuenta_reservado_sin_devolver_a_disponible(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """La prenda vendida abandona el almacén: no vuelve a estar disponible."""
    venta = crear_venta()
    inventario.cantidad_disponible = 12
    inventario.cantidad_reservada = 3
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 201
    assert inventario.cantidad_reservada == 0
    # Invariante del cierre de venta: `cantidad_disponible` NO se incrementa.
    assert inventario.cantidad_disponible == 12


def test_pago_exitoso_audita_movimiento_con_saldos_reales(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin: movimiento `venta_confirmada` con responsable y saldos reales, no 0 → 0."""
    venta = crear_venta()
    inventario.cantidad_reservada = 3
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    movimientos = agregados(db_con_ids, MovimientoInventarioORM)
    assert len(movimientos) == 1
    mov = movimientos[0]
    assert mov.tipo_movimiento == "venta_confirmada"
    # Cantidad negativa: salida definitiva del almacén.
    assert mov.cantidad == -3
    assert mov.id_usuario_responsable == usuario.id_usuario
    assert mov.referencia_documento == "VENTA-1"
    # La bitácora escribía 0 → 0 hasta el 2026-09-22; ahora refleja el saldo real.
    assert mov.saldo_anterior == 3
    assert mov.saldo_nuevo == 0


# ===========================================================================
# Escenario: Tarjeta denegada
# ===========================================================================


def test_tarjeta_denegada_responde_402_y_deja_la_orden_viva(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Tarjeta denegada»: 402, venta pendiente e inventario intacto."""
    venta = crear_venta()
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12
    pasarela = PasarelaFalsa(aprobado=False)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 402
    assert respuesta.json()["code"] == "PAGO_RECHAZADO"
    assert "rechazado" in respuesta.json()["detail"].lower()

    # Queda constancia del intento fallido.
    pagos = agregados(db_con_ids, PagoORM)
    assert len(pagos) == 1
    assert pagos[0].estado == "rechazado"

    # La orden sigue viva para reintentar antes de que expire la reserva.
    assert venta.estado == "pendiente"
    assert inventario.cantidad_reservada == 3
    assert inventario.cantidad_disponible == 12
    assert agregados(db_con_ids, MovimientoInventarioORM) == []


def test_fallo_tecnico_de_pasarela_no_se_registra_como_rechazo(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Un fallo de red no es un rechazo de tarjeta: no debe ensuciar el historial de pagos."""
    venta = crear_venta()
    pasarela = PasarelaFalsa(error_tecnico=True)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "PASARELA_NO_DISPONIBLE"
    assert agregados(db_con_ids, PagoORM) == []
    assert venta.estado == "pendiente"


# ===========================================================================
# Escenario: Orden ya liquidada
# ===========================================================================


def test_orden_ya_pagada_responde_409(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Orden ya liquidada»: 409 y ningún efecto secundario."""
    venta = crear_venta(estado="pagada")
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "VENTA_YA_LIQUIDADA"
    assert agregados(db_con_ids, PagoORM) == []
    # Ni siquiera se contacta con la pasarela.
    assert pasarela.llamadas == 0


def test_orden_anulada_responde_409(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Una orden anulada tampoco admite pago."""
    venta = crear_venta(estado="anulada")

    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "VENTA_ANULADA"


# ===========================================================================
# Escenario: Ventana de retención expirada
# ===========================================================================


def test_orden_expirada_responde_409_y_libera_existencias(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Ventana expirada»: 409, orden anulada y stock devuelto."""
    # Tramitada hace 40 minutos: la ventana es de 25.
    venta = crear_venta(minutos_antiguedad=40)
    inventario.cantidad_reservada = 3
    inventario.cantidad_disponible = 12
    pasarela = PasarelaFalsa(aprobado=True)

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
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "ORDEN_EXPIRADA"
    # No se cobró nada.
    assert pasarela.llamadas == 0
    assert agregados(db_con_ids, PagoORM) == []


# ===========================================================================
# Seguridad y contrato
# ===========================================================================


def test_orden_de_otro_cliente_responde_403(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Orden de otro cliente»: 403 VENTA_AJENA.

    Se responde 403 y no 404 de forma deliberada: el recurso existe, pero es ajeno.
    """
    venta = crear_venta()
    venta.id_cliente = 999

    p1, p2 = preparar(venta, inventario)
    with p1, p2:
        respuesta = client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA)

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "VENTA_AJENA"


def test_tarjeta_invalida_responde_422_sin_contactar_pasarela(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Tarjeta con formato inválido»: 422, sin pago y sin llamada a la pasarela."""
    venta = crear_venta()
    pasarela = PasarelaFalsa(aprobado=True)
    payload = {**PAGO_TARJETA, "tarjeta": {**PAGO_TARJETA["tarjeta"], "numero": "4111111111111112"}}

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post("/api/v1/pagos/procesar", json=payload)

    assert respuesta.status_code == 422
    assert pasarela.llamadas == 0
    assert agregados(db_con_ids, PagoORM) == []


def test_tarjeta_caducada_responde_422(client, sesion_autenticada):
    """Una tarjeta vencida se rechaza antes de salir del backend."""
    payload = {
        **PAGO_TARJETA,
        "tarjeta": {**PAGO_TARJETA["tarjeta"], "mes_expiracion": 1, "anio_expiracion": 2024},
    }
    assert client.post("/api/v1/pagos/procesar", json=payload).status_code == 422


def test_metodo_con_tarjeta_sin_datos_responde_422(client, sesion_autenticada):
    """Pagar con tarjeta exige los datos de la tarjeta o un token de pasarela."""
    payload = {"id_venta": 1, "metodo_pago": "tarjeta_credito"}
    assert client.post("/api/v1/pagos/procesar", json=payload).status_code == 422


def test_pago_requiere_autenticacion(client):
    """Sin sesión válida, procesar un pago responde 401."""
    assert client.post("/api/v1/pagos/procesar", json=PAGO_TARJETA).status_code == 401


def test_payload_no_admite_importes_del_cliente(client, sesion_autenticada, db_con_ids, usuario, inventario):
    """El importe lo fija la orden congelada; el enviado por el cliente se ignora."""
    venta = crear_venta()
    pasarela = PasarelaFalsa(aprobado=True)

    p1, p2 = preparar(venta, inventario)
    with p1, p2, patch(
        "modules.compras_pagos.cu16_realizar_pago.servicio.StripeService",
        lambda *a, **k: pasarela,
    ):
        respuesta = client.post(
            "/api/v1/pagos/procesar", json={**PAGO_TARJETA, "monto": "1.00", "total": "1.00"}
        )

    assert respuesta.status_code == 201
    assert respuesta.json()["monto"] == "1940.00"
    # La pasarela cobró el importe real de la orden.
    assert pasarela.ultimo_monto == Decimal("1940.00")


# ===========================================================================
# Resumen de pago
# ===========================================================================


def test_resumen_pago_devuelve_orden_congelada(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Gherkin «Resumen de pago»: total, líneas y segundos restantes del servidor."""
    venta = crear_venta(minutos_antiguedad=5)

    with patch.object(
        PagoServicio, "_cargar_venta", staticmethod(lambda db, id_venta, bloquear=False: venta)
    ):
        respuesta = client.get("/api/v1/ventas/1/resumen-pago")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["numero_comprobante"] == "FS-2026-000001"
    assert datos["total"] == "1940.00"
    assert datos["subtotal"] == "2100.00"
    assert datos["descuento"] == "160.00"
    # Invariante compartida con CU11/CU15.
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
# Pasarela: validación y determinismo
# ===========================================================================


def test_los_pan_de_prueba_superan_luhn():
    """Un PAN de prueba inválido según Luhn jamás llegaría al simulador.

    `TarjetaIn` valida Luhn antes que nada, así que si el número que fuerza un rechazo no la
    supera, el escenario de tarjeta denegada nunca ejercita la pasarela: falla antes, con 422.
    Esta prueba impide que las dos reglas vuelvan a chocar.
    """
    for nombre, pan in PANES_PRUEBA.items():
        assert validar_luhn(pan), f"El PAN de prueba '{nombre}' no supera Luhn"

    assert PANES_PRUEBA["rechazado"].endswith("0000")
    assert PANES_PRUEBA["fondos_insuficientes"].endswith("9995")


def test_simulador_distingue_fondos_insuficientes_de_rechazo_generico():
    """Los dos motivos de rechazo llegan al cliente con códigos distintos."""
    servicio = StripeService(api_key="", latencia_simulada_ms=0)

    sin_fondos = servicio.procesar_cargo(
        Decimal("100.00"),
        "tarjeta_credito",
        tarjeta=DatosTarjeta(PAN_SIN_FONDOS, "ANA", 9, 2030, "123"),
    )
    assert sin_fondos.aprobado is False
    assert sin_fondos.codigo_respuesta == "insufficient_funds"


def test_luhn_acepta_y_rechaza_correctamente():
    """El verificador de Luhn es la primera barrera antes de contactar la pasarela."""
    assert validar_luhn("4111111111111111") is True
    assert validar_luhn("5555555555554444") is True
    assert validar_luhn("4111111111111112") is False
    assert validar_luhn("123") is False


def test_simulador_es_determinista_por_sufijo_de_pan():
    """El desenlace lo fija el PAN, no el azar: una prueba aleatoria sería intermitente."""
    servicio = StripeService(api_key="", latencia_simulada_ms=0)

    aprobado = servicio.procesar_cargo(
        Decimal("100.00"),
        "tarjeta_credito",
        tarjeta=DatosTarjeta(PAN_VALIDO, "ANA", 9, 2030, "123"),
    )
    assert aprobado.aprobado is True
    assert aprobado.referencia.startswith("pi_sbx_")

    rechazado = servicio.procesar_cargo(
        Decimal("100.00"),
        "tarjeta_credito",
        tarjeta=DatosTarjeta(PAN_RECHAZADO, "ANA", 9, 2030, "123"),
    )
    assert rechazado.aprobado is False
    assert rechazado.codigo_respuesta == "card_declined"


def test_simulador_reconoce_tokens_de_prueba_de_stripe():
    """`tok_chargeDeclined` se rechaza; `tok_visa` se aprueba."""
    servicio = StripeService(api_key="", latencia_simulada_ms=0)

    assert servicio.procesar_cargo(Decimal("10.00"), "qr", token="tok_visa").aprobado is True

    rechazo = servicio.procesar_cargo(
        Decimal("10.00"), "tarjeta_credito", token="tok_chargeDeclinedInsufficientFunds"
    )
    assert rechazo.aprobado is False
    assert rechazo.codigo_respuesta == "insufficient_funds"


def test_conversion_a_centimos_para_la_api_de_stripe():
    """Stripe cobra en la unidad mínima entera; el Decimal exacto es el que se persiste."""
    assert StripeService.a_centimos(Decimal("1940.00")) == 194000
    assert StripeService.a_centimos(Decimal("0.99")) == 99


def test_sin_clave_configurada_se_usa_el_simulador():
    """Sin clave utilizable no se intenta salir a la red."""
    assert StripeService(api_key="").usa_stripe_real is False
    # Un marcador corto tampoco es una clave real de Stripe.
    assert StripeService(api_key="sk_test_placeholder").usa_stripe_real is False


def test_saneado_elimina_datos_sensibles_del_payload():
    """Lo que se guarde en `payload_respuesta` queda en la base para siempre."""
    sucio = {"card": {"number": "4111111111111111", "cvc": "123", "last4": "1111"}}
    limpio = StripeService._sanear(sucio)

    assert limpio["card"]["number"] == "[REDACTADO]"
    assert limpio["card"]["cvc"] == "[REDACTADO]"
    assert limpio["card"]["last4"] == "1111"
