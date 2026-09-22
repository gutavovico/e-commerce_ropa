"""Suite de pruebas automatizadas para CU24: Gestionar Inventario, Stock y Existencias por Sucursal.

Cubre estrictamente los criterios de aceptacion:
- # AC-1: Seguridad RBAC (JWT con roles administrador y encargado_sucursal requeridos; bloqueo a cajero/cliente).
- # AC-2: Segregacion territorial forzosa para encargado_sucursal (bloqueo 403 ante sedes ajenas).
- # AC-3: Consulta paginada y calculo determinista de estado (optimo, alerta_baja, agotado).
- # AC-4: Filtros multicriterio combinados (sede, categoria, estado_stock, busqueda textual q).
- # AC-5: Alta inicial de existencias fisicas con primer movimiento de Kardex (ingreso_proveedor).
- # AC-6: Rechazo de inventario duplicado en la misma sucursal para la misma variante (409 Conflict).
- # AC-7: Rechazo de operacion sobre sucursal o prenda/variante inactiva (422 Unprocessable Entity).
- # AC-8: Ajuste manual positivo y negativo con trazabilidad de Kardex y actualizacion de timestamp.
- # AC-9: Rechazo si el ajuste manual por decremento supera las existencias disponibles (409 Conflict).
- # AC-10: Validacion sintactica de justificacion obligatoria del ajuste (minimo 5 caracteres significativos).
- # AC-11: Transferencia atomica inter-sucursal con doble asiento en Kardex (salida y entrada).
- # AC-12: Rechazo de auto-transferencia hacia la misma sucursal de origen (422 Unprocessable Entity).
- # AC-13: Rechazo de transferencia si el stock disponible en origen es insuficiente (409 Conflict).
- # AC-14: Consulta cronologica inmutable del historial de movimientos de Kardex.
- # AC-15: Consulta publica y abierta de disponibilidad fisica de piezas en vitrina por tienda activa.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import CategoriaORM, ColorORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.gestion_operativa.cu24_inventario_stock.errores import (
    AutoTransferenciaError,
    EntidadInactivaError,
    InventarioDuplicadoError,
    InventarioNoEncontradoError,
    StockInsuficienteError,
    SucursalNoAutorizadaError,
)
from modules.gestion_operativa.cu24_inventario_stock.esquemas import (
    EstadoStockCalculadoEnum,
    InventarioAjusteIn,
    InventarioCrearIn,
    InventarioFiltrosIn,
    TipoAjusteManualEnum,
    TipoMovimientoEnum,
    TransferenciaInterSucursalIn,
)
from modules.gestion_operativa.cu24_inventario_stock.modelos import (
    InventarioSucursalORM,
    MovimientoInventarioORM,
)
from modules.gestion_operativa.cu24_inventario_stock.servicio import (
    ServicioGestionInventario,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM


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


def crear_usuario_cliente_mock(id_usuario: int = 3) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente@fashionstore.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Ana"
    usuario.apellidos = "Cliente"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 4, id_sucursal: int = 10) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Pedro"
    usuario.apellidos = "Cajero"
    usuario.activo = True
    return usuario


def mock_entidad_sucursal(id_sucursal: int = 10, nombre: str = "Boutique Central", activa: bool = True) -> SucursalORM:
    ciudad = MagicMock(spec=CiudadORM)
    ciudad.id_ciudad = 1
    ciudad.nombre = "La Paz"

    sucursal = MagicMock(spec=SucursalORM)
    sucursal.id_sucursal = id_sucursal
    sucursal.nombre = nombre
    sucursal.direccion = "Av. 16 de Julio #1490"
    sucursal.activa = activa
    sucursal.ciudad = ciudad
    return sucursal


def mock_entidad_variante(id_variante: int = 100, sku: str = "BER-CHA-L-NEG", activo: bool = True) -> VarianteProductoORM:
    cat = MagicMock(spec=CategoriaORM)
    cat.id_categoria = 1
    cat.nombre = "Chaquetas"

    prod = MagicMock(spec=ProductoORM)
    prod.id_producto = 50
    prod.nombre = "Chaqueta Cuero Atelier"
    prod.precio_base = Decimal("150.00")
    prod.activo = activo
    prod.imagen_url = "https://cdn.fashionstore.com/chaqueta.jpg"
    prod.categoria = cat

    talla = MagicMock(spec=TallaORM)
    talla.id_talla = 3
    talla.codigo = "L"
    talla.nombre = "L"

    color = MagicMock(spec=ColorORM)
    color.id_color = 2
    color.nombre = "Negro Obsidiana"
    color.codigo_hex = "#0F172A"

    variante = MagicMock(spec=VarianteProductoORM)
    variante.id_variante = id_variante
    variante.id_producto = prod.id_producto
    variante.sku = sku
    variante.precio_extra = Decimal("10.00")
    variante.activo = activo
    variante.producto = prod
    variante.talla = talla
    variante.color = color
    return variante


def mock_entidad_inventario(
    id_inventario: int = 1,
    id_sucursal: int = 10,
    id_variante: int = 100,
    disponible: int = 20,
    reservada: int = 2,
    stock_minimo: int = 5,
    stock_alerta: int = 8,
) -> InventarioSucursalORM:
    inv = MagicMock(spec=InventarioSucursalORM)
    inv.id_inventario = id_inventario
    inv.id_sucursal = id_sucursal
    inv.id_variante = id_variante
    inv.id_temporada = 1
    inv.cantidad_disponible = disponible
    inv.cantidad_reservada = reservada
    inv.stock_minimo = stock_minimo
    inv.stock_alerta = stock_alerta
    inv.estado = "disponible" if disponible > 0 else "agotada"
    inv.actualizado_en = datetime.now(timezone.utc)
    inv.sucursal = mock_entidad_sucursal(id_sucursal=id_sucursal)
    inv.variante = mock_entidad_variante(id_variante=id_variante)
    return inv


# -----------------------------------------------------------------------------
# PRUEBAS DE SEGURIDAD RBAC Y SEGREGACION TERRITORIAL (# AC-1, # AC-2)
# -----------------------------------------------------------------------------

def test_ac1_endpoint_admin_inventario_401_sin_token(client):
    """# AC-1: Acceso a endpoints administrativos sin token Bearer debe responder 401."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)

    res = client.get("/api/v1/admin/inventario")
    assert res.status_code == 401
    assert res.json()["code"] == "TOKEN_INVALIDO"


def test_ac1_endpoint_admin_inventario_403_rol_cliente(client):
    """# AC-1: Usuario autenticado con rol cliente es rechazado con 403."""
    cliente = crear_usuario_cliente_mock()
    app.dependency_overrides[get_current_user] = lambda: cliente
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/inventario")
        assert res.status_code == 403
        assert res.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_ac1_endpoint_admin_inventario_403_rol_cajero(client):
    """# AC-1: Usuario autenticado con rol cajero es rechazado con 403."""
    cajero = crear_usuario_cajero_mock()
    app.dependency_overrides[get_current_user] = lambda: cajero
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/inventario")
        assert res.status_code == 403
        assert res.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_ac2_segregacion_encargado_bloqueado_en_otra_sucursal_403(client):
    """# AC-2: Encargado de sucursal 10 intentando consultar sucursal 20 recibe 403 SUCURSAL_NO_AUTORIZADA."""
    encargado = crear_usuario_encargado_mock(id_usuario=2, id_sucursal=10)
    app.dependency_overrides[get_current_user] = lambda: encargado
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/inventario?id_sucursal=20")
        assert res.status_code == 403
        data = res.json()
        assert data["code"] == "SUCURSAL_NO_AUTORIZADA"
    finally:
        app.dependency_overrides.clear()


def test_ac2_segregacion_encargado_bloqueado_en_mutacion_otra_sucursal_403():
    """# AC-2: Servicio lanza SucursalNoAutorizadaError si un encargado intenta mutar sede ajena."""
    servicio = ServicioGestionInventario()
    encargado = crear_usuario_encargado_mock(id_usuario=2, id_sucursal=10)

    # Intento de alta en sede 20
    payload_crear = InventarioCrearIn(
        id_sucursal=20,
        id_variante=100,
        cantidad_inicial=10,
    )
    with pytest.raises(SucursalNoAutorizadaError):
        servicio.crear_inventario_inicial(MagicMock(), payload_crear, encargado)


def test_ac2_admin_acceso_global_multisede():
    """# AC-2: Administrador no tiene restriccion territorial y puede operar cualquier sede."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    # No debe levantar excepcion al validar cualquier sede
    servicio._validar_acceso_sucursal(admin, 10)
    servicio._validar_acceso_sucursal(admin, 99)


# -----------------------------------------------------------------------------
# PRUEBAS DE CONSULTA PAGINADA Y CALCULOS DE ESTADO (# AC-3, # AC-4)
# -----------------------------------------------------------------------------

def test_ac3_calculo_determinista_de_estado():
    """# AC-3: Verifica el calculo determinista de optimo, alerta_baja y agotado."""
    servicio = ServicioGestionInventario()

    # Agotado cuando disponible <= 0
    assert servicio._calcular_estado_stock(0, 5) == EstadoStockCalculadoEnum.AGOTADO
    assert servicio._calcular_estado_stock(-2, 5) == EstadoStockCalculadoEnum.AGOTADO

    # Alerta baja cuando 0 < disponible <= stock_alerta
    assert servicio._calcular_estado_stock(1, 5) == EstadoStockCalculadoEnum.ALERTA_BAJA
    assert servicio._calcular_estado_stock(5, 5) == EstadoStockCalculadoEnum.ALERTA_BAJA

    # Optimo cuando disponible > stock_alerta
    assert servicio._calcular_estado_stock(6, 5) == EstadoStockCalculadoEnum.OPTIMO
    assert servicio._calcular_estado_stock(100, 5) == EstadoStockCalculadoEnum.OPTIMO


def test_ac3_ac4_listar_inventario_con_filtros():
    """# AC-3, # AC-4: Servicio retorna listado paginado con calculo de paginas y estado."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    inv1 = mock_entidad_inventario(id_inventario=1, disponible=15, stock_alerta=5)
    inv2 = mock_entidad_inventario(id_inventario=2, disponible=3, stock_alerta=5)

    mock_db = MagicMock()
    mock_db.scalar.return_value = 2  # Conteo total

    scalars_mock = MagicMock()
    scalars_mock.unique.return_value.all.return_value = [inv1, inv2]
    mock_db.scalars.return_value = scalars_mock

    filtros = InventarioFiltrosIn(pagina=1, limite=10, q="Atelier")
    resultado = servicio.listar_inventario(mock_db, filtros, admin)

    assert resultado.total == 2
    assert resultado.pagina == 1
    assert resultado.total_paginas == 1
    assert len(resultado.items) == 2
    assert resultado.items[0].estado_calculado == EstadoStockCalculadoEnum.OPTIMO
    assert resultado.items[1].estado_calculado == EstadoStockCalculadoEnum.ALERTA_BAJA


# -----------------------------------------------------------------------------
# PRUEBAS DE ALTA INICIAL Y DUPLICIDAD (# AC-5, # AC-6, # AC-7)
# -----------------------------------------------------------------------------

def test_ac5_crear_inventario_inicial_exitoso_con_asiento_kardex():
    """# AC-5: Creacion de inventario inicial genera el registro y su primer movimiento de Kardex."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    sucursal = mock_entidad_sucursal(id_sucursal=10, activa=True)
    variante = mock_entidad_variante(id_variante=100, activo=True)

    def db_get_side_effect(model_class, pk):
        if model_class == SucursalORM and pk == 10:
            return sucursal
        if model_class == VarianteProductoORM and pk == 100:
            return variante
        return None

    mock_db.get.side_effect = db_get_side_effect
    mock_db.scalar.return_value = None  # No hay duplicado

    def refresh_side_effect(obj):
        obj.__dict__["id_inventario"] = 1
        obj.__dict__["sucursal"] = sucursal
        obj.__dict__["variante"] = variante

    mock_db.refresh.side_effect = refresh_side_effect



    payload = InventarioCrearIn(
        id_sucursal=10,
        id_variante=100,
        cantidad_inicial=25,
        stock_minimo=5,
        stock_alerta=8,
        observacion="Primer lote importado",
    )

    resultado = servicio.crear_inventario_inicial(mock_db, payload, admin)

    assert mock_db.add.call_count >= 2  # Inventario y Movimiento
    assert mock_db.commit.called
    assert resultado.cantidad_disponible == 25
    assert resultado.estado_calculado == EstadoStockCalculadoEnum.OPTIMO


def test_ac6_crear_inventario_duplicado_409():
    """# AC-6: Intento de dar de alta un inventario ya existente lanza InventarioDuplicadoError."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    mock_db.get.side_effect = lambda model, pk: mock_entidad_sucursal() if model == SucursalORM else mock_entidad_variante()
    mock_db.scalar.return_value = mock_entidad_inventario()  # Ya existe

    payload = InventarioCrearIn(id_sucursal=10, id_variante=100, cantidad_inicial=5)

    with pytest.raises(InventarioDuplicadoError) as exc_info:
        servicio.crear_inventario_inicial(mock_db, payload, admin)
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "INVENTARIO_DUPLICADO"


def test_ac7_crear_inventario_entidad_inactiva_422():
    """# AC-7: Intento de alta con sucursal inactiva o variante inactiva lanza EntidadInactivaError."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    sucursal_inactiva = mock_entidad_sucursal(id_sucursal=10, activa=False)
    mock_db.get.return_value = sucursal_inactiva

    payload = InventarioCrearIn(id_sucursal=10, id_variante=100, cantidad_inicial=5)

    with pytest.raises(EntidadInactivaError) as exc_info:
        servicio.crear_inventario_inicial(mock_db, payload, admin)
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "ENTIDAD_INACTIVA_PARA_INVENTARIO"


# -----------------------------------------------------------------------------
# PRUEBAS DE AJUSTE FISICO MANUAL (# AC-8, # AC-9, # AC-10)
# -----------------------------------------------------------------------------

def test_ac8_ajuste_manual_incremento_exito():
    """# AC-8: Ajuste positivo incrementa stock disponible y asienta en Kardex."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    inv = mock_entidad_inventario(id_inventario=1, disponible=10)
    mock_db = MagicMock()
    mock_db.get.return_value = inv

    payload = InventarioAjusteIn(
        tipo_ajuste=TipoAjusteManualEnum.INCREMENTO,
        cantidad=5,
        motivo="Conteo fisico de auditoria bimestral",
    )

    resultado = servicio.ajustar_inventario(mock_db, 1, payload, admin)

    assert inv.cantidad_disponible == 15
    assert mock_db.commit.called
    assert resultado.cantidad_disponible == 15


def test_ac8_ajuste_manual_decremento_exito():
    """# AC-8: Ajuste negativo reduce stock disponible y asienta en Kardex."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    inv = mock_entidad_inventario(id_inventario=1, disponible=10)
    mock_db = MagicMock()
    mock_db.get.return_value = inv

    payload = InventarioAjusteIn(
        tipo_ajuste=TipoAjusteManualEnum.DECREMENTO,
        cantidad=4,
        motivo="Merma por prenda danada en exhibicion",
    )

    resultado = servicio.ajustar_inventario(mock_db, 1, payload, admin)

    assert inv.cantidad_disponible == 6
    assert mock_db.commit.called
    assert resultado.cantidad_disponible == 6


def test_ac9_ajuste_decremento_excede_disponible_409():
    """# AC-9: Ajuste por decremento que supere el stock disponible debe lanzar StockInsuficienteError."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    inv = mock_entidad_inventario(id_inventario=1, disponible=5)
    mock_db = MagicMock()
    mock_db.get.return_value = inv

    payload = InventarioAjusteIn(
        tipo_ajuste=TipoAjusteManualEnum.DECREMENTO,
        cantidad=10,  # Supera los 5 disponibles
        motivo="Perdida total de inventario",
    )

    with pytest.raises(StockInsuficienteError) as exc_info:
        servicio.ajustar_inventario(mock_db, 1, payload, admin)
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "STOCK_INSUFICIENTE"


def test_ac10_ajuste_motivo_menor_a_5_caracteres_falla():
    """# AC-10: Pydantic v2 debe rechazar motivos con menos de 5 caracteres significativos."""
    with pytest.raises(ValidationError):
        InventarioAjusteIn(
            tipo_ajuste=TipoAjusteManualEnum.INCREMENTO,
            cantidad=2,
            motivo="  ab  ",  # Longitud saneada 2 < 5
        )


# -----------------------------------------------------------------------------
# PRUEBAS DE TRANSFERENCIA INTER-SUCURSAL (# AC-11, # AC-12, # AC-13)
# -----------------------------------------------------------------------------

def test_ac11_transferencia_inter_sucursal_atomica_exito():
    """# AC-11: Transferencia descuenta en origen, suma en destino y genera 2 movimientos espejo."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    suc_orig = mock_entidad_sucursal(id_sucursal=10, nombre="Sede Origen", activa=True)
    suc_dest = mock_entidad_sucursal(id_sucursal=20, nombre="Sede Destino", activa=True)
    variante = mock_entidad_variante(id_variante=100, sku="PRENDA-TEST")

    def db_get_side_effect(model_class, pk):
        if model_class == SucursalORM and pk == 10:
            return suc_orig
        if model_class == SucursalORM and pk == 20:
            return suc_dest
        if model_class == VarianteProductoORM and pk == 100:
            return variante
        return None

    mock_db.get.side_effect = db_get_side_effect

    inv_origen = mock_entidad_inventario(id_inventario=1, id_sucursal=10, disponible=20)
    inv_destino = mock_entidad_inventario(id_inventario=2, id_sucursal=20, disponible=5)

    # Simular select(...).with_for_update() para origen y destino
    mock_db.scalar.side_effect = [inv_origen, inv_destino]

    payload = TransferenciaInterSucursalIn(
        id_sucursal_origen=10,
        id_sucursal_destino=20,
        id_variante=100,
        cantidad=8,
        motivo="Reposicion urgente de piezas",
    )

    comprobante = servicio.transferir_mercaderia(mock_db, payload, admin)

    assert inv_origen.cantidad_disponible == 12  # 20 - 8
    assert inv_destino.cantidad_disponible == 13  # 5 + 8
    assert mock_db.add_all.called  # Se agregan los dos movimientos
    assert mock_db.commit.called
    assert comprobante.cantidad_transferida == 8
    assert comprobante.saldo_origen_nuevo == 12
    assert comprobante.saldo_destino_nuevo == 13


def test_ac12_auto_transferencia_misma_sucursal_422():
    """# AC-12: Transferencia donde origen == destino debe ser rechazada."""
    # Validacion a nivel DTO Pydantic
    with pytest.raises(ValidationError):
        TransferenciaInterSucursalIn(
            id_sucursal_origen=10,
            id_sucursal_destino=10,
            id_variante=100,
            cantidad=5,
            motivo="Traspaso interno",
        )

    # Validacion a nivel Servicio
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()
    payload_mock = MagicMock(spec=TransferenciaInterSucursalIn)
    payload_mock.id_sucursal_origen = 10
    payload_mock.id_sucursal_destino = 10

    with pytest.raises(AutoTransferenciaError) as exc_info:
        servicio.transferir_mercaderia(MagicMock(), payload_mock, admin)
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "TRANSFERENCIA_MISMA_SUCURSAL"


def test_ac13_transferencia_stock_insuficiente_origen_409():
    """# AC-13: Transferencia con stock insuficiente en sede origen lanza StockInsuficienteError."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    mock_db.get.side_effect = lambda model, pk: mock_entidad_sucursal(id_sucursal=pk, activa=True)

    # Solo 3 unidades en origen
    inv_origen = mock_entidad_inventario(id_inventario=1, id_sucursal=10, disponible=3)
    mock_db.scalar.return_value = inv_origen

    payload = TransferenciaInterSucursalIn(
        id_sucursal_origen=10,
        id_sucursal_destino=20,
        id_variante=100,
        cantidad=10,  # Se piden 10 pero solo hay 3
        motivo="Traslado de vitrina",
    )

    with pytest.raises(StockInsuficienteError) as exc_info:
        servicio.transferir_mercaderia(mock_db, payload, admin)
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "STOCK_INSUFICIENTE"


# -----------------------------------------------------------------------------
# PRUEBAS DE HISTORIAL KARDEX (# AC-14)
# -----------------------------------------------------------------------------

def test_ac14_obtener_historial_kardex_exitoso():
    """# AC-14: Obtiene la bitacora de movimientos cronologicos del inventario."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    inv = mock_entidad_inventario(id_inventario=1, disponible=20)
    mock_db = MagicMock()
    mock_db.get.return_value = inv

    mov1 = MagicMock(spec=MovimientoInventarioORM)
    mov1.id_movimiento = 101
    mov1.id_inventario = 1
    mov1.tipo_movimiento = TipoMovimientoEnum.INGRESO_PROVEEDOR.value
    mov1.cantidad = 20
    mov1.saldo_anterior = 0
    mov1.saldo_nuevo = 20
    mov1.motivo = "Carga inicial"
    mov1.referencia_documento = "FAC-001"
    mov1.id_usuario = 1
    mov1.usuario_responsable = admin
    mov1.creado_en = datetime.now(timezone.utc)

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [mov1]
    mock_db.scalars.return_value = scalars_mock

    kardex = servicio.obtener_kardex(mock_db, 1, admin)

    assert kardex.id_inventario == 1
    assert kardex.saldo_actual == 20
    assert len(kardex.movimientos) == 1
    assert kardex.movimientos[0].tipo_movimiento == "ingreso_proveedor"
    assert kardex.movimientos[0].usuario_nombre == "Admin General"


def test_ac14_kardex_inventario_no_encontrado_404():
    """# AC-14: Si el inventario no existe, lanza InventarioNoEncontradoError."""
    servicio = ServicioGestionInventario()
    admin = crear_usuario_admin_mock()

    mock_db = MagicMock()
    mock_db.get.return_value = None

    with pytest.raises(InventarioNoEncontradoError) as exc_info:
        servicio.obtener_kardex(mock_db, 999, admin)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "INVENTARIO_NO_ENCONTRADO"


# -----------------------------------------------------------------------------
# PRUEBAS DE DISPONIBILIDAD PUBLICA (# AC-15)
# -----------------------------------------------------------------------------

def test_ac15_consultar_disponibilidad_publica_200(client):
    """# AC-15: Endpoint publico sin auth retorna sucursales activas con stock para la variante."""
    app.dependency_overrides.pop(get_current_user, None)

    mock_db = MagicMock()
    variante = mock_entidad_variante(id_variante=100, activo=True)
    mock_db.get.return_value = variante

    inv1 = mock_entidad_inventario(id_inventario=1, id_sucursal=10, disponible=12)
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [inv1]
    mock_db.scalars.return_value = scalars_mock

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        res = client.get("/api/v1/inventario/disponibilidad/100")
        assert res.status_code == 200
        data = res.json()
        assert data["id_variante"] == 100
        assert data["sku"] == "BER-CHA-L-NEG"
        assert len(data["sucursales"]) == 1
        assert data["sucursales"][0]["cantidad_disponible"] == 12
        assert data["sucursales"][0]["estado"] == "disponible"
    finally:
        app.dependency_overrides.clear()


def test_ac15_disponibilidad_publica_variante_inactiva_422():
    """# AC-15: Si la variante o prenda esta inactiva, responde 422 EntidadInactivaError."""
    servicio = ServicioGestionInventario()
    mock_db = MagicMock()
    variante_inactiva = mock_entidad_variante(id_variante=100, activo=False)
    mock_db.get.return_value = variante_inactiva

    with pytest.raises(EntidadInactivaError) as exc_info:
        servicio.consultar_disponibilidad_publica(mock_db, 100)
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "ENTIDAD_INACTIVA_PARA_INVENTARIO"
