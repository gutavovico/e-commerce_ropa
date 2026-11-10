"""Pruebas unitarias del script de carga de Menshopping (RF15), sin base de datos.

Spec: `.specs/modules/plataforma/P2-RF15-menshopping.md` §4. La carga completa contra PostgreSQL (con
rollback) está en `tests/integracion/test_multitenant.py` §RF15.
"""

import copy
import json
from decimal import Decimal

import pytest

from scripts import cargar_menshopping as carga


@pytest.fixture
def datos():
    return carga.cargar_datos()


def test_reparto_con_division_entera():
    assert carga.reparto(10, 2) == [5, 5]  # Santa Cruz
    assert carga.reparto(5, 2) == [2, 2]   # Beni: RF15, división entera
    with pytest.raises(carga.CargaError):
        carga.reparto(5, 0)


def test_los_datos_cumplen_rf15(datos):
    assert [s["unidades_por_prenda"] for s in datos["sucursales"]] == [10, 5]
    assert sorted(p["categoria"] for p in datos["prendas"]) == [
        "Camisas formales", "Camisetas", "Pantalones", "Pantalones de gala"]
    assert [Decimal(p["precio"]) for p in datos["prendas"]] == [Decimal("120"), Decimal("280"), Decimal("350"), Decimal("480")]
    assert datos["tallas"] == ["M", "L"]
    assert len(datos["usuarios"]) == 5
    # Sin contraseñas en el archivo versionado (R2)
    assert all(not ({"password", "clave", "password_hash"} & set(u)) for u in datos["usuarios"])


@pytest.mark.parametrize("cambio, mensaje", [
    (lambda d: d["sucursales"].pop(), "2 sucursales"),
    (lambda d: d["prendas"].pop(), "4 categorías"),
    (lambda d: d["tallas"].append("XL"), "2 variantes"),
    (lambda d: d["usuarios"][1].update(rol="cliente"), "Rol no admitido"),
    (lambda d: d["usuarios"][1].update(sucursal="la-paz"), "sucursal de Menshopping"),
    (lambda d: d["prendas"][0].update(precio="0"), "Precio inválido"),
])
def test_datos_invalidos_se_rechazan(datos, tmp_path, cambio, mensaje):
    alterados = copy.deepcopy(datos)
    cambio(alterados)
    ruta = tmp_path / "menshopping.json"
    ruta.write_text(json.dumps(alterados), encoding="utf-8")
    with pytest.raises(carga.CargaError, match=mensaje):
        carga.cargar_datos(ruta)


@pytest.mark.parametrize("clave", ["corta1A", "sinmayuscula1", "SINMINUSCULA1", "SinDigitos"])
def test_contrasena_debil_se_rechaza(clave):
    with pytest.raises(carga.CargaError):
        carga.validar_clave(clave)


def test_faltan_png_del_vestidor_no_se_carga_nada(datos, tmp_path):
    (tmp_path / "menshopping_camiseta.png").write_bytes(b"png")
    with pytest.raises(carga.CargaError, match="menshopping_pantalon.png"):
        carga.verificar_imagenes(datos, tmp_path)


def test_con_los_png_usa_la_foto_de_catalogo_si_existe(datos, tmp_path):
    for p in datos["prendas"]:
        (tmp_path / p["imagen_vestidor"]).write_bytes(b"png")
    (tmp_path / "menshopping_camisa_catalogo.jpg").write_bytes(b"jpg")
    imagenes = carga.verificar_imagenes(datos, tmp_path)
    assert imagenes.vestidor["camiseta"] == "/ar/menshopping_camiseta.png"
    assert imagenes.catalogo["camiseta"] == "/ar/menshopping_camiseta.png"   # sin foto: el PNG
    assert imagenes.catalogo["camisa"] == "/ar/menshopping_camisa_catalogo.jpg"
