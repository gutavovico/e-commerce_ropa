"""Pruebas automatizadas para CU30: Consultar bitacora.

Cubre exhaustivamente:
- AC-1: Autenticacion y control de acceso RBAC (401 sin token, 403 roles no autorizados, 200 para administrador y admin).
- AC-2: Filtrado multicriterio (fechas, severidad, modulo, accion, termino textual q).
- AC-3: Inspeccion de detalle unitario de evento con payloads estructurados.
- AC-4: Manejo de errores de dominio (404 no encontrado).
- AC-5: Validacion de esquemas Pydantic e invariantes de consulta.
"""

from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from core.security import create_access_token
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.seguridad.cu30_bitacora.errores import (
    EventoBitacoraNoEncontradoError,
    PermisoDenegadoBitacoraError,
)
from modules.seguridad.cu30_bitacora.esquemas import (
    BitacoraFiltrosParametros,
    RegistrarEventoBitacoraIn,
)
from modules.seguridad.cu30_bitacora.modelos import Bitacora
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


# -----------------------------------------------------------------------------
# FIXTURES Y UTILIDADES MOCK
# -----------------------------------------------------------------------------


@pytest.fixture
def client():
    """Cliente HTTP para pruebas de endpoints."""
    return TestClient(app)


def crear_usuario_mock(rol: str = "administrador", id_usuario: int = 1) -> UsuarioORM:
    """Genera un mock de usuario con el rol especificado."""
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = f"{rol}@fashionstore.com"
    usuario.nombres = "Operador"
    usuario.apellidos = "Auditoria"
    usuario.rol = rol
    usuario.activo = True
    return usuario


def crear_evento_bitacora_mock(
    id_bitacora: int = 1,
    id_usuario: int = 1,
    usuario_nombre: str = "admin@fashionstore.com",
    accion: str = "CREAR_PRENDA",
    tabla_modulo: str = "PRODUCTOS",
    severidad: str = "INFO",
    payload_anterior: Any = None,
    payload_nuevo: Any = None,
) -> Bitacora:
    """Genera una instancia mock del modelo Bitacora."""
    evento = MagicMock(spec=Bitacora)
    evento.id_bitacora = id_bitacora
    evento.id_usuario = id_usuario
    evento.usuario_nombre = usuario_nombre
    evento.accion = accion
    evento.tabla_modulo = tabla_modulo
    evento.direccion_ip = "192.168.1.100"
    evento.severidad = severidad
    evento.payload_anterior = payload_anterior
    evento.payload_nuevo = payload_nuevo
    evento.creado_en = datetime.now(timezone.utc)
    return evento


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE ESQUEMAS PYDANTIC E INVARIANTES
# -----------------------------------------------------------------------------


def test_esquema_filtros_valores_por_defecto():
    """Valida los valores por defecto del esquema de filtros."""
    filtros = BitacoraFiltrosParametros()
    assert filtros.pagina == 1
    assert filtros.limite == 20
    assert filtros.ordenar_por == "creado_en_desc"
    assert filtros.severidad is None
    assert filtros.q is None


def test_esquema_filtros_personalizados_validos():
    """Valida la asignacion correcta de filtros especificos."""
    filtros = BitacoraFiltrosParametros(
        fecha_inicio=date(2026, 9, 1),
        fecha_fin=date(2026, 9, 22),
        severidad="CRITICAL",
        tabla_modulo="INVENTARIO",
        accion="AJUSTE_STOCK",
        q="Serrano Central",
        ordenar_por="severidad_desc",
        pagina=2,
        limite=50,
    )
    assert filtros.severidad == "CRITICAL"
    assert filtros.tabla_modulo == "INVENTARIO"
    assert filtros.pagina == 2
    assert filtros.limite == 50


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE SERVICIO Y LOGICA DE DOMINIO
# -----------------------------------------------------------------------------


def test_servicio_validar_permisos_exitoso_administrador():
    """Permite el acceso a usuarios con rol administrador o admin."""
    usuario_admin = crear_usuario_mock("administrador")
    ServicioBitacoraAuditoria.validar_permisos_administrador(usuario_admin)

    usuario_alias = crear_usuario_mock("admin")
    ServicioBitacoraAuditoria.validar_permisos_administrador(usuario_alias)


def test_servicio_validar_permisos_denegado_roles_no_autorizados():
    """Rechaza con PermisoDenegadoBitacoraError a roles sin privilegios de auditoria."""
    for rol in ["encargado_sucursal", "cajero", "cliente", "invitado"]:
        usuario = crear_usuario_mock(rol)
        with pytest.raises(PermisoDenegadoBitacoraError):
            ServicioBitacoraAuditoria.validar_permisos_administrador(usuario)


def test_servicio_validar_permisos_denegado_anonimo():
    """Rechaza el acceso cuando no hay usuario autenticado."""
    with pytest.raises(PermisoDenegadoBitacoraError):
        ServicioBitacoraAuditoria.validar_permisos_administrador(None)


def test_servicio_listar_eventos_vacio():
    """Retorna respuesta estructurada limpia cuando no hay registros coincidentes."""
    mock_db = MagicMock()
    mock_row_metricas = MagicMock()
    mock_row_metricas.total = 0
    mock_row_metricas.criticos = 0
    mock_row_metricas.advertencias = 0
    mock_row_metricas.usuarios_activos = 0
    mock_db.execute.return_value.first.return_value = mock_row_metricas

    usuario_admin = crear_usuario_mock("administrador")
    filtros = BitacoraFiltrosParametros()

    resultado = ServicioBitacoraAuditoria.listar_eventos(
        db=mock_db,
        filtros=filtros,
        usuario_actual=usuario_admin,
    )

    assert resultado.total == 0
    assert resultado.items == []
    assert resultado.metricas.total_eventos == 0
    assert resultado.metricas.eventos_criticos == 0


def test_servicio_listar_eventos_con_datos():
    """Calcula metricas y mapea items con bandera computada tiene_payload."""
    mock_db = MagicMock()
    mock_row_metricas = MagicMock()
    mock_row_metricas.total = 2
    mock_row_metricas.criticos = 1
    mock_row_metricas.advertencias = 0
    mock_row_metricas.usuarios_activos = 1
    mock_db.execute.return_value.first.return_value = mock_row_metricas

    evento_1 = crear_evento_bitacora_mock(
        id_bitacora=1,
        accion="DESACTIVAR_SUCURSAL",
        severidad="CRITICAL",
        payload_anterior={"activo": True},
        payload_nuevo={"activo": False},
    )
    evento_2 = crear_evento_bitacora_mock(
        id_bitacora=2,
        accion="CONSULTAR_CATALOGO",
        severidad="INFO",
        payload_anterior=None,
        payload_nuevo=None,
    )
    mock_db.execute.return_value.scalars.return_value.all.return_value = [evento_1, evento_2]

    usuario_admin = crear_usuario_mock("administrador")
    filtros = BitacoraFiltrosParametros()

    resultado = ServicioBitacoraAuditoria.listar_eventos(
        db=mock_db,
        filtros=filtros,
        usuario_actual=usuario_admin,
    )

    assert resultado.total == 2
    assert len(resultado.items) == 2
    assert resultado.items[0].tiene_payload is True
    assert resultado.items[1].tiene_payload is False
    assert resultado.metricas.eventos_criticos == 1


def test_servicio_obtener_evento_exitoso():
    """Recupera el detalle completo de un evento con sus snapshots JSON."""
    mock_db = MagicMock()
    evento = crear_evento_bitacora_mock(
        id_bitacora=42,
        payload_anterior={"precio": 150.0},
        payload_nuevo={"precio": 180.0},
    )
    mock_db.execute.return_value.scalar_one_or_none.return_value = evento

    usuario_admin = crear_usuario_mock("administrador")
    detalle = ServicioBitacoraAuditoria.obtener_evento_por_id(
        db=mock_db,
        id_bitacora=42,
        usuario_actual=usuario_admin,
    )

    assert detalle.id_bitacora == 42
    assert detalle.payload_anterior == {"precio": 150.0}
    assert detalle.payload_nuevo == {"precio": 180.0}
    assert detalle.tiene_payload is True


def test_servicio_obtener_evento_inexistente_lanza_error():
    """Lanza EventoBitacoraNoEncontradoError si el evento no existe."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    usuario_admin = crear_usuario_mock("administrador")
    with pytest.raises(EventoBitacoraNoEncontradoError):
        ServicioBitacoraAuditoria.obtener_evento_por_id(
            db=mock_db,
            id_bitacora=999,
            usuario_actual=usuario_admin,
        )


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE INTEGRACION HTTP (ROUTER, AUTENTICACION Y RBAC)
# -----------------------------------------------------------------------------


def test_endpoint_bitacora_sin_token_401(client: TestClient):
    """Acceso a /api/v1/admin/bitacora sin token debe fallar con 401."""
    response = client.get("/api/v1/admin/bitacora")
    assert response.status_code == 401


def test_endpoint_bitacora_rol_no_autorizado_403(client: TestClient):
    """Acceso con rol encargado_sucursal o cliente debe responder 403."""
    mock_db = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_mock("encargado_sucursal")
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token = create_access_token({"sub": "2", "rol": "encargado_sucursal"})
        response = client.get(
            "/api/v1/admin/bitacora",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_bitacora_rol_administrador_200(client: TestClient):
    """Acceso con rol administrador debe responder 200 con payload paginado."""
    mock_db = MagicMock()
    mock_row_metricas = MagicMock()
    mock_row_metricas.total = 1
    mock_row_metricas.criticos = 0
    mock_row_metricas.advertencias = 0
    mock_row_metricas.usuarios_activos = 1
    mock_db.execute.return_value.first.return_value = mock_row_metricas
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        crear_evento_bitacora_mock(id_bitacora=10)
    ]

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_mock("administrador")
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token = create_access_token({"sub": "1", "rol": "administrador"})
        response = client.get(
            "/api/v1/admin/bitacora",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "metricas" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_bitacora_detalle_evento_200(client: TestClient):
    """Obtencion de detalle de evento por ID responde 200 con snapshots."""
    mock_db = MagicMock()
    evento = crear_evento_bitacora_mock(
        id_bitacora=77,
        payload_anterior={"color": "Azul"},
        payload_nuevo={"color": "Dorado"},
    )
    mock_db.execute.return_value.scalar_one_or_none.return_value = evento

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_mock("administrador")
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token = create_access_token({"sub": "1", "rol": "administrador"})
        response = client.get(
            "/api/v1/admin/bitacora/77",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id_bitacora"] == 77
        assert data["payload_anterior"] == {"color": "Azul"}
        assert data["payload_nuevo"] == {"color": "Dorado"}
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_bitacora_detalle_evento_404(client: TestClient):
    """Solicitud de evento inexistente responde 404."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_mock("administrador")
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token = create_access_token({"sub": "1", "rol": "administrador"})
        response = client.get(
            "/api/v1/admin/bitacora/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
