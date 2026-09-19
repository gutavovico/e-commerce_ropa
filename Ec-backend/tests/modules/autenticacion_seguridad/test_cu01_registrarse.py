"""Pruebas unitarias y de integracion para CU01: Registrarse."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.errors import ConflictError
from main import app
from modules.autenticacion_seguridad.cu01_registrarse.esquemas import (
    RegistroClienteIn,
    RegistroClienteOut,
)
from modules.autenticacion_seguridad.cu01_registrarse.router import (
    servicio_registro,
)
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM


def test_esquema_registro_cliente_in_valido():
    """Valida que RegistroClienteIn acepte datos correctos y normalice tallas."""
    datos = RegistroClienteIn(
        email="cliente.test@fashionstore.com",
        password="PasswordSeguro123!",
        nombres="Ana Maria",
        apellidos="Garcia Morales",
        telefono="+591 70012345",
        talla_preferida="m",
        ciudad_preferida=1,
    )
    assert datos.email == "cliente.test@fashionstore.com"
    assert datos.talla_preferida == "M"


def test_esquema_registro_cliente_in_password_corta_falla():
    """Valida que una contrasena de menos de 8 caracteres falle validacion."""
    with pytest.raises(Exception):
        RegistroClienteIn(
            email="cliente.test@fashionstore.com",
            password="123",
            nombres="Ana",
            apellidos="Garcia",
        )


def test_esquema_registro_cliente_in_talla_invalida_falla():
    """Valida que una talla no permitida falle validacion."""
    with pytest.raises(Exception):
        RegistroClienteIn(
            email="cliente.test@fashionstore.com",
            password="PasswordSeguro123!",
            nombres="Ana",
            apellidos="Garcia",
            talla_preferida="XXXL",
        )


def test_servicio_registro_cliente_exitoso(monkeypatch):
    """Prueba unitaria de ServicioRegistroUsuario con session mockeada."""
    mock_db = MagicMock()
    # Simular que el usuario no existe en BD
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_db.scalars.return_value = mock_scalars

    def fake_flush():
        for call_args in mock_db.add.call_args_list:
            obj = call_args[0][0]
            if isinstance(obj, UsuarioORM) and obj.id_usuario is None:
                obj.id_usuario = 1

    mock_db.flush.side_effect = fake_flush

    datos = RegistroClienteIn(
        email="nuevo.cliente@fashionstore.com",
        password="Password123!",
        nombres="Carlos",
        apellidos="Mendoza",
    )

    resultado = servicio_registro.registrar_cliente(db=mock_db, datos=datos)

    assert isinstance(resultado, RegistroClienteOut)
    assert resultado.id_usuario == 1
    assert resultado.email == "nuevo.cliente@fashionstore.com"
    assert resultado.rol == "cliente"
    assert resultado.token_acceso is not None
    assert resultado.tipo_token == "bearer"
    assert mock_db.commit.called


def test_servicio_registro_cliente_email_duplicado_lanza_conflict():
    """Prueba que un correo existente lance ConflictError (409)."""
    mock_db = MagicMock()
    usuario_existente = UsuarioORM(
        id_usuario=1,
        email="existente@fashionstore.com",
        password_hash="hash",
        nombres="Juan",
        apellidos="Perez",
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario_existente
    mock_db.scalars.return_value = mock_scalars

    datos = RegistroClienteIn(
        email="existente@fashionstore.com",
        password="Password123!",
        nombres="Juan",
        apellidos="Perez",
    )

    with pytest.raises(ConflictError) as exc_info:
        servicio_registro.registrar_cliente(db=mock_db, datos=datos)

    assert exc_info.value.code == "USUARIO_YA_EXISTE"


def test_endpoint_post_registrarse_201_exitoso(monkeypatch):
    """Prueba de integracion HTTP del endpoint /api/v1/autenticacion/registrarse."""
    mock_db = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_db.scalars.return_value = mock_scalars

    def fake_flush():
        for call_args in mock_db.add.call_args_list:
            obj = call_args[0][0]
            if isinstance(obj, UsuarioORM) and obj.id_usuario is None:
                obj.id_usuario = 42

    mock_db.flush.side_effect = fake_flush

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "email": "ana.garcia@fashionstore.com",
                "password": "PasswordSeguro123!",
                "nombres": "Ana",
                "apellidos": "Garcia",
                "telefono": "+591 71234567",
                "talla_preferida": "S",
            }
            respuesta = client.post("/api/v1/autenticacion/registrarse", json=payload)

            assert respuesta.status_code == 201
            datos_resp = respuesta.json()
            assert datos_resp["id_usuario"] == 42
            assert datos_resp["email"] == "ana.garcia@fashionstore.com"
            assert datos_resp["rol"] == "cliente"
            assert "token_acceso" in datos_resp
            assert datos_resp["tipo_token"] == "bearer"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_registrarse_409_conflicto(monkeypatch):
    """Prueba que el endpoint responda HTTP 409 ante un correo ya registrado."""
    mock_db = MagicMock()
    usuario_existente = UsuarioORM(
        id_usuario=99,
        email="duplicado@fashionstore.com",
        password_hash="hash",
        nombres="Pedro",
        apellidos="Gomez",
    )
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = usuario_existente
    mock_db.scalars.return_value = mock_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "email": "duplicado@fashionstore.com",
                "password": "PasswordSeguro123!",
                "nombres": "Pedro",
                "apellidos": "Gomez",
            }
            respuesta = client.post("/api/v1/autenticacion/registrarse", json=payload)

            assert respuesta.status_code == 409
            datos_resp = respuesta.json()
            assert datos_resp["code"] == "USUARIO_YA_EXISTE"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_registrarse_422_validacion():
    """Prueba que un payload con email invalido o clave corta retorne HTTP 422."""
    with TestClient(app) as client:
        payload_invalido = {
            "email": "no-es-un-email",
            "password": "123",
            "nombres": "A",
            "apellidos": "B",
        }
        respuesta = client.post("/api/v1/autenticacion/registrarse", json=payload_invalido)
        assert respuesta.status_code == 422
