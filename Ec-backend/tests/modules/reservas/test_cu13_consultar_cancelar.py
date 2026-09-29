"""Pruebas de CU13 (Consultar y cancelar reservas) y CU14 (Consultar estado de reserva).

Cada prueba cita el escenario Gherkin que verifica, definido en
`.specs/changes/CU13-CU14-consultar-cancelar-reservas/spec.md`, sección A.3.

El repositorio se sustituye siempre por dobles (`patch.multiple`): la suite no sale a la red ni
depende del orden de las consultas SQL, igual que en `test_cu16_pagos.py`.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import (
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    SucursalORM,
    TallaORM,
    VarianteProductoORM,
)
from modules.comercial.cu28_ventas_reservas.modelos import ReservaDetalleORM, ReservaORM
from modules.reservas.cu13_consultar_cancelar_reservas.repositorio import (
    ReservaConsultaRepositorio,
)
from modules.reservas.modelos import MovimientoInventarioORM

AHORA = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fábricas de datos
# ---------------------------------------------------------------------------


def usuario_cliente(id_usuario: int = 10) -> UsuarioORM:
    return UsuarioORM(
        id_usuario=id_usuario,
        email="madame.dubois@fashionstore.com",
        rol="cliente",
        nombres="Madame",
        apellidos="Dubois",
        activo=True,
    )


def crear_sucursal(id_sucursal: int = 1) -> SucursalORM:
    return SucursalORM(
        id_sucursal=id_sucursal,
        id_ciudad=1,
        nombre="Atelier Serrano - Madrid",
        direccion="Calle Serrano 48",
        activa=True,
    )


def crear_variante(id_variante: int = 10) -> VarianteProductoORM:
    variante = VarianteProductoORM(
        id_variante=id_variante,
        id_producto=1,
        id_talla=2,
        id_color=1,
        sku="ATEL-2025-VD9-38-MAR",
        precio_extra=Decimal("0.00"),
    )
    variante.producto = ProductoORM(
        id_producto=1,
        id_categoria=1,
        nombre="Vestido Plisado en Seda Marfil Natural",
        precio_base=Decimal("890.00"),
        imagen_url="https://cdn.fashionstore.test/vestido.jpg",
        activo=True,
    )
    variante.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    variante.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F2EB")
    return variante


def crear_reserva(
    id_reserva: int = 501,
    id_cliente: int = 10,
    estado: str = "pendiente",
    minutos_hasta_la_cita: int = 60,
    cantidad: int = 1,
    id_variante: int = 10,
) -> ReservaORM:
    """Reserva con una línea, en el estado y horario indicados.

    `minutos_hasta_la_cita` positivo = cita futura; negativo = cita ya pasada hace esos minutos.
    """
    reserva = ReservaORM(
        id_reserva=id_reserva,
        id_cliente=id_cliente,
        id_sucursal=1,
        fecha_hora_atencion=AHORA + timedelta(minutes=minutos_hasta_la_cita),
        estado=estado,
        canal_origen="web",
        creado_en=AHORA - timedelta(days=1),
        observacion=None,
    )
    reserva.sucursal = crear_sucursal()
    detalle = ReservaDetalleORM(
        id_reserva_detalle=1,
        id_reserva=id_reserva,
        id_variante=id_variante,
        cantidad=cantidad,
    )
    detalle.variante = crear_variante(id_variante)
    reserva.detalles = [detalle]
    return reserva


def crear_inventario(
    id_inventario: int = 100,
    id_variante: int = 10,
    cantidad_disponible: int = 5,
    cantidad_reservada: int = 1,
) -> InventarioSucursalORM:
    return InventarioSucursalORM(
        id_inventario=id_inventario,
        id_variante=id_variante,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=cantidad_disponible,
        cantidad_reservada=cantidad_reservada,
    )


def crear_movimiento_reserva(id_inventario: int = 100) -> MovimientoInventarioORM:
    return MovimientoInventarioORM(
        id_movimiento=900,
        id_inventario=id_inventario,
        tipo_movimiento="reserva",
        cantidad=1,
        referencia_documento="RESERVA-501",
        motivo="Apartado para cita",
        saldo_anterior=6,
        saldo_nuevo=5,
    )


def preparar(
    reservas: list | None = None,
    reserva_individual: ReservaORM | None = None,
    movimiento: MovimientoInventarioORM | None = None,
    inventario: InventarioSucursalORM | None = None,
    sin_movimiento: bool = False,
    sin_inventario: bool = False,
):
    """Sustituye el repositorio de CU13 por dobles deterministas."""
    dobles = {}
    if reservas is not None:
        dobles["buscar_reservas_de_cliente"] = staticmethod(
            lambda db, id_cliente: reservas
        )
    if reserva_individual is not None:
        dobles["obtener_reserva_para_actualizar"] = staticmethod(
            lambda db, id_reserva: reserva_individual if id_reserva == reserva_individual.id_reserva else None
        )
    if sin_movimiento:
        dobles["buscar_movimiento_reserva"] = staticmethod(lambda db, id_reserva, id_variante: None)
    elif movimiento is not None:
        dobles["buscar_movimiento_reserva"] = staticmethod(
            lambda db, id_reserva, id_variante: movimiento
        )
    if sin_inventario:
        dobles["obtener_inventario_por_id"] = staticmethod(lambda db, id_inventario: None)
    elif inventario is not None:
        dobles["obtener_inventario_por_id"] = staticmethod(
            lambda db, id_inventario: inventario
        )
    dobles.setdefault(
        "registrar_movimiento_liberacion",
        staticmethod(lambda **kwargs: MovimientoInventarioORM(**{
            k: v for k, v in kwargs.items() if k not in ("db", "id_usuario", "referencia", "motivo")
        })),
    )
    return patch.multiple(ReservaConsultaRepositorio, **dobles)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def sesion_autenticada(db):
    usuario = usuario_cliente()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario
    yield usuario
    app.dependency_overrides.clear()


# ===========================================================================
# Escenario: Consultar mis reservas
# ===========================================================================


def test_consultar_mis_reservas_separa_proximas_e_historial(client, sesion_autenticada, db):
    pendiente = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=120)
    cancelada = crear_reserva(id_reserva=2, estado="cancelada", minutos_hasta_la_cita=-500)

    with preparar(reservas=[pendiente, cancelada]):
        respuesta = client.get("/api/v1/reservas/mias")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos["proximas"]) == 1
    assert datos["proximas"][0]["id_reserva"] == 1
    assert datos["proximas"][0]["puede_cancelar"] is True
    assert len(datos["historial"]) == 1
    assert datos["historial"][0]["id_reserva"] == 2
    assert datos["historial"][0]["puede_cancelar"] is False
    assert datos["resumen"]["activas"] == 1
    assert datos["resumen"]["proxima"]["id_reserva"] == 1


def test_consultar_sin_reservas_responde_200_vacio(client, sesion_autenticada, db):
    with preparar(reservas=[]):
        respuesta = client.get("/api/v1/reservas/mias")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["resumen"] == {"activas": 0, "proxima": None}
    assert datos["proximas"] == []
    assert datos["historial"] == []


def test_reserva_out_expone_prendas_para_cu14(client, sesion_autenticada, db):
    """CU14: la propia lista ya trae el detalle completo de la cita (decisión D5)."""
    reserva = crear_reserva(id_reserva=1, estado="confirmada", minutos_hasta_la_cita=90, cantidad=2)

    with preparar(reservas=[reserva]):
        respuesta = client.get("/api/v1/reservas/mias")

    item = respuesta.json()["proximas"][0]
    assert item["estado"] == "confirmada"
    assert item["sucursal"]["nombre"] == "Atelier Serrano - Madrid"
    assert item["items"][0]["nombre_producto"] == "Vestido Plisado en Seda Marfil Natural"
    assert item["items"][0]["talla_codigo"] == "38"
    assert item["items"][0]["color_hex"] == "#F5F2EB"
    assert item["items"][0]["cantidad"] == 2
    assert item["total_prendas"] == 2
    assert item["codigo_reserva"].startswith("RES-")


def test_pendiente_vencida_por_tolerancia_libera_stock_al_listar(client, sesion_autenticada, db):
    """Gherkin «Reserva vencida»: la cita pasó hace más de 2h y nadie la atendió."""
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=-200)
    inventario = crear_inventario(cantidad_disponible=5, cantidad_reservada=1)
    movimiento = crear_movimiento_reserva()

    with preparar(reservas=[reserva], reserva_individual=reserva, movimiento=movimiento, inventario=inventario):
        respuesta = client.get("/api/v1/reservas/mias")

    assert respuesta.status_code == 200
    assert reserva.estado == "vencida"
    assert inventario.cantidad_disponible == 6
    assert inventario.cantidad_reservada == 0
    datos = respuesta.json()
    assert datos["historial"][0]["estado"] == "vencida"
    assert datos["resumen"]["activas"] == 0


def test_pendiente_con_cita_reciente_no_vence_todavia(client, sesion_autenticada, db):
    """La tolerancia de 2h aún no se cumplió: sigue pendiente y en 'proximas'."""
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=-30)

    with preparar(reservas=[reserva]):
        respuesta = client.get("/api/v1/reservas/mias")

    assert reserva.estado == "pendiente"
    assert respuesta.json()["proximas"][0]["estado"] == "pendiente"
    # Ya pasó la hora de la cita: no se puede cancelar, pero tampoco venció aún.
    assert respuesta.json()["proximas"][0]["puede_cancelar"] is False


def test_reserva_ya_vencida_no_se_libera_dos_veces_al_listar(client, sesion_autenticada, db):
    """Idempotencia del vencimiento perezoso: una reserva que ya está 'vencida' no vuelve a
    intentar liberar stock (ni siquiera se relee con bloqueo)."""
    reserva = crear_reserva(id_reserva=1, estado="vencida", minutos_hasta_la_cita=-500)
    llamadas_bloqueo = []

    def fake_obtener_con_bloqueo(db_, id_reserva):
        llamadas_bloqueo.append(id_reserva)
        return reserva

    with preparar(reservas=[reserva]), patch.object(
        ReservaConsultaRepositorio,
        "obtener_reserva_para_actualizar",
        staticmethod(fake_obtener_con_bloqueo),
    ), patch.object(
        ReservaConsultaRepositorio, "registrar_movimiento_liberacion"
    ) as mock_liberar:
        respuesta = client.get("/api/v1/reservas/mias")

    assert respuesta.status_code == 200
    assert respuesta.json()["historial"][0]["estado"] == "vencida"
    assert llamadas_bloqueo == []  # nunca se relee con FOR UPDATE: ya no es candidata
    mock_liberar.assert_not_called()


def test_reservas_no_expone_la_de_otro_cliente(client, sesion_autenticada, db):
    """El repositorio filtra por id_cliente; aquí se comprueba que se le pasa el id correcto."""
    reserva = crear_reserva(id_reserva=1, id_cliente=999)
    capturado = {}

    def fake_buscar(db_, id_cliente):
        capturado["id_cliente"] = id_cliente
        return [reserva]

    with patch.object(ReservaConsultaRepositorio, "buscar_reservas_de_cliente", staticmethod(fake_buscar)):
        client.get("/api/v1/reservas/mias")

    assert capturado["id_cliente"] == 10  # el usuario autenticado, no el dueño real de la reserva


def test_reservas_mias_requiere_autenticacion(client):
    assert client.get("/api/v1/reservas/mias").status_code == 401


# ===========================================================================
# Escenario: Cancelar una reserva
# ===========================================================================


def test_cancelar_reserva_pendiente_libera_stock_y_registra_movimiento(client, sesion_autenticada, db):
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=120, cantidad=2)
    inventario = crear_inventario(cantidad_disponible=5, cantidad_reservada=3)
    movimiento = crear_movimiento_reserva()

    with preparar(reserva_individual=reserva, movimiento=movimiento, inventario=inventario):
        respuesta = client.post(
            "/api/v1/reservas/1/cancelar", json={"motivo": "No podré asistir ese día"}
        )

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estado"] == "cancelada"
    assert datos["puede_cancelar"] is False

    assert reserva.estado == "cancelada"
    # Las 2 unidades de la línea vuelven a estar disponibles, en la MISMA fila (no se recalcula).
    assert inventario.cantidad_disponible == 7
    assert inventario.cantidad_reservada == 1


def test_cancelar_reserva_confirmada_tambien_es_valido(client, sesion_autenticada, db):
    reserva = crear_reserva(id_reserva=1, estado="confirmada", minutos_hasta_la_cita=120)
    inventario = crear_inventario()
    movimiento = crear_movimiento_reserva()

    with preparar(reserva_individual=reserva, movimiento=movimiento, inventario=inventario):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Cambio de planes"})

    assert respuesta.status_code == 200
    assert reserva.estado == "cancelada"


def test_cancelar_reserva_ajena_responde_403_sin_tocar_inventario(client, sesion_autenticada, db):
    reserva = crear_reserva(id_reserva=1, id_cliente=999, estado="pendiente")
    inventario = crear_inventario()

    with preparar(reserva_individual=reserva, inventario=inventario):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "No es mía"})

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "RESERVA_AJENA"
    assert reserva.estado == "pendiente"
    assert inventario.cantidad_disponible == 5


def test_cancelar_reserva_inexistente_responde_404(client, sesion_autenticada, db):
    with patch.object(
        ReservaConsultaRepositorio,
        "obtener_reserva_para_actualizar",
        staticmethod(lambda db_, id_reserva: None),
    ):
        respuesta = client.post("/api/v1/reservas/999/cancelar", json={"motivo": "No existe"})

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "RESERVA_NO_ENCONTRADA"


@pytest.mark.parametrize("estado_no_cancelable", ["cancelada", "atendida", "en_atencion"])
def test_cancelar_reserva_no_cancelable_responde_409(client, sesion_autenticada, db, estado_no_cancelable):
    reserva = crear_reserva(id_reserva=1, estado=estado_no_cancelable, minutos_hasta_la_cita=120)
    inventario = crear_inventario()

    with preparar(reserva_individual=reserva, inventario=inventario):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Ya no puedo"})

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "RESERVA_NO_CANCELABLE"
    assert inventario.cantidad_disponible == 5


def test_cancelar_reserva_cuya_hora_ya_llego_responde_409(client, sesion_autenticada, db):
    """Dentro de la tolerancia de 2h tras la cita: ni vencida ni cancelable."""
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=-30)

    with preparar(reserva_individual=reserva):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Llegué tarde"})

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "RESERVA_NO_CANCELABLE"
    assert reserva.estado == "pendiente"


def test_cancelar_reserva_vencida_responde_409_y_libera_en_el_acto(client, sesion_autenticada, db):
    """Si al intentar cancelar resulta que ya venció (tolerancia superada), se libera igual."""
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=-200)
    inventario = crear_inventario(cantidad_disponible=5, cantidad_reservada=1)
    movimiento = crear_movimiento_reserva()

    with preparar(reserva_individual=reserva, movimiento=movimiento, inventario=inventario):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Se me pasó la hora"})

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "RESERVA_VENCIDA"
    assert reserva.estado == "vencida"
    assert inventario.cantidad_disponible == 6


def test_doble_cancelacion_la_segunda_responde_409(client, sesion_autenticada, db):
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=120)
    inventario = crear_inventario(cantidad_disponible=5, cantidad_reservada=1)
    movimiento = crear_movimiento_reserva()

    with preparar(reserva_individual=reserva, movimiento=movimiento, inventario=inventario):
        primera = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Cambio de planes"})
        segunda = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Cambio de planes"})

    assert primera.status_code == 200
    assert segunda.status_code == 409
    assert segunda.json()["code"] == "RESERVA_NO_CANCELABLE"
    # El stock solo se liberó una vez.
    assert inventario.cantidad_disponible == 6
    assert inventario.cantidad_reservada == 0


def test_cancelar_sin_motivo_responde_422(client, sesion_autenticada):
    respuesta = client.post("/api/v1/reservas/1/cancelar", json={})
    assert respuesta.status_code == 422


def test_cancelar_motivo_muy_corto_responde_422(client, sesion_autenticada):
    respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "no"})
    assert respuesta.status_code == 422


def test_cancelar_requiere_autenticacion(client):
    assert client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Motivo válido"}).status_code == 401


# ===========================================================================
# Localización correcta de la fila de inventario (no se adivina la temporada)
# ===========================================================================


def test_cancelar_libera_la_fila_del_movimiento_no_otra_con_mas_stock(client, sesion_autenticada, db):
    """Aunque exista otra fila de la misma variante con más stock, se libera la referenciada."""
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=120)
    # La fila que CU12 apartó realmente (id_inventario=100), distinta de una hipotética
    # id_inventario=200 con más stock que jamás debería tocarse.
    inventario_correcto = crear_inventario(id_inventario=100, cantidad_disponible=5, cantidad_reservada=1)
    movimiento = crear_movimiento_reserva(id_inventario=100)

    llamadas_inventario = []

    def fake_obtener_inventario(db_, id_inventario):
        llamadas_inventario.append(id_inventario)
        return inventario_correcto if id_inventario == 100 else None

    with preparar(reserva_individual=reserva, movimiento=movimiento), patch.object(
        ReservaConsultaRepositorio, "obtener_inventario_por_id", staticmethod(fake_obtener_inventario)
    ):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Cambié de opinión"})

    assert respuesta.status_code == 200
    assert llamadas_inventario == [100]
    assert inventario_correcto.cantidad_disponible == 6


def test_cancelar_sin_movimiento_de_traza_responde_409(client, sesion_autenticada, db):
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=120)

    with preparar(reserva_individual=reserva, sin_movimiento=True):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Cambié de opinión"})

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "RESERVA_SIN_TRAZA"
    assert reserva.estado == "pendiente"


def test_cancelar_con_inventario_insuficiente_responde_409_sin_cambios(client, sesion_autenticada, db):
    """`cantidad_reservada` no alcanza para las unidades de la línea: dato inconsistente, no se toca."""
    reserva = crear_reserva(id_reserva=1, estado="pendiente", minutos_hasta_la_cita=120, cantidad=3)
    inventario = crear_inventario(cantidad_disponible=5, cantidad_reservada=1)  # solo 1, hacen falta 3
    movimiento = crear_movimiento_reserva()

    with preparar(reserva_individual=reserva, movimiento=movimiento, inventario=inventario):
        respuesta = client.post("/api/v1/reservas/1/cancelar", json={"motivo": "Cambié de opinión"})

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "RESERVA_SIN_TRAZA"
    assert reserva.estado == "pendiente"
    assert inventario.cantidad_disponible == 5
    assert inventario.cantidad_reservada == 1


# ===========================================================================
# Servicio: formato del código de reserva compartido con CU12
# ===========================================================================


def test_codigo_reserva_usa_el_mismo_formato_que_cu12():
    from modules.reservas.utilidades import formatear_codigo_reserva

    creado = datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)
    assert formatear_codigo_reserva(12, creado) == "RES-2026-0012"
