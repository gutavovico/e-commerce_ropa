"""Pruebas de CU11: Gestionar carrito de compras (Bolsa de Compra).

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
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu11_gestionar_carrito.servicio import (
    calcular_iva_incluido,
    redondear,
)

from .conftest import ID_LINEA


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


def repositorio(*, lineas, linea=None, inventario=None, variante=None, carrito, cliente):
    """Sustituye los métodos del repositorio que consume el servicio."""
    return patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_lineas=lambda db, id_carrito: lineas,
        obtener_linea=lambda db, id_carrito_detalle: linea,
        obtener_variante=lambda db, id_variante: variante,
        obtener_inventario=lambda db, id_variante, id_sucursal, cantidad=1, bloquear=False: (
            inventario
        ),
        obtener_promociones_por_producto=lambda db, ids: {},
        obtener_sucursal_activa=lambda db, id_sucursal: None,
    )


# ---------------------------------------------------------------------------
# Escenario: Bolsa vacía
# ---------------------------------------------------------------------------


def test_bolsa_vacia_responde_200_con_lista_vacia(
    client, sesion_autenticada, usuario, carrito
):
    """Gherkin «Bolsa vacía»: 200 con items vacío y total 0.00, nunca 404."""
    with repositorio(lineas=[], carrito=carrito, cliente=usuario.cliente):
        respuesta = client.get("/api/v1/carrito")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["items"] == []
    assert datos["resumen"]["total"] == "0.00"
    assert datos["resumen"]["total_prendas"] == 0
    assert datos["expira_en"] is None


# ---------------------------------------------------------------------------
# Escenario: Actualización exitosa de cantidad
# ---------------------------------------------------------------------------


def test_actualizar_cantidad_exitosa_recalcula_resumen(
    client, sesion_autenticada, usuario, carrito, linea, variante, inventario
):
    """Gherkin «Actualización exitosa»: 200, cantidad 2 y resumen recalculado."""
    with repositorio(
        lineas=[linea],
        linea=linea,
        inventario=inventario,
        variante=variante,
        carrito=carrito,
        cliente=usuario.cliente,
    ):
        respuesta = client.patch(f"/api/v1/carrito/items/{ID_LINEA}", json={"cantidad": 2})

    assert respuesta.status_code == 200
    assert linea.cantidad == 2

    resumen = respuesta.json()["resumen"]
    assert resumen["total_prendas"] == 2
    # 890,00 x 2, sin promociones vigentes sobre este producto.
    assert resumen["subtotal"] == "1780.00"
    assert resumen["descuento"] == "0.00"
    assert resumen["total"] == "1780.00"


# ---------------------------------------------------------------------------
# Escenario: Intento de sobrepasar el stock de la sucursal
# ---------------------------------------------------------------------------


def test_sobrepasar_stock_responde_409_y_no_altera_cantidad(
    client, sesion_autenticada, usuario, carrito, linea, variante, inventario
):
    """Gherkin «Intento de sobrepasar el stock»: 409 y la cantidad no cambia."""
    linea.cantidad = 2
    inventario.cantidad_disponible = 2

    with repositorio(
        lineas=[linea],
        linea=linea,
        inventario=inventario,
        variante=variante,
        carrito=carrito,
        cliente=usuario.cliente,
    ):
        respuesta = client.patch(f"/api/v1/carrito/items/{ID_LINEA}", json={"cantidad": 3})

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["code"] == "STOCK_INSUFICIENTE"
    # El mensaje identifica la prenda concreta y las cifras en juego.
    assert "Vestido Plisado en Seda Marfil Natural" in cuerpo["detail"]
    assert "Disponibles: 2" in cuerpo["detail"]
    assert "solicitadas: 3" in cuerpo["detail"]

    # La cantidad almacenada permanece intacta.
    assert linea.cantidad == 2


# ---------------------------------------------------------------------------
# Escenario: Eliminación de una prenda
# ---------------------------------------------------------------------------


def test_eliminar_prenda_purga_la_linea(
    client, sesion_autenticada, db, usuario, carrito, linea
):
    """Gherkin «Eliminación de una prenda»: se borra la línea y se recalcula el total."""
    with repositorio(
        lineas=[],  # tras el borrado la bolsa queda vacía
        linea=linea,
        carrito=carrito,
        cliente=usuario.cliente,
    ):
        respuesta = client.delete(f"/api/v1/carrito/items/{ID_LINEA}")

    assert respuesta.status_code == 200
    db.delete.assert_called_once_with(linea)
    assert respuesta.json()["items"] == []
    assert respuesta.json()["resumen"]["total"] == "0.00"


# ---------------------------------------------------------------------------
# Escenario: Línea perteneciente a otro cliente
# ---------------------------------------------------------------------------


def test_linea_de_otro_cliente_responde_403(
    client, sesion_autenticada, usuario, carrito, linea, variante, inventario
):
    """Gherkin «Línea de otro cliente»: 403 CARRITO_AJENO.

    Se responde 403 y no 404 de forma deliberada: el recurso existe, pero es ajeno.
    """
    linea.carrito.id_cliente = 999

    with repositorio(
        lineas=[linea],
        linea=linea,
        inventario=inventario,
        variante=variante,
        carrito=carrito,
        cliente=usuario.cliente,
    ):
        respuesta = client.patch(f"/api/v1/carrito/items/{ID_LINEA}", json={"cantidad": 1})

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "CARRITO_AJENO"


def test_linea_inexistente_responde_404(
    client, sesion_autenticada, usuario, carrito
):
    """Una línea que no existe en ninguna bolsa responde 404."""
    with repositorio(lineas=[], linea=None, carrito=carrito, cliente=usuario.cliente):
        respuesta = client.delete("/api/v1/carrito/items/9999")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "LINEA_NO_ENCONTRADA"


# ---------------------------------------------------------------------------
# Alta de prendas en la bolsa (ampliación de alcance §0.2)
# ---------------------------------------------------------------------------


def test_agregar_item_consolida_si_la_prenda_ya_estaba(
    client, sesion_autenticada, db, usuario, carrito, linea, variante, inventario, sucursal
):
    """Añadir la misma variante y boutique suma cantidades en vez de duplicar la línea.

    Duplicar violaría la restricción de unicidad de `carrito_detalle` y descuadraría el
    inventario al tramitar el pedido.
    """
    linea.cantidad = 1
    inventario.cantidad_disponible = 5

    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_variante=lambda db, id_variante: variante,
        obtener_sucursal_activa=lambda db, id_sucursal: sucursal,
        buscar_linea_equivalente=lambda db, c, v, s: linea,
        obtener_inventario=lambda db, v, s, cantidad=1, bloquear=False: inventario,
        obtener_lineas=lambda db, id_carrito: [linea],
        obtener_promociones_por_producto=lambda db, ids: {},
    ):
        respuesta = client.post(
            "/api/v1/carrito/items",
            json={"id_variante": 102, "cantidad": 2, "id_sucursal": 1},
        )

    assert respuesta.status_code == 201
    # 1 existente + 2 añadidas, en una sola línea.
    assert linea.cantidad == 3
    db.add.assert_not_called()
    assert len(respuesta.json()["items"]) == 1


def test_agregar_item_sin_stock_responde_409(
    client, sesion_autenticada, usuario, carrito, variante, inventario, sucursal
):
    """Añadir más unidades de las disponibles en la boutique responde 409."""
    inventario.cantidad_disponible = 1

    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_variante=lambda db, id_variante: variante,
        obtener_sucursal_activa=lambda db, id_sucursal: sucursal,
        buscar_linea_equivalente=lambda db, c, v, s: None,
        obtener_inventario=lambda db, v, s, cantidad=1, bloquear=False: inventario,
    ):
        respuesta = client.post(
            "/api/v1/carrito/items",
            json={"id_variante": 102, "cantidad": 3, "id_sucursal": 1},
        )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "STOCK_INSUFICIENTE"


def test_agregar_variante_inexistente_responde_404(
    client, sesion_autenticada, usuario, carrito
):
    """Una variante que no está en catálogo responde 404."""
    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_variante=lambda db, id_variante: None,
    ):
        respuesta = client.post(
            "/api/v1/carrito/items", json={"id_variante": 999999, "cantidad": 1}
        )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "VARIANTE_NO_ENCONTRADA"


# ---------------------------------------------------------------------------
# Contrato y seguridad
# ---------------------------------------------------------------------------


def test_cantidad_cero_responde_422(client, sesion_autenticada):
    """Para vaciar una línea se usa DELETE, no `cantidad: 0`."""
    respuesta = client.patch(f"/api/v1/carrito/items/{ID_LINEA}", json={"cantidad": 0})
    assert respuesta.status_code == 422


def test_carrito_requiere_autenticacion(client):
    """Sin sesión válida, la bolsa responde 401."""
    assert client.get("/api/v1/carrito").status_code == 401


# ---------------------------------------------------------------------------
# Cálculo financiero
# ---------------------------------------------------------------------------


def test_iva_incluido_se_desglosa_sobre_el_total():
    """El IVA va incluido en el precio: se desglosa para mostrarlo, no se suma."""
    # 1.940,00 / 1,21 = 1.603,31 -> IVA contenido = 336,69
    assert calcular_iva_incluido(Decimal("1940.00")) == Decimal("336.69")
    assert calcular_iva_incluido(Decimal("0.00")) == Decimal("0.00")


def test_redondeo_comercial_a_dos_decimales():
    """Los importes se redondean a céntimo con redondeo comercial."""
    assert redondear(Decimal("10.005")) == Decimal("10.01")
    assert redondear(Decimal("10.004")) == Decimal("10.00")


def test_subtotal_menos_descuento_es_siempre_el_total(
    client, sesion_autenticada, usuario, carrito, linea, variante, inventario
):
    """Con promoción vigente, `subtotal` agrega precios de lista y `total = subtotal - descuento`.

    Es la invariante que hace coherentes las columnas `subtotal`/`descuento`/`total` de `ventas`.
    La maqueta rotulaba el subtotal ya descontado y luego restaba el descuento otra vez.
    """
    with patch.multiple(
        CarritoRepositorio,
        asegurar_cliente=lambda db, usuario: usuario.cliente,
        obtener_o_crear_carrito=lambda db, id_cliente: carrito,
        obtener_lineas=lambda db, id_carrito: [linea],
        obtener_inventario=lambda db, v, s, cantidad=1, bloquear=False: inventario,
        # 15 % de Membresía Privé sobre el producto 1.
        obtener_promociones_por_producto=lambda db, ids: {
            1: (Decimal("15.00"), "Membresia Prive")
        },
    ):
        respuesta = client.get("/api/v1/carrito")

    resumen = respuesta.json()["resumen"]
    assert resumen["subtotal"] == "890.00"       # precio de lista
    assert resumen["descuento"] == "133.50"      # 15 %
    assert resumen["total"] == "756.50"          # subtotal - descuento

    item = respuesta.json()["items"][0]
    assert item["precio_lista"] == "890.00"
    assert item["precio_unitario"] == "756.50"
    assert item["motivo_descuento"] == "Membresia Prive"
