"""CU31-CU32 · Punto de venta presencial.

Las dobles se colocan en la frontera del repositorio (mismo criterio que `conftest.py` del paquete):
la lógica de dominio —precios, retenciones, consolidación, reservas, cupón— se ejecuta de verdad
sobre objetos ORM reales y se comprueban los saldos de inventario movimiento a movimiento.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import AuthorizationError, ConflictError, NotFoundError, UnprocessableEntityError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import ColorORM, InventarioSucursalORM, ProductoORM, TallaORM, VarianteProductoORM
from modules.compras_pagos.cu31_cu32_punto_venta import servicio as modulo
from modules.compras_pagos.cu31_cu32_punto_venta.comprobante_pdf import generar_comprobante_pdf
from modules.compras_pagos.cu31_cu32_punto_venta.esquemas import CobroPosIn, LineaPosIn, VentaPosIn
from modules.compras_pagos.cu31_cu32_punto_venta.servicio import PuntoVentaServicio
from modules.compras_pagos.modelos import PagoORM, VentaDetalleORM, VentaORM
from modules.reservas.atencion_caja import ReservaCajaServicio, _id_desde_referencia
from modules.reservas.modelos import MovimientoInventarioORM

SUCURSAL = 1


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------


def _usuario(rol="cajero", id_sucursal=SUCURSAL, id_usuario=14):
    return UsuarioORM(id_usuario=id_usuario, email=f"{rol}@fs.com", rol=rol, nombres="Caja", apellidos="Uno",
                      activo=True, id_sucursal=id_sucursal)


def _variante(id_variante, precio="45.00", nombre="Camiseta básica amarilla de algodón", sku=None):
    producto = ProductoORM(id_producto=id_variante * 10, nombre=nombre, precio_base=Decimal(precio), activo=True,
                           imagen_url="/ar/x.png")
    variante = VarianteProductoORM(id_variante=id_variante, sku=sku or f"SKU-{id_variante}",
                                   precio_extra=Decimal("0.00"), activo=True)
    variante.producto = producto
    variante.talla = TallaORM(id_talla=3, codigo="M", orden=3)
    variante.color = ColorORM(id_color=58, nombre="Amarillo", codigo_hex="#FACE03")
    return variante


def _inventario(id_inventario, id_variante, disponible=10, reservada=0):
    return InventarioSucursalORM(id_inventario=id_inventario, id_variante=id_variante, id_sucursal=SUCURSAL,
                                 id_temporada=1, cantidad_disponible=disponible, cantidad_reservada=reservada)


def _movimientos(db):
    return [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], MovimientoInventarioORM)]


def _anadidos(db, tipo):
    return [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], tipo)]


@pytest.fixture
def db():
    sesion = MagicMock()

    def _flush():
        for c in sesion.add.call_args_list:
            if isinstance(c.args[0], VentaORM) and c.args[0].id_venta is None:
                c.args[0].id_venta = 500

    sesion.flush.side_effect = _flush
    return sesion


@pytest.fixture
def entorno(monkeypatch):
    """Sustituye los colaboradores de persistencia por dobles controlables."""
    repo = modulo.PuntoVentaRepositorio
    carrito = modulo.CarritoRepositorio
    estado = SimpleNamespace(variantes={}, inventarios={}, retenciones={}, empleado=True)

    monkeypatch.setattr(carrito, "obtener_sucursal_activa", staticmethod(lambda db, i: SimpleNamespace(id_sucursal=i)))
    monkeypatch.setattr(carrito, "obtener_promociones_por_producto", staticmethod(lambda db, ids: {}))
    monkeypatch.setattr(carrito, "obtener_inventario",
                        staticmethod(lambda db, v, s, c=1, bloquear=False: estado.inventarios.get(v)))
    monkeypatch.setattr(repo, "es_empleado", staticmethod(lambda db, i: estado.empleado))
    monkeypatch.setattr(repo, "variantes_por_ids",
                        staticmethod(lambda db, ids: {i: estado.variantes[i] for i in ids if i in estado.variantes}))
    monkeypatch.setattr(repo, "disponible_en_sucursal",
                        staticmethod(lambda db, v, s: estado.inventarios[v].cantidad_disponible if v in estado.inventarios else 0))
    monkeypatch.setattr(repo, "usuario_de_cliente", staticmethod(lambda db, i: None))
    monkeypatch.setattr(repo, "venta_pendiente_de_reserva", staticmethod(lambda db, i: None))
    monkeypatch.setattr(repo, "buscar_retencion_venta",
                        staticmethod(lambda db, venta, v: estado.retenciones.get(v)))
    monkeypatch.setattr(repo, "inventario_por_id", staticmethod(
        lambda db, i, bloquear=True: next(inv for inv in estado.inventarios.values() if inv.id_inventario == i)))
    monkeypatch.setattr(modulo.CheckoutServicio, "generar_numero_comprobante", staticmethod(lambda db: "FS-2026-000099"))
    monkeypatch.setattr(PuntoVentaServicio, "obtener_venta",
                        staticmethod(lambda db, u, i: SimpleNamespace(id_venta=i)))
    return estado


# ---------------------------------------------------------------------------
# Alcance (D9)
# ---------------------------------------------------------------------------


def test_cajero_opera_su_sucursal(db, entorno):
    assert PuntoVentaServicio.resolver_sucursal(db, _usuario(), None) == SUCURSAL


def test_cajero_no_puede_operar_otra_sucursal(db, entorno):
    with pytest.raises(AuthorizationError) as error:
        PuntoVentaServicio.resolver_sucursal(db, _usuario(), 2)
    assert error.value.code == "SUCURSAL_AJENA"


def test_administrador_debe_elegir_sucursal(db, entorno):
    with pytest.raises(UnprocessableEntityError):
        PuntoVentaServicio.resolver_sucursal(db, _usuario("administrador", None, 8), None)
    assert PuntoVentaServicio.resolver_sucursal(db, _usuario("administrador", None, 8), 2) == 2


def test_cajero_sin_sucursal_asignada(db, entorno):
    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.resolver_sucursal(db, _usuario(id_sucursal=None), None)
    assert error.value.code == "SUCURSAL_NO_ASIGNADA"


def test_cobrar_venta_de_otra_sucursal_403():
    venta = VentaORM(id_venta=1, id_sucursal=2)
    with pytest.raises(AuthorizationError):
        PuntoVentaServicio._verificar_alcance(_usuario(), venta)


# ---------------------------------------------------------------------------
# CU31 · Registrar
# ---------------------------------------------------------------------------


def test_registrar_venta_directa_retiene_stock(db, entorno):
    entorno.variantes[137] = _variante(137)
    entorno.inventarios[137] = _inventario(900, 137, disponible=10)

    PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(lineas=[LineaPosIn(id_variante=137, cantidad=1)]))

    venta = _anadidos(db, VentaORM)[0]
    assert (venta.tipo_venta, venta.estado, venta.id_cajero, venta.numero_comprobante) == (
        "presencial", "pendiente", 14, "FS-2026-000099")
    assert venta.total == Decimal("45.00") and venta.id_cliente is None
    detalle = _anadidos(db, VentaDetalleORM)[0]
    assert (detalle.cantidad, detalle.precio_unitario, detalle.id_sucursal) == (1, Decimal("45.00"), SUCURSAL)
    movimiento = _movimientos(db)[0]
    assert (movimiento.tipo_movimiento, movimiento.cantidad, movimiento.referencia_documento) == ("reserva", 1, "VENTA-500")
    assert (movimiento.saldo_anterior, movimiento.saldo_nuevo) == (10, 9)
    assert (entorno.inventarios[137].cantidad_disponible, entorno.inventarios[137].cantidad_reservada) == (9, 1)
    db.commit.assert_called_once()


def test_registrar_sin_stock_suficiente_no_crea_nada(db, entorno):
    entorno.variantes[137] = _variante(137)
    entorno.inventarios[137] = _inventario(900, 137, disponible=10)

    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(lineas=[LineaPosIn(id_variante=137, cantidad=11)]))

    assert error.value.code == "STOCK_INSUFICIENTE"
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_registrar_sin_ficha_de_empleado(db, entorno):
    entorno.empleado = False
    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(lineas=[LineaPosIn(id_variante=137, cantidad=1)]))
    assert error.value.code == "EMPLEADO_NO_REGISTRADO"
    db.add.assert_not_called()


def test_sku_inexistente(db, entorno):
    with pytest.raises(NotFoundError) as error:
        PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(lineas=[LineaPosIn(id_variante=999, cantidad=1)]))
    assert error.value.code == "SKU_NO_ENCONTRADO"


def test_venta_vacia(db, entorno):
    with pytest.raises(UnprocessableEntityError) as error:
        PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(lineas=[]))
    assert error.value.code == "VENTA_VACIA"


def test_precios_los_recalcula_el_servidor(db, entorno):
    """El cuerpo no transporta importes: solo variantes y cantidades (POS-01)."""
    assert "total" not in VentaPosIn.model_fields and "precio_unitario" not in LineaPosIn.model_fields


# ---------------------------------------------------------------------------
# Reserva (D5)
# ---------------------------------------------------------------------------


def _reserva(detalles):
    return SimpleNamespace(id_reserva=7, id_cliente=10, id_sucursal=SUCURSAL, estado="pendiente",
                           creado_en=datetime(2026, 11, 8, tzinfo=timezone.utc), detalles=detalles)


def _detalle_reserva(variante, cantidad=1):
    return SimpleNamespace(id_variante=variante.id_variante, variante=variante, cantidad=cantidad)


def test_lineas_de_reserva_no_se_retienen_dos_veces(db, entorno, monkeypatch):
    blusa = _variante(201, "120.00", "Blusa de satén")
    reserva = _reserva([_detalle_reserva(blusa)])
    monkeypatch.setattr(ReservaCajaServicio, "obtener_para_caja", staticmethod(lambda db, r, s, u: reserva))

    PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(reserva="RES-2026-0007"))

    assert _movimientos(db) == []
    venta = _anadidos(db, VentaORM)[0]
    assert (venta.id_reserva, venta.id_cliente, venta.total) == (7, 10, Decimal("120.00"))
    assert reserva.estado == "en_atencion"


def test_no_se_puede_excluir_una_prenda_ajena_a_la_reserva(db, entorno, monkeypatch):
    reserva = _reserva([_detalle_reserva(_variante(201))])
    monkeypatch.setattr(ReservaCajaServicio, "obtener_para_caja", staticmethod(lambda db, r, s, u: reserva))
    with pytest.raises(UnprocessableEntityError) as error:
        PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(reserva="7", lineas_reserva_excluidas=[999]))
    assert error.value.code == "LINEA_RESERVA_DESCONOCIDA"


def test_prenda_de_la_reserva_no_se_anade_otra_vez(db, entorno, monkeypatch):
    blusa = _variante(201)
    reserva = _reserva([_detalle_reserva(blusa)])
    monkeypatch.setattr(ReservaCajaServicio, "obtener_para_caja", staticmethod(lambda db, r, s, u: reserva))
    with pytest.raises(UnprocessableEntityError) as error:
        PuntoVentaServicio.registrar_venta(db, _usuario(), VentaPosIn(reserva="7", lineas=[LineaPosIn(id_variante=201, cantidad=1)]))
    assert error.value.code == "VARIANTE_YA_EN_RESERVA"


def test_codigo_de_reserva_legible_o_numerico():
    assert _id_desde_referencia("RES-2026-0007") == 7
    assert _id_desde_referencia("res-2026-0012") == 12
    assert _id_desde_referencia("7") == 7
    assert _id_desde_referencia("ZZZ") is None


# ---------------------------------------------------------------------------
# CU32 · Cobrar
# ---------------------------------------------------------------------------


def _venta_pendiente(detalles, total="45.00", id_reserva=None, minutos=5):
    venta = VentaORM(id_venta=500, numero_comprobante="FS-2026-000099", tipo_venta="presencial", estado="pendiente",
                     id_sucursal=SUCURSAL, total=Decimal(total), id_reserva=id_reserva, id_promocion=None,
                     fecha_venta=datetime.now(timezone.utc) - timedelta(minutes=minutos))
    venta.detalles = detalles
    return venta


def _preparar_cobro(monkeypatch, venta, reserva=None):
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "cargar_venta", staticmethod(lambda db, i, bloquear=False: venta))
    monkeypatch.setattr(ReservaCajaServicio, "bloquear", staticmethod(lambda db, i: reserva))


def test_cobro_en_efectivo_con_cambio_consolida_stock(db, entorno, monkeypatch):
    inventario = _inventario(900, 137, disponible=9, reservada=1)
    entorno.inventarios[137] = inventario
    entorno.retenciones[137] = SimpleNamespace(id_inventario=900)
    venta = _venta_pendiente([VentaDetalleORM(id_variante=137, cantidad=1, precio_unitario=Decimal("45.00"))])
    _preparar_cobro(monkeypatch, venta)

    PuntoVentaServicio.cobrar_venta(db, _usuario(), 500, CobroPosIn(metodo_pago="efectivo", monto_recibido=Decimal("50")))

    pago = _anadidos(db, PagoORM)[0]
    assert (pago.estado, pago.monto, pago.payload_respuesta["cambio"]) == ("confirmado", Decimal("45.00"), "5.00")
    assert venta.estado == "pagada"
    movimiento = _movimientos(db)[0]
    assert (movimiento.tipo_movimiento, movimiento.cantidad, movimiento.saldo_anterior, movimiento.saldo_nuevo) == (
        "venta_confirmada", -1, 1, 0)
    assert (inventario.cantidad_disponible, inventario.cantidad_reservada) == (9, 0)


def test_efectivo_insuficiente(db, entorno, monkeypatch):
    venta = _venta_pendiente([])
    _preparar_cobro(monkeypatch, venta)
    with pytest.raises(UnprocessableEntityError) as error:
        PuntoVentaServicio.cobrar_venta(db, _usuario(), 500, CobroPosIn(metodo_pago="efectivo", monto_recibido=Decimal("40")))
    assert error.value.code == "MONTO_INSUFICIENTE"
    assert venta.estado == "pendiente"
    db.add.assert_not_called()


def test_tarjeta_exige_referencia(db, entorno, monkeypatch):
    _preparar_cobro(monkeypatch, _venta_pendiente([]))
    with pytest.raises(UnprocessableEntityError) as error:
        PuntoVentaServicio.cobrar_venta(db, _usuario(), 500, CobroPosIn(metodo_pago="tarjeta_credito"))
    assert error.value.code == "REFERENCIA_REQUERIDA"


def test_tarjeta_rechazada_deja_la_venta_pendiente_sin_mover_stock(db, entorno, monkeypatch):
    venta = _venta_pendiente([VentaDetalleORM(id_variante=137, cantidad=1, precio_unitario=Decimal("45.00"))])
    _preparar_cobro(monkeypatch, venta)

    PuntoVentaServicio.cobrar_venta(db, _usuario(), 500,
                                    CobroPosIn(metodo_pago="tarjeta_debito", referencia="AUT-1", aprobado=False))

    assert _anadidos(db, PagoORM)[0].estado == "rechazado"
    assert venta.estado == "pendiente"
    assert _movimientos(db) == []


def test_doble_cobro_rechazado(db, entorno, monkeypatch):
    venta = _venta_pendiente([])
    venta.estado = "pagada"
    _preparar_cobro(monkeypatch, venta)
    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.cobrar_venta(db, _usuario(), 500, CobroPosIn(metodo_pago="efectivo", monto_recibido=Decimal("50")))
    assert error.value.code == "VENTA_NO_PENDIENTE"
    db.add.assert_not_called()


def test_cobro_desde_reserva_consolida_libera_y_atiende(db, entorno, monkeypatch):
    blusa, falda = _variante(201, "120.00"), _variante(202, "80.00")
    reserva = _reserva([_detalle_reserva(blusa), _detalle_reserva(falda)])
    venta = _venta_pendiente([VentaDetalleORM(id_variante=201, cantidad=1, precio_unitario=Decimal("120.00"))],
                             total="120.00", id_reserva=7)
    _preparar_cobro(monkeypatch, venta, reserva)
    llamadas = []
    monkeypatch.setattr(ReservaCajaServicio, "consolidar_linea",
                        staticmethod(lambda db, r, d, u, i, n: llamadas.append(("consolidar", d.id_variante))))
    monkeypatch.setattr(ReservaCajaServicio, "liberar_linea",
                        staticmethod(lambda db, r, d, u, n: llamadas.append(("liberar", d.id_variante))))

    PuntoVentaServicio.cobrar_venta(db, _usuario(), 500,
                                    CobroPosIn(metodo_pago="tarjeta_credito", referencia="AUT-123"))

    assert llamadas == [("consolidar", 201), ("liberar", 202)]
    assert (reserva.estado, reserva.atendido_por) == ("atendida", 14)
    assert venta.estado == "pagada"


def test_cupon_agotado_al_cobrar(db, entorno, monkeypatch):
    venta = _venta_pendiente([])
    venta.id_promocion = 3
    venta.promocion = SimpleNamespace(codigo_cupon="MAISON-2025")
    _preparar_cobro(monkeypatch, venta)
    monkeypatch.setattr(modulo.CarritoRepositorio, "consumir_uso_cupon", staticmethod(lambda db, p: False))
    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.cobrar_venta(db, _usuario(), 500, CobroPosIn(metodo_pago="efectivo", monto_recibido=Decimal("50")))
    assert error.value.code == "CUPON_AGOTADO"


def test_cobrar_una_orden_vencida_la_anula(db, entorno, monkeypatch):
    venta = _venta_pendiente([], minutos=180)
    _preparar_cobro(monkeypatch, venta)
    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.cobrar_venta(db, _usuario(), 500, CobroPosIn(metodo_pago="efectivo", monto_recibido=Decimal("50")))
    assert error.value.code == "VENTA_NO_PENDIENTE"
    assert venta.estado == "anulada"
    db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Anular (POS-10)
# ---------------------------------------------------------------------------


def test_anular_libera_lo_retenido_en_caja_y_conserva_la_reserva(db, entorno, monkeypatch):
    inventario = _inventario(900, 137, disponible=9, reservada=1)
    entorno.inventarios[137] = inventario
    entorno.retenciones[137] = SimpleNamespace(id_inventario=900)
    blusa = _variante(201)
    reserva = _reserva([_detalle_reserva(blusa)])
    reserva.estado = "en_atencion"
    venta = _venta_pendiente([
        VentaDetalleORM(id_variante=201, cantidad=1, precio_unitario=Decimal("45.00")),
        VentaDetalleORM(id_variante=137, cantidad=1, precio_unitario=Decimal("45.00")),
    ], id_reserva=7)
    _preparar_cobro(monkeypatch, venta, reserva)

    PuntoVentaServicio.anular_venta(db, _usuario(), 500, "El cliente se arrepintió")

    movimientos = _movimientos(db)
    assert len(movimientos) == 1  # solo la línea de caja; la de reserva sigue apartada
    assert (movimientos[0].tipo_movimiento, movimientos[0].cantidad) == ("cancelacion_pedido", 1)
    assert (inventario.cantidad_disponible, inventario.cantidad_reservada) == (10, 0)
    assert (venta.estado, reserva.estado) == ("anulada", "confirmada")


# ---------------------------------------------------------------------------
# Reserva: consolidar y liberar sobre la fila exacta
# ---------------------------------------------------------------------------


def test_reserva_consolida_y_libera_sobre_su_fila(db, monkeypatch):
    fila = _inventario(700, 201, disponible=4, reservada=2)
    repo = __import__("modules.reservas.atencion_caja", fromlist=["x"]).ReservaConsultaRepositorio
    monkeypatch.setattr(repo, "buscar_movimiento_reserva", staticmethod(lambda db, r, v: SimpleNamespace(id_inventario=700)))
    monkeypatch.setattr(repo, "obtener_inventario_por_id", staticmethod(lambda db, i: fila))
    reserva = _reserva([])
    detalle = SimpleNamespace(id_variante=201, cantidad=1)

    ReservaCajaServicio.consolidar_linea(db, reserva, detalle, _usuario(), 500, "FS-2026-000099")
    ReservaCajaServicio.liberar_linea(db, reserva, detalle, _usuario(), "FS-2026-000099")

    tipos = [m.tipo_movimiento for m in _movimientos(db)]
    assert tipos == ["venta_confirmada", "liberacion_reserva"]
    assert (fila.cantidad_disponible, fila.cantidad_reservada) == (5, 0)


# ---------------------------------------------------------------------------
# Comprobante PDF
# ---------------------------------------------------------------------------


def test_comprobante_pdf_es_un_pdf_valido():
    from modules.compras_pagos.cu31_cu32_punto_venta.esquemas import LineaVentaPosOut, PagoPosOut, VentaPosOut

    ahora = datetime(2026, 11, 8, 12, 30, tzinfo=timezone.utc)
    venta = VentaPosOut(
        id_venta=500, numero_comprobante="FS-2026-000099", estado="pagada", fecha_venta=ahora, id_sucursal=1,
        nombre_sucursal="Atelier Serrano - Madrid", direccion_sucursal="Calle Serrano 48", cajero_nombre="Caja Uno",
        subtotal=Decimal("45.00"), descuento=Decimal("0.00"), total=Decimal("45.00"), iva_incluido=Decimal("7.81"),
        lineas=[LineaVentaPosOut(id_variante=137, sku="FS-CAMISETA", nombre_producto="Camiseta básica amarilla",
                                 talla_codigo="M", color_nombre="Amarillo", cantidad=1, precio_lista=Decimal("45.00"),
                                 precio_unitario=Decimal("45.00"), subtotal_linea=Decimal("45.00"), origen="caja")],
        pagos=[PagoPosOut(id_pago=1, metodo_pago="efectivo", monto=Decimal("45.00"), estado="confirmado",
                          monto_recibido=Decimal("50.00"), cambio=Decimal("5.00"), creado_en=ahora)],
    )
    contenido = generar_comprobante_pdf(venta)
    assert contenido.startswith(b"%PDF") and len(contenido) > 1000


def test_comprobante_pdf_no_disponible_si_esta_pendiente(db, monkeypatch):
    monkeypatch.setattr(PuntoVentaServicio, "obtener_venta",
                        staticmethod(lambda db, u, i: SimpleNamespace(estado="pendiente", numero_comprobante="X")))
    with pytest.raises(ConflictError) as error:
        PuntoVentaServicio.comprobante_pdf(db, _usuario(), 500)
    assert error.value.code == "COMPROBANTE_NO_DISPONIBLE"


# ---------------------------------------------------------------------------
# RBAC del router
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cliente", "proveedor"])
def test_roles_ajenos_a_la_caja_reciben_403(client, rol):
    from core.deps import get_current_user
    from main import app

    app.dependency_overrides[get_current_user] = lambda: _usuario(rol)
    try:
        respuesta = client.get("/api/v1/pos/ventas")
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 403


def test_sin_sesion_401(client):
    assert client.get("/api/v1/pos/ventas").status_code == 401


# ---------------------------------------------------------------------------
# Búsquedas de apoyo a la caja (prenda, cliente, reservas del cliente, cupones)
# ---------------------------------------------------------------------------


def test_buscar_variantes_devuelve_todas_las_coincidencias_con_stock_de_la_sucursal(db, entorno, monkeypatch):
    from modules.catalogo.modelos import CategoriaORM

    m, l = _variante(137, sku="CAM-AMA-M"), _variante(138, sku="CAM-AMA-L")
    for v in (m, l):
        v.producto.categoria = CategoriaORM(id_categoria=4, nombre="Camisetas")
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "buscar_variantes", staticmethod(lambda db, q: [m, l]))
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "disponibles_en_sucursal",
                        staticmethod(lambda db, ids, s: {137: 4}))

    resultado = PuntoVentaServicio.buscar_variantes(db, _usuario(), "camiseta", None)

    assert [v.sku for v in resultado] == ["CAM-AMA-M", "CAM-AMA-L"]
    assert resultado[0].categoria_nombre == "Camisetas"
    assert resultado[0].disponible_en_sucursal == 4
    assert resultado[1].disponible_en_sucursal == 0  # agotada: se muestra, no se oculta
    assert resultado[0].precio_final == Decimal("45.00")


def test_buscar_variantes_sin_coincidencias(db, entorno, monkeypatch):
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "buscar_variantes", staticmethod(lambda db, q: []))
    assert PuntoVentaServicio.buscar_variantes(db, _usuario(), "zzz", None) == []


def test_buscar_clientes_por_nombre_o_correo(db, monkeypatch):
    ana = UsuarioORM(id_usuario=3, email="ana@correo.com", nombres="Ana", apellidos="Valenzuela", rol="cliente")
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "buscar_clientes", staticmethod(lambda db, q: [ana]))

    resultado = PuntoVentaServicio.buscar_clientes(db, "ana")

    assert [(c.id_cliente, c.email) for c in resultado] == [(3, "ana@correo.com")]


def test_reservas_del_cliente_solo_las_atendibles_de_la_sucursal(db, monkeypatch):
    from modules.reservas.cu13_consultar_cancelar_reservas.repositorio import ReservaConsultaRepositorio

    ahora = datetime.now(timezone.utc)

    def reserva(id_reserva, estado, sucursal=SUCURSAL, horas=2):
        r = SimpleNamespace(id_reserva=id_reserva, estado=estado, id_sucursal=sucursal,
                            fecha_hora_atencion=ahora + timedelta(hours=horas), creado_en=ahora, detalles=[])
        return r

    reservas = [
        reserva(1, "confirmada", horas=5),
        reserva(2, "pendiente", horas=1),
        reserva(3, "en_atencion"),          # ya está en una orden de caja
        reserva(4, "cancelada"),
        reserva(5, "confirmada", sucursal=9),  # otra boutique
        reserva(6, "confirmada", horas=-3),    # vencería al cargarla
    ]
    monkeypatch.setattr(ReservaConsultaRepositorio, "buscar_reservas_de_cliente", staticmethod(lambda db, i: reservas))
    ana = UsuarioORM(id_usuario=3, email="ana@correo.com", nombres="Ana", apellidos="Valenzuela", rol="cliente")
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "usuario_de_cliente", staticmethod(lambda db, i: ana))

    resultado = PuntoVentaServicio.reservas_de_cliente(db, _usuario(), 3, None)

    assert [r.id_reserva for r in resultado] == [2, 1]  # ordenadas por cita
    assert resultado[0].cliente.email == "ana@correo.com"
    db.add.assert_not_called()  # solo lectura: no vence nada


def test_reservas_de_cliente_inexistente(db, monkeypatch):
    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "usuario_de_cliente", staticmethod(lambda db, i: None))
    with pytest.raises(NotFoundError) as error:
        PuntoVentaServicio.reservas_de_cliente(db, _usuario(), 999, None)
    assert error.value.code == "CLIENTE_NO_ENCONTRADO"


def test_cupones_disponibles_con_usos_restantes(db, monkeypatch):
    from modules.comercial.cu27_promociones.modelos import PromocionORM

    ahora = datetime.now(timezone.utc)
    limitado = PromocionORM(id_promocion=1, nombre="Bienvenida", codigo_cupon=" BIENVENIDA10 ",
                            tipo_descuento="porcentaje", valor_descuento=Decimal("10.00"), alcance="global",
                            fecha_inicio=ahora, fecha_fin=ahora + timedelta(days=5), limite_usos=50, usos_actuales=48)
    libre = PromocionORM(id_promocion=2, nombre="Atelier", codigo_cupon="ATELIER5", tipo_descuento="monto_fijo",
                         valor_descuento=Decimal("5.00"), alcance="global", fecha_inicio=ahora,
                         fecha_fin=ahora + timedelta(days=5), limite_usos=None, usos_actuales=0)
    recibido = {}

    def falso(db, texto, momento):
        recibido["texto"] = texto
        return [limitado, libre]

    monkeypatch.setattr(modulo.PuntoVentaRepositorio, "cupones_vigentes", staticmethod(falso))

    resultado = PuntoVentaServicio.cupones_disponibles(db, None)

    assert recibido["texto"] is None  # sin texto: todos los vigentes
    assert [(c.codigo, c.usos_restantes) for c in resultado] == [("BIENVENIDA10", 2), ("ATELIER5", None)]


def test_rutas_de_busqueda_publicadas():
    from main import app

    rutas = set(app.openapi()["paths"])
    for ruta in ("/api/v1/pos/variantes", "/api/v1/pos/clientes", "/api/v1/pos/clientes/{id_cliente}/reservas",
                 "/api/v1/pos/cupones"):
        assert ruta in rutas
