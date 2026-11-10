"""Pruebas unitarias de P2-CU14 (dispositivo y catálogo), P2-CU20 (conflictos y cierre), la bandeja
de avisos y el reembolso de Stripe. Sin base de datos.

Spec: `.specs/changes/P2-CU14-CU15-CU19-CU20-sin-conexion/`.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import ConflictError, NotFoundError
from integrations.stripe_service import ResultadoReembolso, StripeService
from modules.sincronizacion.avisos_cliente import servicio as avisos_srv
from modules.sincronizacion.cu14_dispositivo_catalogo import servicio as cu14
from modules.sincronizacion.cu14_dispositivo_catalogo.esquemas import DispositivoIn
from modules.sincronizacion.cu20_conflictos import servicio as cu20
from modules.sincronizacion.modelos import AvisoClienteORM, ConflictoSyncORM

AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def usuario():
    return SimpleNamespace(id_usuario=10, nombres="Ana", apellidos="Rojas", email="ana@x.com", rol="cliente")


@pytest.fixture(autouse=True)
def sin_bitacora(monkeypatch):
    for modulo in (cu14, cu20):
        monkeypatch.setattr(
            modulo.ServicioBitacoraAuditoria, "registrar_evento_seguro", classmethod(lambda cls, **kw: None)
        )


def parametros(**cambios):
    base = dict(operacion_offline_habilitada=True, dias_antiguedad_offline=7, horas_vencimiento_reserva=24, moneda="BOB")
    base.update(cambios)
    return SimpleNamespace(**base)


# ---------------------------------------------------------------------------------------------
# CU14 · Dispositivo
# ---------------------------------------------------------------------------------------------

def test_codigo_corto_son_los_cuatro_primeros_hexadecimales():
    assert cu14.codigo_corto(uuid.UUID("3f9a2c1e-0000-4000-8000-000000000000")) == "3F9A"


@pytest.mark.parametrize("creado", [True, False])
def test_registrar_dispositivo_lo_crea_o_lo_reutiliza(monkeypatch, usuario, creado):
    identificador = uuid.uuid4()
    dispositivo = SimpleNamespace(
        id_dispositivo=1, identificador=identificador, id_cliente=10, plataforma="pwa",
        codigo_corto="ABCD", registrado_en=AHORA, ultima_descarga_en=None,
    )
    monkeypatch.setattr(cu14, "exigir_cliente", lambda db, u: 10)
    monkeypatch.setattr(cu14.DispositivoRepositorio, "insertar_si_falta", staticmethod(lambda *a: creado))
    monkeypatch.setattr(cu14.DispositivoRepositorio, "por_identificador", staticmethod(lambda *a, **kw: dispositivo))
    monkeypatch.setattr(cu14.ParametrosEmpresaServicio, "vigentes", staticmethod(lambda db: parametros(operacion_offline_habilitada=False)))

    salida, fue_creado = cu14.DispositivoServicio.registrar(MagicMock(), usuario, DispositivoIn(identificador=identificador, plataforma="pwa"))

    assert fue_creado is creado
    assert salida.codigo_corto == "ABCD"
    assert salida.operacion_offline_habilitada is False  # A5: se registra igual


def test_dispositivo_de_otro_cliente_responde_409(monkeypatch, usuario):
    identificador = uuid.uuid4()
    ajeno = SimpleNamespace(id_dispositivo=1, id_cliente=99)
    monkeypatch.setattr(cu14, "exigir_cliente", lambda db, u: 10)
    monkeypatch.setattr(cu14.DispositivoRepositorio, "insertar_si_falta", staticmethod(lambda *a: False))
    monkeypatch.setattr(cu14.DispositivoRepositorio, "por_identificador", staticmethod(lambda *a, **kw: ajeno))
    with pytest.raises(ConflictError) as exc:
        cu14.DispositivoServicio.registrar(MagicMock(), usuario, DispositivoIn(identificador=identificador, plataforma="flutter"))
    assert exc.value.code == "DISPOSITIVO_DE_OTRO_CLIENTE"


def test_dispositivo_desconocido_responde_404(monkeypatch, usuario):
    monkeypatch.setattr(cu14, "exigir_cliente", lambda db, u: 10)
    monkeypatch.setattr(cu14.DispositivoRepositorio, "por_identificador", staticmethod(lambda *a, **kw: None))
    with pytest.raises(NotFoundError) as exc:
        cu14.DispositivoServicio.del_cliente(MagicMock(), usuario, uuid.uuid4())
    assert exc.value.code == "DISPOSITIVO_NO_ENCONTRADO"


# ---------------------------------------------------------------------------------------------
# CU14 · Catálogo
# ---------------------------------------------------------------------------------------------

def preparar_catalogo(monkeypatch):
    repo = cu14.CatalogoLocalRepositorio
    variante = SimpleNamespace(id_variante=41, sku="MSH-CAM-M", id_talla=2, id_color=1, precio_extra=Decimal("10.00"), activo=True)
    inactiva = SimpleNamespace(id_variante=42, sku="MSH-CAM-L", id_talla=3, id_color=1, precio_extra=Decimal("0"), activo=False)
    producto = SimpleNamespace(
        id_producto=5, nombre="Camiseta", descripcion="Algodón", id_categoria=1,
        precio_base=Decimal("120.00"), imagen_url="/ar/x.png", variantes=[variante, inactiva],
    )
    sin_variantes = SimpleNamespace(id_producto=6, nombre="Sin stock", descripcion=None, id_categoria=1,
                                    precio_base=Decimal("1"), imagen_url=None, variantes=[inactiva])
    promo = SimpleNamespace(id_promocion=1, nombre="Otoño", tipo_descuento="porcentaje", valor_descuento=Decimal("10"),
                            alcance="producto", id_categoria=None, id_producto=5, fecha_fin=AHORA, codigo_cupon=None)
    cupon = SimpleNamespace(**{**promo.__dict__, "id_promocion": 2, "codigo_cupon": "SECRETO"})
    sucursal = SimpleNamespace(id_sucursal=3, nombre="Santa Cruz", direccion="Av. 1", ciudad=SimpleNamespace(nombre="Santa Cruz"),
                               horario_apertura=None, horario_cierre=None)
    monkeypatch.setattr(repo, "productos_activos", staticmethod(lambda db: [producto, sin_variantes]))
    monkeypatch.setattr(repo, "categorias", staticmethod(lambda db: [SimpleNamespace(id_categoria=1, nombre="Camisetas", id_categoria_padre=None)]))
    monkeypatch.setattr(repo, "tallas", staticmethod(lambda db, ids: [SimpleNamespace(id_talla=i, codigo="M", orden=1) for i in sorted(ids)]))
    monkeypatch.setattr(repo, "colores", staticmethod(lambda db, ids: [SimpleNamespace(id_color=i, nombre="Negro", codigo_hex=None) for i in sorted(ids)]))
    monkeypatch.setattr(repo, "promociones_vigentes", staticmethod(lambda db, t: [promo, cupon]))
    monkeypatch.setattr(repo, "productos_de_promociones", staticmethod(lambda db, ids: {1: [5]}))
    monkeypatch.setattr(repo, "sucursales_activas", staticmethod(lambda db: [sucursal]))
    monkeypatch.setattr(repo, "existencias", staticmethod(lambda db, ids: [(41, 3, 5)]))
    monkeypatch.setattr(cu14.ParametrosEmpresaServicio, "vigentes", staticmethod(lambda db: parametros()))
    monkeypatch.setattr(cu14, "ahora", lambda: AHORA)
    dispositivo = SimpleNamespace(id_dispositivo=1, ultima_descarga_en=None)
    monkeypatch.setattr(cu14.DispositivoServicio, "del_cliente", staticmethod(lambda *a, **kw: dispositivo))
    logs = []
    monkeypatch.setattr(cu14.DispositivoRepositorio, "registrar_log", staticmethod(lambda db, **kw: logs.append(kw)))
    return dispositivo, logs


def test_descarga_completa_trae_lo_de_la_empresa_y_registra_la_descarga(monkeypatch, usuario):
    dispositivo, logs = preparar_catalogo(monkeypatch)
    paquete = cu14.CatalogoSinConexionServicio.descargar(MagicMock(), usuario, uuid.uuid4(), "completo")

    assert paquete.generado_en == AHORA and paquete.moneda == "BOB"
    assert [p.id_producto for p in paquete.productos] == [5]          # sin variantes activas: fuera
    assert [v.id_variante for v in paquete.productos[0].variantes] == [41]
    assert paquete.productos[0].variantes[0].precio == Decimal("130.00")
    assert paquete.productos[0].descripcion == "Algodón"
    assert [p.id_promocion for p in paquete.promociones] == [1]       # el cupón no se publica
    assert paquete.existencias[0].cantidad_disponible == 5
    assert dispositivo.ultima_descarga_en == AHORA
    assert logs[0]["tipo"] == "descarga" and logs[0]["resultado"] == "ok"


def test_descarga_indispensable_omite_descripciones_y_promociones(monkeypatch, usuario):
    preparar_catalogo(monkeypatch)
    paquete = cu14.CatalogoSinConexionServicio.descargar(MagicMock(), usuario, uuid.uuid4(), "indispensable")
    assert paquete.modo == "indispensable"
    assert paquete.productos[0].descripcion is None
    assert paquete.promociones == []
    assert paquete.existencias  # lo indispensable para reservar sí viene


def test_el_catalogo_serializa_importes_como_cadena(monkeypatch, usuario):
    preparar_catalogo(monkeypatch)
    paquete = cu14.CatalogoSinConexionServicio.descargar(MagicMock(), usuario, uuid.uuid4(), "completo")
    json = paquete.model_dump(mode="json")
    assert json["productos"][0]["precio_base"] == "120.00"


# ---------------------------------------------------------------------------------------------
# CU20 · Conflictos
# ---------------------------------------------------------------------------------------------

def conflicto(estado="pendiente", **cambios):
    base = dict(id_conflicto=7, id_venta=501, id_pago=90, id_sucursal=3, tipo="stock_insuficiente",
                detalle={}, estado=estado, creado_en=AHORA, intentos_reembolso=0, aceptado_por=None,
                aceptado_en=None, resuelto_en=None, referencia_reembolso=None, ultimo_error=None)
    base.update(cambios)
    return ConflictoSyncORM(**base)


def compra_en_conflicto(monkeypatch, estado_venta="pendiente", escenario=None):
    venta = SimpleNamespace(id_venta=501, id_cliente=10, estado=estado_venta, numero_comprobante="WEB-1",
                            total=Decimal("120.00"), fecha_venta=AHORA, detalles=[])
    pago = SimpleNamespace(id_pago=90, referencia_pasarela="pi_1", monto=Decimal("120.00"), estado="confirmado",
                           payload_respuesta={"escenario_prueba": escenario} if escenario else {},
                           metodo_pago="tarjeta", confirmado_en=AHORA)
    monkeypatch.setattr(cu20.PagoServicio, "cargar_compra_para_cobro", staticmethod(lambda db, v, p, bloquear=True: (venta, pago)))
    monkeypatch.setattr(cu20.ConflictosServicio, "_detalle", staticmethod(lambda db, c: c))
    return venta, pago


def encargado():
    return SimpleNamespace(id_usuario=2, nombres="Eva", apellidos="", email="e@x.com", rol="encargado_sucursal")


def test_aceptar_reembolso_anula_la_compra_sin_tocar_inventario_y_avisa(monkeypatch):
    c = conflicto()
    venta, _ = compra_en_conflicto(monkeypatch)
    monkeypatch.setattr(cu20.ConflictosRepositorio, "obtener", staticmethod(lambda db, i, s, bloquear=False: c))
    monkeypatch.setattr(cu20.SucursalesEmpleadoServicio, "autorizadas", staticmethod(lambda u: frozenset({3})))
    monkeypatch.setattr(cu20, "ahora", lambda: AHORA)
    db = MagicMock()

    cu20.ConflictosServicio.aceptar_reembolso(db, encargado(), 7)

    assert c.estado == "reembolso_pendiente" and c.aceptado_por == 2 and c.aceptado_en == AHORA
    assert venta.estado == "anulada"
    aviso = next(a.args[0] for a in db.add.call_args_list if isinstance(a.args[0], AvisoClienteORM))
    assert aviso.tipo == "reembolso_aceptado" and aviso.mensaje == cu20.MENSAJE_REEMBOLSO_ACEPTADO
    assert not any("Movimiento" in type(a.args[0]).__name__ for a in db.add.call_args_list)
    db.commit.assert_called_once()


def test_aceptar_un_conflicto_ya_resuelto_responde_409(monkeypatch):
    c = conflicto(estado="reembolso_pendiente")
    monkeypatch.setattr(cu20.ConflictosRepositorio, "obtener", staticmethod(lambda db, i, s, bloquear=False: c))
    monkeypatch.setattr(cu20.SucursalesEmpleadoServicio, "autorizadas", staticmethod(lambda u: None))
    with pytest.raises(ConflictError) as exc:
        cu20.ConflictosServicio.aceptar_reembolso(MagicMock(), encargado(), 7)
    assert exc.value.code == "CONFLICTO_YA_RESUELTO"


def test_encargado_no_ve_conflictos_de_sucursales_no_autorizadas(monkeypatch):
    alcance = {}

    def obtener(db, i, sucursales, bloquear=False):
        alcance["sucursales"] = sucursales
        return None  # fuera de su alcance el repositorio no lo encuentra

    monkeypatch.setattr(cu20.ConflictosRepositorio, "obtener", staticmethod(obtener))
    monkeypatch.setattr(cu20.SucursalesEmpleadoServicio, "autorizadas", staticmethod(lambda u: frozenset({4})))
    with pytest.raises(NotFoundError):
        cu20.ConflictosServicio.detalle(MagicMock(), encargado(), 7)
    assert alcance["sucursales"] == frozenset({4})


@pytest.mark.parametrize("dia, esperado", [(date(2026, 11, 30), True), (date(2026, 11, 29), False), (date(2028, 2, 29), True)])
def test_ultimo_dia_del_mes(monkeypatch, dia, esperado):
    monkeypatch.setattr(cu20, "hoy", lambda: dia)
    assert cu20.es_ultimo_dia_del_mes() is esperado


def test_cierre_fuera_del_ultimo_dia_sin_forzar_responde_409(monkeypatch):
    monkeypatch.setattr(cu20, "es_ultimo_dia_del_mes", lambda: False)
    with pytest.raises(ConflictError) as exc:
        cu20.ConflictosServicio.procesar_cierre(MagicMock(), SimpleNamespace(id_usuario=1, rol="administrador"), forzar=False)
    assert exc.value.code == "CIERRE_NO_DISPONIBLE"


class PasarelaFalsa:
    def __init__(self, exitoso=True):
        self.exitoso = exitoso
        self.llamadas = []

    def reembolsar(self, referencia, monto, clave, escenario_prueba=None):
        self.llamadas.append((referencia, monto, clave))
        return ResultadoReembolso(self.exitoso, "re_1" if self.exitoso else None, "ok" if self.exitoso else "rechazado")


def preparar_cierre(monkeypatch, c):
    monkeypatch.setattr(cu20.ConflictosRepositorio, "ids_por_reembolsar", staticmethod(lambda db: [c.id_conflicto]))
    monkeypatch.setattr(cu20.ConflictosRepositorio, "tomar_para_reembolso", staticmethod(lambda db, i: c))
    monkeypatch.setattr(cu20, "tenant_actual", lambda db: 2)
    monkeypatch.setattr(cu20, "ahora", lambda: AHORA)


def test_cierre_forzado_reembolsa_y_resuelve(monkeypatch):
    c = conflicto(estado="reembolso_pendiente")
    _, pago = compra_en_conflicto(monkeypatch, estado_venta="anulada")
    preparar_cierre(monkeypatch, c)
    monkeypatch.setattr(cu20, "es_ultimo_dia_del_mes", lambda: False)
    pasarela = PasarelaFalsa()
    db = MagicMock()

    salida = cu20.ConflictosServicio.procesar_cierre(db, SimpleNamespace(id_usuario=1, rol="administrador"), forzar=True, pasarela=pasarela)

    assert (salida.forzado, salida.procesados, salida.reembolsados, salida.fallidos) == (True, 1, 1, [])
    assert pasarela.llamadas == [("pi_1", Decimal("120.00"), "reembolso-2-7-1")]
    assert pago.estado == "reembolsado"
    assert c.estado == "resuelto" and c.referencia_reembolso == "re_1" and c.intentos_reembolso == 1
    aviso = next(a.args[0] for a in db.add.call_args_list if isinstance(a.args[0], AvisoClienteORM))
    assert aviso.tipo == "reembolso_procesado"


def test_reembolso_fallido_sigue_pendiente_con_motivo_e_intento(monkeypatch):
    c = conflicto(estado="reembolso_pendiente", intentos_reembolso=1)
    _, pago = compra_en_conflicto(monkeypatch, estado_venta="anulada")
    preparar_cierre(monkeypatch, c)
    monkeypatch.setattr(cu20, "es_ultimo_dia_del_mes", lambda: True)
    pasarela = PasarelaFalsa(exitoso=False)

    salida = cu20.ConflictosServicio.procesar_cierre(MagicMock(), SimpleNamespace(id_usuario=1, rol="administrador"), pasarela=pasarela)

    assert (salida.forzado, salida.reembolsados, len(salida.fallidos)) == (False, 0, 1)
    assert pasarela.llamadas[0][2] == "reembolso-2-7-2"   # segundo intento, clave nueva
    assert c.estado == "reembolso_pendiente" and c.intentos_reembolso == 2 and c.ultimo_error == "rechazado"
    assert pago.estado == "confirmado"


def test_cierre_salta_lo_que_otro_cierre_tiene_tomado(monkeypatch):
    monkeypatch.setattr(cu20, "es_ultimo_dia_del_mes", lambda: True)
    monkeypatch.setattr(cu20.ConflictosRepositorio, "ids_por_reembolsar", staticmethod(lambda db: [7]))
    monkeypatch.setattr(cu20.ConflictosRepositorio, "tomar_para_reembolso", staticmethod(lambda db, i: None))
    monkeypatch.setattr(cu20, "tenant_actual", lambda db: 2)
    pasarela = PasarelaFalsa()
    salida = cu20.ConflictosServicio.procesar_cierre(MagicMock(), SimpleNamespace(id_usuario=1, rol="administrador"), pasarela=pasarela)
    assert salida.procesados == 0 and pasarela.llamadas == []


def test_el_cajero_no_accede_a_conflictos_y_el_encargado_no_cierra():
    from fastapi.testclient import TestClient

    from core.database import get_db
    from core.deps import get_current_user
    from main import app

    app.dependency_overrides[get_db] = lambda: MagicMock()
    try:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id_usuario=1, rol="cajero")
        assert TestClient(app).get("/api/v1/conflictos-sync").status_code == 403
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id_usuario=2, rol="encargado_sucursal")
        assert TestClient(app).post("/api/v1/conflictos-sync/procesar-cierre", json={"forzar": True}).status_code == 403
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------------------------
# Avisos y Stripe
# ---------------------------------------------------------------------------------------------

def test_tipo_de_aviso_desconocido_se_rechaza():
    with pytest.raises(ValueError):
        avisos_srv.AvisosServicio.crear(MagicMock(), id_cliente=1, tipo="push", titulo="t", mensaje="m")


def test_marcar_aviso_ajeno_responde_404(monkeypatch, usuario):
    monkeypatch.setattr(avisos_srv, "exigir_cliente", lambda db, u: 10)
    monkeypatch.setattr(avisos_srv.AvisosRepositorio, "del_cliente", staticmethod(lambda db, c, i: None))
    with pytest.raises(NotFoundError):
        avisos_srv.AvisosServicio.marcar_leido(MagicMock(), usuario, 5)


def test_simulador_de_stripe_reembolsa_y_puede_fallar():
    stripe = StripeService(api_key="")
    assert stripe.reembolsar("pi_1", Decimal("10"), "k").exitoso is True
    fallo = stripe.reembolsar("pi_1", Decimal("10"), "k", escenario_prueba="reembolso_fallido")
    assert fallo.exitoso is False and fallo.referencia is None
