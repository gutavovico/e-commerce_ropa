"""Pruebas unitarias de P2-CU19 · Sincronizar operaciones pendientes (sin base de datos).

Spec: `.specs/changes/P2-CU14-CU15-CU19-CU20-sin-conexion/` (AC-19.2 a AC-19.9, AC-19.12).
La concurrencia real (mismo UUID a la vez, última unidad) está en `tests/integracion/test_multitenant.py`.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from core.errors import AuthorizationError, ConflictError, DomainError
from integrations.stripe_service import ErrorPasarela, ResultadoPasarela
from modules.sincronizacion.cu19_sincronizar import servicio as srv
from modules.sincronizacion.cu19_sincronizar.esquemas import OperacionIn
from modules.sincronizacion.cu19_sincronizar.saneado import sanear
from modules.sincronizacion.modelos import ConflictoSyncORM, OperacionSyncORM

AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)
ID_DISPOSITIVO = 7


@pytest.fixture
def db():
    sesion = MagicMock()
    sesion.begin_nested.return_value.__exit__.return_value = False  # no tragarse excepciones
    return sesion


@pytest.fixture
def usuario():
    return SimpleNamespace(id_usuario=10, nombres="Ana", apellidos="Rojas", email="ana@x.com", rol="cliente")


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    """Reloj fijo, sin operación previa, suscripción vigente y 7 días de antigüedad."""
    monkeypatch.setattr(srv, "ahora", lambda: AHORA)
    monkeypatch.setattr(srv.SincronizacionRepositorio, "operacion", staticmethod(lambda db, u: None))
    monkeypatch.setattr(srv.SincronizacionRepositorio, "conflicto_de_venta", staticmethod(lambda db, v: None))
    monkeypatch.setattr(srv.SuscripcionServicio, "validar", staticmethod(lambda db, **kw: None))
    monkeypatch.setattr(srv.SincronizacionServicio, "_dias_antiguedad", staticmethod(lambda db: 7))
    monkeypatch.setattr(srv.ServicioBitacoraAuditoria, "registrar_evento_seguro", classmethod(lambda cls, **kw: None))


def operacion_reserva(**cambios) -> OperacionIn:
    base = dict(
        uuid=uuid.uuid4(),
        tipo="reserva",
        id_sucursal=3,
        registrada_en=AHORA - timedelta(hours=2),
        codigo_provisional="PROV-3F9A-000004",
        datos={
            "fecha_hora_atencion": (AHORA + timedelta(hours=3)).isoformat(),
            "items": [{"id_variante": 41, "cantidad": 1}],
        },
    )
    base.update(cambios)
    return OperacionIn(**base)


def operacion_compra(**cambios) -> OperacionIn:
    base = dict(
        uuid=uuid.uuid4(),
        tipo="compra_interrumpida",
        registrada_en=AHORA - timedelta(minutes=10),
        datos={"id_venta": 501, "id_pago": 90, "client_secret": "pi_x_secret_y"},
    )
    base.update(cambios)
    return OperacionIn(**base)


def prendas_activas(monkeypatch, sucursal=True, activo=True):
    monkeypatch.setattr(
        srv.ReservaRepositorio, "obtener_sucursal_activa",
        staticmethod(lambda db, i: SimpleNamespace(id_sucursal=i) if sucursal else None),
    )
    variante = SimpleNamespace(id_variante=41, activo=activo, producto=SimpleNamespace(activo=True))
    monkeypatch.setattr(srv.ReservaRepositorio, "obtener_variante_con_prenda", staticmethod(lambda db, i: variante))


def filas_insertadas(db):
    return [c.args[0] for c in db.add.call_args_list]


# ---------------------------------------------------------------------------------------------
# Saneado (AC-19.12, RN43)
# ---------------------------------------------------------------------------------------------

def test_saneado_descarta_secretos_y_campos_desconocidos():
    datos = {"id_venta": 5, "id_pago": 6, "client_secret": "pi_secret", "token": "jwt", "tarjeta": "4242"}
    assert sanear("compra_interrumpida", datos) == {"id_venta": 5, "id_pago": 6}
    reserva = sanear("reserva", {
        "fecha_hora_atencion": "2026-11-09T10:00:00Z", "password": "x",
        "items": [{"id_variante": 1, "cantidad": 2, "precio": "1.00"}],
    })
    assert reserva == {"fecha_hora_atencion": "2026-11-09T10:00:00Z", "items": [{"id_variante": 1, "cantidad": 2}]}


# ---------------------------------------------------------------------------------------------
# Reservas
# ---------------------------------------------------------------------------------------------

def test_reserva_valida_se_confirma_con_codigo_definitivo(db, usuario, monkeypatch):
    prendas_activas(monkeypatch)
    reserva = SimpleNamespace(id_reserva=123)
    capturado = {}

    def registrar(db_, usuario_, payload, codigo_provisional=None):
        capturado.update(payload=payload, provisional=codigo_provisional)
        return SimpleNamespace(reserva=reserva)

    monkeypatch.setattr(srv.ReservaServicio, "registrar", staticmethod(registrar))
    monkeypatch.setattr(srv.ReservaServicio, "auditar", staticmethod(lambda *a: None))
    monkeypatch.setattr(srv.ReservaServicio, "codigo", staticmethod(lambda r: "RES-2026-000123"))

    op = operacion_reserva()
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", op, None)

    assert resultado.estado == "confirmada"
    assert resultado.codigo_reserva == "RES-2026-000123"
    assert capturado["provisional"] == "PROV-3F9A-000004"
    assert capturado["payload"].canal_origen == "movil"
    fila = next(f for f in filas_insertadas(db) if isinstance(f, OperacionSyncORM))
    assert fila.estado == "confirmada" and fila.id_reserva == 123 and fila.id_sucursal == 3
    db.commit.assert_called_once()


def test_reserva_sin_stock_se_rechaza_con_aviso_y_sin_conflicto(db, usuario, monkeypatch):
    prendas_activas(monkeypatch)

    def sin_stock(*a, **kw):
        raise ConflictError("Sin stock", code="STOCK_INSUFICIENTE_RESERVA", datos={"disponible": 0})

    monkeypatch.setattr(srv.ReservaServicio, "registrar", staticmethod(sin_stock))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", operacion_reserva(), None)

    assert resultado.estado == "rechazada" and resultado.motivo == "STOCK_INSUFICIENTE"
    db.rollback.assert_called()  # nada de la reserva queda
    filas = filas_insertadas(db)
    assert not any(isinstance(f, ConflictoSyncORM) for f in filas)  # S8: no es un conflicto de CU20
    aviso = next(f for f in filas if type(f).__name__ == "AvisoClienteORM")
    assert aviso.tipo == "reserva_cancelada" and aviso.id_cliente == 10
    assert "PROV-3F9A-000004" in aviso.mensaje


@pytest.mark.parametrize("cambios, motivo", [
    ({"registrada_en": AHORA - timedelta(days=8)}, "ANTIGUEDAD_EXCEDIDA"),
    ({"registrada_en": AHORA + timedelta(hours=1)}, "FECHA_INVALIDA"),
    ({"id_sucursal": None}, "DATOS_INVALIDOS"),
    ({"datos": {"items": []}}, "DATOS_INVALIDOS"),
])
def test_reglas_de_la_reserva(db, usuario, monkeypatch, cambios, motivo):
    prendas_activas(monkeypatch)
    monkeypatch.setattr(srv.ReservaServicio, "registrar", staticmethod(lambda *a, **kw: pytest.fail("no debe reservar")))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", operacion_reserva(**cambios), None)
    assert (resultado.estado, resultado.motivo) == ("rechazada", motivo)


def test_antiguedad_dentro_del_margen_de_reloj_se_acepta(db, usuario, monkeypatch):
    prendas_activas(monkeypatch)
    monkeypatch.setattr(srv.ReservaServicio, "registrar", staticmethod(lambda *a, **kw: SimpleNamespace(reserva=SimpleNamespace(id_reserva=1))))
    monkeypatch.setattr(srv.ReservaServicio, "auditar", staticmethod(lambda *a: None))
    monkeypatch.setattr(srv.ReservaServicio, "codigo", staticmethod(lambda r: "RES"))
    op = operacion_reserva(registrada_en=AHORA - timedelta(days=7, minutes=3))
    assert srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", op, None).estado == "confirmada"


@pytest.mark.parametrize("sucursal, activo, motivo", [(False, True, "SUCURSAL_INACTIVA"), (True, False, "PRODUCTO_INACTIVO")])
def test_sucursal_o_prenda_inactiva(db, usuario, monkeypatch, sucursal, activo, motivo):
    prendas_activas(monkeypatch, sucursal=sucursal, activo=activo)
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", operacion_reserva(), None)
    assert (resultado.estado, resultado.motivo) == ("rechazada", motivo)


def test_suscripcion_vencida_rechaza_la_reserva(db, usuario, monkeypatch):
    def vencida(db, **kw):
        raise AuthorizationError("vencida", code="SUSCRIPCION_NO_VIGENTE")

    monkeypatch.setattr(srv.SuscripcionServicio, "validar", staticmethod(vencida))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", operacion_reserva(), None)
    assert (resultado.estado, resultado.motivo) == ("rechazada", "SUSCRIPCION_NO_VIGENTE")


# ---------------------------------------------------------------------------------------------
# Idempotencia (AC-19.3, RN35)
# ---------------------------------------------------------------------------------------------

def test_operacion_ya_recibida_devuelve_el_resultado_guardado_sin_ejecutar(db, usuario, monkeypatch):
    op = operacion_reserva()
    previa = OperacionSyncORM(
        uuid_operacion=op.uuid, id_dispositivo=ID_DISPOSITIVO, estado="confirmada",
        resultado={"estado": "confirmada", "codigo_reserva": "RES-1", "id_reserva": 1},
    )
    monkeypatch.setattr(srv.SincronizacionRepositorio, "operacion", staticmethod(lambda db, u: previa))
    monkeypatch.setattr(srv.ReservaServicio, "registrar", staticmethod(lambda *a, **kw: pytest.fail("duplicado")))

    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", op, None)

    assert resultado.repetida is True and resultado.codigo_reserva == "RES-1"
    db.add.assert_not_called()


def test_uuid_de_otro_dispositivo_no_revela_su_resultado(db, usuario, monkeypatch):
    op = operacion_reserva()
    previa = OperacionSyncORM(uuid_operacion=op.uuid, id_dispositivo=99, estado="confirmada", resultado={"codigo_reserva": "RES-9"})
    monkeypatch.setattr(srv.SincronizacionRepositorio, "operacion", staticmethod(lambda db, u: previa))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", op, None)
    assert (resultado.estado, resultado.motivo, resultado.codigo_reserva) == ("rechazada", "UUID_DUPLICADO", None)


def test_mismo_uuid_a_la_vez_deshace_y_devuelve_el_del_otro_envio(db, usuario, monkeypatch):
    prendas_activas(monkeypatch)
    op = operacion_reserva()
    monkeypatch.setattr(srv.ReservaServicio, "registrar", staticmethod(lambda *a, **kw: SimpleNamespace(reserva=SimpleNamespace(id_reserva=2))))
    monkeypatch.setattr(srv.ReservaServicio, "auditar", staticmethod(lambda *a: None))
    monkeypatch.setattr(srv.ReservaServicio, "codigo", staticmethod(lambda r: "RES-2"))
    ganadora = OperacionSyncORM(uuid_operacion=op.uuid, id_dispositivo=ID_DISPOSITIVO, estado="confirmada",
                                resultado={"estado": "confirmada", "codigo_reserva": "RES-1", "id_reserva": 1})
    lecturas = iter([None, ganadora])
    monkeypatch.setattr(srv.SincronizacionRepositorio, "operacion", staticmethod(lambda db, u: next(lecturas)))
    db.flush.side_effect = IntegrityError("INSERT", {}, Exception("uq_operaciones_sync_uuid"))

    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "web", op, None)

    assert resultado.codigo_reserva == "RES-1" and resultado.repetida
    db.rollback.assert_called()  # la reserva RES-2 de este envío se deshizo
    db.commit.assert_not_called()


# ---------------------------------------------------------------------------------------------
# Compra interrumpida (AC-19.7 a AC-19.9)
# ---------------------------------------------------------------------------------------------

def compra(monkeypatch, estado_venta="pendiente", estado_pago="pendiente", id_cliente=10, producto_activo=True):
    variante = SimpleNamespace(id_variante=41, activo=True, producto=SimpleNamespace(activo=producto_activo))
    sucursal = SimpleNamespace(id_sucursal=3, activa=True)
    venta = SimpleNamespace(
        id_venta=501, id_cliente=id_cliente, estado=estado_venta, id_sucursal=3,
        fecha_venta=AHORA - timedelta(minutes=30), sucursal=sucursal,
        detalles=[SimpleNamespace(id_sucursal=3, sucursal=sucursal, variante=variante, cantidad=1)],
    )
    pago = SimpleNamespace(id_pago=90, estado=estado_pago, monto=Decimal("120.00"), payload_respuesta={})
    monkeypatch.setattr(srv.PagoServicio, "cargar_compra_para_cobro", staticmethod(lambda db, v, p: (venta, pago)))
    return venta, pago


def aprobar(monkeypatch, aprobado=True):
    resultado = ResultadoPasarela(aprobado=aprobado, referencia="pi_1", codigo_respuesta="x", mensaje="m")
    monkeypatch.setattr(srv.PagoServicio, "verificar_cobro", staticmethod(lambda pago, pasarela=None: resultado))

    def confirmar(db, pago, res):
        pago.estado = "confirmado"

    monkeypatch.setattr(srv.PagoServicio, "marcar_cobro_confirmado", staticmethod(confirmar))


def test_compra_ya_pagada_por_el_webhook_se_confirma_sin_volver_a_cobrar(db, usuario, monkeypatch):
    compra(monkeypatch, estado_venta="pagada", estado_pago="confirmado")
    monkeypatch.setattr(srv.PagoServicio, "verificar_cobro", staticmethod(lambda *a, **kw: pytest.fail("no verifica")))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert (resultado.estado, resultado.id_venta) == ("confirmada", 501)


def test_compra_cobrada_con_retencion_vigente_se_completa(db, usuario, monkeypatch):
    venta, _ = compra(monkeypatch)
    aprobar(monkeypatch)
    completadas = []
    monkeypatch.setattr(srv.PagoServicio, "completar_venta_cobrada", staticmethod(lambda db, v, r: completadas.append(v.id_venta)))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert resultado.estado == "confirmada" and completadas == [501]
    fila = next(f for f in filas_insertadas(db) if isinstance(f, OperacionSyncORM))
    assert fila.datos == {"id_venta": 501, "id_pago": 90}  # sin client_secret


def test_pago_no_aprobado_rechaza_la_operacion(db, usuario, monkeypatch):
    _, pago = compra(monkeypatch)
    aprobar(monkeypatch, aprobado=False)
    monkeypatch.setattr(srv.PagoServicio, "marcar_cobro_rechazado", staticmethod(lambda db, p, r: setattr(p, "estado", "rechazado")))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert (resultado.estado, resultado.motivo) == ("rechazada", "PAGO_NO_APROBADO")
    assert pago.estado == "rechazado"


def test_pasarela_caida_pide_reintentar_sin_guardar_nada(db, usuario, monkeypatch):
    compra(monkeypatch)

    def caida(*a, **kw):
        raise ErrorPasarela("sin red")

    monkeypatch.setattr(srv.PagoServicio, "verificar_cobro", staticmethod(caida))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert (resultado.estado, resultado.motivo) == ("reintentar", "PASARELA_NO_DISPONIBLE")
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_compra_cobrada_sin_stock_queda_en_conflicto_nunca_rechazada(db, usuario, monkeypatch):
    compra(monkeypatch, estado_venta="anulada")
    aprobar(monkeypatch)

    def sin_stock(db, venta, responsable):
        raise ConflictError("x", code="STOCK_INSUFICIENTE", datos={"esperado": 1, "encontrado": 0})

    monkeypatch.setattr(srv.PagoServicio, "retomar_y_completar_venta_cobrada", staticmethod(sin_stock))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)

    assert (resultado.estado, resultado.motivo) == ("en_conflicto", "STOCK_INSUFICIENTE")
    conflicto = next(f for f in filas_insertadas(db) if isinstance(f, ConflictoSyncORM))
    assert conflicto.tipo == "stock_insuficiente" and conflicto.estado == "pendiente"
    assert conflicto.id_pago == 90 and conflicto.detalle["esperado"] == 1 and conflicto.detalle["encontrado"] == 0
    db.commit.assert_called_once()


def test_compra_cobrada_con_producto_inactivo_devuelve_la_retencion(db, usuario, monkeypatch):
    venta, _ = compra(monkeypatch, producto_activo=False)
    aprobar(monkeypatch)
    devueltas = []
    monkeypatch.setattr(srv.CheckoutServicio, "devolver_existencias", staticmethod(lambda db, v, r: devueltas.append(v.id_venta)))
    monkeypatch.setattr(srv.PagoServicio, "completar_venta_cobrada", staticmethod(lambda *a: pytest.fail("no completa")))

    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)

    assert (resultado.estado, resultado.motivo) == ("en_conflicto", "PRODUCTO_INACTIVO")
    assert devueltas == [501]
    conflicto = next(f for f in filas_insertadas(db) if isinstance(f, ConflictoSyncORM))
    assert conflicto.tipo == "producto_inactivo"


def test_compra_cobrada_con_suscripcion_vencida_queda_en_conflicto(db, usuario, monkeypatch):
    compra(monkeypatch)
    aprobar(monkeypatch)
    monkeypatch.setattr(srv.CheckoutServicio, "devolver_existencias", staticmethod(lambda *a: 1))

    def vencida(db, **kw):
        raise AuthorizationError("vencida", code="SUSCRIPCION_NO_VIGENTE")

    monkeypatch.setattr(srv.SuscripcionServicio, "validar", staticmethod(vencida))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert (resultado.estado, resultado.motivo) == ("en_conflicto", "SUSCRIPCION_NO_VIGENTE")


def test_segundo_envio_de_una_compra_ya_en_conflicto_no_abre_otro_reembolso(db, usuario, monkeypatch):
    compra(monkeypatch, estado_venta="anulada", estado_pago="confirmado")
    existente = SimpleNamespace(id_venta=501, id_conflicto=33)
    monkeypatch.setattr(srv.SincronizacionRepositorio, "conflicto_de_venta", staticmethod(lambda db, v: existente))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert (resultado.estado, resultado.id_conflicto) == ("en_conflicto", 33)
    assert not any(isinstance(f, ConflictoSyncORM) for f in filas_insertadas(db))


@pytest.mark.parametrize("motivo_esperado, preparar", [
    ("VENTA_AJENA", lambda mp: compra(mp, id_cliente=99)),
    ("DATOS_INVALIDOS", lambda mp: None),
])
def test_compra_ajena_o_incompleta_se_rechaza(db, usuario, monkeypatch, motivo_esperado, preparar):
    preparar(monkeypatch)
    datos = {"id_venta": 501, "id_pago": 90} if motivo_esperado == "VENTA_AJENA" else {"id_venta": "x"}
    resultado = srv.SincronizacionServicio._procesar(
        db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(datos=datos), None
    )
    assert (resultado.estado, resultado.motivo) == ("rechazada", motivo_esperado)


def test_compra_no_digital_se_rechaza_sin_romper_el_lote(db, usuario, monkeypatch):
    def efectivo(db, v, p):
        raise ConflictError("no digital", code="METODO_NO_SOPORTADO")

    monkeypatch.setattr(srv.PagoServicio, "cargar_compra_para_cobro", staticmethod(efectivo))
    resultado = srv.SincronizacionServicio._procesar(db, usuario, ID_DISPOSITIVO, "movil", operacion_compra(), None)
    assert (resultado.estado, resultado.motivo) == ("rechazada", "DATOS_INVALIDOS")


# ---------------------------------------------------------------------------------------------
# Contrato HTTP
# ---------------------------------------------------------------------------------------------

def test_lote_de_mas_de_50_operaciones_responde_422():
    from fastapi.testclient import TestClient

    from core.database import get_db
    from core.deps import get_current_user
    from main import app

    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id_usuario=10, rol="cliente")
    try:
        ops = [{"uuid": str(uuid.uuid4()), "tipo": "reserva", "registrada_en": AHORA.isoformat(), "datos": {}}] * 51
        r = TestClient(app).post("/api/v1/sin-conexion/sincronizar", json={"dispositivo": str(uuid.uuid4()), "operaciones": ops})
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_un_empleado_no_puede_sincronizar():
    from fastapi.testclient import TestClient

    from core.database import get_db
    from core.deps import get_current_user
    from main import app

    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id_usuario=1, rol="cajero")
    try:
        r = TestClient(app).get(f"/api/v1/sin-conexion/operaciones?dispositivo={uuid.uuid4()}")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()
