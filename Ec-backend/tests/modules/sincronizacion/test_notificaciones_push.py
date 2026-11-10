"""Pruebas unitarias de Notificaciones Push (FCM · RF37 / Parte C).

Cubre:
- AC-C1: Registro y actualización del token push asociado al dispositivo.
- AC-C2: Disparadores en los 7 eventos de negocio.
- AC-C3: Envío posterior al commit; si hay rollback, no se envía ningún push.
- AC-C4: Resiliencia ante fallos de FCM / sin credenciales (mejor esfuerzo).
- AC-C6: Aislamiento por empresa (tenant scoping).
- AC-C7: Endpoint protegido /api/v1/reservas/vencer-expiradas con X-Tareas-Token.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from core.config import settings
from integrations.fcm_service import (
    _al_confirmar_transaccion,
    _al_revertir_transaccion,
    enviar_push,
    limpiar_historial_pruebas,
    notificar_cliente,
    obtener_historial_pruebas,
    programar_push,
)
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.reservas.cu13_consultar_cancelar_reservas.esquemas import ReservaCancelarIn
from modules.reservas.cu13_consultar_cancelar_reservas.servicio import ReservaConsultaServicio
from modules.sincronizacion.avisos_cliente.servicio import AvisosServicio
from modules.sincronizacion.cu14_dispositivo_catalogo.esquemas import (
    DispositivoIn,
    DispositivoTokenPushIn,
)
from modules.sincronizacion.cu14_dispositivo_catalogo.servicio import DispositivoServicio


class SesionSimulada:
    def __init__(self):
        self.info = {}

    def commit(self):
        _al_confirmar_transaccion(self)

    def rollback(self):
        _al_revertir_transaccion(self)

    def add(self, obj):
        pass

    def flush(self):
        pass

    def refresh(self, obj):
        pass

    def execute(self, stmt):
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_exec = MagicMock()
        mock_exec.scalars.return_value = mock_scalars
        return mock_exec


@pytest.fixture(autouse=True)
def limpiar_fcm():
    limpiar_historial_pruebas()
    yield
    limpiar_historial_pruebas()


@pytest.fixture
def db():
    return SesionSimulada()


@pytest.fixture
def usuario():
    return SimpleNamespace(
        id_usuario=10,
        nombres="Ana",
        apellidos="Rojas",
        email="ana@fashionstore.test",
        rol="cliente",
        activo=True,
    )


# ---------------------------------------------------------------------------------------------
# AC-C4: Modo simulador y resiliencia ante ausencias de credenciales
# ---------------------------------------------------------------------------------------------

def test_ac_c4_envio_sin_credenciales_es_resiliente():
    """AC-C4: Enviar push sin credenciales opera en modo simulador y no arroja excepción."""
    resultado = enviar_push(
        token="token_fcm_ficticio_123",
        titulo="Prueba de Moda",
        cuerpo="Tu pedido está listo",
        datos={"pantalla": "compras", "id": "1"},
    )
    assert resultado is True
    historial = obtener_historial_pruebas()
    assert len(historial) == 1
    assert historial[0]["token"] == "token_fcm_ficticio_123"
    assert historial[0]["datos"]["pantalla"] == "compras"


# ---------------------------------------------------------------------------------------------
# AC-C3: Despacho estricto post-commit (rollback lo descarta)
# ---------------------------------------------------------------------------------------------

def test_ac_c3_push_solo_tras_commit(db):
    """AC-C3: Las notificaciones solo se envían tras commit; un rollback las descarta."""
    programar_push(
        db,
        token="token_123",
        titulo="Transacción pendiente",
        cuerpo="Este push se descartará",
    )
    assert len(obtener_historial_pruebas()) == 0

    # Rollback descarta el push
    db.rollback()
    assert len(obtener_historial_pruebas()) == 0

    # Ahora programamos y confirmamos con commit
    programar_push(
        db,
        token="token_456",
        titulo="Transacción exitosa",
        cuerpo="Este push sí se envía",
    )
    assert len(obtener_historial_pruebas()) == 0

    db.commit()
    historial = obtener_historial_pruebas()
    assert len(historial) == 1
    assert historial[0]["token"] == "token_456"
    assert historial[0]["titulo"] == "Transacción exitosa"


# ---------------------------------------------------------------------------------------------
# AC-C1: Registro y actualización del token push asociado al dispositivo
# ---------------------------------------------------------------------------------------------

def test_ac_c1_actualizar_token_push_en_servicio(db, usuario, monkeypatch):
    """AC-C1: Asociar token push al dispositivo registrado."""
    identificador = uuid.uuid4()
    dispositivo_mock = SimpleNamespace(
        id_dispositivo=1,
        identificador=identificador,
        id_cliente=10,
        plataforma="flutter",
        codigo_corto="ABCD",
        registrado_en=datetime.now(timezone.utc),
        ultima_descarga_en=None,
        token_push=None,
    )

    monkeypatch.setattr(
        "modules.sincronizacion.cu14_dispositivo_catalogo.servicio.exigir_cliente",
        lambda _db, _u: 10,
    )
    monkeypatch.setattr(
        "modules.sincronizacion.cu14_dispositivo_catalogo.servicio.SuscripcionServicio.validar",
        lambda _db, funcionalidad: None,
    )
    monkeypatch.setattr(
        "modules.sincronizacion.cu14_dispositivo_catalogo.servicio.DispositivoRepositorio.insertar_si_falta",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "modules.sincronizacion.cu14_dispositivo_catalogo.servicio.DispositivoRepositorio.por_identificador",
        lambda _db, _id, **kw: dispositivo_mock,
    )
    monkeypatch.setattr(
        "modules.sincronizacion.cu14_dispositivo_catalogo.servicio.ParametrosEmpresaServicio.vigentes",
        lambda _db: SimpleNamespace(
            operacion_offline_habilitada=True,
            dias_antiguedad_offline=7,
            horas_vencimiento_reserva=24,
            moneda="BOB",
        ),
    )
    monkeypatch.setattr(
        "modules.sincronizacion.cu14_dispositivo_catalogo.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro",
        classmethod(lambda cls, **kw: None),
    )

    # Actualizar token push
    payload_token = DispositivoTokenPushIn(
        identificador=identificador, token_push="fcm_token_nuevo_abc"
    )
    res_token = DispositivoServicio.actualizar_token_push(db, usuario, payload_token)
    assert res_token.ok is True
    assert res_token.token_push == "fcm_token_nuevo_abc"
    assert dispositivo_mock.token_push == "fcm_token_nuevo_abc"


# ---------------------------------------------------------------------------------------------
# AC-C6: Aislamiento de dispositivos por empresa
# ---------------------------------------------------------------------------------------------

def test_ac_c6_notificar_cliente_consulta_dispositivos(db, monkeypatch):
    """AC-C6: notificar_cliente programa pushes a los dispositivos con token del cliente."""
    dev1 = SimpleNamespace(id_dispositivo=1, id_cliente=10, token_push="token_tenant_a")
    dev2 = SimpleNamespace(id_dispositivo=2, id_cliente=10, token_push="")

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [dev1, dev2]
    mock_exec = MagicMock()
    mock_exec.scalars.return_value = mock_scalars

    monkeypatch.setattr(db, "execute", lambda stmt: mock_exec)

    total = notificar_cliente(
        db,
        id_cliente=10,
        titulo="Aviso Boutique",
        cuerpo="Contenido exclusivo",
        datos={"pantalla": "avisos"},
    )
    # Solo dev1 tiene token no vacío
    assert total == 1

    db.commit()
    historial = obtener_historial_pruebas()
    assert len(historial) == 1
    assert historial[0]["token"] == "token_tenant_a"
    assert historial[0]["titulo"] == "Aviso Boutique"


# ---------------------------------------------------------------------------------------------
# AC-C7: Endpoint protegido /api/v1/reservas/vencer-expiradas con X-Tareas-Token
# ---------------------------------------------------------------------------------------------

def test_ac_c7_endpoint_vencer_reservas_seguridad(db):
    """AC-C7: /api/v1/reservas/vencer-expiradas exige cabecera X-Tareas-Token correcta."""
    from core.database import get_db
    app.dependency_overrides[get_db] = lambda: db
    try:
        cliente = TestClient(app)

        # 1. Sin cabecera -> 401
        resp = cliente.post("/api/v1/reservas/vencer-expiradas")
        assert resp.status_code == 401

        # 2. Con cabecera incorrecta -> 401
        resp = cliente.post(
            "/api/v1/reservas/vencer-expiradas",
            headers={"X-Tareas-Token": "token-falso-erroneo"},
        )
        assert resp.status_code == 401

        # 3. Con cabecera válida -> 200
        with patch(
            "modules.reservas.cu13_consultar_cancelar_reservas.servicio.ReservaConsultaServicio.vencer_todas_expiradas",
            return_value=3,
        ):
            resp = cliente.post(
                "/api/v1/reservas/vencer-expiradas",
                headers={"X-Tareas-Token": settings.TAREAS_TOKEN},
            )
            assert resp.status_code == 200
            datos = resp.json()
            assert datos["ok"] is True
            assert datos["vencidas_total"] == 3
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------------------------
# Eventos AC-C2: Disparadores de notificaciones
# ---------------------------------------------------------------------------------------------

def test_evento_aviso_dispara_push(db, monkeypatch):
    """Evento 4: Creación de aviso en sincronización/conflictos programa push con pantalla 'avisos'."""
    dev = SimpleNamespace(id_dispositivo=101, id_cliente=25, token_push="token_push_cliente_25")
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [dev]
    mock_exec = MagicMock()
    mock_exec.scalars.return_value = mock_scalars
    monkeypatch.setattr(db, "execute", lambda stmt: mock_exec)

    AvisosServicio.crear(
        db,
        id_cliente=25,
        tipo="reembolso_aceptado",
        titulo="Reembolso Aprobado",
        mensaje="Tu reembolso por falta de stock ha sido aprobado.",
        id_venta=50,
    )
    db.commit()

    historial = obtener_historial_pruebas()
    assert len(historial) == 1
    assert historial[0]["token"] == "token_push_cliente_25"
    assert historial[0]["datos"]["pantalla"] == "avisos"
    assert historial[0]["datos"]["id"] == "50"


def test_evento_pago_y_retiro_disparan_push(db, monkeypatch):
    """Eventos 5 y 6: Pago confirmado y Pedido listo para recoger (retiro en sucursal)."""
    dev = SimpleNamespace(id_dispositivo=202, id_cliente=30, token_push="token_cliente_pago")
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [dev]
    mock_exec = MagicMock()
    mock_exec.scalars.return_value = mock_scalars
    monkeypatch.setattr(db, "execute", lambda stmt: mock_exec)

    venta = SimpleNamespace(
        id_venta=77,
        numero_comprobante="CMP-2026-00077",
        id_cliente=30,
        id_sucursal=1,
        tipo_venta="online",
        estado="pendiente",
        total=Decimal("450.00"),
        tipo_entrega="retiro_sucursal",
    )

    with patch.object(PagoServicio, "_consolidar_inventario"), \
         patch.object(PagoServicio, "_retirar_de_la_bolsa"):
        PagoServicio.completar_venta_cobrada(db, venta, id_usuario_responsable=1)
        db.commit()

    historial = obtener_historial_pruebas()
    assert len(historial) == 2
    titulos = [h["titulo"] for h in historial]
    assert "Pago confirmado" in titulos
    assert "Pedido listo para recoger" in titulos
    for h in historial:
        assert h["datos"]["pantalla"] == "compras"
        assert h["datos"]["id"] == "77"


def test_evento_reserva_cancelada_dispara_push(db, usuario, monkeypatch):
    """Evento 2: Cancelación de reserva por el cliente dispara push con pantalla 'reservas'."""
    reserva_mock = SimpleNamespace(
        id_reserva=15,
        id_cliente=10,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc),
        fecha_hora_atencion=datetime.now(timezone.utc),
        detalles=[],
    )

    dev = SimpleNamespace(id_dispositivo=303, id_cliente=10, token_push="token_reserva_cliente")
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [dev]
    mock_exec = MagicMock()
    mock_exec.scalars.return_value = mock_scalars
    monkeypatch.setattr(db, "execute", lambda stmt: mock_exec)

    monkeypatch.setattr(
        "modules.reservas.cu13_consultar_cancelar_reservas.repositorio.ReservaConsultaRepositorio.obtener_reserva_para_actualizar",
        lambda _db, _id: reserva_mock,
    )
    monkeypatch.setattr(
        "modules.reservas.cu13_consultar_cancelar_reservas.servicio.ReservaConsultaServicio._vencer_si_corresponde",
        lambda _db, _r, _u: False,
    )
    monkeypatch.setattr(
        "modules.reservas.cu13_consultar_cancelar_reservas.servicio.ReservaConsultaServicio._liberar_stock",
        lambda _db, _r, _u, _m: None,
    )
    monkeypatch.setattr(
        "modules.seguridad.cu30_bitacora.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro",
        classmethod(lambda cls, **kw: None),
    )
    monkeypatch.setattr(
        "modules.reservas.cu13_consultar_cancelar_reservas.servicio.ReservaConsultaServicio._construir_salida",
        lambda _r: SimpleNamespace(id_reserva=15, estado="cancelada"),
    )

    # El datetime de atención en el futuro para que no rechace por hora de cita
    from datetime import timedelta
    reserva_mock.fecha_hora_atencion = datetime.now(timezone.utc) + timedelta(days=2)

    ReservaConsultaServicio.cancelar_reserva(
        db, usuario, id_reserva=15, payload=ReservaCancelarIn(motivo="Viaje de improvisto")
    )

    historial = obtener_historial_pruebas()
    assert len(historial) == 1
    assert historial[0]["token"] == "token_reserva_cliente"
    assert historial[0]["titulo"] == "Reserva cancelada"
    assert historial[0]["datos"]["pantalla"] == "reservas"
    assert historial[0]["datos"]["id"] == "15"
