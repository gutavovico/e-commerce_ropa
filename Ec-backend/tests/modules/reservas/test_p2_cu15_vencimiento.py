"""P2-CU15 · Reservar varias prendas: vencimiento por las horas de la empresa (RN25) y alternativas.

Spec: `.specs/finalized/P2-CU14-CU15-CU19-CU20-sin-conexion/spec.md` AC-15.1 a AC-15.4.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import ConflictError, DomainError
from modules.reservas.cu12_reservar_prendas import servicio as cu12
from modules.reservas.cu12_reservar_prendas.esquemas import ReservaCrearIn
from modules.reservas.cu13_consultar_cancelar_reservas.servicio import ReservaConsultaServicio
from modules.reservas.modelos import ReservaORM

AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def entorno(monkeypatch):
    repo = cu12.ReservaRepositorio
    sucursal = SimpleNamespace(id_sucursal=1, nombre="Santa Cruz", direccion="Av. 1")
    variante = SimpleNamespace(
        id_variante=10, sku="X", precio_extra=Decimal("0"),
        producto=SimpleNamespace(nombre="Camisa", precio_base=Decimal("350.00")),
        talla=SimpleNamespace(codigo="M"), color=SimpleNamespace(nombre="Blanco"),
    )
    inventario = SimpleNamespace(id_inventario=100, cantidad_disponible=3, cantidad_reservada=0)
    creadas = []

    def crear_reserva(db, **campos):
        reserva = ReservaORM(id_reserva=55, estado="pendiente", **campos)
        creadas.append(reserva)
        return reserva

    monkeypatch.setattr(cu12, "ahora_utc", lambda: AHORA)
    monkeypatch.setattr(repo, "obtener_sucursal_activa", staticmethod(lambda db, i: sucursal))
    monkeypatch.setattr(repo, "asegurar_cliente", staticmethod(lambda db, u: SimpleNamespace(id_cliente=u.id_usuario)))
    monkeypatch.setattr(repo, "obtener_variante_con_prenda", staticmethod(lambda db, i: variante))
    monkeypatch.setattr(repo, "obtener_inventario_para_reserva", staticmethod(lambda db, v, s, c: inventario))
    monkeypatch.setattr(repo, "crear_reserva", staticmethod(crear_reserva))
    monkeypatch.setattr(repo, "crear_detalle_reserva", staticmethod(lambda db, **kw: SimpleNamespace(id_reserva_detalle=1)))
    monkeypatch.setattr(repo, "registrar_movimiento_inventario", staticmethod(lambda db, **kw: None))
    return SimpleNamespace(inventario=inventario, creadas=creadas)


def pedido(horas_hasta_la_cita: float, cantidad: int = 1) -> ReservaCrearIn:
    return ReservaCrearIn(
        id_sucursal=1,
        fecha_hora_atencion=AHORA + timedelta(hours=horas_hasta_la_cita),
        items=[{"id_variante": 10, "cantidad": cantidad}],
    )


USUARIO = SimpleNamespace(id_usuario=10)


def test_vence_a_las_horas_vigentes_de_la_empresa(entorno, monkeypatch):
    monkeypatch.setattr(cu12.ReservaServicio, "horas_vencimiento", staticmethod(lambda db: 48))
    registrada = cu12.ReservaServicio.registrar(MagicMock(), USUARIO, pedido(30), codigo_provisional="PROV-AB12-000001")
    reserva = registrada.reserva
    assert reserva.creado_en == AHORA
    assert reserva.vence_en == AHORA + timedelta(hours=48)
    assert reserva.codigo_provisional == "PROV-AB12-000001"
    assert entorno.inventario.cantidad_disponible == 2 and entorno.inventario.cantidad_reservada == 1


def test_sesion_simulada_usa_las_24_horas_de_rn25():
    assert cu12.ReservaServicio.horas_vencimiento(MagicMock()) == 24


def test_cita_posterior_al_vencimiento_se_rechaza_sin_apartar_stock(entorno, monkeypatch):
    monkeypatch.setattr(cu12.ReservaServicio, "horas_vencimiento", staticmethod(lambda db: 24))
    with pytest.raises(DomainError) as exc:
        cu12.ReservaServicio.registrar(MagicMock(), USUARIO, pedido(25))
    assert exc.value.code == "CITA_FUERA_DE_PLAZO"
    assert entorno.inventario.cantidad_disponible == 3 and entorno.creadas == []


def test_stock_insuficiente_propone_otras_sucursales(entorno, monkeypatch):
    monkeypatch.setattr(cu12.ReservaServicio, "horas_vencimiento", staticmethod(lambda db: 24))
    otra = SimpleNamespace(id_sucursal=2, nombre="Beni")
    monkeypatch.setattr(cu12.ReservaRepositorio, "sucursales_con_existencias", staticmethod(lambda db, v, c, excluir: [otra]))
    with pytest.raises(ConflictError) as exc:
        cu12.ReservaServicio.registrar(MagicMock(), USUARIO, pedido(3, cantidad=5))
    assert exc.value.code == "STOCK_INSUFICIENTE_RESERVA"
    assert exc.value.datos == {"id_variante": 10, "disponible": 3, "alternativas": [{"id_sucursal": 2, "nombre": "Beni"}]}


def test_el_409_http_incluye_las_alternativas():
    from fastapi.testclient import TestClient

    from main import app

    @app.get("/__prueba_409")
    def _lanzar():
        raise ConflictError("sin stock", code="STOCK_INSUFICIENTE_RESERVA", datos={"alternativas": [{"id_sucursal": 2}]})

    try:
        cuerpo = TestClient(app).get("/__prueba_409").json()
        assert cuerpo == {"alternativas": [{"id_sucursal": 2}], "detail": "sin stock", "code": "STOCK_INSUFICIENTE_RESERVA"}
    finally:
        app.router.routes.pop()


@pytest.mark.parametrize("vence_en, esperado", [(AHORA - timedelta(minutes=1), True), (AHORA + timedelta(minutes=1), False)])
def test_vence_por_vence_en_y_no_por_la_hora_de_la_cita(monkeypatch, vence_en, esperado):
    from modules.reservas.cu13_consultar_cancelar_reservas import servicio as cu13

    monkeypatch.setattr(cu13, "ahora", lambda: AHORA)
    reserva = ReservaORM(
        estado="pendiente",
        fecha_hora_atencion=AHORA + timedelta(days=3),  # con la regla del Parcial 1 no vencería
        vence_en=vence_en,
    )
    assert ReservaConsultaServicio._es_candidata_a_vencer(reserva) is esperado
