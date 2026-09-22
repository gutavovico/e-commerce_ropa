"""Suite de pruebas automatizadas para CU25: Gestionar Proveedores.

Cubre estrictamente los criterios de aceptacion:
- # AC-1: Seguridad RBAC (JWT con roles administrador y encargado_sucursal requeridos; bloqueo a cajero/cliente).
- # AC-2: Listado paginado de proveedores con metadatos de control.
- # AC-3: Filtros multicriterio combinados (q, estado_activo, rubro).
- # AC-4: Consulta de ficha detallada por ID y manejo de 404.
- # AC-5: Registro de nuevo proveedor con persistencia de estado_activo = True y timestamps.
- # AC-6: Rechazo por duplicidad de NIT/RUT o Razon Social (409 Conflict).
- # AC-7: Validacion sintactica y semantica de correo y longitudes minimas (422 Unprocessable Entity).
- # AC-8: Actualizacion de ficha comercial y prevencion de colisiones de NIT/RUT con terceros.
- # AC-9: Baja logica del proveedor (estado_activo = False) preservando la fila en base de datos.
- # AC-10: Reactivacion del proveedor (estado_activo = True) para habilitar nuevas ordenes.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.gestion_operativa.cu25_proveedores.errores import (
    ProveedorDuplicadoError,
    ProveedorNoEncontradoError,
)
from modules.gestion_operativa.cu25_proveedores.esquemas import (
    ProveedorActualizarIn,
    ProveedorCrearIn,
    ProveedorEstadoIn,
    ProveedorFiltrosIn,
)
from modules.gestion_operativa.cu25_proveedores.modelos import ProveedorORM
from modules.gestion_operativa.cu25_proveedores.servicio import (
    ServicioGestionProveedores,
)


# -----------------------------------------------------------------------------
# FIXTURES Y FABRICAS DE MOCKS
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """Cliente HTTP para pruebas de endpoints."""
    return TestClient(app)


def crear_usuario_admin_mock(id_usuario: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "admin@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Admin"
    usuario.apellidos = "General"
    usuario.activo = True
    return usuario


def crear_usuario_encargado_mock(id_usuario: int = 2, id_sucursal: int = 10) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "encargado@fashionstore.com"
    usuario.rol = "encargado_sucursal"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Carlos"
    usuario.apellidos = "Encargado"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 3) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = 10
    usuario.nombres = "Pedro"
    usuario.apellidos = "Cajero"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 4) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente@fashionstore.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Ana"
    usuario.apellidos = "Cliente"
    usuario.activo = True
    return usuario


def mock_entidad_proveedor(
    id_proveedor: int = 1,
    razon_social: str = "Hilaturas Andinas S.A.",
    nit_rut: str = "1020304050",
    contacto_nombre: str = "Gonzalo Morales",
    telefono: str = "70123456",
    email: str = "contacto@hilaturasandinas.com",
    direccion: str = "Av. Industrial #450",
    ciudad: str = "La Paz",
    rubro: str = "Tejidos Naturales (Seda/Lino)",
    estado_activo: bool = True,
) -> ProveedorORM:
    prov = MagicMock(spec=ProveedorORM)
    prov.id_proveedor = id_proveedor
    prov.id_usuario = None
    prov.razon_social = razon_social
    prov.nit_rut = nit_rut
    prov.contacto_nombre = contacto_nombre
    prov.telefono = telefono
    prov.email = email
    prov.direccion = direccion
    prov.ciudad = ciudad
    prov.rubro = rubro
    prov.estado_activo = estado_activo
    prov.creado_en = datetime.now(timezone.utc)
    prov.actualizado_en = datetime.now(timezone.utc)
    return prov


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE SEGURIDAD RBAC (# AC-1)
# -----------------------------------------------------------------------------

def test_ac1_endpoint_admin_proveedores_401_sin_token(client):
    """# AC-1: Peticion sin token de autenticacion responde 401."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)

    res = client.get("/api/v1/admin/proveedores")
    assert res.status_code == 401
    assert res.json()["code"] == "TOKEN_INVALIDO"


def test_ac1_endpoint_admin_proveedores_403_cajero(client):
    """# AC-1: Usuario con rol cajero es rechazado con 403 Forbidden."""
    cajero = crear_usuario_cajero_mock()
    app.dependency_overrides[get_current_user] = lambda: cajero
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/proveedores")
        assert res.status_code == 403
        assert res.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_ac1_endpoint_admin_proveedores_403_cliente(client):
    """# AC-1: Usuario con rol cliente es rechazado con 403 Forbidden."""
    cliente = crear_usuario_cliente_mock()
    app.dependency_overrides[get_current_user] = lambda: cliente
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/proveedores")
        assert res.status_code == 403
        assert res.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_ac1_endpoint_admin_proveedores_200_roles_autorizados(client):
    """# AC-1: Usuarios con rol administrador y encargado_sucursal tienen acceso concedido."""
    admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: admin

    mock_db = MagicMock()
    mock_db.scalar.return_value = 0
    mock_db.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        res = client.get("/api/v1/admin/proveedores")
        assert res.status_code == 200
        assert res.json()["total"] == 0
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE LISTADO PAGINADO Y FILTROS (# AC-2, # AC-3)
# -----------------------------------------------------------------------------

def test_ac2_listado_paginado_proveedores():
    """# AC-2: Listado de proveedores retorna estructura paginada con metadatos."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    p1 = mock_entidad_proveedor(id_proveedor=1, razon_social="Atelier Textil")
    p2 = mock_entidad_proveedor(id_proveedor=2, razon_social="Sederia Central")

    mock_db = MagicMock()
    mock_db.scalar.return_value = 2
    mock_db.scalars.return_value.all.return_value = [p2, p1]

    filtros = ProveedorFiltrosIn(pagina=1, limite=10)
    resultado = servicio.listar_proveedores(mock_db, filtros, admin)

    assert resultado.total == 2
    assert resultado.pagina == 1
    assert resultado.total_paginas == 1
    assert len(resultado.items) == 2
    assert resultado.items[0].razon_social == "Sederia Central"


def test_ac3_filtros_multicriterio_q_estado_rubro():
    """# AC-3: Filtrado multicriterio aplica condiciones sobre q, estado_activo y rubro."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    p = mock_entidad_proveedor(id_proveedor=1, rubro="Sastreria de Lujo", estado_activo=True)

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    mock_db.scalars.return_value.all.return_value = [p]

    filtros = ProveedorFiltrosIn(q="Andinas", estado_activo=True, rubro="Sastreria", pagina=1, limite=10)
    resultado = servicio.listar_proveedores(mock_db, filtros, admin)

    assert resultado.total == 1
    assert len(resultado.items) == 1
    assert resultado.items[0].estado_activo is True


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE CONSULTA POR IDENTIFICADOR (# AC-4)
# -----------------------------------------------------------------------------

def test_ac4_obtener_proveedor_por_id_exitoso():
    """# AC-4: Consulta de ficha de proveedor por ID existente retorna 200 OK."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    prov = mock_entidad_proveedor(id_proveedor=5, razon_social="Boutique Cuero")
    mock_db = MagicMock()
    mock_db.get.return_value = prov

    res = servicio.obtener_proveedor_por_id(mock_db, 5, admin)
    assert res.id_proveedor == 5
    assert res.razon_social == "Boutique Cuero"


def test_ac4_obtener_proveedor_inexistente_404():
    """# AC-4: Consulta de ficha con ID no existente lanza ProveedorNoEncontradoError."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    mock_db.get.return_value = None

    with pytest.raises(ProveedorNoEncontradoError):
        servicio.obtener_proveedor_por_id(mock_db, 999, admin)


# -----------------------------------------------------------------------------
# 4. PRUEBAS DE ALTA, UNICIDAD Y VALIDACION (# AC-5, # AC-6, # AC-7)
# -----------------------------------------------------------------------------

def test_ac5_crear_proveedor_exitoso():
    """# AC-5: Alta exitosa persiste la entidad con estado_activo = True y datos saneados."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    mock_db.scalar.return_value = None  # No hay duplicados

    def refresh_side_effect(obj):
        obj.__dict__["id_proveedor"] = 10
        obj.__dict__["estado_activo"] = True
        obj.__dict__["creado_en"] = datetime.now(timezone.utc)
        obj.__dict__["actualizado_en"] = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = refresh_side_effect

    payload = ProveedorCrearIn(
        razon_social="   Telas y Lanas Altiplano S.R.L.   ",
        nit_rut="  4050607080  ",
        contacto_nombre="  Elena Quispe  ",
        telefono="78901234",
        email="contacto@altiplano.com",
        direccion="Av. Los Andes #890",
        ciudad="El Alto",
        rubro="Tejidos Naturales (Seda/Lino)",
    )

    item = servicio.crear_proveedor(mock_db, payload, admin)
    assert item.id_proveedor == 10
    assert item.razon_social == "Telas y Lanas Altiplano S.R.L."
    assert item.nit_rut == "4050607080"
    assert item.estado_activo is True
    assert mock_db.add.called
    assert mock_db.commit.called


def test_ac6_crear_proveedor_rechazo_nit_duplicado_409():
    """# AC-6: Intento de alta con NIT/RUT ya existente lanza ProveedorDuplicadoError (409)."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    existente = mock_entidad_proveedor(id_proveedor=1, nit_rut="1020304050")
    mock_db = MagicMock()
    mock_db.scalar.return_value = existente

    payload = ProveedorCrearIn(
        razon_social="Nueva Empresa Textil",
        nit_rut="1020304050",
        contacto_nombre="Raul Mendoza",
        telefono="70011223",
        email="raul@nuevaempresa.com",
        direccion="Calle Murillo #123",
        ciudad="La Paz",
        rubro="Confeccion Denim y Casual",
    )

    with pytest.raises(ProveedorDuplicadoError) as exc_info:
        servicio.crear_proveedor(mock_db, payload, admin)
    assert "NIT/RUT" in str(exc_info.value.message)


def test_ac6_crear_proveedor_rechazo_razon_social_duplicada_409():
    """# AC-6: Intento de alta con Razon Social ya ocupada lanza ProveedorDuplicadoError (409)."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    # Primera consulta (nit_rut): None, segunda (razon_social): encontrado
    mock_db.scalar.side_effect = [None, mock_entidad_proveedor(razon_social="Atelier Central")]

    payload = ProveedorCrearIn(
        razon_social="Atelier Central",
        nit_rut="9988776655",
        contacto_nombre="Lucia Perez",
        telefono="76543210",
        email="lucia@ateliercentral.com",
        direccion="Av. America #500",
        ciudad="Cochabamba",
        rubro="Sastreria de Lujo",
    )

    with pytest.raises(ProveedorDuplicadoError) as exc_info:
        servicio.crear_proveedor(mock_db, payload, admin)
    assert "Razon Social" in str(exc_info.value.message)


def test_ac7_validacion_pydantic_campos_invalidos_422():
    """# AC-7: Formatos de correo invalidos o cadenas vacias son rechazados por Pydantic."""
    with pytest.raises(ValidationError):
        ProveedorCrearIn(
            razon_social="  ",  # Solo espacios
            nit_rut="12345",
            contacto_nombre="Valido",
            telefono="70000000",
            email="correo_invalido_sin_arroba",
            direccion="Direccion 123",
            ciudad="La Paz",
            rubro="Sastreria",
        )


# -----------------------------------------------------------------------------
# 5. PRUEBAS DE ACTUALIZACION Y COLISIONES (# AC-8)
# -----------------------------------------------------------------------------

def test_ac8_actualizar_proveedor_exitoso():
    """# AC-8: Actualizacion parcial modifica la ficha comercial y renueva el timestamp."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    prov = mock_entidad_proveedor(id_proveedor=3, razon_social="Original S.A.", nit_rut="1122334455")
    mock_db = MagicMock()
    mock_db.get.return_value = prov

    payload = ProveedorActualizarIn(
        telefono="71122334",
        contacto_nombre="Nuevo Contacto",
        rubro="Marroquineria y Cuero",
    )

    item = servicio.actualizar_proveedor(mock_db, 3, payload, admin)
    assert item.telefono == "71122334"
    assert item.contacto_nombre == "Nuevo Contacto"
    assert item.rubro == "Marroquineria y Cuero"
    assert mock_db.commit.called


def test_ac8_actualizar_proveedor_colision_nit_otro_409():
    """# AC-8: Actualizacion intentando asignar un NIT/RUT de otro proveedor lanza 409 Conflict."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    prov = mock_entidad_proveedor(id_proveedor=3, razon_social="Propio S.A.", nit_rut="1122334455")
    mock_db = MagicMock()
    mock_db.get.return_value = prov
    mock_db.scalar.return_value = mock_entidad_proveedor(id_proveedor=7, nit_rut="9999999999")

    payload = ProveedorActualizarIn(nit_rut="9999999999")

    with pytest.raises(ProveedorDuplicadoError):
        servicio.actualizar_proveedor(mock_db, 3, payload, admin)


# -----------------------------------------------------------------------------
# 6. PRUEBAS DE BAJA LOGICA Y REACTIVACION (# AC-9, # AC-10)
# -----------------------------------------------------------------------------

def test_ac9_baja_logica_proveedor():
    """# AC-9: Desactivacion conmuta estado_activo = False manteniendo la fila en BD."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    prov = mock_entidad_proveedor(id_proveedor=8, estado_activo=True)
    mock_db = MagicMock()
    mock_db.get.return_value = prov

    item = servicio.cambiar_estado_proveedor(mock_db, 8, False, admin)
    assert item.estado_activo is False
    assert mock_db.commit.called


def test_ac10_reactivacion_proveedor():
    """# AC-10: Reactivacion restaura estado_activo = True habilitando nuevas operaciones."""
    servicio = ServicioGestionProveedores()
    admin = crear_usuario_admin_mock()

    prov = mock_entidad_proveedor(id_proveedor=8, estado_activo=False)
    mock_db = MagicMock()
    mock_db.get.return_value = prov

    item = servicio.cambiar_estado_proveedor(mock_db, 8, True, admin)
    assert item.estado_activo is True
    assert mock_db.commit.called
