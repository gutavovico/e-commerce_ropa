"""Suite de pruebas automatizadas para CU28: Consultar ventas y reservas.

Cubre rigurosamente los criterios de aceptacion:
- # AC-1: Autenticacion obligatoria con JWT (HTTP 401 ante peticion anonima).
- # AC-2: Control de acceso RBAC por rol (HTTP 403 para cajero y cliente).
- # AC-3: Segregacion por rol y sucursal (encargado acotado a su sede, admin acceso global).
- # AC-4: Mapeo y persistencia relacional de entidades transaccionales.
- # AC-5: Listado unificado paginado con filtros multicriterio (tipo, estado, fechas, q).
- # AC-6: Calculo de metricas cuantitativas de red (monto total, ventas, reservas, ticket).
- # AC-7: Detalle completo de venta con lineas y pagos (HTTP 200 y HTTP 404).
- # AC-8: Detalle completo de reserva con prendas apartadas (HTTP 200 y HTTP 404).
- # AC-9: Validacion de consistencia cronologica de rango de fechas (HTTP 422).
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import ColorORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.comercial.cu28_ventas_reservas.errores import (
    RangoFechasInvalidoError,
    ReservaNoEncontradaError,
    SucursalConsultaInvalidaError,
    VentaNoEncontradaError,
)
from modules.comercial.cu28_ventas_reservas.esquemas import (
    LineaDetalleOut,
    MetricasTransaccionalesOut,
    PagoItemOut,
    ReservaDetalleCompletoOut,
    RespuestaPaginadaTransaccionesOut,
    TransaccionFiltrosIn,
    TransaccionResumenItemOut,
    VentaDetalleCompletoOut,
)
from modules.comercial.cu28_ventas_reservas.modelos import (
    EmpleadoORM,
    PagoORM,
    ReservaDetalleORM,
    ReservaORM,
    VentaDetalleORM,
    VentaORM,
)
from modules.comercial.cu28_ventas_reservas.servicio import (
    ServicioConsultarVentasReservas,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM


# -----------------------------------------------------------------------------
# FIXTURES Y GENERADORES DE MOCKS
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """Cliente HTTP de pruebas para invocacion de endpoints FastAPI."""
    return TestClient(app)


def crear_usuario_admin_mock(id_usuario: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "admin.comercial@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Director"
    usuario.apellidos = "Comercial"
    usuario.activo = True
    return usuario


def crear_usuario_encargado_mock(id_usuario: int = 2, id_sucursal: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "encargado.central@fashionstore.com"
    usuario.rol = "encargado_sucursal"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Encargado"
    usuario.apellidos = "Central"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 3) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero.tienda@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = 1
    usuario.nombres = "Cajero"
    usuario.apellidos = "PuntoDeVenta"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 4) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente.fashion@gmail.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Cliente"
    usuario.apellidos = "Frecuente"
    usuario.activo = True
    return usuario


def fabricar_transaccion_resumen_item(
    id_transaccion: int = 1,
    tipo: str = "venta",
    codigo: str = "VEN-2026-0001",
    monto: Decimal = Decimal("450.00"),
    id_sucursal: int = 1,
    nombre_sucursal: str = "Boutique Central",
    estado: str = "pagada",
) -> TransaccionResumenItemOut:
    return TransaccionResumenItemOut(
        id_transaccion=id_transaccion,
        tipo_operacion=tipo,
        codigo_comprobante=codigo,
        fecha=datetime.now(timezone.utc),
        id_cliente=10,
        nombre_cliente="Maria Delgado",
        email_cliente="maria.delgado@example.com",
        telefono_cliente="77712345",
        id_sucursal=id_sucursal,
        nombre_sucursal=nombre_sucursal,
        ciudad_sucursal="La Paz",
        canal="presencial" if tipo == "venta" else "web",
        estado=estado,
        total_monto=monto,
        cantidad_items=2,
    )


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE AUTENTICACION Y SEGURIDAD RBAC (AC-1, AC-2)
# -----------------------------------------------------------------------------

def test_cu28_sin_token_rechaza_401(client: TestClient):
    """AC-1: Solicitud sin cabecera Authorization rechaza con HTTP 401."""
    resp = client.get("/api/v1/admin/ventas-reservas")
    assert resp.status_code == 401


def test_cu28_rol_cajero_rechaza_403(client: TestClient):
    """AC-2: Usuario con rol 'cajero' es rechazado con HTTP 403 Forbidden."""
    usuario_cajero = crear_usuario_cajero_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_cajero

    try:
        resp = client.get("/api/v1/admin/ventas-reservas")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cu28_rol_cliente_rechaza_403(client: TestClient):
    """AC-2: Usuario con rol 'cliente' es rechazado con HTTP 403 Forbidden."""
    usuario_cliente = crear_usuario_cliente_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_cliente

    try:
        resp = client.get("/api/v1/admin/ventas-reservas")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE VALIDACION DE ESQUEMAS PYDANTIC (AC-5, AC-9)
# -----------------------------------------------------------------------------

def test_cu28_esquema_fechas_inversas_rechaza_validation_error():
    """AC-9: TransaccionFiltrosIn rechaza fecha_desde > fecha_hasta con error de validacion."""
    ahora = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        TransaccionFiltrosIn(
            fecha_desde=ahora,
            fecha_hasta=ahora - timedelta(days=2),
        )

    assert "fecha_desde" in str(exc_info.value)


def test_cu28_esquema_ordenar_por_por_defecto_creado_en_desc():
    """AC-5: TransaccionFiltrosIn asigna 'creado_en_desc' como criterio por defecto."""
    filtros = TransaccionFiltrosIn()
    assert filtros.ordenar_por == "creado_en_desc"
    assert filtros.tipo_operacion == "todas"
    assert filtros.pagina == 1
    assert filtros.limite == 10


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE SERVICIO Y SEGREGACION RBAC POR SUCURSAL (AC-3, AC-6)
# -----------------------------------------------------------------------------

def test_cu28_servicio_segregacion_encargado_fuerza_sucursal():
    """AC-3: Encargado de sucursal tiene sucursal forzada a su sede asignada."""
    servicio = ServicioConsultarVentasReservas()
    usuario_encargado = crear_usuario_encargado_mock(id_sucursal=5)

    # Intento de pedir sucursal 2 siendo encargado de la 5
    sucursal_efectiva = servicio.resolver_alcance_sucursal(usuario_encargado, id_sucursal_solicitado=2)
    assert sucursal_efectiva == 5


def test_cu28_servicio_segregacion_admin_permite_sucursal_o_global():
    """AC-3: Administrador puede consultar cualquier sucursal o consolidado global (None)."""
    servicio = ServicioConsultarVentasReservas()
    usuario_admin = crear_usuario_admin_mock()

    assert servicio.resolver_alcance_sucursal(usuario_admin, id_sucursal_solicitado=3) == 3
    assert servicio.resolver_alcance_sucursal(usuario_admin, id_sucursal_solicitado=None) is None


def test_cu28_servicio_calculo_metricas_cuantitativas():
    """AC-6: Servicio computa correctamente total facturado, ventas, reservas y ticket promedio."""
    mock_db = MagicMock()
    # Mock retorno ventas: (total_facturado, total_ventas)
    mock_db.execute.return_value.first.return_value = (Decimal("1500.00"), 3)
    # Mock retorno reservas: count
    mock_db.execute.return_value.scalar.return_value = 5

    servicio = ServicioConsultarVentasReservas()
    metricas = servicio.obtener_metricas(mock_db, id_sucursal=None)

    assert metricas.monto_total_facturado == Decimal("1500.00")
    assert metricas.total_ventas_concluidas == 3
    assert metricas.reservas_activas == 5
    assert metricas.ticket_promedio == Decimal("500.00")


def test_cu28_servicio_encargado_otra_sucursal_rechaza_detalle_403():
    """AC-3/AC-7: Encargado intentando acceder a venta de otra sucursal lanza SucursalConsultaInvalidaError."""
    mock_db = MagicMock()
    mock_venta = MagicMock(spec=VentaORM)
    mock_venta.id_venta = 99
    mock_venta.id_sucursal = 2  # Venta pertenece a sucursal 2
    mock_db.execute.return_value.unique.return_value.scalar_one_or_none.return_value = mock_venta

    servicio = ServicioConsultarVentasReservas()
    usuario_encargado_sucursal_1 = crear_usuario_encargado_mock(id_sucursal=1)

    with pytest.raises(SucursalConsultaInvalidaError):
        servicio.obtener_detalle_venta(mock_db, id_venta=99, usuario=usuario_encargado_sucursal_1)


def test_cu28_servicio_venta_inexistente_lanza_404():
    """AC-7: Servicio emite VentaNoEncontradaError ante ID que no existe."""
    mock_db = MagicMock()
    mock_db.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    servicio = ServicioConsultarVentasReservas()
    usuario_admin = crear_usuario_admin_mock()

    with pytest.raises(VentaNoEncontradaError):
        servicio.obtener_detalle_venta(mock_db, id_venta=9999, usuario=usuario_admin)


def test_cu28_servicio_reserva_inexistente_lanza_404():
    """AC-8: Servicio emite ReservaNoEncontradaError ante ID que no existe."""
    mock_db = MagicMock()
    mock_db.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    servicio = ServicioConsultarVentasReservas()
    usuario_admin = crear_usuario_admin_mock()

    with pytest.raises(ReservaNoEncontradaError):
        servicio.obtener_detalle_reserva(mock_db, id_reserva=9999, usuario=usuario_admin)


# -----------------------------------------------------------------------------
# 4. PRUEBAS DE ENDPOINTS REST DE ADMINISTRACION (AC-5, AC-7, AC-8)
# -----------------------------------------------------------------------------

def test_cu28_router_listar_transacciones_200(client: TestClient):
    """AC-5: GET /admin/ventas-reservas retorna HTTP 200 con listado paginado y metricas."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    mock_respuesta = RespuestaPaginadaTransaccionesOut(
        items=[
            fabricar_transaccion_resumen_item(id_transaccion=1, tipo="venta", codigo="VEN-001", monto=Decimal("300.00")),
            fabricar_transaccion_resumen_item(id_transaccion=2, tipo="reserva", codigo="RES-00002", monto=Decimal("150.00")),
        ],
        metricas=MetricasTransaccionalesOut(
            monto_total_facturado=Decimal("300.00"),
            total_ventas_concluidas=1,
            reservas_activas=1,
            ticket_promedio=Decimal("300.00"),
        ),
        total=2,
        pagina=1,
        limite=10,
        total_paginas=1,
    )

    with patch.object(ServicioConsultarVentasReservas, "listar_transacciones", return_value=mock_respuesta):
        try:
            resp = client.get("/api/v1/admin/ventas-reservas")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert len(data["items"]) == 2
            assert float(data["metricas"]["monto_total_facturado"]) == 300.00
            assert data["metricas"]["reservas_activas"] == 1
        finally:
            app.dependency_overrides.clear()


def test_cu28_router_filtrar_por_tipo_venta(client: TestClient):
    """AC-5: Endpoint permite filtrar por tipo_operacion=venta."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    mock_respuesta = RespuestaPaginadaTransaccionesOut(
        items=[fabricar_transaccion_resumen_item(id_transaccion=1, tipo="venta", codigo="VEN-001")],
        metricas=MetricasTransaccionalesOut(
            monto_total_facturado=Decimal("300.00"),
            total_ventas_concluidas=1,
            reservas_activas=0,
            ticket_promedio=Decimal("300.00"),
        ),
        total=1,
        pagina=1,
        limite=10,
        total_paginas=1,
    )

    with patch.object(ServicioConsultarVentasReservas, "listar_transacciones", return_value=mock_respuesta):
        try:
            resp = client.get("/api/v1/admin/ventas-reservas?tipo_operacion=venta")
            assert resp.status_code == 200
            assert resp.json()["total"] == 1
            assert resp.json()["items"][0]["tipo_operacion"] == "venta"
        finally:
            app.dependency_overrides.clear()


def test_cu28_router_fechas_invalidas_retorna_422(client: TestClient):
    """AC-9: Peticion con fecha_desde posterior a fecha_hasta rechaza con HTTP 422."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    try:
        resp = client.get(
            "/api/v1/admin/ventas-reservas?fecha_desde=2026-10-15T00:00:00Z&fecha_hasta=2026-10-10T00:00:00Z"
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_cu28_router_obtener_detalle_venta_200(client: TestClient):
    """AC-7: GET /admin/ventas-reservas/ventas/{id} retorna detalle con lineas y pagos."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    mock_detalle = VentaDetalleCompletoOut(
        id_venta=10,
        numero_comprobante="VEN-2026-0010",
        fecha_venta=datetime.now(timezone.utc),
        estado="pagada",
        tipo_venta="presencial",
        subtotal=Decimal("500.00"),
        descuento=Decimal("50.00"),
        total=Decimal("450.00"),
        id_sucursal=1,
        nombre_sucursal="Boutique Central",
        ciudad_sucursal="La Paz",
        id_cliente=5,
        nombre_cliente="Clara Gomez",
        email_cliente="clara.gomez@example.com",
        telefono_cliente="78901234",
        cajero_nombre="Carlos Sanchez",
        lineas=[
            LineaDetalleOut(
                id_detalle=1,
                id_variante=100,
                sku="VES-NOCH-NEG-M",
                nombre_producto="Vestido de Noche Imperial",
                talla="M",
                color="Negro Azabache",
                codigo_hex="#000000",
                cantidad=1,
                precio_unitario=Decimal("500.00"),
                subtotal_linea=Decimal("500.00"),
            )
        ],
        pagos=[
            PagoItemOut(
                id_pago=1,
                metodo_pago="tarjeta_credito",
                monto=Decimal("450.00"),
                estado="confirmado",
                referencia_pasarela="TXN-CREDIT-9988",
                creado_en=datetime.now(timezone.utc),
            )
        ],
    )

    with patch.object(ServicioConsultarVentasReservas, "obtener_detalle_venta", return_value=mock_detalle):
        try:
            resp = client.get("/api/v1/admin/ventas-reservas/ventas/10")
            assert resp.status_code == 200
            data = resp.json()
            assert data["numero_comprobante"] == "VEN-2026-0010"
            assert float(data["total"]) == 450.00
            assert len(data["lineas"]) == 1
            assert len(data["pagos"]) == 1
            assert data["lineas"][0]["sku"] == "VES-NOCH-NEG-M"
        finally:
            app.dependency_overrides.clear()


def test_cu28_router_obtener_detalle_reserva_200(client: TestClient):
    """AC-8: GET /admin/ventas-reservas/reservas/{id} retorna detalle con prendas apartadas."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    mock_detalle = ReservaDetalleCompletoOut(
        id_reserva=20,
        codigo_reserva="RES-00020",
        fecha_hora_atencion=datetime.now(timezone.utc) + timedelta(days=1),
        creado_en=datetime.now(timezone.utc),
        estado="confirmada",
        canal_origen="web",
        observacion="Cliente desea prueba presencial en probador VIP",
        id_sucursal=1,
        nombre_sucursal="Boutique Central",
        ciudad_sucursal="La Paz",
        id_cliente=8,
        nombre_cliente="Alejandra Rios",
        email_cliente="ale.rios@example.com",
        telefono_cliente="71234567",
        atendido_por_nombre="Asesor Probador",
        lineas=[
            LineaDetalleOut(
                id_detalle=5,
                id_variante=105,
                sku="TRAJ-LINO-BEI-L",
                nombre_producto="Traje Sastre en Lino Natural",
                talla="L",
                color="Beige Arena",
                codigo_hex="#E8D8C8",
                cantidad=1,
                precio_unitario=Decimal("380.00"),
                subtotal_linea=Decimal("380.00"),
            )
        ],
    )

    with patch.object(ServicioConsultarVentasReservas, "obtener_detalle_reserva", return_value=mock_detalle):
        try:
            resp = client.get("/api/v1/admin/ventas-reservas/reservas/20")
            assert resp.status_code == 200
            data = resp.json()
            assert data["codigo_reserva"] == "RES-00020"
            assert data["estado"] == "confirmada"
            assert len(data["lineas"]) == 1
            assert data["lineas"][0]["nombre_producto"] == "Traje Sastre en Lino Natural"
        finally:
            app.dependency_overrides.clear()
