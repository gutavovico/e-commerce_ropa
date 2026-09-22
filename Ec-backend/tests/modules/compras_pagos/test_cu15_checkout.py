"""Pruebas de CU15: Comprar desde la plataforma (tramitación del pedido).

Cada prueba cita el escenario Gherkin que verifica, definido en
`.specs/changes/change-carrito-checkout.md`, sección A.6.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.catalogo.modelos import PromocionORM, VentaDetalleORM, VentaORM
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio
from modules.reservas.modelos import MovimientoInventarioORM

PAYLOAD_DOMICILIO = {
    "tipo_venta": "digital_web",
    "tipo_entrega": "domicilio",
    "direccion_envio": "Calle de Claudio Coello 48, 4º B, 28001 Madrid",
}


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con FastAPI."""
    return TestClient(app)


@pytest.fixture
def sesion_autenticada(db, usuario):
    """Inyecta la sesión simulada y el usuario autenticado durante la prueba."""
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db_con_ids(db):
    """Simula la asignación de identificadores que haría PostgreSQL en el flush."""
    contador = {"venta": 0, "detalle": 0}

    def asignar_id(objeto):
        if isinstance(objeto, VentaORM) and objeto.id_venta is None:
            contador["venta"] += 1
            objeto.id_venta = contador["venta"]
        elif isinstance(objeto, VentaDetalleORM) and objeto.id_venta_detalle is None:
            contador["detalle"] += 1
            objeto.id_venta_detalle = contador["detalle"]

    db.add.side_effect = asignar_id
    return db


def repositorio_checkout(*, lineas, inventario, cliente, carrito, promocion=None, usos_ok=True):
    """Sustituye los métodos del repositorio que consume el checkout."""
    return patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_lineas=lambda db, id_carrito: lineas,
        obtener_inventario=lambda db, v, s, cantidad=1, bloquear=False: inventario,
        obtener_promociones_por_producto=lambda db, ids: {},
        obtener_sucursal_activa=lambda db, id_sucursal: None,
        obtener_promocion_por_cupon=lambda db, codigo: promocion,
        consumir_uso_cupon=lambda db, promo: usos_ok,
        vaciar_carrito=lambda db, id_carrito: len(lineas),
    )


def objetos_agregados(db, tipo):
    """Recupera del mock de sesión las entidades de un tipo concreto que se persistieron."""
    return [llamada.args[0] for llamada in db.add.call_args_list
            if isinstance(llamada.args[0], tipo)]


# ---------------------------------------------------------------------------
# Escenario: Tramitación exitosa con entrega a domicilio
# ---------------------------------------------------------------------------


def test_tramitacion_exitosa_crea_venta_pendiente(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Gherkin «Tramitación exitosa»: 201, venta pendiente, líneas y bolsa vaciada."""
    with repositorio_checkout(
        lineas=[linea], inventario=inventario, cliente=usuario.cliente, carrito=carrito
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    assert respuesta.status_code == 201
    datos = respuesta.json()

    assert datos["estado"] == "pendiente"
    assert datos["tipo_venta"] == "digital_web"
    assert datos["tipo_entrega"] == "domicilio"
    assert datos["total"] == "890.00"
    assert datos["total_prendas"] == 1
    assert datos["numero_comprobante"].startswith("FS-")
    # La ventana de garantía viaja en la respuesta para alimentar la cuenta atrás.
    assert datos["expira_en"] is not None

    # Se persistió exactamente una cabecera y una línea.
    ventas = objetos_agregados(db_con_ids, VentaORM)
    detalles = objetos_agregados(db_con_ids, VentaDetalleORM)
    assert len(ventas) == 1
    assert ventas[0].estado == "pendiente"
    assert len(detalles) == 1
    # El precio queda congelado en la línea.
    assert detalles[0].precio_unitario == Decimal("890.00")
    # `subtotal_linea` es GENERATED ALWAYS: no debe escribirse desde el ORM.
    assert detalles[0].subtotal_linea is None


def test_tramitacion_conserva_la_sucursal_de_expedicion_por_linea(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """La boutique de cada prenda sobrevive al paso de bolsa a orden.

    `ventas.id_sucursal` es un único valor, así que sin `venta_detalle.id_sucursal` se perdía
    de qué boutique salía cada prenda: justo lo que necesita logística.
    """
    with repositorio_checkout(
        lineas=[linea], inventario=inventario, cliente=usuario.cliente, carrito=carrito
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    detalles = objetos_agregados(db_con_ids, VentaDetalleORM)
    assert detalles[0].id_sucursal == linea.id_sucursal
    assert respuesta.json()["items"][0]["nombre_sucursal"] == "Atelier Serrano - Madrid"


def test_tramitacion_retiene_existencias_y_audita_el_movimiento(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Las unidades pasan de disponibles a reservadas, con auditoría y responsable."""
    inventario.cantidad_disponible = 2
    inventario.cantidad_reservada = 0
    linea.cantidad = 1

    with repositorio_checkout(
        lineas=[linea], inventario=inventario, cliente=usuario.cliente, carrito=carrito
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    assert respuesta.status_code == 201
    # Retención, no descuento firme: el stock se libera si el pago no llega.
    assert inventario.cantidad_disponible == 1
    assert inventario.cantidad_reservada == 1

    movimientos = objetos_agregados(db_con_ids, MovimientoInventarioORM)
    assert len(movimientos) == 1
    assert movimientos[0].tipo_movimiento == "reserva"
    assert movimientos[0].cantidad == 1
    # La trazabilidad exige saber quién originó el movimiento.
    assert movimientos[0].id_usuario_responsable == usuario.id_usuario
    assert movimientos[0].referencia_documento.startswith("VENTA-")


def test_tramitacion_vacia_la_bolsa(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Tras tramitar, el contenido vive en la orden y la bolsa queda vacía."""
    vaciados = {}

    def vaciar(db, id_carrito):
        vaciados["id"] = id_carrito
        return 1

    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_lineas=lambda db, id_carrito: [linea],
        obtener_inventario=lambda db, v, s, cantidad=1, bloquear=False: inventario,
        obtener_promociones_por_producto=lambda db, ids: {},
        vaciar_carrito=vaciar,
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    assert respuesta.status_code == 201
    assert vaciados["id"] == carrito.id_carrito


# ---------------------------------------------------------------------------
# Escenario: Tramitación con bolsa vacía
# ---------------------------------------------------------------------------


def test_bolsa_vacia_responde_409_y_no_crea_venta(
    client, sesion_autenticada, db_con_ids, usuario, carrito
):
    """Gherkin «Tramitación con bolsa vacía»: 409 y ninguna venta registrada."""
    with repositorio_checkout(
        lineas=[], inventario=None, cliente=usuario.cliente, carrito=carrito
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CARRITO_VACIO"
    assert objetos_agregados(db_con_ids, VentaORM) == []


# ---------------------------------------------------------------------------
# Escenario: Recogida en boutique sin indicar sucursal
# ---------------------------------------------------------------------------


def test_recogida_sin_sucursal_responde_422(client, sesion_autenticada):
    """Gherkin «Recogida sin sucursal»: 422 SUCURSAL_RETIRO_REQUERIDA."""
    respuesta = client.post(
        "/api/v1/ventas/checkout",
        json={"tipo_venta": "digital_web", "tipo_entrega": "recogida_boutique"},
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "SUCURSAL_RETIRO_REQUERIDA"


def test_domicilio_sin_direccion_responde_error(client, sesion_autenticada):
    """La entrega a domicilio exige dirección: sin ella la orden no sería despachable."""
    respuesta = client.post(
        "/api/v1/ventas/checkout",
        json={"tipo_venta": "digital_web", "tipo_entrega": "domicilio"},
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "DIRECCION_REQUERIDA"


def test_recogida_en_boutique_fija_la_sucursal_responsable(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario, sucursal
):
    """En Click & Collect manda la boutique de recogida como sucursal de cabecera."""
    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_lineas=lambda db, id_carrito: [linea],
        obtener_inventario=lambda db, v, s, cantidad=1, bloquear=False: inventario,
        obtener_promociones_por_producto=lambda db, ids: {},
        obtener_sucursal_activa=lambda db, id_sucursal: sucursal,
        vaciar_carrito=lambda db, id_carrito: 1,
    ):
        respuesta = client.post(
            "/api/v1/ventas/checkout",
            json={
                "tipo_venta": "digital_movil",
                "tipo_entrega": "recogida_boutique",
                "id_sucursal_retiro": 1,
            },
        )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["tipo_entrega"] == "recogida_boutique"
    assert datos["nombre_sucursal_retiro"] == "Atelier Serrano - Madrid"

    venta = objetos_agregados(db_con_ids, VentaORM)[0]
    assert venta.id_sucursal == sucursal.id_sucursal
    assert venta.id_sucursal_retiro == sucursal.id_sucursal


# ---------------------------------------------------------------------------
# Escenario: Cupón inválido
# ---------------------------------------------------------------------------


def test_cupon_inexistente_responde_error_y_no_crea_venta(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Gherkin «Cupón inválido»: error CUPON_INVALIDO y ninguna venta creada."""
    with repositorio_checkout(
        lineas=[linea],
        inventario=inventario,
        cliente=usuario.cliente,
        carrito=carrito,
        promocion=None,
    ):
        respuesta = client.post(
            "/api/v1/ventas/checkout", json={**PAYLOAD_DOMICILIO, "codigo_cupon": "NO-EXISTE"}
        )

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "CUPON_INVALIDO"
    assert objetos_agregados(db_con_ids, VentaORM) == []


def test_cupon_valido_aplica_descuento_con_tope(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """El cupón porcentual descuenta sobre la base y respeta su tope máximo."""
    from datetime import date, timedelta

    cupon = PromocionORM(
        id_promocion=1,
        nombre="Bono Atelier de Bienvenida",
        codigo_cupon="MAISON-2025",
        tipo_descuento="porcentaje",
        valor_descuento=Decimal("10.00"),
        tope_descuento=Decimal("50.00"),  # tope por debajo del 10 % de 890
        alcance="global",
        activa=True,
        fecha_inicio=date.today() - timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=30),
        usos_actuales=0,
    )

    with repositorio_checkout(
        lineas=[linea],
        inventario=inventario,
        cliente=usuario.cliente,
        carrito=carrito,
        promocion=cupon,
    ):
        respuesta = client.post(
            "/api/v1/ventas/checkout",
            json={**PAYLOAD_DOMICILIO, "codigo_cupon": "MAISON-2025"},
        )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    # 10 % de 890 = 89,00, pero el tope lo limita a 50,00.
    assert datos["descuento"] == "50.00"
    assert datos["total"] == "840.00"
    assert datos["cupon_aplicado"] == "MAISON-2025"
    assert datos["nombre_promocion"] == "Bono Atelier de Bienvenida"


def test_cupon_con_usos_agotados_responde_error(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Si otro checkout consumió el último uso, el cupón se rechaza.

    El límite se comprueba con un UPDATE condicional atómico, no leyendo y escribiendo después:
    dos compras simultáneas no pueden superar `limite_usos`.
    """
    from datetime import date, timedelta

    cupon = PromocionORM(
        id_promocion=1,
        nombre="Bono Agotado",
        codigo_cupon="MAISON-2025",
        tipo_descuento="porcentaje",
        valor_descuento=Decimal("10.00"),
        alcance="global",
        activa=True,
        fecha_inicio=date.today() - timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=30),
        limite_usos=1,
        usos_actuales=1,
    )

    with repositorio_checkout(
        lineas=[linea],
        inventario=inventario,
        cliente=usuario.cliente,
        carrito=carrito,
        promocion=cupon,
        usos_ok=False,  # el UPDATE condicional no afectó filas
    ):
        respuesta = client.post(
            "/api/v1/ventas/checkout",
            json={**PAYLOAD_DOMICILIO, "codigo_cupon": "MAISON-2025"},
        )

    assert respuesta.status_code == 400
    assert respuesta.json()["code"] == "CUPON_INVALIDO"
    assert "límite de usos" in respuesta.json()["detail"]


# ---------------------------------------------------------------------------
# Escenario: Agotamiento entre la carga de la bolsa y la tramitación
# ---------------------------------------------------------------------------


def test_agotamiento_durante_el_checkout_responde_409(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Gherkin «Agotamiento entre carga y tramitación»: 409 y nada se altera."""
    linea.cantidad = 2
    inventario.cantidad_disponible = 0  # otro cliente se llevó las últimas unidades
    inventario.cantidad_reservada = 0

    with repositorio_checkout(
        lineas=[linea], inventario=inventario, cliente=usuario.cliente, carrito=carrito
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "STOCK_INSUFICIENTE"

    # Ni venta, ni movimiento de inventario, ni alteración del stock.
    assert objetos_agregados(db_con_ids, VentaORM) == []
    assert objetos_agregados(db_con_ids, MovimientoInventarioORM) == []
    assert inventario.cantidad_disponible == 0
    assert inventario.cantidad_reservada == 0


def test_checkout_bloquea_el_inventario_antes_de_escribir(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Prueba de concurrencia: la lectura de inventario debe ser `SELECT ... FOR UPDATE`.

    Sin el bloqueo, dos checkouts simultáneos sobre la última unidad podrían tener éxito ambos
    y dejar el stock en negativo. Se verifica que el servicio pide el bloqueo explícitamente.
    """
    bloqueos = []

    def obtener_inventario(db, id_variante, id_sucursal, cantidad=1, bloquear=False):
        bloqueos.append(bloquear)
        return inventario

    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_lineas=lambda db, id_carrito: [linea],
        obtener_inventario=obtener_inventario,
        obtener_promociones_por_producto=lambda db, ids: {},
        vaciar_carrito=lambda db, id_carrito: 1,
    ):
        respuesta = client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO)

    assert respuesta.status_code == 201
    # La validación previa a la escritura se hace con bloqueo.
    assert bloqueos[0] is True


def test_dos_checkout_simultaneos_sobre_la_ultima_unidad(
    db_con_ids, usuario, carrito, linea, inventario
):
    """Concurrencia: sobre la última unidad, el segundo comprador recibe 409.

    Se simula la serialización que impone `FOR UPDATE`: el primer checkout consume la unidad y
    el segundo encuentra el inventario ya a cero.
    """
    from core.errors import ConflictError
    from modules.compras_pagos.cu15_comprar_plataforma.esquemas import CheckoutIn

    inventario.cantidad_disponible = 1
    inventario.cantidad_reservada = 0
    linea.cantidad = 1

    payload = CheckoutIn(**PAYLOAD_DOMICILIO)

    with repositorio_checkout(
        lineas=[linea], inventario=inventario, cliente=usuario.cliente, carrito=carrito
    ):
        # Primer comprador: obtiene la unidad.
        primera = CheckoutServicio.tramitar_pedido(db_con_ids, usuario, payload)
        assert primera.estado == "pendiente"
        assert inventario.cantidad_disponible == 0
        assert inventario.cantidad_reservada == 1

        # Segundo comprador sobre el mismo inventario ya agotado.
        with pytest.raises(ConflictError) as excinfo:
            CheckoutServicio.tramitar_pedido(db_con_ids, usuario, payload)

    assert excinfo.value.code == "STOCK_INSUFICIENTE"
    # El stock nunca queda negativo.
    assert inventario.cantidad_disponible == 0


# ---------------------------------------------------------------------------
# Escenario: Los importes enviados por el cliente se ignoran
# ---------------------------------------------------------------------------


def test_importes_del_cliente_se_ignoran(
    client, sesion_autenticada, db_con_ids, usuario, carrito, linea, inventario
):
    """Gherkin «Los importes del cliente se ignoran»: manda el cálculo del servidor."""
    with repositorio_checkout(
        lineas=[linea], inventario=inventario, cliente=usuario.cliente, carrito=carrito
    ):
        respuesta = client.post(
            "/api/v1/ventas/checkout",
            json={**PAYLOAD_DOMICILIO, "total": "1.00", "subtotal": "1.00", "descuento": "0.00"},
        )

    assert respuesta.status_code == 201
    assert respuesta.json()["total"] == "890.00"
    assert objetos_agregados(db_con_ids, VentaORM)[0].total == Decimal("890.00")


# ---------------------------------------------------------------------------
# Comprobante y seguridad
# ---------------------------------------------------------------------------


def test_numero_comprobante_usa_la_secuencia_de_postgresql(db_con_ids):
    """El comprobante se deriva de una secuencia, inmune a condiciones de carrera."""
    db_con_ids.execute.return_value.scalar_one.return_value = 42
    numero = CheckoutServicio._generar_numero_comprobante(db_con_ids)

    assert numero.startswith("FS-")
    assert numero.endswith("-000042")

    sql = str(db_con_ids.execute.call_args.args[0])
    assert "nextval" in sql
    assert "seq_comprobante_venta" in sql


def test_checkout_requiere_autenticacion(client):
    """Sin sesión válida, tramitar el pedido responde 401."""
    assert client.post("/api/v1/ventas/checkout", json=PAYLOAD_DOMICILIO).status_code == 401


# ---------------------------------------------------------------------------
# Liberación de la retención (dependencia con CU16)
# ---------------------------------------------------------------------------


def test_liberar_retencion_devuelve_las_unidades_al_stock(
    client, sesion_autenticada, db_con_ids, usuario, inventario
):
    """Una orden no pagada devuelve sus unidades retenidas al stock disponible."""
    inventario.cantidad_disponible = 0
    inventario.cantidad_reservada = 1

    venta = VentaORM(
        id_venta=1,
        numero_comprobante="FS-2026-000001",
        id_cliente=usuario.id_usuario,
        id_sucursal=1,
        tipo_venta="digital_web",
        estado="pendiente",
        subtotal=Decimal("890.00"),
        descuento=Decimal("0.00"),
        total=Decimal("890.00"),
    )
    venta.detalles = [
        VentaDetalleORM(
            id_venta_detalle=1,
            id_venta=1,
            id_variante=102,
            cantidad=1,
            precio_unitario=Decimal("890.00"),
            id_sucursal=1,
        )
    ]
    db_con_ids.execute.return_value.scalars.return_value.first.return_value = venta

    with patch.object(
        CarritoRepositorio,
        "obtener_inventario",
        lambda db, v, s, cantidad=1, bloquear=False: inventario,
    ):
        respuesta = client.post("/api/v1/ventas/1/liberar-retencion")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["unidades_liberadas"] == 1
    assert datos["estado"] == "anulada"

    # El stock vuelve a estar disponible.
    assert inventario.cantidad_disponible == 1
    assert inventario.cantidad_reservada == 0

    movimientos = objetos_agregados(db_con_ids, MovimientoInventarioORM)
    assert movimientos[0].tipo_movimiento == "cancelacion_pedido"


def test_liberar_retencion_de_venta_pagada_responde_409(
    client, sesion_autenticada, db_con_ids, usuario
):
    """Una venta ya pagada no tiene existencias retenidas que liberar."""
    venta = VentaORM(
        id_venta=1,
        numero_comprobante="FS-2026-000001",
        id_sucursal=1,
        tipo_venta="digital_web",
        estado="pagada",
        subtotal=Decimal("890.00"),
        descuento=Decimal("0.00"),
        total=Decimal("890.00"),
    )
    venta.detalles = []
    db_con_ids.execute.return_value.scalars.return_value.first.return_value = venta

    respuesta = client.post("/api/v1/ventas/1/liberar-retencion")

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "VENTA_NO_LIBERABLE"
