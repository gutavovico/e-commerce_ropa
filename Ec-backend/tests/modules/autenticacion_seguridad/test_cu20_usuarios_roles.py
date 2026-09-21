"""Pruebas automatizadas para CU20: Gestionar Usuarios y Roles (RBAC).

Verifica exhaustivamente los criterios de aceptacion:
- # AC-1: Seguridad RBAC (Token Bearer y rol administrador obligatorio).
- # AC-2: Alta exitosa de usuario para los 4 roles soportados.
- # AC-3: Deteccion y rechazo de correo duplicado (HTTP 409).
- # AC-4: Obligatoriedad de sucursal para roles operativos (encargado, cajero).
- # AC-5: Validacion de existencia y estado activo de la sucursal (HTTP 422).
- # AC-6: Listado paginado con filtros multicriterio.
- # AC-7: Consulta individual de ficha tecnica (HTTP 200 y 404).
- # AC-8: Modificacion de atributos y transicion de rol.
- # AC-9: Deteccion de colisiones de correo al actualizar.
- # AC-10: Conmutacion de estado activo / inactivo.
- # AC-11: Salvaguarda anti-bloqueo del ultimo administrador activo (HTTP 409).
- # AC-12: Bloqueo de auto-desactivacion del administrador en sesion (HTTP 409).
- # AC-13: Restablecimiento administrativo de contrasena segura.
- # AC-14: Proteccion de integridad referencial en baja fisica (HTTP 409).
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.cu20_usuarios_roles.errores import (
    AutoModificacionBloqueadaError,
    EmailDuplicadoError,
    SucursalInvalidaError,
    SucursalRequeridaError,
    UltimoAdministradorError,
    UsuarioConDependenciasError,
    UsuarioNoEncontradoError,
)
from modules.autenticacion_seguridad.cu20_usuarios_roles.esquemas import (
    ResetPasswordIn,
    RolUsuarioEnum,
    UsuarioActualizarIn,
    UsuarioCrearIn,
    UsuarioEstadoIn,
    validar_complejidad_password,
)
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM


# -----------------------------------------------------------------------------
# FIXTURES Y ENTIDADES MOCK
# -----------------------------------------------------------------------------


@pytest.fixture
def client():
    """Cliente HTTP para pruebas de la API."""
    return TestClient(app)


def crear_usuario_mock(
    id_usuario: int = 1,
    email: str = "admin@fashionstore.com",
    rol: str = "administrador",
    id_sucursal: int | None = None,
    activo: bool = True,
    nombres: str = "Gustavo",
    apellidos: str = "Vico",
) -> UsuarioORM:
    """Instancia un mock de UsuarioORM con propiedades validas."""
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = email
    usuario.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$dummyhash"
    usuario.nombres = nombres
    usuario.apellidos = apellidos
    usuario.telefono = "+591 70000001"
    usuario.rol = rol
    usuario.id_sucursal = id_sucursal
    usuario.activo = activo
    usuario.fecha_registro = datetime.now(timezone.utc)
    usuario.ultimo_acceso = None

    if id_sucursal:
        sucursal = MagicMock(spec=SucursalORM)
        sucursal.id_sucursal = id_sucursal
        sucursal.nombre = "Boutique Calacoto Central"
        sucursal.activa = True

        ciudad = MagicMock(spec=CiudadORM)
        ciudad.nombre = "La Paz"
        sucursal.ciudad = ciudad

        usuario.sucursal = sucursal
    else:
        usuario.sucursal = None

    return usuario


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE ESQUEMAS PYDANTIC (INVARIANTES Y VALIDACIONES)
# -----------------------------------------------------------------------------


def test_esquema_password_complejidad():
    """Verifica el cumplimiento de politicas de contrasena robusta."""
    with pytest.raises(ValueError, match="al menos 8 caracteres"):
        validar_complejidad_password("Short1!")

    with pytest.raises(ValueError, match="letra mayuscula"):
        validar_complejidad_password("minuscula123!")

    with pytest.raises(ValueError, match="letra minuscula"):
        validar_complejidad_password("MAYUSCULA123!")

    with pytest.raises(ValueError, match="digito numerico"):
        validar_complejidad_password("SoloLetras!")

    assert validar_complejidad_password("AdminSeguro2026!") == "AdminSeguro2026!"


def test_esquema_usuario_crear_invariantes_sucursal():
    """# AC-4: Valida obligatoriedad y auto-nulificacion de id_sucursal segun rol."""
    # 1. Encargado sin sucursal -> Falla
    with pytest.raises(ValidationError) as exc:
        UsuarioCrearIn(
            email="encargado@fashionstore.com",
            password="PasswordSeguro123!",
            nombres="Carlos",
            apellidos="Mendoza",
            rol=RolUsuarioEnum.ENCARGADO_SUCURSAL,
            id_sucursal=None,
        )
    assert "id_sucursal es estrictamente obligatorio" in str(exc.value)

    # 2. Cajero con sucursal negativa o 0 -> Falla
    with pytest.raises(ValidationError) as exc:
        UsuarioCrearIn(
            email="cajero@fashionstore.com",
            password="PasswordSeguro123!",
            nombres="Lucia",
            apellidos="Roca",
            rol=RolUsuarioEnum.CAJERO,
            id_sucursal=0,
        )
    assert "id_sucursal es estrictamente obligatorio" in str(exc.value)

    # 3. Administrador con sucursal indicada -> Se auto-nulifica a None
    admin_in = UsuarioCrearIn(
        email="admin2@fashionstore.com",
        password="PasswordSeguro123!",
        nombres="Roberto",
        apellidos="Gomez",
        rol=RolUsuarioEnum.ADMINISTRADOR,
        id_sucursal=99,
    )
    assert admin_in.id_sucursal is None

    # 4. Cliente con sucursal -> Se auto-nulifica a None
    cliente_in = UsuarioCrearIn(
        email="cliente2@fashionstore.com",
        password="PasswordSeguro123!",
        nombres="Maria",
        apellidos="Lopez",
        rol=RolUsuarioEnum.CLIENTE,
        id_sucursal=15,
    )
    assert cliente_in.id_sucursal is None


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE SEGURIDAD RBAC (# AC-1)
# -----------------------------------------------------------------------------


def test_ac1_seguridad_rbac_sin_token_401(client):
    """# AC-1: Peticiones sin token deben ser rechazadas con HTTP 401."""
    app.dependency_overrides.clear()
    resp = client.get("/api/v1/admin/usuarios")
    assert resp.status_code == 401


def test_ac1_seguridad_rbac_rol_no_autorizado_403(client):
    """# AC-1: Roles no administradores deben ser rechazados con HTTP 403."""
    db_mock = MagicMock()
    for rol_no_permitido in ["encargado_sucursal", "cajero", "cliente"]:
        usuario_no_admin = crear_usuario_mock(
            id_usuario=5, rol=rol_no_permitido, email="operativo@fs.com"
        )
        app.dependency_overrides[get_db] = lambda: db_mock
        app.dependency_overrides[get_current_user] = lambda: usuario_no_admin

        resp = client.get("/api/v1/admin/usuarios")
        assert resp.status_code == 403
        assert resp.json()["code"] == "ACCESO_DENEGADO"

    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE CREACION DE USUARIOS (# AC-2, # AC-3, # AC-4, # AC-5)
# -----------------------------------------------------------------------------


def test_ac2_crear_usuario_admin_exito(client):
    """# AC-2: Creacion exitosa de una cuenta con rol administrador."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    # Simulacion: no existe email duplicado
    db_mock.scalars.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {
        "email": "nuevo.admin@fashionstore.com",
        "password": "PasswordSeguro2026!",
        "nombres": "Elena",
        "apellidos": "Torres",
        "telefono": "+591 71234567",
        "rol": "administrador",
    }

    resp = client.post("/api/v1/admin/usuarios", json=payload)
    assert resp.status_code == 201
    datos = resp.json()
    assert datos["email"] == "nuevo.admin@fashionstore.com"
    assert datos["rol"] == "administrador"
    assert datos["id_sucursal"] is None
    assert db_mock.add.called
    assert db_mock.commit.called
    app.dependency_overrides.clear()


def test_ac2_crear_usuario_encargado_con_sucursal_exito(client):
    """# AC-2 y # AC-4: Creacion exitosa de encargado con sucursal activa vinculada."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    # No hay duplicado de email
    db_mock.scalars.return_value.first.return_value = None

    # Sucursal existente y activa
    sucursal_mock = MagicMock(spec=SucursalORM)
    sucursal_mock.id_sucursal = 3
    sucursal_mock.activa = True
    db_mock.scalar.return_value = sucursal_mock

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {
        "email": "encargado.central@fashionstore.com",
        "password": "PasswordSeguro2026!",
        "nombres": "Mariana",
        "apellidos": "Paz",
        "telefono": "+591 79998888",
        "rol": "encargado_sucursal",
        "id_sucursal": 3,
    }

    resp = client.post("/api/v1/admin/usuarios", json=payload)
    assert resp.status_code == 201
    datos = resp.json()
    assert datos["rol"] == "encargado_sucursal"
    assert datos["id_sucursal"] == 3
    app.dependency_overrides.clear()


def test_ac3_crear_usuario_email_duplicado_409(client):
    """# AC-3: Rechazo ante colision de correo electronico (HTTP 409)."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    # Simular colision en base de datos
    db_mock.scalars.return_value.first.return_value = crear_usuario_mock(
        email="existente@fashionstore.com"
    )

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {
        "email": "existente@fashionstore.com",
        "password": "PasswordSeguro2026!",
        "nombres": "Pedro",
        "apellidos": "Vargas",
        "rol": "cajero",
        "id_sucursal": 1,
    }

    resp = client.post("/api/v1/admin/usuarios", json=payload)
    assert resp.status_code == 409
    assert resp.json()["code"] == "EMAIL_DUPLICADO"
    app.dependency_overrides.clear()


def test_ac5_crear_usuario_sucursal_inactiva_422(client):
    """# AC-5: Rechazo si la sucursal indicada no existe o se encuentra inactiva (HTTP 422)."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    # No hay colision de email
    db_mock.scalars.return_value.first.return_value = None

    # Sucursal inactiva
    sucursal_inactiva = MagicMock(spec=SucursalORM)
    sucursal_inactiva.id_sucursal = 10
    sucursal_inactiva.activa = False
    db_mock.scalar.return_value = sucursal_inactiva

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {
        "email": "cajero.inactivo@fashionstore.com",
        "password": "PasswordSeguro2026!",
        "nombres": "David",
        "apellidos": "Rios",
        "rol": "cajero",
        "id_sucursal": 10,
    }

    resp = client.post("/api/v1/admin/usuarios", json=payload)
    assert resp.status_code == 422
    assert resp.json()["code"] == "SUCURSAL_INEXISTENTE_O_INACTIVA"
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 4. PRUEBAS DE LISTADO Y DETALLE (# AC-6, # AC-7)
# -----------------------------------------------------------------------------


def test_ac6_listar_usuarios_paginado_filtros(client):
    """# AC-6: Consulta paginada con filtros multicriterio."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    u1 = crear_usuario_mock(id_usuario=1, email="admin@fs.com", rol="administrador")
    u2 = crear_usuario_mock(
        id_usuario=2, email="cajero1@fs.com", rol="cajero", id_sucursal=1
    )

    db_mock.scalar.return_value = 2  # total
    db_mock.scalars.return_value.unique.return_value.all.return_value = [u1, u2]

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.get("/api/v1/admin/usuarios?pagina=1&limite=10&rol=cajero&q=cajero")
    assert resp.status_code == 200
    datos = resp.json()
    assert datos["total"] == 2
    assert len(datos["items"]) == 2
    assert datos["pagina"] == 1
    assert datos["total_paginas"] == 1
    app.dependency_overrides.clear()


def test_ac7_obtener_usuario_por_id_exito_y_404(client):
    """# AC-7: Consulta individual por ID y manejo de recurso no encontrado."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_existente = crear_usuario_mock(id_usuario=42, email="usuario42@fs.com")
    db_mock.scalars.return_value.unique.return_value.first.side_effect = [
        usuario_existente,
        None,
    ]

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    # Caso exitoso
    resp_ok = client.get("/api/v1/admin/usuarios/42")
    assert resp_ok.status_code == 200
    assert resp_ok.json()["id_usuario"] == 42

    # Caso no encontrado (404)
    resp_404 = client.get("/api/v1/admin/usuarios/999")
    assert resp_404.status_code == 404
    assert resp_404.json()["code"] == "USUARIO_NO_ENCONTRADO"
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 5. PRUEBAS DE ACTUALIZACION Y SALVAGUARDAS (# AC-8, # AC-11, # AC-12)
# -----------------------------------------------------------------------------


def test_ac8_actualizar_usuario_exito(client):
    """# AC-8: Actualizacion exitosa de datos y rol."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(id_usuario=2, rol="cliente")
    db_mock.scalars.return_value.unique.return_value.first.return_value = usuario_target

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {
        "nombres": "Nombre Actualizado",
        "apellidos": "Apellido Actualizado",
        "telefono": "+591 77771111",
    }

    resp = client.put("/api/v1/admin/usuarios/2", json=payload)
    assert resp.status_code == 200
    assert usuario_target.nombres == "Nombre Actualizado"
    assert usuario_target.apellidos == "Apellido Actualizado"
    app.dependency_overrides.clear()


def test_ac11_salvaguarda_ultimo_admin_activo_bloqueo_desactivacion_409(client):
    """# AC-11: Bloqueo de desactivacion si es el unico administrador activo."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    # Usuario target es admin con ID 2
    admin_target = crear_usuario_mock(id_usuario=2, rol="administrador", activo=True)
    db_mock.scalars.return_value.unique.return_value.first.return_value = admin_target

    # Simular que conteo de otros administradores activos es 0
    db_mock.scalar.return_value = 0

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.patch("/api/v1/admin/usuarios/2/estado", json={"activo": False})
    assert resp.status_code == 409
    assert resp.json()["code"] == "ULTIMO_ADMINISTRADOR_BLOQUEADO"
    app.dependency_overrides.clear()


def test_ac11_salvaguarda_ultimo_admin_activo_bloqueo_degradacion_409(client):
    """# AC-11: Bloqueo de degradacion de rol si es el unico administrador activo."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    admin_target = crear_usuario_mock(id_usuario=2, rol="administrador", activo=True)
    db_mock.scalars.return_value.unique.return_value.first.return_value = admin_target

    # Conteo de otros administradores es 0
    db_mock.scalar.return_value = 0

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {"rol": "cliente"}
    resp = client.put("/api/v1/admin/usuarios/2", json=payload)
    assert resp.status_code == 409
    assert resp.json()["code"] == "ULTIMO_ADMINISTRADOR_BLOQUEADO"
    app.dependency_overrides.clear()


def test_ac12_bloqueo_auto_desactivacion_admin_en_sesion_409(client):
    """# AC-12: El administrador en sesion no puede desactivarse a si mismo."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador", activo=True)
    db_mock = MagicMock()

    db_mock.scalars.return_value.unique.return_value.first.return_value = admin_sesion

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.patch("/api/v1/admin/usuarios/1/estado", json={"activo": False})
    assert resp.status_code == 409
    assert resp.json()["code"] == "AUTO_DESACTIVACION_NO_PERMITIDA"
    app.dependency_overrides.clear()


def test_ac12_bloqueo_auto_degradacion_admin_en_sesion_409(client):
    """# AC-12: El administrador en sesion no puede degradar su propio rol."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador", activo=True)
    db_mock = MagicMock()

    db_mock.scalars.return_value.unique.return_value.first.return_value = admin_sesion

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {"rol": "cajero", "id_sucursal": 1}
    resp = client.put("/api/v1/admin/usuarios/1", json=payload)
    assert resp.status_code == 409
    assert resp.json()["code"] == "AUTO_DESACTIVACION_NO_PERMITIDA"
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 6. RESTABLECIMIENTO DE CONTRASENA Y ELIMINACION (# AC-13, # AC-14)
# -----------------------------------------------------------------------------


def test_ac13_reset_password_exito(client):
    """# AC-13: Restablecimiento de contrasena administrativa con hash renovado."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(id_usuario=2, email="cajero@fs.com")
    db_mock.scalars.return_value.unique.return_value.first.return_value = usuario_target

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {"nuevo_password": "NuevaPasswordRobusta2026!"}
    resp = client.post("/api/v1/admin/usuarios/2/reset-password", json=payload)
    assert resp.status_code == 200
    assert db_mock.commit.called
    app.dependency_overrides.clear()


def test_ac14_eliminar_usuario_con_dependencias_409(client):
    """# AC-14: Rechazo ante eliminacion fisica de usuario con movimientos de inventario."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(id_usuario=3, rol="cajero")
    db_mock.scalar.return_value = usuario_target

    # Simular existencia de movimientos de inventario
    db_mock.execute.return_value.first.return_value = (1,)

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.delete("/api/v1/admin/usuarios/3")
    assert resp.status_code == 409
    assert resp.json()["code"] == "USUARIO_CON_DEPENDENCIAS"
    app.dependency_overrides.clear()


def test_ac14_eliminar_usuario_sin_dependencias_exito_204(client):
    """# AC-14: Eliminacion fisica exitosa de usuario sin historial operativo."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(id_usuario=4, rol="cliente")
    db_mock.scalar.return_value = usuario_target

    # Simular ausencia de dependencias operativas
    db_mock.execute.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.delete("/api/v1/admin/usuarios/4")
    assert resp.status_code == 204
    assert db_mock.delete.called
    assert db_mock.commit.called
    app.dependency_overrides.clear()


def test_ac14_eliminar_propio_admin_en_sesion_409(client):
    """# AC-12 / # AC-14: El administrador en sesion no puede eliminarse a si mismo."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    db_mock.scalar.return_value = admin_sesion

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.delete("/api/v1/admin/usuarios/1")
    assert resp.status_code == 409
    assert resp.json()["code"] == "AUTO_DESACTIVACION_NO_PERMITIDA"
    app.dependency_overrides.clear()


def test_ac2_crear_usuario_cliente_exito(client):
    """# AC-2: Creacion de usuario con rol cliente e instanciacion de perfil."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()
    db_mock.scalars.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {
        "email": "nuevo.cliente@gmail.com",
        "password": "PasswordCliente2026!",
        "nombres": "Camila",
        "apellidos": "Suarez",
        "rol": "cliente",
    }
    resp = client.post("/api/v1/admin/usuarios", json=payload)
    assert resp.status_code == 201
    assert resp.json()["rol"] == "cliente"
    assert resp.json()["id_sucursal"] is None
    app.dependency_overrides.clear()


def test_ac8_actualizar_usuario_rol_operativo_sin_sucursal_422(client):
    """# AC-8 / # AC-4: Rechazo al actualizar a rol operativo sin sucursal asignada."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(id_usuario=5, rol="cliente", id_sucursal=None)
    db_mock.scalars.return_value.unique.return_value.first.return_value = usuario_target

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {"rol": "cajero"}
    resp = client.put("/api/v1/admin/usuarios/5", json=payload)
    assert resp.status_code == 422
    assert resp.json()["code"] == "SUCURSAL_REQUERIDA"
    app.dependency_overrides.clear()


def test_ac9_actualizar_usuario_email_duplicado_409(client):
    """# AC-9: Deteccion y rechazo si el nuevo email ya pertenece a otro usuario."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(
        id_usuario=5, email="actual@fs.com", rol="cajero", id_sucursal=1
    )
    db_mock.scalars.return_value.unique.return_value.first.return_value = usuario_target

    # Simular que la consulta de unicidad detecta otro usuario
    otro_usuario = crear_usuario_mock(id_usuario=8, email="duplicado@fs.com")
    db_mock.scalars.return_value.first.return_value = otro_usuario

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    payload = {"email": "duplicado@fs.com"}
    resp = client.put("/api/v1/admin/usuarios/5", json=payload)
    assert resp.status_code == 409
    assert resp.json()["code"] == "EMAIL_DUPLICADO"
    app.dependency_overrides.clear()


def test_ac10_cambiar_estado_usuario_exito(client):
    """# AC-10: Conmutacion logica de estado activo / suspendido."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    usuario_target = crear_usuario_mock(id_usuario=3, activo=True)
    db_mock.scalars.return_value.unique.return_value.first.return_value = usuario_target

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.patch("/api/v1/admin/usuarios/3/estado", json={"activo": False})
    assert resp.status_code == 200
    assert usuario_target.activo is False
    assert db_mock.commit.called
    app.dependency_overrides.clear()


def test_ac13_reset_password_debil_422(client):
    """# AC-13: Rechazo con HTTP 422 ante contrasena debil en reset administrativo."""
    admin_sesion = crear_usuario_mock(id_usuario=1, rol="administrador")
    db_mock = MagicMock()

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_sesion

    resp = client.post(
        "/api/v1/admin/usuarios/2/reset-password", json={"nuevo_password": "123"}
    )
    assert resp.status_code == 422
    app.dependency_overrides.clear()

