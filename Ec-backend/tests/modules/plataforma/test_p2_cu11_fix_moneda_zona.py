"""Pruebas del fix de P2-CU11 · Moneda y zona horaria de Bolivia, sin base de datos.

Spec: `.specs/finalized/P2-CU11-fix-moneda-zona-bolivia/spec.md` §6. Lo que depende de PostgreSQL
(migración 0016, `TimeZone` de la sesión, 409 con ventas reales) está en
`tests/integracion/test_multitenant.py`.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core import tiempo
from core.moneda import TASA_IVA, formatear_importe
from integrations.stripe_service import StripeService
from modules.autenticacion_seguridad.cu02_iniciar_sesion.esquemas import TenantSesionOut
from modules.compras_pagos.cu31_cu32_punto_venta import servicio as pos
from modules.compras_pagos.cu31_cu32_punto_venta.comprobante_pdf import _renglones
from modules.plataforma.cu02_acceso_empresa.esquemas import EmpresaOut
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio

BOLIVIA = timezone(timedelta(hours=-4))


class _Reloj(datetime):
    """`datetime.now` fijo: 2026-11-09 a las 22:30 en Bolivia (02:30 del 10 en UTC)."""

    @classmethod
    def now(cls, tz=None):
        fijo = datetime(2026, 11, 10, 2, 30, tzinfo=timezone.utc)
        return fijo.astimezone(tz) if tz else fijo.replace(tzinfo=None)


@pytest.fixture
def noche_en_bolivia(monkeypatch):
    monkeypatch.setattr(tiempo, "datetime", _Reloj)


# ------------------------------------------------------------------ M5: hora de Bolivia

def test_a_las_22_de_bolivia_hoy_sigue_siendo_el_mismo_dia(noche_en_bolivia):
    assert tiempo.ahora().date().isoformat() == "2026-11-10"  # en UTC ya es mañana
    assert tiempo.hoy().isoformat() == "2026-11-09"
    inicio = tiempo.inicio_del_dia()
    assert inicio.utcoffset() == timedelta(hours=-4)
    assert inicio.astimezone(timezone.utc) == datetime(2026, 11, 9, 4, 0, tzinfo=timezone.utc)


def test_la_caja_lista_las_ventas_desde_la_medianoche_de_bolivia(noche_en_bolivia, monkeypatch):
    desde_recibido = {}
    monkeypatch.setattr(pos.PuntoVentaServicio, "resolver_sucursal", staticmethod(lambda db, u, s: 3))
    monkeypatch.setattr(pos.PuntoVentaServicio, "_vencer_pendientes", staticmethod(lambda db, u, s: None))
    monkeypatch.setattr(
        pos.PuntoVentaRepositorio, "listar_ventas",
        staticmethod(lambda db, s, e, desde: desde_recibido.setdefault("desde", desde) and []),
    )
    pos.PuntoVentaServicio.listar_ventas(MagicMock(), SimpleNamespace(rol="cajero"), None, None, True)
    assert desde_recibido["desde"].astimezone(timezone.utc) == datetime(2026, 11, 9, 4, 0, tzinfo=timezone.utc)


# ------------------------------------------------------------------ M8 y M9: formato e IVA

@pytest.mark.parametrize("valor, moneda, esperado", [
    (Decimal("1234.5"), "BOB", "Bs 1.234,50"),
    (Decimal("120"), "BOB", "Bs 120,00"),
    (Decimal("0.005"), "USD", "US$ 0,01"),
    ("98765.43", "USD", "US$ 98.765,43"),
])
def test_formato_de_importes(valor, moneda, esperado):
    assert formatear_importe(valor, moneda) == esperado


def test_iva_de_bolivia():
    assert TASA_IVA == Decimal("0.13")


def test_comprobante_pdf_en_la_moneda_de_la_empresa():
    from modules.compras_pagos.cu31_cu32_punto_venta.esquemas import LineaVentaPosOut, PagoPosOut, VentaPosOut

    ahora = datetime(2026, 11, 9, 12, 30, tzinfo=timezone.utc)
    venta = VentaPosOut(
        id_venta=500, numero_comprobante="FS-2026-000099", estado="pagada", fecha_venta=ahora, id_sucursal=1,
        nombre_sucursal="Centro", direccion_sucursal="Calle 1", cajero_nombre="Caja Uno",
        subtotal=Decimal("120.00"), descuento=Decimal("0.00"), total=Decimal("120.00"), iva_incluido=Decimal("13.81"),
        lineas=[LineaVentaPosOut(id_variante=1, sku="FS-1", nombre_producto="Blusa", talla_codigo="M",
                                 color_nombre="Rojo", cantidad=1, precio_lista=Decimal("120.00"),
                                 precio_unitario=Decimal("120.00"), subtotal_linea=Decimal("120.00"), origen="caja")],
        pagos=[PagoPosOut(id_pago=1, metodo_pago="efectivo", monto=Decimal("120.00"), estado="confirmado",
                          monto_recibido=Decimal("150.00"), cambio=Decimal("30.00"), creado_en=ahora)],
    )
    texto = str(_renglones(venta, "USD"))
    assert "US$ 120,00" in texto and "US$ 30,00" in texto
    assert "IVA (13 %) incluido" in texto
    assert "€" not in texto


# ------------------------------------------------------------------ M6 y M7: moneda en contratos y Stripe

def test_la_moneda_viaja_en_los_datos_de_la_empresa():
    assert EmpresaOut(codigo="fashionstore", nombre="FASHION STORE").moneda == "BOB"
    assert EmpresaOut(codigo="m", nombre="M", moneda="USD").moneda == "USD"
    assert TenantSesionOut(codigo="m", nombre="M", moneda="USD").model_dump()["moneda"] == "USD"


def test_sin_empresa_en_la_sesion_la_moneda_es_la_por_defecto():
    assert ParametrosEmpresaServicio.moneda(MagicMock()) == "BOB"


def test_el_simulador_de_stripe_cobra_en_la_moneda_indicada():
    servicio = StripeService(api_key="", latencia_simulada_ms=0)
    assert servicio.crear_intento(Decimal("100.00"), "tarjeta_credito").payload["currency"] == "bob"
    assert servicio.crear_intento(Decimal("100.00"), "tarjeta_credito", moneda="USD").payload["currency"] == "usd"


def test_stripe_real_recibe_la_moneda_de_la_empresa(monkeypatch):
    import stripe

    recibido = {}

    def crear(**kwargs):
        recibido.update(kwargs)
        return {"id": "pi_x", "client_secret": "pi_x_secret", "status": "requires_payment_method"}

    monkeypatch.setattr(stripe.PaymentIntent, "create", staticmethod(crear))
    servicio = StripeService(api_key="sk_test_" + "a" * 99, latencia_simulada_ms=0)
    assert servicio.usa_stripe_real
    servicio.crear_intento(Decimal("150.50"), "tarjeta_credito", moneda="BOB")
    assert recibido["currency"] == "bob"
    assert recibido["amount"] == 15050
