"""Fixtures compartidas por las pruebas de CU11 (Bolsa de Compra) y CU15 (Checkout).

Las dobles se colocan en la frontera del **repositorio**, no en la secuencia de llamadas de
SQLAlchemy. Mockear `db.execute(...).scalar_one_or_none()` por posición acopla la prueba al
orden exacto de las consultas: cualquier reordenación interna del servicio la rompe sin que haya
ningún defecto real. Sustituir los métodos del repositorio expresa la intención y deja que la
lógica de dominio —que es lo que se quiere verificar— se ejecute de verdad.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import (
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    SucursalORM,
    TallaORM,
    VarianteProductoORM,
)
from modules.compras_pagos.modelos import CarritoDetalleORM, CarritoORM

ID_CLIENTE = 10
ID_CARRITO = 77
ID_VARIANTE = 102
ID_SUCURSAL = 1
ID_LINEA = 44

PRECIO_BASE = Decimal("890.00")


@pytest.fixture
def usuario() -> UsuarioORM:
    """Usuario autenticado con rol cliente y su ficha asociada."""
    user = UsuarioORM(
        id_usuario=ID_CLIENTE,
        email="madame.dubois@fashionstore.com",
        rol="cliente",
        nombres="Madame",
        apellidos="Dubois",
        activo=True,
    )
    user.cliente = ClienteORM(
        id_cliente=ID_CLIENTE, talla_preferida="38", acepta_marketing=True
    )
    return user


@pytest.fixture
def sucursal() -> SucursalORM:
    """Boutique real del catálogo sembrado en Neon."""
    return SucursalORM(
        id_sucursal=ID_SUCURSAL,
        id_ciudad=1,
        nombre="Atelier Serrano - Madrid",
        direccion="Calle Serrano 48",
        telefono="+34 91 555 1234",
        activa=True,
    )


@pytest.fixture
def variante() -> VarianteProductoORM:
    """Variante de prenda con producto, talla y color resueltos."""
    producto = ProductoORM(
        id_producto=1,
        id_categoria=2,
        nombre="Vestido Plisado en Seda Marfil Natural",
        precio_base=PRECIO_BASE,
        imagen_url="https://cdn.fashionstore.test/vestido.jpg",
        activo=True,
    )
    var = VarianteProductoORM(
        id_variante=ID_VARIANTE,
        id_producto=1,
        id_talla=2,
        id_color=1,
        sku="ATEL-2025-V09-IV-38",
        precio_extra=Decimal("0.00"),
    )
    var.producto = producto
    var.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    var.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F0EA")
    return var


@pytest.fixture
def carrito() -> CarritoORM:
    """Bolsa activa del cliente."""
    return CarritoORM(
        id_carrito=ID_CARRITO,
        id_cliente=ID_CLIENTE,
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    )


@pytest.fixture
def linea(carrito, variante, sucursal) -> CarritoDetalleORM:
    """Línea de bolsa enlazada a su carrito, variante y boutique de expedición."""
    detalle = CarritoDetalleORM(
        id_carrito_detalle=ID_LINEA,
        id_carrito=ID_CARRITO,
        id_variante=ID_VARIANTE,
        id_sucursal=ID_SUCURSAL,
        cantidad=1,
        agregado_en=datetime.now(timezone.utc),
    )
    detalle.carrito = carrito
    detalle.variante = variante
    detalle.sucursal = sucursal
    return detalle


@pytest.fixture
def inventario() -> InventarioSucursalORM:
    """Existencias de la variante en la boutique (2 unidades disponibles)."""
    return InventarioSucursalORM(
        id_inventario=900,
        id_variante=ID_VARIANTE,
        id_sucursal=ID_SUCURSAL,
        id_temporada=1,
        cantidad_disponible=2,
        cantidad_reservada=0,
    )


@pytest.fixture
def db():
    """Sesión de base de datos simulada.

    Solo se espera de ella que acepte `add`, `delete`, `flush`, `commit` y `refresh`: toda
    consulta real pasa por el repositorio, que las pruebas sustituyen.
    """
    sesion = MagicMock()
    sesion.execute.return_value.scalar_one.return_value = 1
    return sesion
