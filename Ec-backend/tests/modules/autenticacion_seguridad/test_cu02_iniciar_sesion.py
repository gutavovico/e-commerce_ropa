"""Pruebas unitarias y de integracion para CU02: Iniciar Sesion (Login)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.errors import AuthenticationError, AuthorizationError
from core.security import decode_access_token, hash_password
from main import app
from modules.autenticacion_seguridad.cu02_iniciar_sesion.esquemas import (
    LoginIn,
    LoginOut,
)
from modules.autenticacion_seguridad.cu02_iniciar_sesion.router import (
    servicio_login,
)
from modules.autenticacion_seguridad.modelos import UsuarioORM


# --- 1. Pruebas Unitarias de Esquemas Pydantic ---


def test_esquema_login_in_valido():
    """Valida que LoginIn acepte credenciales validas y recorte espacios."""
    datos = LoginIn(
        email="  c.laurent@atelier-mode.fr  ",
        password="PasswordSeguro123!",
        recordar_dispositivo=True,
    )
    assert datos.email == "c.laurent@atelier-mode.fr"
    assert datos.password == "PasswordSeguro123!"
    assert datos.recordar_dispositivo is True


def test_esquema_login_in_email_invalido():
    """Valida que un email mal formado dispare error de validacion."""
    with pytest.raises(ValidationError):
        LoginIn(email="no-es-correo", password="PasswordSeguro123!")


def test_esquema_login_in_password_vacia():
    """Valida que una contrasena vacia falle la validacion."""
    with pytest.raises(ValidationError):
        LoginIn(email="usuario@fashionstore.com", password="")


def test_esquema_login_out():
    """Valida construccion correcta del esquema LoginOut."""
    salida = LoginOut(
        access_token="fake.jwt.token",
        token_type="bearer",
        id_usuario=5,
        email="usuario@fashionstore.com",
        nombres="Claire",
        apellidos="Laurent",
        rol="cliente",
    )
    assert salida.id_usuario == 5
    assert salida.email == "usuario@fashionstore.com"
    assert salida.token_type == "bearer"
    assert salida.rol == "cliente"


# --- 2. Pruebas Unitarias del Servicio de Dominio ---


def test_servicio_login_exitoso():
    """Prueba de autenticacion exitosa: clave valida, cuenta activa y emision de JWT."""
    mock_db = MagicMock()
    clave_plana = "PasswordSeguro123!"
    hash_clave = hash_password(clave_plana)

    usuario = UsuarioORM(
        id_usuario=10,
        email="c.laurent@atelier-mode.fr",
        password_hash=hash_clave,
        nombres="Claire",
        apellidos="Laurent",
        rol="cliente",
        activo=True,
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario
    mock_db.scalars.return_value = mock_scalars

    datos = LoginIn(
        email="c.laurent@atelier-mode.fr",
        password=clave_plana,
        recordar_dispositivo=False,
    )

    resultado = servicio_login.autenticar_usuario(db=mock_db, datos=datos)

    assert isinstance(resultado, LoginOut)
    assert resultado.id_usuario == 10
    assert resultado.email == "c.laurent@atelier-mode.fr"
    assert resultado.nombres == "Claire"
    assert resultado.apellidos == "Laurent"
    assert resultado.rol == "cliente"
    assert resultado.token_type == "bearer"
    assert resultado.access_token is not None

    # Verificar claims dentro del token JWT
    claims = decode_access_token(resultado.access_token)
    assert claims["sub"] == "10"
    assert claims["email"] == "c.laurent@atelier-mode.fr"
    assert claims["rol"] == "cliente"

    # Verificar que se actualizo ultimo_acceso y se hizo commit
    assert usuario.ultimo_acceso is not None
    assert mock_db.commit.called


def test_servicio_login_credenciales_invalidas_password():
    """Prueba que una contrasena incorrecta lance AuthenticationError con CREDENCIALES_INVALIDAS."""
    mock_db = MagicMock()
    hash_clave = hash_password("PasswordSeguro123!")

    usuario = UsuarioORM(
        id_usuario=10,
        email="c.laurent@atelier-mode.fr",
        password_hash=hash_clave,
        nombres="Claire",
        apellidos="Laurent",
        rol="cliente",
        activo=True,
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario
    mock_db.scalars.return_value = mock_scalars

    datos = LoginIn(
        email="c.laurent@atelier-mode.fr",
        password="ContrasenaErronea!",
    )

    with pytest.raises(AuthenticationError) as exc_info:
        servicio_login.autenticar_usuario(db=mock_db, datos=datos)

    assert exc_info.value.code == "CREDENCIALES_INVALIDAS"
    assert exc_info.value.message == "Credenciales incorrectas"


def test_servicio_login_credenciales_invalidas_email():
    """Prueba que un correo inexistente lance el mismo AuthenticationError (anti-enumeracion)."""
    mock_db = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_db.scalars.return_value = mock_scalars

    datos = LoginIn(
        email="no.existe@atelier-mode.fr",
        password="CualquierPassword123!",
    )

    with pytest.raises(AuthenticationError) as exc_info:
        servicio_login.autenticar_usuario(db=mock_db, datos=datos)

    assert exc_info.value.code == "CREDENCIALES_INVALIDAS"
    assert exc_info.value.message == "Credenciales incorrectas"


def test_servicio_login_cuenta_inactiva():
    """Prueba que una cuenta con activo=False lance AuthorizationError con CUENTA_INACTIVA."""
    mock_db = MagicMock()
    clave_plana = "PasswordSeguro123!"
    hash_clave = hash_password(clave_plana)

    usuario = UsuarioORM(
        id_usuario=15,
        email="suspendido@atelier-mode.fr",
        password_hash=hash_clave,
        nombres="Usuario",
        apellidos="Suspendido",
        rol="cliente",
        activo=False,
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario
    mock_db.scalars.return_value = mock_scalars

    datos = LoginIn(
        email="suspendido@atelier-mode.fr",
        password=clave_plana,
    )

    with pytest.raises(AuthorizationError) as exc_info:
        servicio_login.autenticar_usuario(db=mock_db, datos=datos)

    assert exc_info.value.code == "CUENTA_INACTIVA"


# --- 3. Pruebas de Integracion HTTP con TestClient ---


def test_endpoint_post_login_200_ok():
    """Prueba HTTP 200 al autenticar credenciales validas contra /api/v1/autenticacion/login."""
    mock_db = MagicMock()
    clave_plana = "AtelierLuxury2026!"
    hash_clave = hash_password(clave_plana)

    usuario = UsuarioORM(
        id_usuario=7,
        email="elena.vance@fashionstore.com",
        password_hash=hash_clave,
        nombres="Elena",
        apellidos="Vance",
        rol="cliente",
        activo=True,
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario
    mock_db.scalars.return_value = mock_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "email": "elena.vance@fashionstore.com",
                "password": "AtelierLuxury2026!",
                "recordar_dispositivo": True,
            }
            respuesta = client.post("/api/v1/autenticacion/login", json=payload)

            assert respuesta.status_code == 200
            datos_resp = respuesta.json()
            assert datos_resp["id_usuario"] == 7
            assert datos_resp["email"] == "elena.vance@fashionstore.com"
            assert datos_resp["nombres"] == "Elena"
            assert datos_resp["apellidos"] == "Vance"
            assert datos_resp["rol"] == "cliente"
            assert datos_resp["token_type"] == "bearer"
            assert "access_token" in datos_resp
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_login_401_credenciales_invalidas():
    """Prueba HTTP 401 si la contrasena no coincide."""
    mock_db = MagicMock()
    hash_clave = hash_password("ClaveCorrecta123!")

    usuario = UsuarioORM(
        id_usuario=7,
        email="elena.vance@fashionstore.com",
        password_hash=hash_clave,
        nombres="Elena",
        apellidos="Vance",
        rol="cliente",
        activo=True,
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario
    mock_db.scalars.return_value = mock_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "email": "elena.vance@fashionstore.com",
                "password": "ClaveEquivocada999!",
            }
            respuesta = client.post("/api/v1/autenticacion/login", json=payload)

            assert respuesta.status_code == 401
            datos_resp = respuesta.json()
            assert datos_resp["code"] == "CREDENCIALES_INVALIDAS"
            assert datos_resp["detail"] == "Credenciales incorrectas"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_login_401_usuario_inexistente():
    """Prueba HTTP 401 si el correo no existe en la BD."""
    mock_db = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_db.scalars.return_value = mock_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "email": "fantasma@fashionstore.com",
                "password": "CualquierClave123!",
            }
            respuesta = client.post("/api/v1/autenticacion/login", json=payload)

            assert respuesta.status_code == 401
            datos_resp = respuesta.json()
            assert datos_resp["code"] == "CREDENCIALES_INVALIDAS"
            assert datos_resp["detail"] == "Credenciales incorrectas"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_login_403_cuenta_inactiva():
    """Prueba HTTP 403 si la cuenta del usuario esta inactiva."""
    mock_db = MagicMock()
    clave_plana = "AtelierLuxury2026!"
    hash_clave = hash_password(clave_plana)

    usuario = UsuarioORM(
        id_usuario=9,
        email="bloqueado@fashionstore.com",
        password_hash=hash_clave,
        nombres="Usuario",
        apellidos="Bloqueado",
        rol="cliente",
        activo=False,
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario
    mock_db.scalars.return_value = mock_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "email": "bloqueado@fashionstore.com",
                "password": clave_plana,
            }
            respuesta = client.post("/api/v1/autenticacion/login", json=payload)

            assert respuesta.status_code == 403
            datos_resp = respuesta.json()
            assert datos_resp["code"] == "CUENTA_INACTIVA"
            assert "inactiva o suspendida" in datos_resp["detail"]
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_login_422_validacion():
    """Prueba HTTP 422 ante payload con email invalido o campos vacios."""
    with TestClient(app) as client:
        payload = {
            "email": "correo_no_valido",
            "password": "",
        }
        respuesta = client.post("/api/v1/autenticacion/login", json=payload)
        assert respuesta.status_code == 422
