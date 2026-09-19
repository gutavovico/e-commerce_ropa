"""Pruebas unitarias y de integracion para CU04: Gestionar Perfil del Cliente."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user, require_roles
from core.errors import AuthenticationError, AuthorizationError
from core.security import create_access_token
from main import app
from modules.autenticacion_seguridad.cu04_gestionar_perfil.esquemas import (
    PerfilClienteOut,
    PerfilClienteUpdateIn,
    ResumenAtelierOut,
)
from modules.autenticacion_seguridad.cu04_gestionar_perfil.servicio import (
    ServicioPerfilCliente,
)
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM


# --- 1. Pruebas Unitarias de Esquemas Pydantic ---


def test_esquema_resumen_atelier_defaults():
    """Valida los valores por defecto del resumen atelier de alta costura."""
    resumen = ResumenAtelierOut()
    assert resumen.visitas_registradas == 32
    assert resumen.boutiques_visitadas == 4
    assert resumen.preferencia_textil == "100% Seda & Lana"
    assert resumen.estatus_membresia == "Nivel Platino"


def test_esquema_perfil_cliente_out_valido():
    """Valida que PerfilClienteOut acepte datos completos y genere estructura correcta."""
    perfil = PerfilClienteOut(
        id_usuario=8402,
        numero_socio="#8402",
        email="madame.dubois@fashionstore.com",
        rol="cliente",
        fecha_registro=datetime(2021, 10, 15, 12, 0, tzinfo=timezone.utc),
        miembro_desde="Octubre 2021",
        ultimo_acceso=datetime.now(timezone.utc),
        nombres="Madame",
        apellidos="Dubois",
        telefono="+33 1 42 68 55 00",
        fecha_nacimiento=date(1988, 5, 20),
        genero="femenino",
        talla_preferida="M",
        ciudad_preferida=1,
        acepta_marketing=True,
    )
    assert perfil.numero_socio == "#8402"
    assert perfil.email == "madame.dubois@fashionstore.com"
    assert perfil.talla_preferida == "M"
    assert perfil.resumen_atelier.visitas_registradas == 32


def test_esquema_perfil_cliente_update_in_valido():
    """Valida que PerfilClienteUpdateIn acepte actualizaciones parciales validas."""
    datos = PerfilClienteUpdateIn(
        nombres="  Claire  ",
        telefono="+591 70012345",
        talla_preferida="S",
        genero="femenino",
        acepta_marketing=False,
    )
    assert datos.nombres == "  Claire  "
    assert datos.talla_preferida == "S"
    assert datos.genero == "femenino"
    assert datos.acepta_marketing is False


def test_esquema_perfil_cliente_update_in_talla_invalida():
    """Valida que una talla fuera del estandar de alta costura falle la validacion."""
    with pytest.raises(ValidationError):
        PerfilClienteUpdateIn(talla_preferida="EXTRA_GIGANTE_INVALIDA")


def test_esquema_perfil_cliente_update_in_genero_invalido():
    """Valida que un valor de genero no contemplado falle la validacion."""
    with pytest.raises(ValidationError):
        PerfilClienteUpdateIn(genero="desconocido_no_permitido")


# --- 2. Pruebas Unitarias del Servicio de Dominio ---


def test_servicio_obtener_perfil_existente():
    """Valida que ServicioPerfilCliente formatee correctamente la informacion de usuario y cliente."""
    usuario = UsuarioORM(
        id_usuario=12,
        email="c.laurent@atelier.com",
        nombres="Claire",
        apellidos="Laurent",
        telefono="+33 6 12 34 56 78",
        rol="cliente",
        activo=True,
        fecha_registro=datetime(2023, 3, 10, 8, 30, tzinfo=timezone.utc),
    )
    cliente = ClienteORM(
        id_cliente=12,
        genero="femenino",
        talla_preferida="38",
        acepta_marketing=True,
    )
    usuario.cliente = cliente

    mock_db = MagicMock()
    perfil = ServicioPerfilCliente.obtener_perfil(mock_db, usuario)

    assert perfil.id_usuario == 12
    assert perfil.numero_socio == "#0012"
    assert perfil.miembro_desde == "Marzo 2023"
    assert perfil.nombres == "Claire"
    assert perfil.apellidos == "Laurent"
    assert perfil.talla_preferida == "38"
    assert perfil.acepta_marketing is True


def test_servicio_obtener_perfil_autocrea_cliente_si_no_existe():
    """Valida creacion transparente de ClienteORM si un usuario registrado carecia de este."""
    usuario = UsuarioORM(
        id_usuario=99,
        email="nuevo.cliente@atelier.com",
        nombres="Nuevo",
        apellidos="Cliente",
        rol="cliente",
        activo=True,
        fecha_registro=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    usuario.cliente = None

    mock_db = MagicMock()
    # Simular efecto de db.refresh seteando usuario.cliente
    def _mock_refresh(u):
        if u.cliente is None:
            u.cliente = ClienteORM(id_cliente=u.id_usuario, acepta_marketing=True)

    mock_db.refresh.side_effect = _mock_refresh

    perfil = ServicioPerfilCliente.obtener_perfil(mock_db, usuario)

    assert perfil.id_usuario == 99
    assert perfil.numero_socio == "#0099"
    assert mock_db.add.called
    assert mock_db.commit.called


def test_servicio_actualizar_perfil_atomico():
    """Valida actualizacion simultanea de campos en UsuarioORM y ClienteORM."""
    usuario = UsuarioORM(
        id_usuario=7,
        email="elena.vance@fashionstore.com",
        nombres="Elena",
        apellidos="Vance",
        telefono="77711223",
        rol="cliente",
        activo=True,
        fecha_registro=datetime(2022, 10, 5, tzinfo=timezone.utc),
    )
    cliente = ClienteORM(
        id_cliente=7,
        genero="femenino",
        talla_preferida="S",
        acepta_marketing=True,
    )
    usuario.cliente = cliente

    mock_db = MagicMock()
    datos_update = PerfilClienteUpdateIn(
        nombres="Elena Victoria",
        apellidos="Vance Laurent",
        telefono="  +591 78945612  ",
        talla_preferida="M",
        genero="femenino",
        fecha_nacimiento=date(1995, 8, 14),
        acepta_marketing=False,
    )

    resultado = ServicioPerfilCliente.actualizar_perfil(mock_db, usuario, datos_update)

    assert usuario.nombres == "Elena Victoria"
    assert usuario.apellidos == "Vance Laurent"
    assert usuario.telefono == "+591 78945612"
    assert cliente.talla_preferida == "M"
    assert cliente.acepta_marketing is False
    assert mock_db.commit.called


# --- 3. Pruebas Unitarias de Dependencias de Seguridad (deps.py) ---


def test_deps_get_current_user_sin_token():
    """Valida AuthenticationError (401) cuando no se provee token en la peticion."""
    mock_db = MagicMock()
    with pytest.raises(AuthenticationError) as exc_info:
        get_current_user(token=None, db=mock_db)
    assert exc_info.value.code == "TOKEN_INVALIDO"


def test_deps_get_current_user_token_corrupto():
    """Valida AuthenticationError (401) cuando el token JWT esta mal formado."""
    mock_db = MagicMock()
    with pytest.raises(AuthenticationError) as exc_info:
        get_current_user(token="token.completamente.falso", db=mock_db)
    assert exc_info.value.code == "TOKEN_INVALIDO"


def test_deps_require_roles_bloquea_rol_no_permitido():
    """Valida AuthorizationError (403) cuando el rol del usuario no tiene permisos."""
    usuario = UsuarioORM(
        id_usuario=50,
        email="cajero@fashionstore.com",
        rol="cajero",
        activo=True,
    )
    validador_cliente = require_roles(["cliente"])

    with pytest.raises(AuthorizationError) as exc_info:
        validador_cliente(usuario=usuario)
    assert exc_info.value.code == "ACCESO_DENEGADO"


# --- 4. Pruebas de Integracion HTTP con TestClient ---


def test_endpoint_get_perfil_200_ok():
    """Prueba HTTP 200 al consultar el perfil con token Bearer valido de cliente."""
    mock_db = MagicMock()
    usuario = UsuarioORM(
        id_usuario=8402,
        email="madame.dubois@fashionstore.com",
        nombres="Madame",
        apellidos="Dubois",
        telefono="+33 1 42 68 55 00",
        rol="cliente",
        activo=True,
        fecha_registro=datetime(2021, 10, 15, 12, 0, tzinfo=timezone.utc),
        ultimo_acceso=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
    )
    cliente = ClienteORM(
        id_cliente=8402,
        genero="femenino",
        talla_preferida="M",
        acepta_marketing=True,
    )
    usuario.cliente = cliente

    # Token firmado con el helper del sistema
    token = create_access_token(
        data={"sub": str(usuario.id_usuario), "email": usuario.email, "rol": "cliente"}
    )

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = usuario
    mock_db.execute.return_value = mock_scalar_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}
            respuesta = client.get("/api/v1/perfil", headers=headers)

            assert respuesta.status_code == 200
            datos = respuesta.json()
            assert datos["id_usuario"] == 8402
            assert datos["numero_socio"] == "#8402"
            assert datos["email"] == "madame.dubois@fashionstore.com"
            assert datos["nombres"] == "Madame"
            assert datos["apellidos"] == "Dubois"
            assert datos["talla_preferida"] == "M"
            assert datos["miembro_desde"] == "Octubre 2021"
            assert "resumen_atelier" in datos
            assert datos["resumen_atelier"]["visitas_registradas"] == 32
    finally:
        app.dependency_overrides.clear()


def test_endpoint_patch_perfil_200_ok():
    """Prueba HTTP 200 al actualizar exitosamente datos con PATCH /api/v1/perfil."""
    mock_db = MagicMock()
    usuario = UsuarioORM(
        id_usuario=8402,
        email="madame.dubois@fashionstore.com",
        nombres="Madame",
        apellidos="Dubois",
        telefono="+33 1 42 68 55 00",
        rol="cliente",
        activo=True,
        fecha_registro=datetime(2021, 10, 15, tzinfo=timezone.utc),
    )
    cliente = ClienteORM(
        id_cliente=8402,
        genero="femenino",
        talla_preferida="M",
        acepta_marketing=True,
    )
    usuario.cliente = cliente

    token = create_access_token(
        data={"sub": str(usuario.id_usuario), "email": usuario.email, "rol": "cliente"}
    )

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = usuario
    mock_db.execute.return_value = mock_scalar_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "nombres": "Camille",
                "telefono": "+33 6 99 88 77 66",
                "talla_preferida": "S",
                "acepta_marketing": False,
            }
            respuesta = client.patch("/api/v1/perfil", headers=headers, json=payload)

            assert respuesta.status_code == 200
            datos = respuesta.json()
            assert datos["nombres"] == "Camille"
            assert datos["talla_preferida"] == "S"
            assert datos["acepta_marketing"] is False
    finally:
        app.dependency_overrides.clear()


def test_endpoint_get_perfil_401_sin_token():
    """Prueba HTTP 401 si no se envia la cabecera Authorization."""
    with TestClient(app) as client:
        respuesta = client.get("/api/v1/perfil")
        assert respuesta.status_code == 401
        datos = respuesta.json()
        assert datos["code"] == "TOKEN_INVALIDO"


def test_endpoint_get_perfil_401_token_invalido():
    """Prueba HTTP 401 si se envia un Bearer token corrupto o invalido."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer token_completamente_invalido"}
        respuesta = client.get("/api/v1/perfil", headers=headers)
        assert respuesta.status_code == 401
        datos = respuesta.json()
        assert datos["code"] == "TOKEN_INVALIDO"


def test_endpoint_get_perfil_403_rol_no_cliente():
    """Prueba HTTP 403 si un usuario con rol 'administrador' o 'cajero' intenta consultar perfil de cliente."""
    mock_db = MagicMock()
    usuario_admin = UsuarioORM(
        id_usuario=1,
        email="admin@fashionstore.com",
        nombres="Admin",
        apellidos="Sistema",
        rol="administrador",
        activo=True,
    )

    token = create_access_token(
        data={"sub": str(usuario_admin.id_usuario), "email": usuario_admin.email, "rol": "administrador"}
    )

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = usuario_admin
    mock_db.execute.return_value = mock_scalar_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}
            respuesta = client.get("/api/v1/perfil", headers=headers)
            assert respuesta.status_code == 403
            datos = respuesta.json()
            assert datos["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_patch_perfil_422_talla_invalida():
    """Prueba HTTP 422 si se envia una talla que no cumple el patron de alta costura."""
    mock_db = MagicMock()
    usuario = UsuarioORM(
        id_usuario=8402,
        email="cliente@fashionstore.com",
        rol="cliente",
        activo=True,
    )
    usuario.cliente = ClienteORM(id_cliente=8402)

    token = create_access_token(
        data={"sub": str(usuario.id_usuario), "email": usuario.email, "rol": "cliente"}
    )

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = usuario
    mock_db.execute.return_value = mock_scalar_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"talla_preferida": "TALLA_GIGANTE_INVENTADA"}
            respuesta = client.patch("/api/v1/perfil", headers=headers, json=payload)
            assert respuesta.status_code == 422
    finally:
        app.dependency_overrides.clear()
