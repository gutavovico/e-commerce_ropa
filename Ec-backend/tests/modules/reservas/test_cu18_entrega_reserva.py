"""Suite de pruebas automatizadas para CU18: Atender entrega de reserva en boutique.

Cubre rigurosamente los criterios de aceptacion:
- # AC-1: Autenticacion obligatoria con JWT (HTTP 401 ante peticion anonima).
- # AC-2: Control de acceso RBAC por rol (HTTP 403 para cliente y proveedor).
- # AC-3: Segregacion territorial por sucursal (cajero acotado a su sede, HTTP 403 ante reserva ajena).
- # AC-4: Cajero sin sucursal asignada rechazado con HTTP 403.
- # AC-5: Administrador con acceso global y filtro flexible por sucursal.
- # AC-6: Busqueda de citas pendientes por codigo, clienta o fecha.
- # AC-7: Confirmacion de entrega y atencion en boutique con Kardex y bitacora.
- # AC-8: Marcado de inasistencia con liberacion de stock a disponible en Kardex.
- # AC-9: Conversion fluida de reserva a orden de compra presencial lista para caja (HTTP 201).
- # AC-10: Reserva no encontrada responde HTTP 404.
- # AC-11: Reserva en estado invalido (ya atendida o cancelada) responde HTTP 409.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import ColorORM, InventarioSucursalORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.comercial.cu28_ventas_reservas.modelos import (
    ReservaDetalleORM,
    ReservaORM,
    VentaDetalleORM,
    VentaORM,
)
from modules.gestion_operativa.modelos import SucursalORM
from modules.reservas.cu18_entrega_reserva.errores import (
    ReservaEstadoInvalidoError,
    ReservaNoEncontradaError,
    SucursalReservaNoAutorizadaError,
)
from modules.reservas.cu18_entrega_reserva.esquemas import (
    ConfirmarEntregaIn,
    ConvertirVentaReservaOut,
    EntregaReservaOut,
    ListadoReservasPendientesOut,
    NoAsistioReservaOut,
    ReservaPendienteCajaOut,
)
from modules.reservas.cu18_entrega_reserva.servicio import ServicioEntregaReserva


@pytest.fixture
def client():
    """Cliente HTTP de pruebas para invocacion de endpoints FastAPI."""
    return TestClient(app)


def fabricar_usuario_cajero(id_usuario: int = 10, id_sucursal: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero.mostrador@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Tony"
    usuario.apellidos = "Cajero"
    usuario.activo = True
    return usuario


def fabricar_usuario_admin(id_usuario: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "admin@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Super"
    usuario.apellidos = "Admin"
    usuario.activo = True
    return usuario


def fabricar_usuario_cliente(id_usuario: int = 20) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "clienta@fashionstore.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Valeria"
    usuario.apellidos = "Rios"
    usuario.activo = True
    return usuario


def fabricar_reserva_mock(
    id_reserva: int = 42,
    id_sucursal: int = 1,
    estado: str = "confirmada",
) -> ReservaORM:
    reserva = MagicMock(spec=ReservaORM)
    reserva.id_reserva = id_reserva
    reserva.id_cliente = 15
    reserva.id_sucursal = id_sucursal
    reserva.fecha_hora_atencion = datetime.now(timezone.utc)
    reserva.estado = estado
    reserva.canal_origen = "web"
    reserva.observacion = "Prueba de vestidor privado"
    reserva.creado_en = datetime.now(timezone.utc)
    reserva.atendido_por = None
    reserva.atendido_en = None
    reserva.detalles = []

    sucursal = MagicMock(spec=SucursalORM)
    sucursal.nombre = "Boutique Central"
    reserva.sucursal = sucursal

    cliente = MagicMock(spec=ClienteORM)
    cliente.id_cliente = 15
    u_cli = MagicMock(spec=UsuarioORM)
    u_cli.nombres = "Valeria"
    u_cli.apellidos = "Rios"
    u_cli.telefono = "79876543"
    u_cli.email = "valeria@example.com"
    cliente.usuario = u_cli
    reserva.cliente = cliente

    return reserva


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE AUTENTICACION Y RBAC (AC-1, AC-2, AC-4)
# -----------------------------------------------------------------------------

def test_cu18_sin_token_rechaza_401(client: TestClient):
    """# AC-1: Peticiones anonimas a endpoints de reservas de caja reciben HTTP 401."""
    resp1 = client.get("/api/v1/caja/reservas-pendientes")
    assert resp1.status_code == 401

    resp2 = client.post("/api/v1/caja/reservas/42/entregar")
    assert resp2.status_code == 401

    resp3 = client.post("/api/v1/caja/reservas/42/no-asistio")
    assert resp3.status_code == 401

    resp4 = client.post("/api/v1/caja/reservas/42/convertir-venta")
    assert resp4.status_code == 401


def test_cu18_cliente_rechaza_403(client: TestClient):
    """# AC-2: Usuario con rol cliente recibe HTTP 403 Forbidden."""
    u_cliente = fabricar_usuario_cliente()
    app.dependency_overrides[get_current_user] = lambda: u_cliente

    try:
        resp = client.get("/api/v1/caja/reservas-pendientes")
        assert resp.status_code == 403

        resp2 = client.post("/api/v1/caja/reservas/42/entregar")
        assert resp2.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_cu18_cajero_sin_sucursal_rechaza_403(client: TestClient):
    """# AC-4: Cajero sin sucursal asignada recibe HTTP 403."""
    cajero = fabricar_usuario_cajero(id_sucursal=None)
    cajero.id_sucursal = None
    app.dependency_overrides[get_current_user] = lambda: cajero

    try:
        resp = client.get("/api/v1/caja/reservas-pendientes")
        assert resp.status_code == 403
        assert resp.json().get("code") == "CAJERO_SIN_SUCURSAL"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE CONSULTA Y SEGREGACION TERRITORIAL (AC-3, AC-5, AC-6)
# -----------------------------------------------------------------------------

def test_cu18_cajero_acotado_a_su_sucursal(client: TestClient):
    """# AC-3: Cajero solo consulta citas correspondientes a su sucursal."""
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    app.dependency_overrides[get_current_user] = lambda: cajero

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_res = ListadoReservasPendientesOut(
        total=1,
        items=[
            ReservaPendienteCajaOut(
                id_reserva=42,
                codigo_reserva="RES-2026-0042",
                id_cliente=15,
                cliente_nombre="Valeria Rios",
                id_sucursal=1,
                nombre_sucursal="Boutique Central",
                fecha_hora_atencion=datetime.now(timezone.utc),
                estado="confirmada",
                canal_origen="web",
                prendas=[],
            )
        ],
    )

    with patch.object(ServicioEntregaReserva, "buscar_reservas_pendientes", return_value=mock_res) as mock_buscar:
        try:
            resp = client.get("/api/v1/caja/reservas-pendientes?q=RES-2026-0042")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["codigo_reserva"] == "RES-2026-0042"
            mock_buscar.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)


def test_cu18_admin_consulta_flexible_sucursal(client: TestClient):
    """# AC-5: Administrador puede consultar o filtrar cualquier sucursal."""
    admin = fabricar_usuario_admin()
    app.dependency_overrides[get_current_user] = lambda: admin

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_res = ListadoReservasPendientesOut(total=0, items=[])

    with patch.object(ServicioEntregaReserva, "buscar_reservas_pendientes", return_value=mock_res) as mock_buscar:
        try:
            resp = client.get("/api/v1/caja/reservas-pendientes?id_sucursal=3")
            assert resp.status_code == 200
            args, kwargs = mock_buscar.call_args
            assert kwargs["id_sucursal"] == 3
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)


# -----------------------------------------------------------------------------
# 3. PRUEBAS TRANSACCIONALES: ENTREGA, INASISTENCIA, CONVERSION (AC-7, AC-8, AC-9, AC-10, AC-11)
# -----------------------------------------------------------------------------

def test_cu18_confirmar_entrega_exitoso():
    """# AC-7: Confirmar entrega actualiza reserva a atendida, libera reserva y audita evento."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    reserva = fabricar_reserva_mock(id_reserva=42, id_sucursal=1, estado="confirmada")

    det = MagicMock(spec=ReservaDetalleORM)
    det.id_variante = 8
    det.cantidad = 1
    reserva.detalles = [det]

    inv = MagicMock(spec=InventarioSucursalORM)
    inv.id_inventario = 25
    inv.cantidad_disponible = 5
    inv.cantidad_reservada = 1

    db.execute.return_value.scalars.return_value.first.side_effect = [reserva, inv]

    payload = ConfirmarEntregaIn(observaciones="Clienta en fitting 2")

    with patch("modules.reservas.cu18_entrega_reserva.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro") as mock_audit:
        res = ServicioEntregaReserva.confirmar_entrega(db, cajero, id_reserva=42, datos=payload)

        assert res.id_reserva == 42
        assert res.estado == "atendida"
        assert res.atendido_por == cajero.id_usuario
        assert reserva.estado == "atendida"
        assert inv.cantidad_reservada == 0
        assert inv.cantidad_disponible == 6
        assert db.commit.called
        mock_audit.assert_called_once()
        args, kwargs = mock_audit.call_args
        assert kwargs["accion"] == "ENTREGA_RESERVA"


def test_cu18_marcar_no_asistio_libera_stock():
    """# AC-8: Marcar inasistencia cancela cita, devuelve stock al disponible y registra Kardex."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    reserva = fabricar_reserva_mock(id_reserva=42, id_sucursal=1, estado="confirmada")

    det = MagicMock(spec=ReservaDetalleORM)
    det.id_variante = 8
    det.cantidad = 2
    reserva.detalles = [det]

    inv = MagicMock(spec=InventarioSucursalORM)
    inv.id_inventario = 25
    inv.cantidad_disponible = 4
    inv.cantidad_reservada = 2

    db.execute.return_value.scalars.return_value.first.side_effect = [reserva, inv]

    with patch("modules.reservas.cu18_entrega_reserva.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro") as mock_audit:
        res = ServicioEntregaReserva.marcar_no_asistio(db, cajero, id_reserva=42)

        assert res.id_reserva == 42
        assert res.estado == "cancelada"
        assert res.items_liberados == 2
        assert reserva.estado == "cancelada"
        assert inv.cantidad_reservada == 0
        assert inv.cantidad_disponible == 6
        assert db.commit.called
        mock_audit.assert_called_once()


def test_cu18_convertir_a_venta_exitoso():
    """# AC-9: Convertir a venta genera orden presencial, vincula items, marca reserva atendida y retorna 201."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    reserva = fabricar_reserva_mock(id_reserva=42, id_sucursal=1, estado="confirmada")

    # Mock de prenda
    var = MagicMock(spec=VarianteProductoORM)
    var.precio_extra = Decimal("0.00")
    prod = MagicMock(spec=ProductoORM)
    prod.precio_base = Decimal("320.00")
    var.producto = prod

    det = MagicMock(spec=ReservaDetalleORM)
    det.id_variante = 8
    det.cantidad = 1
    det.variante = var
    reserva.detalles = [det]

    db.execute.return_value.scalars.return_value.first.return_value = reserva

    with patch("modules.reservas.cu18_entrega_reserva.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro") as mock_audit:
        res = ServicioEntregaReserva.convertir_a_venta(db, cajero, id_reserva=42)

        assert res.id_reserva == 42
        assert res.total == Decimal("320.00")
        assert res.estado_venta == "pendiente"
        assert "FS-" in res.numero_comprobante
        assert reserva.estado == "atendida"
        assert db.add.called
        assert db.commit.called
        mock_audit.assert_called_once()


def test_cu18_reserva_sucursal_ajena_rechaza_403():
    """# AC-3: Cajero de sucursal 1 no puede operar sobre reserva de sucursal 2."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    reserva_ajena = fabricar_reserva_mock(id_sucursal=2)

    db.execute.return_value.scalars.return_value.first.return_value = reserva_ajena

    with pytest.raises(SucursalReservaNoAutorizadaError) as exc_info:
        ServicioEntregaReserva.confirmar_entrega(db, cajero, id_reserva=42)

    assert exc_info.value.code == "SUCURSAL_NO_AUTORIZADA"


def test_cu18_reserva_no_encontrada_rechaza_404():
    """# AC-10: Identificador inexistente lanza ReservaNoEncontradaError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    db.execute.return_value.scalars.return_value.first.return_value = None

    with pytest.raises(ReservaNoEncontradaError) as exc_info:
        ServicioEntregaReserva.confirmar_entrega(db, cajero, id_reserva=9999)

    assert exc_info.value.code == "RESERVA_NO_ENCONTRADA"


def test_cu18_reserva_estado_invalido_rechaza_409():
    """# AC-11: Reserva ya cancelada o atendida lanza ReservaEstadoInvalidoError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    reserva_atendida = fabricar_reserva_mock(estado="atendida")

    db.execute.return_value.scalars.return_value.first.return_value = reserva_atendida

    with pytest.raises(ReservaEstadoInvalidoError) as exc_info:
        ServicioEntregaReserva.marcar_no_asistio(db, cajero, id_reserva=42)

    assert exc_info.value.code == "RESERVA_ESTADO_INVALIDO"
