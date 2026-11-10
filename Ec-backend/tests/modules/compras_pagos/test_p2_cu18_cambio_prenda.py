"""Pruebas unitarias de P2-CU18 · Registrar cambio de prenda (sin base de datos).

Spec: `.specs/changes/P2-CU18-cambio-prenda/` (AC-1 a AC-10). La concurrencia y el kardex reales
están en `tests/integracion/test_multitenant.py`.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from modules.compras_pagos.cu18_cambio_prenda import servicio as srv
from modules.compras_pagos.cu18_cambio_prenda.esquemas import CambioIn
from modules.compras_pagos.modelos import CambioPrendaDetalleORM, CambioPrendaORM

D = Decimal


def variante(id_variante, nombre="Camisa", activo=True):
    return SimpleNamespace(
        id_variante=id_variante, sku=f"SKU-{id_variante}", activo=activo,
        producto=SimpleNamespace(id_producto=id_variante * 10, nombre=nombre, activo=True),
        talla=SimpleNamespace(codigo="M"), color=SimpleNamespace(nombre="Blanco"),
    )


def linea(id_detalle, id_variante, cantidad, precio):
    return SimpleNamespace(
        id_venta_detalle=id_detalle, id_variante=id_variante, cantidad=cantidad,
        precio_unitario=D(precio), variante=variante(id_variante),
    )


@pytest.fixture
def venta():
    # Dos líneas: 2 × 100 + 1 × 300 = 500; con un cupón de 50, total pagado 450 (factor 0,9).
    return SimpleNamespace(
        id_venta=501, numero_comprobante="FS-2026-000501", estado="pagada", total=D("450.00"),
        fecha_venta=datetime(2026, 11, 5, 15, tzinfo=timezone.utc), id_cliente=None,
    )


@pytest.fixture
def lineas():
    return [linea(1, 41, 2, "100.00"), linea(2, 42, 1, "300.00")]


@pytest.fixture(autouse=True)
def entorno(monkeypatch, venta, lineas):
    repo = srv.CambioPrendaRepositorio
    monkeypatch.setattr(srv.PuntoVentaServicio, "resolver_sucursal", staticmethod(lambda db, u, s: 3))
    monkeypatch.setattr(srv.PuntoVentaServicio, "_auditar", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(srv.CambioPrendaServicio, "plazo_dias", staticmethod(lambda db: 15))
    monkeypatch.setattr(srv, "hoy", lambda: date(2026, 11, 10))
    monkeypatch.setattr(repo, "venta", staticmethod(lambda db, i, bloquear=False: venta))
    monkeypatch.setattr(repo, "venta_por_comprobante", staticmethod(lambda db, c: venta))
    monkeypatch.setattr(repo, "lineas_de_venta", staticmethod(lambda db, i: lineas))
    monkeypatch.setattr(repo, "ya_cambiadas", staticmethod(lambda db, ids: {}))
    nuevas = {51: variante(51, "Pantalón"), 52: variante(52, "Camiseta")}
    monkeypatch.setattr(srv.PuntoVentaRepositorio, "variantes_por_ids", staticmethod(
        lambda db, ids: {i: nuevas.get(i) or variante(i) for i in ids}))
    monkeypatch.setattr(srv.CarritoRepositorio, "obtener_promociones_por_producto", staticmethod(lambda db, ids: {}))
    precios = {51: D("280.00"), 52: D("80.00")}
    monkeypatch.setattr(srv.CarritoServicio, "precio_linea", staticmethod(
        lambda v, c, p: (precios.get(v.id_variante, D("100.00")), precios.get(v.id_variante, D("100.00")), None, None, None)))
    monkeypatch.setattr(srv.PuntoVentaRepositorio, "disponible_en_sucursal", staticmethod(lambda db, v, s: 10))
    return nuevas


def cambio(devueltas, nuevas, cobro=None):
    return CambioIn(id_venta=501, devueltas=[{"id_venta_detalle": d, "cantidad": c} for d, c in devueltas],
                    nuevas=[{"id_variante": v, "cantidad": c} for v, c in nuevas], cobro=cobro)


# ------------------------------------------------------------------ valor devuelto (F2)

def test_el_cupon_se_reparte_y_nunca_se_devuelve_mas_de_lo_pagado(venta, lineas):
    factor = srv.CambioPrendaServicio.factor_pagado(venta, lineas)
    assert factor == D("0.9")
    assert srv.CambioPrendaServicio.valor_unitario(D("100.00"), factor) == D("90.00")
    # Sin cupón (o con gastos que suban el total), el valor es el precio de la línea
    venta.total = D("520.00")
    assert srv.CambioPrendaServicio.valor_unitario(D("100.00"), srv.CambioPrendaServicio.factor_pagado(venta, lineas)) == D("100.00")


# ------------------------------------------------------------------ plazo (AC-3)

@pytest.mark.parametrize("hoy, plazo, permitido", [
    (date(2026, 11, 10), 15, True),    # 5 días
    (date(2026, 11, 20), 15, True),    # justo el día 15
    (date(2026, 11, 21), 15, False),   # día 16
    (date(2026, 11, 6), 0, False),     # cambios desactivados
])
def test_plazo_de_cambio(monkeypatch, venta, hoy, plazo, permitido):
    monkeypatch.setattr(srv, "hoy", lambda: hoy)
    monkeypatch.setattr(srv.CambioPrendaServicio, "plazo_dias", staticmethod(lambda db: plazo))
    if permitido:
        srv.CambioPrendaServicio._exigir_plazo(MagicMock(), venta)
    else:
        with pytest.raises(ConflictError) as exc:
            srv.CambioPrendaServicio._exigir_plazo(MagicMock(), venta)
        assert exc.value.code == "PLAZO_DE_CAMBIO_VENCIDO"
        assert exc.value.datos["dias_transcurridos"] == (hoy - date(2026, 11, 5)).days


def test_la_fecha_se_cuenta_en_hora_de_bolivia(monkeypatch, venta):
    # 02:00 UTC del 6 es todavía el 5 en Bolivia (UTC−4)
    venta.fecha_venta = datetime(2026, 11, 6, 2, tzinfo=timezone.utc)
    monkeypatch.setattr(srv, "hoy", lambda: date(2026, 11, 6))
    assert srv.CambioPrendaServicio.dias_desde(venta) == 1


# ------------------------------------------------------------------ AC-1, AC-2

def test_venta_cambiable_con_unidades_y_valor_pagado(monkeypatch):
    monkeypatch.setattr(srv.CambioPrendaRepositorio, "ya_cambiadas", staticmethod(lambda db, ids: {1: 1}))
    salida = srv.CambioPrendaServicio.venta_cambiable(MagicMock(), SimpleNamespace(), "fs-2026-000501", None)
    assert (salida.dias_transcurridos, salida.plazo_dias) == (5, 15)
    primera = salida.lineas[0]
    assert (primera.vendidas, primera.ya_cambiadas, primera.cambiables) == (2, 1, 1)
    assert primera.valor_unitario == D("90.00")


@pytest.mark.parametrize("estado", ["pendiente", "anulada"])
def test_venta_no_pagada_no_existe_para_el_cambio(venta, estado):
    venta.estado = estado
    with pytest.raises(NotFoundError) as exc:
        srv.CambioPrendaServicio.venta_cambiable(MagicMock(), SimpleNamespace(), "x", None)
    assert exc.value.code == "VENTA_NO_ENCONTRADA"


# ------------------------------------------------------------------ AC-4, AC-6

def test_previsualizar_calcula_la_diferencia_en_el_servidor():
    previo = srv.CambioPrendaServicio.previsualizar(MagicMock(), SimpleNamespace(), cambio([(2, 1)], [(51, 1)]))
    assert previo.valor_devuelto == D("270.00")   # 300 × 0,9
    assert previo.valor_nuevo == D("280.00")
    assert previo.diferencia == D("10.00")


@pytest.mark.parametrize("devueltas, mensaje", [
    ([(99, 1)], "no es de la venta"),        # línea ajena
    ([(1, 3)], "quedan 2 unidades"),         # más de las vendidas
])
def test_cantidades_no_cambiables(devueltas, mensaje):
    with pytest.raises(ConflictError, match=mensaje) as exc:
        srv.CambioPrendaServicio.previsualizar(MagicMock(), SimpleNamespace(), cambio(devueltas, [(51, 1)]))
    assert exc.value.code == "CANTIDAD_NO_CAMBIABLE"


def test_ya_cambiadas_reducen_lo_que_queda(monkeypatch):
    monkeypatch.setattr(srv.CambioPrendaRepositorio, "ya_cambiadas", staticmethod(lambda db, ids: {1: 2}))
    with pytest.raises(ConflictError, match="quedan 0 unidades"):
        srv.CambioPrendaServicio.previsualizar(MagicMock(), SimpleNamespace(), cambio([(1, 1)], [(51, 1)]))


def test_prenda_nueva_sin_stock(monkeypatch):
    monkeypatch.setattr(srv.PuntoVentaRepositorio, "disponible_en_sucursal", staticmethod(lambda db, v, s: 0))
    with pytest.raises(ConflictError) as exc:
        srv.CambioPrendaServicio.previsualizar(MagicMock(), SimpleNamespace(), cambio([(2, 1)], [(51, 1)]))
    assert exc.value.code == "STOCK_INSUFICIENTE"


# ------------------------------------------------------------------ AC-7

def test_cobro_de_la_diferencia():
    c = srv.CambioPrendaServicio._cobro
    assert c(D("-90.00"), cambio([(2, 1)], [(52, 1)])) == ("efectivo", None, None, None)   # F1
    assert c(D("0.00"), cambio([(2, 1)], [(52, 1)])) == (None, None, None, None)
    with pytest.raises(UnprocessableEntityError) as exc:
        c(D("10.00"), cambio([(2, 1)], [(51, 1)]))
    assert exc.value.code == "COBRO_REQUERIDO"
    with pytest.raises(UnprocessableEntityError) as exc:
        c(D("10.00"), cambio([(2, 1)], [(51, 1)], {"metodo_pago": "efectivo", "monto_recibido": "5"}))
    assert exc.value.code == "MONTO_INSUFICIENTE"
    assert c(D("10.00"), cambio([(2, 1)], [(51, 1)], {"metodo_pago": "efectivo", "monto_recibido": "20"})) == (
        "efectivo", D("20.00"), D("10.00"), None)
    with pytest.raises(UnprocessableEntityError) as exc:
        c(D("10.00"), cambio([(2, 1)], [(51, 1)], {"metodo_pago": "qr"}))
    assert exc.value.code == "REFERENCIA_REQUERIDA"


# ------------------------------------------------------------------ AC-8 (sin base de datos)

def test_registrar_mueve_inventario_y_guarda_el_cambio(monkeypatch):
    filas = {41: SimpleNamespace(id_inventario=1, cantidad_disponible=3),
             52: SimpleNamespace(id_inventario=2, cantidad_disponible=5)}
    monkeypatch.setattr(srv.CambioPrendaRepositorio, "inventario", staticmethod(lambda db, v, s, m: filas.get(v)))
    monkeypatch.setattr(srv.CambioPrendaRepositorio, "siguiente_comprobante", staticmethod(lambda db, t, a: "CAM-2026-00001"))
    capturado = {}
    monkeypatch.setattr(srv.CambioPrendaServicio, "obtener", staticmethod(lambda db, u, i: capturado.setdefault("salida", i)))
    db = MagicMock()

    def fijar_id():
        for llamada in db.add.call_args_list:
            obj = llamada.args[0]
            if isinstance(obj, CambioPrendaORM) and obj.id_cambio is None:
                obj.id_cambio = 7

    db.flush.side_effect = fijar_id

    srv.CambioPrendaServicio.registrar(db, SimpleNamespace(id_usuario=9), cambio([(1, 1)], [(52, 1)]))

    agregados = [c.args[0] for c in db.add.call_args_list]
    cab = next(a for a in agregados if isinstance(a, CambioPrendaORM))
    assert (cab.valor_devuelto, cab.valor_nuevo, cab.diferencia, cab.metodo_pago) == (D("90.00"), D("80.00"), D("-10.00"), "efectivo")
    detalles = [a for a in agregados if isinstance(a, CambioPrendaDetalleORM)]
    assert {(d.tipo, d.id_variante) for d in detalles} == {("devuelta", 41), ("nueva", 52)}
    movimientos = [a for a in agregados if type(a).__name__ == "MovimientoInventarioORM"]
    assert {(m.tipo_movimiento, m.cantidad, m.referencia_documento) for m in movimientos} == {
        ("devolucion", 1, "CAMBIO-7"), ("venta_confirmada", -1, "CAMBIO-7")}
    assert (filas[41].cantidad_disponible, filas[52].cantidad_disponible) == (4, 4)
    db.commit.assert_called_once()
    assert capturado["salida"] == 7


def test_registrar_sin_stock_de_la_nueva_no_confirma(monkeypatch):
    monkeypatch.setattr(srv.CambioPrendaRepositorio, "inventario", staticmethod(
        lambda db, v, s, m: SimpleNamespace(id_inventario=1, cantidad_disponible=0)))
    monkeypatch.setattr(srv.CambioPrendaRepositorio, "siguiente_comprobante", staticmethod(lambda db, t, a: "CAM-2026-00001"))
    db = MagicMock()
    with pytest.raises(ConflictError) as exc:
        srv.CambioPrendaServicio.registrar(db, SimpleNamespace(id_usuario=9), cambio([(1, 1)], [(52, 1)]))
    assert exc.value.code == "STOCK_INSUFICIENTE"
    db.commit.assert_not_called()


# ------------------------------------------------------------------ contrato HTTP (T-BE-03)

def _cliente_http(rol):
    from fastapi.testclient import TestClient

    from core.database import get_db
    from core.deps import get_current_user
    from main import app

    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id_usuario=9, rol=rol, nombres="A", apellidos="B", email="a@b.c")
    return app, TestClient(app)


def test_el_cliente_no_accede_a_los_cambios():
    app, cliente = _cliente_http("cliente")
    try:
        assert cliente.get("/api/v1/pos/cambios/venta?comprobante=FS-1").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_plazo_vencido_responde_409_con_los_dias(monkeypatch):
    monkeypatch.setattr(srv, "hoy", lambda: date(2026, 11, 30))
    app, cliente = _cliente_http("cajero")
    try:
        r = cliente.get("/api/v1/pos/cambios/venta?comprobante=FS-2026-000501")
        assert r.status_code == 409
        assert r.json()["code"] == "PLAZO_DE_CAMBIO_VENCIDO"
        assert (r.json()["dias_transcurridos"], r.json()["plazo_dias"]) == (25, 15)
    finally:
        app.dependency_overrides.clear()


def test_cambio_sin_prendas_responde_422():
    app, cliente = _cliente_http("cajero")
    try:
        r = cliente.post("/api/v1/pos/cambios/previsualizar", json={"id_venta": 501, "devueltas": [], "nuevas": []})
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()
