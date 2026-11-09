"""Pruebas unitarias y de contrato HTTP para P2-CU09 y P2-CU10 (Suscripción de la empresa + Stripe)."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.errors import ConflictError, NotFoundError, PaymentRequiredError
from core.tiempo import hoy as hoy_bolivia
from integrations.stripe_service import ResultadoPasarela, StripeService
from main import app
from modules.plataforma.cu09_cu10_suscripcion_empresa.esquemas import (
    ConfirmarCambioSuscripcionIn,
    IniciarPagoSuscripcionIn,
)
from modules.plataforma.cu09_cu10_suscripcion_empresa.repositorio import (
    MiSuscripcionRepositorio,
)
from modules.plataforma.cu09_cu10_suscripcion_empresa.router import (
    exigir_administrador_empresa,
)
from modules.plataforma.cu09_cu10_suscripcion_empresa.servicio import (
    MiSuscripcionServicio,
)


def _admin_falso(id_tenant: int = 1, id_usuario: int = 10):
    return SimpleNamespace(
        id_usuario=id_usuario,
        id_tenant=id_tenant,
        email="admin@atelier.com",
        rol="administrador",
        activo=True,
    )


def _tenant_falso(id_tenant: int = 1):
    return SimpleNamespace(
        id_tenant=id_tenant,
        codigo="atelier-central",
        nombre="Atelier Central",
        estado="activa",
    )


def _plan_falso(
    id_plan: int = 2,
    nombre: str = "Profesional",
    precio: str = "79.00",
    max_suc: int = 3,
    max_emp: int | None = 15,
    activo: bool = True,
):
    return SimpleNamespace(
        id_plan=id_plan,
        nombre=nombre,
        precio_mensual=Decimal(precio),
        max_sucursales_activas=max_suc,
        max_empleados=max_emp,
        activo=activo,
    )


def _suscripcion_falsa(
    id_suscripcion: int = 100,
    id_tenant: int = 1,
    id_plan: int = 2,
    estado: str = "activa",
    dias_desde_inicio: int = 10,
    dias_hasta_vencimiento: int = 20,
):
    hoy = hoy_bolivia()
    return SimpleNamespace(
        id_suscripcion=id_suscripcion,
        id_tenant=id_tenant,
        id_plan=id_plan,
        estado=estado,
        fecha_inicio=hoy - timedelta(days=dias_desde_inicio),
        fecha_vencimiento=hoy + timedelta(days=dias_hasta_vencimiento),
    )


def _catalogo_funcionalidades_falso():
    return [
        SimpleNamespace(codigo="productos", nombre="Catálogo de productos", descripcion="Prendas y variantes"),
        SimpleNamespace(codigo="ventas", nombre="Ventas y caja", descripcion="POS y checkout"),
        SimpleNamespace(codigo="reservas", nombre="Reservas", descripcion="Reservas omnicanal"),
        SimpleNamespace(codigo="reportes_ia", nombre="Reportes con IA", descripcion="Asistente analítico IA"),
    ]


# ======================================================================================
# AC-01, AC-02 y AC-03: P2-CU09 Consultar suscripción y uso del plan
# ======================================================================================


def test_ac01_cu09_consultar_mi_suscripcion_vigente():
    """AC-01: Devuelve suscripción vigente, días restantes, uso de sucursales/empleados, funcionalidades e historial."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=3, max_emp=15)
    susc = _suscripcion_falsa(dias_hasta_vencimiento=18)

    ahora = datetime.now(timezone.utc)
    hist_item = SimpleNamespace(
        id_historial=1,
        id_suscripcion=100,
        evento="alta",
        detalle={"plan": "Profesional"},
        id_usuario=10,
        creado_en=ahora,
    )

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan)),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_sucursales_activas",
            return_value=[
                {"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. Principal 10"},
                {"id_sucursal": 2, "nombre": "Boutique Sur", "direccion": "Calle 21"},
            ],
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=6),
        patch.object(
            MiSuscripcionRepositorio,
            "funcionalidades_por_plan",
            return_value=["productos", "ventas", "reservas"],
        ),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_catalogo_funcionalidades",
            return_value=_catalogo_funcionalidades_falso(),
        ),
        patch.object(
            MiSuscripcionRepositorio,
            "planes_activos_con_funcionalidad",
            return_value=["Empresarial"],
        ),
        patch.object(MiSuscripcionRepositorio, "listar_historial", return_value=[hist_item]),
    ):
        res = MiSuscripcionServicio.consultar_mi_suscripcion(db, usuario)

    assert res.empresa.codigo == "atelier-central"
    assert res.suscripcion.nombre_plan == "Profesional"
    assert res.suscripcion.vigente is True
    assert res.suscripcion.estado_efectivo == "activa"
    assert res.suscripcion.dias_restantes == 18
    assert res.suscripcion.proxima_a_vencer is False
    assert res.uso.sucursales.usados == 2
    assert res.uso.sucursales.limite == 3
    assert res.uso.sucursales.al_limite is False
    assert res.uso.empleados.usados == 6
    assert len(res.funcionalidades_incluidas) == 3
    assert len(res.funcionalidades_no_incluidas) == 1
    assert res.funcionalidades_no_incluidas[0].codigo == "reportes_ia"
    assert res.funcionalidades_no_incluidas[0].planes_que_la_incluyen == ["Empresarial"]
    assert len(res.historial) == 1


def test_ac02_cu09_a1_suscripcion_vencida_permite_consulta_y_reporta_estado():
    """AC-02 (CU09 A1 / CU10 A4): Una suscripción con fecha pasada no lanza 403 y reporta estado_efectivo='vencida'."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan = _plan_falso(id_plan=1, nombre="Basico", precio="29.00", max_suc=1, max_emp=5)
    susc = _suscripcion_falsa(estado="activa", dias_desde_inicio=40, dias_hasta_vencimiento=-5)

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan)),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_sucursales_activas",
            return_value=[{"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. 1"}],
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=5),
        patch.object(
            MiSuscripcionRepositorio, "funcionalidades_por_plan", return_value=["productos", "ventas"]
        ),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_catalogo_funcionalidades",
            return_value=_catalogo_funcionalidades_falso(),
        ),
        patch.object(
            MiSuscripcionRepositorio, "planes_activos_con_funcionalidad", return_value=["Profesional"]
        ),
        patch.object(MiSuscripcionRepositorio, "listar_historial", return_value=[]),
    ):
        res = MiSuscripcionServicio.consultar_mi_suscripcion(db, usuario)

    assert res.suscripcion.vigente is False
    assert res.suscripcion.estado_efectivo == "vencida"
    assert res.suscripcion.dias_restantes == -5
    # AC-03 (CU09 A2): Tanto sucursales (1/1) como empleados (5/5) están al límite
    assert res.uso.sucursales.al_limite is True
    assert res.uso.empleados.al_limite is True


# ======================================================================================
# AC-04 y AC-05: P2-CU10 Planes disponibles y validación CU10 A1 (exceso de uso)
# ======================================================================================


def test_ac04_cu10_listar_planes_evalua_compatibilidad_con_uso_actual():
    """AC-04: Lista los planes activos e indica cuáles son incompatibles con las sucursales/empleados actuales."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_basico = _plan_falso(id_plan=1, nombre="Basico", precio="29.00", max_suc=1, max_emp=5)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=3, max_emp=15)
    plan_emp = _plan_falso(id_plan=3, nombre="Empresarial", precio="199.00", max_suc=10, max_emp=None)
    susc = _suscripcion_falsa(id_plan=2)

    sucursales_activas = [
        {"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. 1"},
        {"id_sucursal": 2, "nombre": "Boutique Norte", "direccion": "Av. 2"},
    ]

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
        patch.object(
            MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=sucursales_activas
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=6),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_planes_activos",
            return_value=[plan_basico, plan_pro, plan_emp],
        ),
        patch.object(
            MiSuscripcionRepositorio, "funcionalidades_por_plan", return_value=["productos", "ventas"]
        ),
    ):
        planes = MiSuscripcionServicio.listar_planes_disponibles(db, usuario)

    assert len(planes) == 3
    assert planes[1].precio_mensual == Decimal("79.00")
    assert planes[1].precio_mensual_bob == Decimal("79.00")
    # Plan Básico permite 1 sucursal y 5 empleados; la empresa tiene 2 sucursales y 6 empleados -> incompatible
    assert planes[0].nombre == "Basico"
    assert planes[0].compatible_con_uso_actual is False
    assert "Boutique Centro, Boutique Norte" in (planes[0].motivo_incompatibilidad or "")
    # Plan Profesional es el actual y compatible
    assert planes[1].nombre == "Profesional"
    assert planes[1].es_plan_actual is True
    assert planes[1].compatible_con_uso_actual is True
    # Plan Empresarial (sin límite de empleados) es compatible
    assert planes[2].nombre == "Empresarial"
    assert planes[2].compatible_con_uso_actual is True


def test_ac05_cu10_a1_iniciar_pago_bloquea_bajada_plan_si_uso_supera_limite():
    """AC-05 (CU10 A1): Si la empresa tiene 2 sucursales activas y elige un plan de 1, lanza 409 USO_SUPERA_LIMITE_PLAN."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_basico = _plan_falso(id_plan=1, nombre="Basico", precio="29.00", max_suc=1, max_emp=5)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=3, max_emp=15)
    susc = _suscripcion_falsa(id_plan=2)

    sucursales_activas = [
        {"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. 1"},
        {"id_sucursal": 2, "nombre": "Boutique Sur", "direccion": "Av. 2"},
    ]

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_basico),
        patch.object(
            MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=sucursales_activas
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=3),
    ):
        with pytest.raises(ConflictError) as exc_info:
            MiSuscripcionServicio.iniciar_pago(
                db,
                IniciarPagoSuscripcionIn(id_plan=1, meses=1),
                usuario,
            )

    assert exc_info.value.code == "USO_SUPERA_LIMITE_PLAN"
    assert "Boutique Centro, Boutique Sur" in exc_info.value.message


# ======================================================================================
# AC-06 y AC-07: P2-CU10 Pago con Stripe (CU10 A2 rechazado y flujo exitoso + RN17)
# ======================================================================================


def test_ac06_cu10_a2_pago_stripe_rechazado_mantiene_suscripcion_intacta():
    """AC-06 (CU10 A2): Cuando Stripe rechaza el cobro, lanza 402 PAGO_RECHAZADO y no modifica la suscripción."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=3, max_emp=15)
    plan_emp = _plan_falso(id_plan=3, nombre="Empresarial", precio="199.00", max_suc=10, max_emp=None)
    susc = _suscripcion_falsa(id_plan=2, dias_hasta_vencimiento=5)
    vencimiento_original = susc.fecha_vencimiento

    pasarela_simulada = StripeService(api_key="sk_test_placeholder", latencia_simulada_ms=0)

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_emp),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_sucursales_activas",
            return_value=[{"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. 1"}],
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=4),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
        patch.object(
            MiSuscripcionRepositorio, "actualizar_suscripcion_y_registrar_historial"
        ) as mock_actualizar,
    ):
        with pytest.raises(PaymentRequiredError) as exc_info:
            MiSuscripcionServicio.confirmar_cambio_o_renovacion(
                db,
                ConfirmarCambioSuscripcionIn(
                    id_plan=3,
                    meses=1,
                    referencia_pago="pi_sbx_1234567890",
                    escenario_prueba="rechazado",
                ),
                usuario,
                pasarela=pasarela_simulada,
            )

    assert exc_info.value.code == "PAGO_RECHAZADO"
    mock_actualizar.assert_not_called()
    assert susc.id_plan == 2
    assert susc.fecha_vencimiento == vencimiento_original


def test_ac07_cu10_iniciar_y_confirmar_cambio_plan_con_stripe_registra_historial_y_bitacora():
    """AC-07: Flujo completo de iniciar pago y confirmar con Stripe actualiza suscripción, historial (RN17) y bitácora."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=3, max_emp=15)
    plan_emp = _plan_falso(id_plan=3, nombre="Empresarial", precio="199.00", max_suc=10, max_emp=None)
    susc = _suscripcion_falsa(id_plan=2, estado="vencida", dias_desde_inicio=40, dias_hasta_vencimiento=-2)

    pasarela_simulada = StripeService(api_key="sk_test_placeholder", latencia_simulada_ms=0)

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_emp),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_sucursales_activas",
            return_value=[{"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. 1"}],
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=4),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
    ):
        intento = MiSuscripcionServicio.iniciar_pago(
            db,
            IniciarPagoSuscripcionIn(id_plan=3, meses=2),
            usuario,
            pasarela=pasarela_simulada,
        )

    assert intento.referencia.startswith("pi_sbx_")
    assert intento.monto == Decimal("398.00")
    assert intento.monto_bob == Decimal("398.00")
    assert intento.moneda == "BOB"
    assert intento.operacion == "cambio_plan"
    assert intento.requiere_cobro is True

    # Ahora confirmamos el cambio de plan con la referencia devuelta por Stripe
    resumen_mock = MagicMock()
    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_emp),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(
            MiSuscripcionRepositorio,
            "listar_sucursales_activas",
            return_value=[{"id_sucursal": 1, "nombre": "Boutique Centro", "direccion": "Av. 1"}],
        ),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=4),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
        patch.object(
            MiSuscripcionRepositorio, "actualizar_suscripcion_y_registrar_historial"
        ) as mock_actualizar,
        patch(
            "modules.plataforma.cu09_cu10_suscripcion_empresa.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro"
        ) as mock_bitacora,
        patch.object(MiSuscripcionServicio, "consultar_mi_suscripcion", return_value=resumen_mock),
    ):
        resultado = MiSuscripcionServicio.confirmar_cambio_o_renovacion(
            db,
            ConfirmarCambioSuscripcionIn(
                id_plan=3,
                meses=2,
                referencia_pago=intento.referencia,
                escenario_prueba="exito",
            ),
            usuario,
            direccion_ip="127.0.0.1",
            pasarela=pasarela_simulada,
        )

    assert resultado is resumen_mock
    mock_actualizar.assert_called_once()
    kwargs = mock_actualizar.call_args.kwargs
    assert kwargs["id_plan"] == 3
    assert kwargs["estado"] == "activa"
    assert kwargs["evento"] == "cambio_plan"
    assert kwargs["detalle"]["referencia_pago"] == intento.referencia
    assert kwargs["detalle"]["monto_cobrado"] == "398.00"
    assert kwargs["detalle"]["moneda"] == "BOB"
    mock_bitacora.assert_called_once()


def test_ac07_cu10_renovacion_mismo_plan_vigente_extiende_fecha_vencimiento():
    """AC-07: Si la empresa renueva su mismo plan vigente por 1 mes, suma 30 días a la fecha de vencimiento actual."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=3, max_emp=15)
    susc = _suscripcion_falsa(id_plan=2, estado="activa", dias_desde_inicio=10, dias_hasta_vencimiento=15)
    venc_previo = susc.fecha_vencimiento

    pasarela_simulada = StripeService(api_key="sk_test_placeholder", latencia_simulada_ms=0)
    resumen_mock = MagicMock()

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_pro),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=[]),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=2),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
        patch.object(
            MiSuscripcionRepositorio, "actualizar_suscripcion_y_registrar_historial"
        ) as mock_actualizar,
        patch(
            "modules.plataforma.cu09_cu10_suscripcion_empresa.servicio.ServicioBitacoraAuditoria.registrar_evento_seguro"
        ),
        patch.object(MiSuscripcionServicio, "consultar_mi_suscripcion", return_value=resumen_mock),
    ):
        intento = MiSuscripcionServicio.iniciar_pago(
            db,
            IniciarPagoSuscripcionIn(id_plan=2, meses=1),
            usuario,
            pasarela=pasarela_simulada,
        )
        MiSuscripcionServicio.confirmar_cambio_o_renovacion(
            db,
            ConfirmarCambioSuscripcionIn(
                id_plan=2,
                meses=1,
                referencia_pago=intento.referencia,
            ),
            usuario,
            pasarela=pasarela_simulada,
        )

    kwargs = mock_actualizar.call_args.kwargs
    assert kwargs["evento"] == "renovacion"
    assert kwargs["fecha_vencimiento"] == venc_previo + timedelta(days=30)


def test_cu10_bloquea_confirmar_plan_distinto_o_mas_meses_con_pago_inferior():
    """Bloqueante 1 Auditoría: Con un pago del plan Básico por 1 mes no se puede confirmar Profesional ni 12 meses."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_basico = _plan_falso(id_plan=1, nombre="Basico", precio="29.00", max_suc=2, max_emp=5)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=5, max_emp=15)
    susc = _suscripcion_falsa(id_plan=1, estado="activa")
    pasarela_simulada = StripeService(api_key="sk_test_placeholder", latencia_simulada_ms=0)

    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_basico)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_basico),
        patch.object(MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=[]),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=1),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
    ):
        intento_basico = MiSuscripcionServicio.iniciar_pago(
            db,
            IniciarPagoSuscripcionIn(id_plan=1, meses=1),
            usuario,
            pasarela=pasarela_simulada,
        )

    # 1. Intentar confirmar el Plan Profesional (id_plan=2) usando la referencia del Plan Básico (id_plan=1)
    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_basico)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_pro),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=[]),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=1),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
    ):
        with pytest.raises(ConflictError) as exc_plan:
            MiSuscripcionServicio.confirmar_cambio_o_renovacion(
                db,
                ConfirmarCambioSuscripcionIn(
                    id_plan=2,
                    meses=1,
                    referencia_pago=intento_basico.referencia,
                ),
                usuario,
                pasarela=pasarela_simulada,
            )
    assert exc_plan.value.code in ("PAGO_IMPORTE_NO_COINCIDE", "PAGO_PLAN_NO_COINCIDE")

    # 2. Intentar confirmar 12 meses usando el pago de 1 mes
    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_basico)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_basico),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=[]),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=1),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
    ):
        with pytest.raises(ConflictError) as exc_meses:
            MiSuscripcionServicio.confirmar_cambio_o_renovacion(
                db,
                ConfirmarCambioSuscripcionIn(
                    id_plan=1,
                    meses=12,
                    referencia_pago=intento_basico.referencia,
                ),
                usuario,
                pasarela=pasarela_simulada,
            )
    assert exc_meses.value.code in ("PAGO_IMPORTE_NO_COINCIDE", "PAGO_MESES_NO_COINCIDEN")


def test_cu10_bloquea_pago_de_otra_empresa_moneda_distinta_y_reutilizacion():
    """Bloqueante 1 Auditoría: Rechaza pago de otro tenant, moneda discordante y referencia reutilizada."""
    db = MagicMock()
    usuario = _admin_falso(id_tenant=1)
    tenant = _tenant_falso(1)
    plan_pro = _plan_falso(id_plan=2, nombre="Profesional", precio="79.00", max_suc=5, max_emp=15)
    susc = _suscripcion_falsa(id_plan=2, estado="activa")

    # 1. Referencia ya registrada en historial_suscripcion
    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_pro),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=True),
    ):
        with pytest.raises(ConflictError) as exc_reuso:
            MiSuscripcionServicio.confirmar_cambio_o_renovacion(
                db,
                ConfirmarCambioSuscripcionIn(id_plan=2, meses=1, referencia_pago="pi_usado_1"),
                usuario,
            )
    assert exc_reuso.value.code == "REFERENCIA_PAGO_YA_UTILIZADA"

    # 2. Moneda distinta en el PaymentIntent (USD cuando la empresa opera en BOB)
    pasarela_moneda_distinta = MagicMock()
    pasarela_moneda_distinta.verificar_intento.return_value = ResultadoPasarela(
        aprobado=True,
        referencia="pi_moneda_usd",
        codigo_respuesta="succeeded",
        mensaje="OK",
        payload={
            "id": "pi_moneda_usd",
            "amount": 7900,
            "currency": "usd",
            "metadata": {"id_tenant": "1", "id_plan": "2", "meses": "1"},
        },
    )
    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_pro),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=[]),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=1),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
    ):
        with pytest.raises(ConflictError) as exc_moneda:
            MiSuscripcionServicio.confirmar_cambio_o_renovacion(
                db,
                ConfirmarCambioSuscripcionIn(id_plan=2, meses=1, referencia_pago="pi_moneda_usd"),
                usuario,
                pasarela=pasarela_moneda_distinta,
            )
    assert exc_moneda.value.code == "PAGO_MONEDA_NO_COINCIDE"

    # 3. PaymentIntent perteneciente a otra empresa (id_tenant=99)
    pasarela_otro_tenant = MagicMock()
    pasarela_otro_tenant.verificar_intento.return_value = ResultadoPasarela(
        aprobado=True,
        referencia="pi_otro_tenant",
        codigo_respuesta="succeeded",
        mensaje="OK",
        payload={
            "id": "pi_otro_tenant",
            "amount": 7900,
            "currency": "bob",
            "metadata": {"id_tenant": "99", "id_plan": "2", "meses": "1"},
        },
    )
    with (
        patch.object(MiSuscripcionRepositorio, "obtener_tenant", return_value=tenant),
        patch.object(MiSuscripcionRepositorio, "suscripcion_actual", return_value=(susc, plan_pro)),
        patch.object(MiSuscripcionRepositorio, "obtener_plan", return_value=plan_pro),
        patch.object(MiSuscripcionRepositorio, "referencia_pago_ya_utilizada", return_value=False),
        patch.object(MiSuscripcionRepositorio, "listar_sucursales_activas", return_value=[]),
        patch.object(MiSuscripcionRepositorio, "contar_empleados_activos", return_value=1),
        patch.object(MiSuscripcionRepositorio, "obtener_moneda_empresa", return_value="BOB"),
    ):
        with pytest.raises(ConflictError) as exc_tenant:
            MiSuscripcionServicio.confirmar_cambio_o_renovacion(
                db,
                ConfirmarCambioSuscripcionIn(id_plan=2, meses=1, referencia_pago="pi_otro_tenant"),
                usuario,
                pasarela=pasarela_otro_tenant,
            )
    assert exc_tenant.value.code == "PAGO_EMPRESA_NO_COINCIDE"


def test_contrato_http_rutas_mi_suscripcion_registradas():
    """Verifica que los 4 endpoints de /api/v1/plataforma/mi-suscripcion están registrados en FastAPI."""
    rutas = set(app.openapi()["paths"].keys())
    assert "/api/v1/plataforma/mi-suscripcion" in rutas
    assert "/api/v1/plataforma/mi-suscripcion/planes" in rutas
    assert "/api/v1/plataforma/mi-suscripcion/iniciar-pago" in rutas
    assert "/api/v1/plataforma/mi-suscripcion/confirmar" in rutas

