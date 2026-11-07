"""Pruebas de CU17: Consultar historial de compras."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.compras_pagos.cu11_gestionar_carrito.repositorio import CarritoRepositorio
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.compras_pagos.cu17_historial_compras.repositorio import (
    RepositorioHistorialCompras,
)
from modules.compras_pagos.modelos import PagoORM, VentaDetalleORM, VentaORM


@pytest.fixture
def client():
    """Cliente HTTP para pruebas contra FastAPI."""
    return TestClient(app)


@pytest.fixture
def sesion_autenticada(db, usuario):
    """Inyecta la sesión simulada y el usuario autenticado durante la prueba."""
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario
    yield
    app.dependency_overrides.clear()


def _construir_venta(
    *,
    id_venta: int,
    comprobante: str,
    id_cliente: int,
    estado: str,
    fecha_venta: datetime,
    sucursal,
    variante,
    metodo_pago: str = "tarjeta_credito",
    estado_pago: str = "confirmado",
    referencia: str = "pi_test_123",
) -> VentaORM:
    venta = VentaORM(
        id_venta=id_venta,
        numero_comprobante=comprobante,
        id_cliente=id_cliente,
        id_sucursal=sucursal.id_sucursal,
        tipo_venta="digital_web",
        estado=estado,
        subtotal=Decimal("890.00"),
        descuento=Decimal("0.00"),
        total=Decimal("890.00"),
        fecha_venta=fecha_venta,
        tipo_entrega="domicilio",
        direccion_envio="Av. San Martín #450",
    )
    venta.sucursal = sucursal
    venta.sucursal_retiro = None
    venta.promocion = None

    detalle = VentaDetalleORM(
        id_venta_detalle=id_venta * 10,
        id_venta=id_venta,
        id_variante=variante.id_variante,
        cantidad=1,
        precio_unitario=Decimal("890.00"),
        subtotal_linea=Decimal("890.00"),
        id_sucursal=sucursal.id_sucursal,
    )
    detalle.variante = variante
    detalle.sucursal = sucursal
    venta.detalles = [detalle]

    pago = PagoORM(
        id_pago=id_venta * 100,
        id_venta=id_venta,
        metodo_pago=metodo_pago,
        monto=Decimal("890.00"),
        estado=estado_pago,
        referencia_pasarela=referencia,
        creado_en=fecha_venta,
    )
    venta.pagos = [pago]
    return venta


def test_historial_compras_devuelve_pedidos_y_desglose(
    client, sesion_autenticada, usuario, sucursal, variante
):
    """REQ-CU17-01: Retorna compras del cliente con su desglose y conteos."""
    ahora = datetime.now(timezone.utc)
    venta_pagada = _construir_venta(
        id_venta=20,
        comprobante="FS-2026-000020",
        id_cliente=usuario.id_usuario,
        estado="pagada",
        fecha_venta=ahora,
        sucursal=sucursal,
        variante=variante,
    )
    venta_anulada = _construir_venta(
        id_venta=19,
        comprobante="FS-2026-000019",
        id_cliente=usuario.id_usuario,
        estado="anulada",
        fecha_venta=ahora - timedelta(days=2),
        sucursal=sucursal,
        variante=variante,
        estado_pago="rechazado",
    )

    with patch.object(
        RepositorioHistorialCompras,
        "listar_ventas_cliente",
        return_value=[venta_pagada, venta_anulada],
    ):
        respuesta = client.get("/api/v1/ventas/mias")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["total_pedidos"] == 2
    assert datos["pedidos_completados"] == 1
    assert len(datos["pedidos"]) == 2

    primero = datos["pedidos"][0]
    assert primero["id_venta"] == 20
    assert primero["numero_comprobante"] == "FS-2026-000020"
    assert primero["estado"] == "pagada"
    assert primero["total"] == "890.00"
    assert primero["metodo_pago"] == "tarjeta_credito"
    assert primero["referencia_pasarela"] == "pi_test_123"
    assert primero["nombre_sucursal"] == "Atelier Serrano - Madrid"
    assert len(primero["items"]) == 1

    item = primero["items"][0]
    assert item["sku"] == "ATEL-2025-V09-IV-38"
    assert item["nombre_producto"] == "Vestido Plisado en Seda Marfil Natural"
    assert item["talla"] == "38"
    assert item["color"] == "Seda Marfil"
    assert item["color_hex"] == "#F5F0EA"
    assert item["cantidad"] == 1
    assert item["precio_unitario"] == "890.00"
    assert item["subtotal_linea"] == "890.00"


def test_historial_compras_vacio_devuelve_lista_vacia(
    client, sesion_autenticada, usuario
):
    """REQ-CU17-04: Cliente sin compras recibe 200 OK con lista vacía y contadores en 0."""
    with patch.object(
        RepositorioHistorialCompras,
        "listar_ventas_cliente",
        return_value=[],
    ):
        respuesta = client.get("/api/v1/ventas/mias")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "total_pedidos": 0,
        "pedidos_completados": 0,
        "pedidos": [],
    }


def test_historial_compras_expira_orden_pendiente_vencida(
    client, sesion_autenticada, usuario, sucursal, variante, inventario
):
    """Una orden pendiente cuyo plazo venció se anula y libera stock al consultar el historial."""
    hace_una_hora = CarritoRepositorio.ahora_utc() - timedelta(hours=1)
    inventario.cantidad_disponible = 1
    inventario.cantidad_reservada = 1

    venta_vencida = _construir_venta(
        id_venta=30,
        comprobante="FS-2026-000030",
        id_cliente=usuario.id_usuario,
        estado="pendiente",
        fecha_venta=hace_una_hora,
        sucursal=sucursal,
        variante=variante,
        estado_pago="pendiente",
    )

    with patch.object(
        RepositorioHistorialCompras,
        "listar_ventas_cliente",
        return_value=[venta_vencida],
    ), patch.object(
        PagoServicio,
        "_calcular_expiracion",
        staticmethod(lambda db, v: CarritoRepositorio.ahora_utc() - timedelta(minutes=5)),
    ), patch.object(
        CarritoRepositorio,
        "obtener_inventario",
        lambda db, v, s, cantidad=0, bloquear=False: inventario,
    ):
        respuesta = client.get("/api/v1/ventas/mias")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["pedidos"][0]["estado"] == "anulada"
    assert inventario.cantidad_disponible == 2
    assert inventario.cantidad_reservada == 0


def test_historial_compras_requiere_autenticacion(client):
    """REQ-CU17-02: Sin sesión válida responde 401."""
    respuesta = client.get("/api/v1/ventas/mias")
    assert respuesta.status_code == 401

