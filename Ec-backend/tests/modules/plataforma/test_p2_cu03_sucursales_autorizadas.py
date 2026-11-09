"""Pruebas unitarias de RN07 con sucursales autorizadas (P2-CU03 B4), sin base de datos.

Spec: `.specs/finalized/P2-CU03-CU04-usuarios-sucursales/spec.md` §2 B4. Un empleado con varias
sucursales opera en todas ellas y en ninguna otra; cada sitio conserva su código de error. El
comportamiento contra PostgreSQL (lectura de `empleado_sucursal`) está en
`tests/integracion/test_multitenant.py`.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import AuthorizationError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu28_ventas_reservas.servicio import ServicioConsultarVentasReservas
from modules.comercial.cu29_indicadores.servicio import ServicioIndicadoresEmpresariales
from modules.comercial.cu31_reportes_voz.servicio import ServicioReportesVoz
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.compras_pagos.cu31_cu32_punto_venta import servicio as pos
from modules.gestion_operativa.cu24_inventario_stock.errores import SucursalNoAutorizadaError
from modules.gestion_operativa.cu24_inventario_stock.servicio import ServicioGestionInventario
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio


def empleado(rol: str, principal: int | None = 3, autorizadas=(3, 5)) -> UsuarioORM:
    """Usuario ORM real (no simulado) con sus sucursales ya resueltas, como tras la primera lectura."""
    usuario = UsuarioORM(id_usuario=9, email="e@t.com", rol=rol, id_sucursal=principal)
    usuario.__dict__["_sucursales_autorizadas"] = frozenset(autorizadas)
    return usuario


# ---------------------------------------------------------------- servicio

def test_administrador_opera_en_todas():
    admin = UsuarioORM(id_usuario=1, rol="administrador")
    assert SucursalesEmpleadoServicio.autorizadas(admin) is None
    assert SucursalesEmpleadoServicio.autoriza(admin, 99)


def test_sin_sesion_se_limita_a_la_principal():
    suelto = UsuarioORM(id_usuario=2, rol="cajero", id_sucursal=4)
    assert SucursalesEmpleadoServicio.autorizadas(suelto) == frozenset({4})
    simulado = MagicMock(spec=UsuarioORM)
    simulado.rol, simulado.id_sucursal = "encargado_sucursal", 6
    assert SucursalesEmpleadoServicio.autorizadas(simulado) == frozenset({6})
    assert not SucursalesEmpleadoServicio.autoriza(simulado, None)


def test_varias_sucursales():
    cajero = empleado("cajero")
    assert SucursalesEmpleadoServicio.autoriza(cajero, 3)
    assert SucursalesEmpleadoServicio.autoriza(cajero, 5)
    assert not SucursalesEmpleadoServicio.autoriza(cajero, 7)


# ---------------------------------------------------------------- caja (CU31-CU32)

@pytest.fixture
def sucursal_activa(monkeypatch):
    monkeypatch.setattr(pos.CarritoRepositorio, "obtener_sucursal_activa", staticmethod(lambda db, i: True))


@pytest.mark.parametrize("solicitada, esperada", [(None, 3), (5, 5), (3, 3)])
def test_caja_en_sucursal_autorizada(sucursal_activa, solicitada, esperada):
    assert pos.PuntoVentaServicio.resolver_sucursal(MagicMock(), empleado("cajero"), solicitada) == esperada


def test_caja_en_sucursal_no_autorizada(sucursal_activa):
    with pytest.raises(AuthorizationError) as error:
        pos.PuntoVentaServicio.resolver_sucursal(MagicMock(), empleado("cajero"), 7)
    assert error.value.code == "SUCURSAL_AJENA"


def test_caja_alcance_de_la_venta():
    pos.PuntoVentaServicio._verificar_alcance(empleado("cajero"), SimpleNamespace(id_sucursal=5))
    with pytest.raises(AuthorizationError) as error:
        pos.PuntoVentaServicio._verificar_alcance(empleado("cajero"), SimpleNamespace(id_sucursal=7))
    assert error.value.code == "SUCURSAL_AJENA"


# ---------------------------------------------------------------- cobro en efectivo (CU16)

def test_cobro_en_efectivo():
    PagoServicio._verificar_alcance_caja(empleado("cajero"), SimpleNamespace(id_sucursal_retiro=5))
    PagoServicio._verificar_alcance_caja(UsuarioORM(rol="administrador"), SimpleNamespace(id_sucursal_retiro=7))
    with pytest.raises(AuthorizationError) as error:
        PagoServicio._verificar_alcance_caja(empleado("cajero"), SimpleNamespace(id_sucursal_retiro=7))
    assert error.value.code == "SUCURSAL_AJENA"


# ---------------------------------------------------------------- inventario (CU24)

def test_inventario_encargado():
    ServicioGestionInventario._validar_acceso_sucursal(empleado("encargado_sucursal"), 5)
    with pytest.raises(SucursalNoAutorizadaError):
        ServicioGestionInventario._validar_acceso_sucursal(empleado("encargado_sucursal"), 7)


# ---------------------------------------------------------------- consultas (CU28, CU29)

@pytest.mark.parametrize("servicio", [ServicioConsultarVentasReservas, ServicioIndicadoresEmpresariales])
@pytest.mark.parametrize("solicitada, esperada", [(5, 5), (7, 3), (None, 3)])
def test_consultas_del_encargado(servicio, solicitada, esperada):
    instancia = servicio.__new__(servicio)
    assert instancia.resolver_alcance_sucursal(empleado("encargado_sucursal"), solicitada) == esperada


# ---------------------------------------------------------------- reportes por voz

def test_reportes_por_voz():
    from modules.comercial.cu31_reportes_voz.esquemas import ModuloReporteEnum

    ServicioReportesVoz.validar_permisos(empleado("encargado_sucursal"), ModuloReporteEnum.VENTAS, 5)
    with pytest.raises(Exception) as error:
        ServicioReportesVoz.validar_permisos(empleado("encargado_sucursal"), ModuloReporteEnum.VENTAS, 7)
    assert "no tienes asignada" in str(error.value)
