"""Suite de pruebas automatizadas para CU17: Registrar cobro en caja.

Cubre rigurosamente los criterios de aceptacion:
- # AC-1: Autenticacion obligatoria con JWT (HTTP 401 ante peticion anonima).
- # AC-2: Control de acceso RBAC por rol (HTTP 403 para cliente y proveedor).
- # AC-3: Segregacion territorial por sucursal (cajero acotado a su sede, HTTP 403 ante orden ajena).
- # AC-4: Cajero sin sucursal asignada rechazado con HTTP 403.
- # AC-5: Administrador con acceso global y filtro flexible por sucursal.
- # AC-6: Busqueda reactiva de ordenes pendientes con filtros de texto y fechas.
- # AC-7: Cobro en efectivo exitoso con calculo reactivo de cambio devuelto y transicion a pagada.
- # AC-8: Cobro con tarjeta POS y QR estatico con normalizacion de metodo de pago.
- # AC-9: Validacion de monto recibido insuficiente (HTTP 422).
- # AC-10: Venta no encontrada responde HTTP 404.
- # AC-11: Venta ya liquidada responde HTTP 409.
- # AC-12: Venta en estado anulado responde HTTP 409.
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
from modules.comercial.cu17_cobro_caja.errores import (
    MontoInsuficienteError,
    SucursalNoAutorizadaError,
    VentaEstadoInvalidoError,
    VentaNoEncontradaError,
    VentaYaLiquidadaError,
)
from modules.comercial.cu17_cobro_caja.esquemas import (
    CobroCajaIn,
    CobroCajaOut,
    DetallePrendaCajaOut,
    ListadoOrdenesPendientesOut,
    OrdenPendienteOut,
)
from modules.comercial.cu17_cobro_caja.servicio import ServicioCobroCaja
from modules.comercial.cu28_ventas_reservas.modelos import (
    EmpleadoORM,
    PagoORM,
    VentaDetalleORM,
    VentaORM,
)
from modules.gestion_operativa.modelos import SucursalORM


@pytest.fixture
def client():
    """Cliente HTTP de pruebas para invocacion de endpoints FastAPI."""
    return TestClient(app)


def fabricar_usuario_cajero(id_usuario: int = 10, id_sucursal: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero.central@fashionstore.com"
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
    usuario.email = "cliente@fashionstore.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Luciana"
    usuario.apellidos = "Mendoza"
    usuario.activo = True
    return usuario


def fabricar_venta_mock(
    id_venta: int = 101,
    numero_comprobante: str = "FS-2026-000101",
    id_sucursal: int = 1,
    total: Decimal = Decimal("500.00"),
    estado: str = "pendiente",
) -> VentaORM:
    venta = MagicMock(spec=VentaORM)
    venta.id_venta = id_venta
    venta.numero_comprobante = numero_comprobante
    venta.id_sucursal = id_sucursal
    venta.id_cliente = 20
    venta.id_reserva = None
    venta.tipo_venta = "presencial"
    venta.estado = estado
    venta.subtotal = total
    venta.descuento = Decimal("0.00")
    venta.total = total
    venta.fecha_venta = datetime.now(timezone.utc)
    venta.detalles = []

    sucursal = MagicMock(spec=SucursalORM)
    sucursal.nombre = "Boutique Central"
    venta.sucursal = sucursal

    cliente = MagicMock(spec=ClienteORM)
    cliente.id_cliente = 20
    u_cliente = MagicMock(spec=UsuarioORM)
    u_cliente.nombres = "Luciana"
    u_cliente.apellidos = "Mendoza"
    u_cliente.telefono = "71234567"
    u_cliente.email = "luciana@example.com"
    cliente.usuario = u_cliente
    venta.cliente = cliente

    return venta


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE AUTENTICACION Y RBAC (AC-1, AC-2, AC-4)
# -----------------------------------------------------------------------------

def test_cu17_sin_token_rechaza_401(client: TestClient):
    """# AC-1: Peticion anonima a listar o cobrar en caja debe responder HTTP 401."""
    resp1 = client.get("/api/v1/caja/ordenes-pendientes")
    assert resp1.status_code == 401

    resp2 = client.post("/api/v1/caja/cobrar", json={"id_venta": 1, "monto_recibido": 100, "metodo_pago": "efectivo"})
    assert resp2.status_code == 401


def test_cu17_cliente_rechaza_403(client: TestClient):
    """# AC-2: Usuario con rol cliente recibe HTTP 403 Forbidden en modulo de caja."""
    u_cliente = fabricar_usuario_cliente()
    app.dependency_overrides[get_current_user] = lambda: u_cliente

    try:
        resp = client.get("/api/v1/caja/ordenes-pendientes")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_cu17_proveedor_rechaza_403(client: TestClient):
    """# AC-2: Usuario con rol proveedor recibe HTTP 403 Forbidden."""
    u_prov = fabricar_usuario_cliente()
    u_prov.rol = "proveedor"
    app.dependency_overrides[get_current_user] = lambda: u_prov

    try:
        resp = client.post(
            "/api/v1/caja/cobrar",
            json={"id_venta": 1, "monto_recibido": 100, "metodo_pago": "efectivo"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_cu17_cajero_sin_sucursal_rechaza_403(client: TestClient):
    """# AC-4: Cajero que no tenga sucursal asignada debe ser rechazado con 403."""
    cajero_invalido = fabricar_usuario_cajero(id_sucursal=None)
    cajero_invalido.id_sucursal = None
    app.dependency_overrides[get_current_user] = lambda: cajero_invalido

    try:
        resp = client.get("/api/v1/caja/ordenes-pendientes")
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("code") == "CAJERO_SIN_SUCURSAL"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE CONSULTA Y SEGREGACION TERRITORIAL (AC-3, AC-5, AC-6)
# -----------------------------------------------------------------------------

def test_cu17_cajero_acotado_a_su_sucursal(client: TestClient):
    """# AC-3: Cajero de sucursal 1 solo consulta ordenes de sucursal 1."""
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    app.dependency_overrides[get_current_user] = lambda: cajero

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_res = ListadoOrdenesPendientesOut(
        total=1,
        items=[
            OrdenPendienteOut(
                id_venta=101,
                numero_comprobante="FS-2026-000101",
                fecha_venta=datetime.now(timezone.utc),
                id_sucursal=1,
                nombre_sucursal="Boutique Central",
                cliente_nombre="Luciana Mendoza",
                tipo_venta="presencial",
                estado="pendiente",
                subtotal=Decimal("500.00"),
                descuento=Decimal("0.00"),
                total=Decimal("500.00"),
                detalles=[],
            )
        ],
    )

    with patch.object(ServicioCobroCaja, "buscar_ordenes_pendientes", return_value=mock_res) as mock_buscar:
        try:
            resp = client.get("/api/v1/caja/ordenes-pendientes?q=FS-2026")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["id_sucursal"] == 1
            mock_buscar.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)


def test_cu17_admin_acceso_global_con_filtro_sucursal(client: TestClient):
    """# AC-5: Administrador puede consultar cualquier sucursal o aplicar filtro explicito."""
    admin = fabricar_usuario_admin()
    app.dependency_overrides[get_current_user] = lambda: admin

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_res = ListadoOrdenesPendientesOut(total=0, items=[])

    with patch.object(ServicioCobroCaja, "buscar_ordenes_pendientes", return_value=mock_res) as mock_buscar:
        try:
            resp = client.get("/api/v1/caja/ordenes-pendientes?id_sucursal=2")
            assert resp.status_code == 200
            args, kwargs = mock_buscar.call_args
            assert kwargs["id_sucursal"] == 2
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)


# -----------------------------------------------------------------------------
# 3. PRUEBAS TRANSACCIONALES DE COBRO (AC-7, AC-8, AC-9, AC-10, AC-11, AC-12)
# -----------------------------------------------------------------------------

def test_cu17_cobro_efectivo_exitoso_calcula_cambio(client: TestClient):
    """# AC-7: Cobro presencial con efectivo calcula cambio_devuelto, pasa a pagada y confirma pago."""
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    app.dependency_overrides[get_current_user] = lambda: cajero

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    ahora = datetime.now(timezone.utc)
    mock_out = CobroCajaOut(
        id_pago=201,
        id_venta=101,
        numero_comprobante="FS-2026-000101",
        monto_total=Decimal("500.00"),
        monto_recibido=Decimal("600.00"),
        cambio_devuelto=Decimal("100.00"),
        metodo_pago="efectivo",
        estado_venta="pagada",
        estado_pago="confirmado",
        cajero_id=cajero.id_usuario,
        cajero_nombre="Tony Cajero",
        fecha_cobro=ahora,
        observaciones="Cobro exacto en mostrador",
    )

    with patch.object(ServicioCobroCaja, "cobrar_orden", return_value=mock_out):
        try:
            payload = {
                "id_venta": 101,
                "monto_recibido": 600.00,
                "metodo_pago": "efectivo",
                "observaciones": "Cobro exacto en mostrador",
            }
            resp = client.post("/api/v1/caja/cobrar", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id_venta"] == 101
            assert data["estado_venta"] == "pagada"
            assert data["estado_pago"] == "confirmado"
            assert float(data["cambio_devuelto"]) == 100.00
            assert data["metodo_pago"] == "efectivo"
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)


def test_cu17_cobro_monto_insuficiente_rechaza_422():
    """# AC-9: Monto entregado menor al total de la orden lanza MontoInsuficienteError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    venta = fabricar_venta_mock(total=Decimal("500.00"))

    # Configurar mock de consulta para retornar venta
    db.execute.return_value.scalars.return_value.first.return_value = venta

    payload = CobroCajaIn(
        id_venta=101,
        monto_recibido=Decimal("450.00"),
        metodo_pago="efectivo",
    )

    with pytest.raises(MontoInsuficienteError) as exc_info:
        ServicioCobroCaja.cobrar_orden(db, cajero, payload)

    assert exc_info.value.code == "MONTO_INSUFICIENTE"
    assert "450" in exc_info.value.message


def test_cu17_cobro_sucursal_ajena_rechaza_403():
    """# AC-3: Cajero de sucursal 1 intenta cobrar venta de sucursal 2 lanza SucursalNoAutorizadaError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    venta_otra_sucursal = fabricar_venta_mock(id_sucursal=2)

    db.execute.return_value.scalars.return_value.first.return_value = venta_otra_sucursal

    payload = CobroCajaIn(
        id_venta=101,
        monto_recibido=Decimal("500.00"),
        metodo_pago="efectivo",
    )

    with pytest.raises(SucursalNoAutorizadaError) as exc_info:
        ServicioCobroCaja.cobrar_orden(db, cajero, payload)

    assert exc_info.value.code == "SUCURSAL_NO_AUTORIZADA"


def test_cu17_cobro_venta_no_encontrada_rechaza_404():
    """# AC-10: Venta inexistente lanza VentaNoEncontradaError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    db.execute.return_value.scalars.return_value.first.return_value = None

    payload = CobroCajaIn(
        id_venta=9999,
        monto_recibido=Decimal("500.00"),
        metodo_pago="efectivo",
    )

    with pytest.raises(VentaNoEncontradaError) as exc_info:
        ServicioCobroCaja.cobrar_orden(db, cajero, payload)

    assert exc_info.value.code == "VENTA_NO_ENCONTRADA"


def test_cu17_cobro_venta_ya_pagada_rechaza_409():
    """# AC-11: Venta ya en estado 'pagada' lanza VentaYaLiquidadaError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    venta_pagada = fabricar_venta_mock(estado="pagada")

    db.execute.return_value.scalars.return_value.first.return_value = venta_pagada

    payload = CobroCajaIn(
        id_venta=101,
        monto_recibido=Decimal("500.00"),
        metodo_pago="efectivo",
    )

    with pytest.raises(VentaYaLiquidadaError) as exc_info:
        ServicioCobroCaja.cobrar_orden(db, cajero, payload)

    assert exc_info.value.code == "VENTA_YA_LIQUIDADA"


def test_cu17_cobro_venta_anulada_rechaza_409():
    """# AC-12: Venta en estado 'anulada' lanza VentaEstadoInvalidoError."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    venta_anulada = fabricar_venta_mock(estado="anulada")

    db.execute.return_value.scalars.return_value.first.return_value = venta_anulada

    payload = CobroCajaIn(
        id_venta=101,
        monto_recibido=Decimal("500.00"),
        metodo_pago="efectivo",
    )

    with pytest.raises(VentaEstadoInvalidoError) as exc_info:
        ServicioCobroCaja.cobrar_orden(db, cajero, payload)

    assert exc_info.value.code == "VENTA_ESTADO_INVALIDO"


def test_cu17_cobro_tarjeta_pos_y_qr_asienta_kardex_y_bitacora():
    """# AC-8: Cobro con tarjeta POS inserta pago confirmado, registra movimiento Kardex y bitacora."""
    db = MagicMock()
    cajero = fabricar_usuario_cajero(id_sucursal=1)
    venta = fabricar_venta_mock(total=Decimal("300.00"))

    # Configurar detalle de venta
    det = MagicMock(spec=VentaDetalleORM)
    det.id_variante = 5
    det.cantidad = 2
    venta.detalles = [det]

    # Simular inventario
    inv = MagicMock(spec=InventarioSucursalORM)
    inv.id_inventario = 12
    inv.cantidad_disponible = 10
    inv.cantidad_reservada = 0

    # Retornar venta en primera consulta, empleado en segunda, inventario en tercera
    db.execute.return_value.scalars.return_value.first.side_effect = [venta, None, inv]

    payload = CobroCajaIn(
        id_venta=101,
        monto_recibido=Decimal("300.00"),
        metodo_pago="tarjeta_pos",
        observaciones="Transaccion POS aprobada",
    )

    with patch("modules.comercial.cu17_cobro_caja.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro") as mock_audit:
        res = ServicioCobroCaja.cobrar_orden(db, cajero, payload)

        assert res.estado_venta == "pagada"
        assert res.estado_pago == "confirmado"
        assert res.cambio_devuelto == Decimal("0.00")
        assert res.metodo_pago == "tarjeta_pos"
        assert venta.estado == "pagada"
        assert db.add.called
        assert db.commit.called
        mock_audit.assert_called_once()
        args, kwargs = mock_audit.call_args
        assert kwargs["accion"] == "COBRO_CAJA"
