"""RNF18 · Respaldo manual (parte B de `.specs/changes/P2-cierre-sesion-respaldos-push/`)."""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.plataforma.rnf18_respaldos import servicio as servicio_respaldos
from modules.plataforma.rnf18_respaldos.servicio import (
    RespaldosServicio,
    filtro_empresa,
    orden_por_dependencias,
)

_RUTA_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "restaurar_respaldo.py"
_spec = importlib.util.spec_from_file_location("restaurar_respaldo", _RUTA_SCRIPT)
restaurar = importlib.util.module_from_spec(_spec)
sys.modules["restaurar_respaldo"] = restaurar  # los dataclasses del script lo buscan ahí
_spec.loader.exec_module(restaurar)  # type: ignore[union-attr]


def _texto(composable) -> str:
    return composable.as_string(None)


# --------------------------------------------------------------------------- orden y alcance


def test_orden_por_dependencias_pone_cada_tabla_despues_de_sus_padres():
    orden = orden_por_dependencias(
        ["venta_detalle", "ventas", "tenants", "usuarios"],
        [("venta_detalle", "ventas"), ("ventas", "usuarios"), ("ventas", "tenants"), ("usuarios", "tenants")],
    )
    assert orden == ["tenants", "usuarios", "ventas", "venta_detalle"]


def test_orden_por_dependencias_detecta_un_ciclo():
    with pytest.raises(ValueError, match="ciclo"):
        orden_por_dependencias(["a", "b"], [("a", "b"), ("b", "a")])


def test_ac_b4_filtro_de_empresa_por_tipo_de_tabla():
    assert _texto(filtro_empresa("ventas", ["id_venta", "id_tenant"], 2)) == "id_tenant = 2"
    usuarios = _texto(filtro_empresa("usuarios", ["id_usuario", "id_tenant", "rol"], 2))
    assert usuarios.startswith("id_tenant = 2 OR (id_tenant IS NULL AND (id_usuario IN (SELECT ct.id_cliente")
    assert "rol = 'super_administrador'" in usuarios
    assert '"cliente_tenant"' in _texto(filtro_empresa("clientes", ["id_cliente"], 2))
    # Catálogo global: completo
    assert filtro_empresa("tallas", ["id_talla", "codigo"], 2) is None


# --------------------------------------------------------------------------- generación


@pytest.fixture
def repositorio_falso(monkeypatch):
    repo = SimpleNamespace(
        tablas=lambda db: ["tenants", "tallas", "codigos_recuperacion", "venta_detalle"],
        dependencias=lambda db: [("venta_detalle", "tenants")],
        columnas=lambda db: {
            "tenants": ["id_tenant", "codigo"],
            "tallas": ["id_talla", "codigo"],
            "codigos_recuperacion": ["id_codigo"],
            "venta_detalle": ["id_venta_detalle", "id_tenant", "cantidad"],
        },
        columnas_con_secuencia=lambda db: [("tenants", "id_tenant"), ("codigos_recuperacion", "id_codigo")],
        copiar=MagicMock(side_effect=lambda db, tabla, cols, filtro: b"1\tx\n2\ty\n"),
    )
    monkeypatch.setattr(servicio_respaldos, "RespaldosRepositorio", repo)
    monkeypatch.setattr(
        servicio_respaldos, "buscar_tenant_por_id", lambda db, i: SimpleNamespace(codigo="menshopping")
    )
    monkeypatch.setattr(servicio_respaldos, "revision_alembic", lambda: "0021")
    bitacora = MagicMock()
    monkeypatch.setattr(servicio_respaldos.ServicioBitacoraAuditoria, "registrar_evento_seguro", bitacora)
    return SimpleNamespace(repo=repo, bitacora=bitacora)


SUPER = SimpleNamespace(id_usuario=1, email="super@plataforma.test")


def test_ac_b3_respaldo_de_toda_la_plataforma(repositorio_falso):
    db = MagicMock()
    r = RespaldosServicio.generar(db, SUPER)
    texto = r.contenido.decode()
    assert r.nombre_archivo.startswith("respaldo-plataforma-")
    assert "-- Revisión de Alembic: 0021" in texto
    assert texto.index('COPY fashionstore."tenants"') < texto.index('COPY fashionstore."venta_detalle"')
    assert 'COPY fashionstore."codigos_recuperacion" ("id_codigo") FROM stdin;' in texto
    assert texto.rstrip().endswith("COMMIT;")
    assert r.filas == 8 and r.tablas == 4
    # Sin filtro: toda la plataforma
    assert all(llamada.args[3] is None for llamada in repositorio_falso.repo.copiar.call_args_list)


def test_ac_b4_ac_b6_respaldo_de_una_empresa_filtra_y_queda_en_la_bitacora(repositorio_falso):
    db = MagicMock()
    r = RespaldosServicio.generar(db, SUPER, id_tenant=2, direccion_ip="1.2.3.4")
    texto = r.contenido.decode()
    assert r.nombre_archivo.startswith("respaldo-menshopping-")
    assert "codigos_recuperacion" not in texto
    filtros = {ll.args[1]: ll.args[3] for ll in repositorio_falso.repo.copiar.call_args_list}
    assert _texto(filtros["venta_detalle"]) == "id_tenant = 2"
    assert filtros["tallas"] is None
    evento = repositorio_falso.bitacora.call_args.kwargs
    assert evento["accion"] == "RESPALDO_MANUAL"
    assert evento["payload_nuevo"]["alcance"] == "menshopping"
    assert evento["direccion_ip"] == "1.2.3.4"


def test_respaldo_de_una_empresa_inexistente_404(repositorio_falso, monkeypatch):
    monkeypatch.setattr(servicio_respaldos, "buscar_tenant_por_id", lambda db, i: None)
    from core.errors import NotFoundError

    with pytest.raises(NotFoundError):
        RespaldosServicio.generar(MagicMock(), SUPER, id_tenant=99)


def test_ac_b5_otro_rol_recibe_403():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id_usuario=5, rol="administrador")
    try:
        respuesta = TestClient(app).get("/api/v1/plataforma/respaldos")
        assert respuesta.status_code == 403
        assert respuesta.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------------------------------- restauración


def test_el_script_lee_lo_que_genera_el_servicio(repositorio_falso):
    texto = RespaldosServicio.generar(MagicMock(), SUPER).contenido.decode()
    leido = restaurar.leer_respaldo(texto)
    assert leido.revision == "0021"
    tablas = [b.tabla for b in leido.bloques]
    assert tablas.index('fashionstore."tenants"') < tablas.index('fashionstore."venta_detalle"')
    assert leido.bloques[0].datos == b"1\tx\n2\ty\n"
    assert len(leido.secuencias) == 2


def test_el_script_rechaza_lineas_copy_manipuladas():
    with pytest.raises(ValueError, match="no reconocida"):
        restaurar.leer_respaldo('COPY fashionstore."t" ("a"); DROP TABLE x; --") FROM stdin;\n\\.\n')


@pytest.mark.parametrize(
    "destino",
    [
        "postgresql+psycopg://u:p@ep-principal-123-pooler.us-east-2.aws.neon.tech/neondb",
        "postgresql://otro:p@ep-principal-123.us-east-2.aws.neon.tech/neondb",
    ],
)
def test_ac_b8_el_script_no_restaura_sobre_produccion(destino):
    entorno = {"DATABASE_URL_MIGRACIONES": "postgresql://o:p@ep-principal-123.us-east-2.aws.neon.tech/neondb"}
    with pytest.raises(SystemExit, match="producción"):
        restaurar.verificar_destino(destino, entorno)


def test_ac_b8_otra_rama_si_se_admite():
    entorno = {"DATABASE_URL": "postgresql://a:p@ep-principal-123-pooler.us-east-2.aws.neon.tech/neondb"}
    restaurar.verificar_destino("postgresql://o:p@ep-rama-restauracion-9.us-east-2.aws.neon.tech/neondb", entorno)
