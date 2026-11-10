"""Pruebas unitarias de Fase 3: P2-CU22 (Catálogo de reportes permitidos) y P2-CU21 (Generar reporte con IA en Bs./BOB)."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from core.errors import (
    AuthorizationError,
    UnprocessableEntityError,
)
from modules.comercial.cu21_reportes_ia.esquemas import GenerarReporteIaIn
from modules.comercial.cu21_reportes_ia.interprete_ia import InterpreteReportesIA
from modules.comercial.cu21_reportes_ia.servicio import ReportesIaServicio
from modules.plataforma.cu22_catalogo_reportes.esquemas import (
    CatalogoReporteGuardarIn,
    DimensionReporteInOut,
    MetricaReporteInOut,
)
from modules.plataforma.cu22_catalogo_reportes.servicio import CatalogoReportesServicio


def _usuario_superadmin() -> SimpleNamespace:
    return SimpleNamespace(
        id_usuario=1,
        email="superadmin@fashionstore.com",
        id_tenant=None,
    )


def _usuario_admin_empresa(id_tenant: int = 10) -> SimpleNamespace:
    return SimpleNamespace(
        id_usuario=25,
        email="admin@atelierlapaz.bo",
        id_tenant=id_tenant,
    )


def _catalogo_semilla_mock() -> list[SimpleNamespace]:
    ahora = datetime.now(timezone.utc)
    return [
        SimpleNamespace(
            id_reporte_catalogo=1,
            codigo="ventas_por_sucursal",
            nombre="Ventas e ingresos por sucursal",
            descripcion="Consolidado de ventas en Bolivianos (Bs. / BOB).",
            vista_origen="vw_ventas_por_sucursal",
            metricas=[
                {
                    "codigo": "ingresos_totales_bob",
                    "etiqueta": "Ingresos totales (Bs. BOB)",
                    "expresion": "SUM(total_orden)",
                    "es_monetaria": True,
                }
            ],
            dimensiones=[
                {
                    "codigo": "sucursal",
                    "etiqueta": "Sucursal",
                    "expresion": "sucursal.nombre",
                }
            ],
            filtros_permitidos=["fecha_inicio", "fecha_fin", "id_sucursal", "moneda"],
            tipos_grafico=["barras", "linea", "torta"],
            ejemplos_consulta=[
                "Ventas del último mes por sucursal en bolivianos",
                "Ingresos por tienda en Bs",
            ],
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        ),
        SimpleNamespace(
            id_reporte_catalogo=2,
            codigo="top_productos_vendidos",
            nombre="Prendas más vendidas y facturación en Bs.",
            descripcion="Ranking de prendas por unidades e ingresos en Bolivianos.",
            vista_origen="ranking_productos",
            metricas=[
                {
                    "codigo": "unidades_vendidas",
                    "etiqueta": "Unidades vendidas",
                    "expresion": "SUM(cantidad)",
                    "es_monetaria": False,
                },
                {
                    "codigo": "ingresos_producto_bob",
                    "etiqueta": "Ingresos generados (Bs. BOB)",
                    "expresion": "SUM(subtotal)",
                    "es_monetaria": True,
                },
            ],
            dimensiones=[
                {
                    "codigo": "producto",
                    "etiqueta": "Prenda",
                    "expresion": "producto.nombre",
                }
            ],
            filtros_permitidos=["fecha_inicio", "fecha_fin", "id_sucursal", "id_categoria", "moneda"],
            tipos_grafico=["barras", "torta"],
            ejemplos_consulta=["Top 5 prendas más vendidas con ingresos en Bs."],
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        ),
        SimpleNamespace(
            id_reporte_catalogo=3,
            codigo="inventario_por_sucursal",
            nombre="Disponibilidad y valorización de inventario por sucursal",
            descripcion="Stock disponible, reservado y valorizado en Bolivianos.",
            vista_origen="vw_inventario_consolidado",
            metricas=[
                {
                    "codigo": "valor_inventario_bob",
                    "etiqueta": "Valor inventario (Bs. BOB)",
                    "expresion": "SUM(stock_disponible * precio_base)",
                    "es_monetaria": True,
                }
            ],
            dimensiones=[
                {
                    "codigo": "sucursal",
                    "etiqueta": "Sucursal",
                    "expresion": "sucursal.nombre",
                }
            ],
            filtros_permitidos=["id_sucursal", "id_categoria", "moneda"],
            tipos_grafico=["barras", "torta"],
            ejemplos_consulta=["Stock e inventario valorizado en Bs por sucursal"],
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        ),
        SimpleNamespace(
            id_reporte_catalogo=4,
            codigo="reservas_por_estado_sucursal",
            nombre="Reservas omnicanal por estado y sucursal",
            descripcion="Distribución de reservas activas, expiradas y completadas.",
            vista_origen="vw_reservas_pendientes",
            metricas=[
                {
                    "codigo": "total_reservas",
                    "etiqueta": "Cantidad de reservas",
                    "expresion": "COUNT(id_reserva)",
                    "es_monetaria": False,
                }
            ],
            dimensiones=[
                {
                    "codigo": "estado",
                    "etiqueta": "Estado",
                    "expresion": "reserva.estado",
                }
            ],
            filtros_permitidos=["fecha_inicio", "fecha_fin", "id_sucursal", "estado"],
            tipos_grafico=["barras", "torta", "linea"],
            ejemplos_consulta=["Reservas por estado y sucursal de esta semana"],
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        ),
    ]


# ==============================================================================
# AC-01, AC-02 y AC-03: P2-CU22 Gestionar catálogo de reportes permitidos
# ==============================================================================


class TestP2CU22CatalogoReportesPermitidos:
    """Pruebas unitarias de P2-CU22 (Superadministrador)."""

    @patch("modules.plataforma.cu22_catalogo_reportes.servicio.CatalogoReportesRepositorio")
    def test_ac01_listar_catalogo_con_metadatos_permitidos(self, mock_repo: MagicMock) -> None:
        mock_repo.listar.return_value = _catalogo_semilla_mock()
        db = MagicMock()

        res = CatalogoReportesServicio.listar_catalogo(db, solo_activos=False)

        assert len(res.reportes) == 4
        assert "vw_ventas_por_sucursal" in res.vistas_permitidas
        assert "barras" in res.tipos_grafico_permitidos
        assert "moneda" in res.filtros_permitidos

    @patch("modules.plataforma.cu22_catalogo_reportes.servicio.ServicioBitacoraAuditoria")
    @patch("modules.plataforma.cu22_catalogo_reportes.servicio.CatalogoReportesRepositorio")
    def test_ac01_crear_y_actualizar_reporte_catalogo_valido(
        self, mock_repo: MagicMock, mock_bitacora: MagicMock
    ) -> None:
        ahora = datetime.now(timezone.utc)
        mock_repo.obtener_por_codigo.return_value = None
        mock_repo.crear.side_effect = lambda _db, payload: SimpleNamespace(
            id_reporte_catalogo=5,
            creado_en=ahora,
            actualizado_en=ahora,
            **payload,
        )
        db = MagicMock()
        datos = CatalogoReporteGuardarIn(
            codigo="ventas_mensuales_bob",
            nombre="Ventas mensuales en Bolivianos",
            descripcion="Reporte financiero mensual en Bs.",
            vista_origen="vw_ventas_por_sucursal",
            metricas=[
                MetricaReporteInOut(
                    codigo="total_bob",
                    etiqueta="Total en Bs.",
                    expresion="SUM(total_orden)",
                    es_monetaria=True,
                )
            ],
            dimensiones=[
                DimensionReporteInOut(
                    codigo="sucursal",
                    etiqueta="Sucursal",
                    expresion="sucursal.nombre",
                )
            ],
            filtros_permitidos=["fecha_inicio", "fecha_fin", "moneda"],
            tipos_grafico=["barras", "linea"],
            ejemplos_consulta=["Ventas mensuales en Bs"],
            activo=True,
        )

        creado = CatalogoReportesServicio.crear_reporte(
            db, datos, _usuario_superadmin(), direccion_ip="127.0.0.1"
        )

        assert creado.id_reporte_catalogo == 5
        assert creado.codigo == "ventas_mensuales_bob"
        assert creado.vista_origen == "vw_ventas_por_sucursal"
        mock_bitacora.registrar_evento_seguro.assert_called_once()

    def test_ac02_cu22_a1_rechaza_vista_origen_no_permitida(self) -> None:
        db = MagicMock()
        datos = CatalogoReporteGuardarIn(
            codigo="reporte_ilegal",
            nombre="Acceso directo a usuarios",
            descripcion="Intenta consultar tabla privada",
            vista_origen="autenticacion.usuarios_passwords",
            metricas=[
                MetricaReporteInOut(
                    codigo="conteo",
                    etiqueta="Usuarios",
                    expresion="COUNT(*)",
                    es_monetaria=False,
                )
            ],
            dimensiones=[
                DimensionReporteInOut(
                    codigo="rol",
                    etiqueta="Rol",
                    expresion="rol.nombre",
                )
            ],
            filtros_permitidos=["fecha_inicio"],
            tipos_grafico=["barras"],
            ejemplos_consulta=[],
            activo=True,
        )

        with pytest.raises(UnprocessableEntityError) as exc:
            CatalogoReportesServicio.crear_reporte(db, datos, _usuario_superadmin())
        assert exc.value.code == "VISTA_DATOS_NO_PERMITIDA"

    def test_ac02_cu22_a2_rechaza_metrica_sin_expresion_o_grafico_invalido(self) -> None:
        db = MagicMock()
        datos_sin_expresion = CatalogoReporteGuardarIn(
            codigo="reporte_incompleto",
            nombre="Reporte sin expresión",
            vista_origen="vw_ventas_por_sucursal",
            metricas=[
                MetricaReporteInOut(
                    codigo="total_bob",
                    etiqueta="Total Bs.",
                    expresion="   ",
                    es_monetaria=True,
                )
            ],
            dimensiones=[
                DimensionReporteInOut(
                    codigo="sucursal",
                    etiqueta="Sucursal",
                    expresion="sucursal.nombre",
                )
            ],
            filtros_permitidos=["fecha_inicio"],
            tipos_grafico=["barras"],
        )

        with pytest.raises(UnprocessableEntityError) as exc1:
            CatalogoReportesServicio.crear_reporte(db, datos_sin_expresion, _usuario_superadmin())
        assert exc1.value.code == "ELEMENTO_REPORTE_INVALIDO"

        datos_grafico_invalido = CatalogoReporteGuardarIn(
            codigo="reporte_grafico_raro",
            nombre="Reporte con holograma 3D",
            vista_origen="vw_ventas_por_sucursal",
            metricas=[
                MetricaReporteInOut(
                    codigo="total_bob",
                    etiqueta="Total Bs.",
                    expresion="SUM(total_orden)",
                    es_monetaria=True,
                )
            ],
            dimensiones=[
                DimensionReporteInOut(
                    codigo="sucursal",
                    etiqueta="Sucursal",
                    expresion="sucursal.nombre",
                )
            ],
            filtros_permitidos=["fecha_inicio"],
            tipos_grafico=["holograma_3d"],
        )

        with pytest.raises(UnprocessableEntityError) as exc2:
            CatalogoReportesServicio.crear_reporte(
                db, datos_grafico_invalido, _usuario_superadmin()
            )
        assert exc2.value.code == "ELEMENTO_REPORTE_INVALIDO"

    @patch("modules.plataforma.cu22_catalogo_reportes.servicio.ServicioBitacoraAuditoria")
    @patch("modules.plataforma.cu22_catalogo_reportes.servicio.CatalogoReportesRepositorio")
    def test_ac03_cu22_a3_desactivar_reporte_conserva_historial_y_oculta_para_cu21(
        self, mock_repo: MagicMock, mock_bitacora: MagicMock
    ) -> None:
        item = _catalogo_semilla_mock()[0]
        mock_repo.obtener_por_id.return_value = item

        def _toggle(_db: MagicMock, obj: SimpleNamespace, activo: bool) -> SimpleNamespace:
            obj.activo = activo
            return obj

        mock_repo.cambiar_estado.side_effect = _toggle
        db = MagicMock()

        actualizado = CatalogoReportesServicio.cambiar_estado_reporte(
            db,
            1,
            False,
            _usuario_superadmin(),
        )
        assert actualizado.activo is False
        mock_bitacora.registrar_evento_seguro.assert_called_once()


# ==============================================================================
# AC-04, AC-05, AC-06 y AC-07: P2-CU21 Generar reporte con IA (en Bs. / BOB)
# ==============================================================================


class TestP2CU21GenerarReporteConIA:
    """Pruebas unitarias de P2-CU21 (Administrador de empresa con Plan Profesional)."""

    @patch("modules.comercial.cu21_reportes_ia.servicio.SuscripcionServicio.validar")
    def test_ac04_cu21_a3_rn44_bloquea_plan_basico_o_suscripcion_vencida(
        self, mock_validar_susc: MagicMock
    ) -> None:
        mock_validar_susc.side_effect = AuthorizationError(
            "Su plan actual no incluye la funcionalidad 'reportes_ia' (RN44).",
            code="FUNCIONALIDAD_NO_INCLUIDA",
        )
        db = MagicMock()

        with pytest.raises(AuthorizationError) as exc:
            ReportesIaServicio.generar_reporte(
                db,
                GenerarReporteIaIn(prompt_texto="Ventas del último mes por sucursal"),
                _usuario_admin_empresa(10),
            )
        assert exc.value.code == "FUNCIONALIDAD_NO_INCLUIDA"

    @patch("modules.comercial.cu21_reportes_ia.servicio.ServicioBitacoraAuditoria")
    @patch("modules.comercial.cu21_reportes_ia.servicio.ReportesIaRepositorio")
    @patch("modules.comercial.cu21_reportes_ia.servicio.SuscripcionServicio.validar")
    def test_ac05_flujo_normal_4_reportes_con_conversion_bolivianos_bob(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
        mock_bitacora: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        mock_repo.obtener_moneda_empresa.return_value = "USD"  # Prueba conversión USD -> Bs. (x 6.96)
        mock_repo.listar_catalogo_activo.return_value = _catalogo_semilla_mock()
        mock_repo.listar_sucursales_empresa.return_value = [
            {"id_sucursal": 101, "nombre": "Sucursal La Paz Centro", "ciudad": "La Paz"},
            {"id_sucursal": 102, "nombre": "Sucursal Santa Cruz Equipetrol", "ciudad": "Santa Cruz"},
        ]
        mock_repo.listar_categorias_empresa.return_value = [
            {"id_categoria": 10, "nombre": "Abrigos de Alpaca"}
        ]
        mock_repo.registrar_solicitud.side_effect = lambda _db, **kwargs: SimpleNamespace(
            id_solicitud=77,
            exportaciones=[],
            creado_en=ahora,
            **kwargs,
        )

        # 1) Ventas por sucursal: 100.00 USD -> 696.00 Bs.
        mock_repo.ejecutar_ventas_por_sucursal.return_value = [
            {
                "sucursal": "Sucursal La Paz Centro",
                "cantidad_ventas": 5,
                "ingresos_totales": Decimal("100.00"),
                "ticket_promedio": Decimal("20.00"),
            }
        ]
        db = MagicMock()
        res_ventas = ReportesIaServicio.generar_reporte(
            db,
            GenerarReporteIaIn(
                prompt_texto="Ventas del último mes por sucursal en gráfico de barras",
                tipo_cambio_bob=Decimal("6.96"),
            ),
            _usuario_admin_empresa(10),
        )
        assert res_ventas.estado == "completada"
        assert res_ventas.codigo_reporte == "ventas_por_sucursal"
        assert res_ventas.moneda == "BOB"
        assert res_ventas.simbolo_moneda == "Bs."
        assert res_ventas.tipo_cambio_bob == Decimal("6.96")
        assert res_ventas.resumen_kpis_bob["ingresos_totales_bob"] == 696.0
        assert res_ventas.resumen_kpis_bob["equivalente_usd"] == 100.0
        assert res_ventas.filas[0][2] == 696.0  # 100 USD * 6.96 Bs.

        # 2) Top productos vendidos
        mock_repo.ejecutar_top_productos_vendidos.return_value = [
            {
                "producto": "Abrigo Imperial Alpaca",
                "categoria": "Abrigos de Alpaca",
                "unidades_vendidas": 10,
                "ingresos_producto": Decimal("50.00"),
            }
        ]
        res_top = ReportesIaServicio.generar_reporte(
            db,
            GenerarReporteIaIn(
                prompt_texto="Top prendas más vendidas con mayores ingresos",
                tipo_cambio_bob=Decimal("6.96"),
            ),
            _usuario_admin_empresa(10),
        )
        assert res_top.codigo_reporte == "top_productos_vendidos"
        assert res_top.resumen_kpis_bob["ingresos_totales_bob"] == 348.0  # 50 * 6.96

        # 3) Inventario por sucursal
        mock_repo.ejecutar_inventario_por_sucursal.return_value = [
            {
                "sucursal": "Sucursal La Paz Centro",
                "categoria": "Abrigos de Alpaca",
                "stock_disponible": 15,
                "stock_reservado": 3,
                "valor_inventario": Decimal("200.00"),
            }
        ]
        res_inv = ReportesIaServicio.generar_reporte(
            db,
            GenerarReporteIaIn(
                prompt_texto="Stock disponible y valor de inventario por sucursal",
                tipo_cambio_bob=Decimal("6.96"),
            ),
            _usuario_admin_empresa(10),
        )
        assert res_inv.codigo_reporte == "inventario_por_sucursal"
        assert res_inv.resumen_kpis_bob["valor_inventario_total_bob"] == 1392.0  # 200 * 6.96

        # 4) Reservas por estado y sucursal
        mock_repo.ejecutar_reservas_por_estado_sucursal.return_value = [
            {
                "sucursal": "Sucursal La Paz Centro",
                "estado": "ACTIVA",
                "total_reservas": 8,
                "prendas_reservadas": 12,
            }
        ]
        res_res = ReportesIaServicio.generar_reporte(
            db,
            GenerarReporteIaIn(
                prompt_texto="Reservas activas y expiradas por estado y sucursal",
                tipo_cambio_bob=Decimal("6.96"),
            ),
            _usuario_admin_empresa(10),
        )
        assert res_res.codigo_reporte == "reservas_por_estado_sucursal"
        assert res_res.resumen_kpis_bob["reservas_totales"] == 8

    @patch("modules.comercial.cu21_reportes_ia.servicio.ServicioBitacoraAuditoria")
    @patch("modules.comercial.cu21_reportes_ia.servicio.ReportesIaRepositorio")
    @patch("modules.comercial.cu21_reportes_ia.servicio.SuscripcionServicio.validar")
    def test_ac06_cursos_alternos_a1_ambigua_a2_no_soportada_y_a7_otro_tenant(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
        mock_bitacora: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        mock_repo.obtener_moneda_empresa.return_value = "BOB"
        mock_repo.listar_catalogo_activo.return_value = _catalogo_semilla_mock()
        mock_repo.listar_sucursales_empresa.return_value = [
            {"id_sucursal": 101, "nombre": "Sucursal Central", "ciudad": "La Paz"}
        ]
        mock_repo.listar_categorias_empresa.return_value = []
        mock_repo.registrar_solicitud.side_effect = lambda _db, **kwargs: SimpleNamespace(
            id_solicitud=88,
            exportaciones=[],
            creado_en=ahora,
            **kwargs,
        )
        db = MagicMock()

        # Curso Alterno A1: Solicitud ambigua ("reporte general")
        res_ambigua = ReportesIaServicio.generar_reporte(
            db,
            GenerarReporteIaIn(prompt_texto="dame un reporte general por favor"),
            _usuario_admin_empresa(10),
        )
        assert res_ambigua.estado == "ambigua"
        assert len(res_ambigua.ejemplos_sugeridos) > 0

        # Curso Alterno A2: Solicitud fuera del catálogo ("planilla de sueldos y clima")
        res_no_sop = ReportesIaServicio.generar_reporte(
            db,
            GenerarReporteIaIn(prompt_texto="planilla de salarios de empleados e impuestos"),
            _usuario_admin_empresa(10),
        )
        assert res_no_sop.estado == "no_soportada"

        # Curso Alterno A7: Intento de consultar datos de otra empresa por parámetro explícito
        with pytest.raises(AuthorizationError) as exc_tenant:
            ReportesIaServicio.generar_reporte(
                db,
                GenerarReporteIaIn(
                    prompt_texto="Ventas por sucursal",
                    id_tenant_solicitado=999,
                ),
                _usuario_admin_empresa(10),
            )
        assert exc_tenant.value.code == "FILTRO_REPORTE_NO_AUTORIZADO"

        # Curso Alterno A7: Intento por texto libre ("de otra empresa")
        res_a7_texto = InterpreteReportesIA.interpretar(
            prompt_texto="Muéstrame las ventas de otra empresa competidora",
            catalogo_activo=_catalogo_semilla_mock(),
            sucursales_empresa=[],
            categorias_empresa=[],
        )
        assert res_a7_texto.estado == "rechazada"

    @patch("modules.comercial.cu21_reportes_ia.servicio.ServicioBitacoraAuditoria")
    @patch("modules.comercial.cu21_reportes_ia.servicio.ReportesIaRepositorio")
    @patch("modules.comercial.cu21_reportes_ia.servicio.SuscripcionServicio.validar")
    def test_ac07_exportacion_pdf_y_excel_registra_en_solicitud_rn48(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
        mock_bitacora: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        solicitud_mock = SimpleNamespace(
            id_solicitud=55,
            id_tenant=10,
            id_usuario=25,
            comando_voz_texto="Ventas del último mes por sucursal en Bs",
            tipo_reporte="ventas_por_sucursal",
            estado="completada",
            interpretacion={
                "estado": "completada",
                "codigo_reporte": "ventas_por_sucursal",
                "nombre_reporte": "Ventas e ingresos por sucursal",
                "vista_origen": "vw_ventas_por_sucursal",
                "formato_visualizacion": "ambos",
                "tipo_grafico_sugerido": "barras",
                "explicacion_ia": "Reporte en Bolivianos (Bs.)",
            },
            mensaje_estado="OK",
            exportaciones=[],
            creado_en=ahora,
        )
        mock_repo.obtener_solicitud_empresa.return_value = solicitud_mock
        mock_repo.obtener_tenant.return_value = SimpleNamespace(
            id_tenant=10, nombre="Atelier La Paz"
        )
        mock_repo.obtener_moneda_empresa.return_value = "BOB"
        mock_repo.ejecutar_ventas_por_sucursal.return_value = [
            {
                "sucursal": "Sucursal Prado",
                "cantidad_ventas": 12,
                "ingresos_totales": Decimal("4500.00"),
                "ticket_promedio": Decimal("375.00"),
            }
        ]
        db = MagicMock()

        # Exportar PDF
        pdf_bytes, pdf_mime, pdf_name = ReportesIaServicio.exportar_solicitud(
            db,
            id_solicitud=55,
            formato="pdf",
            usuario=_usuario_admin_empresa(10),
        )
        assert pdf_bytes.startswith(b"%PDF")
        assert pdf_mime == "application/pdf"
        assert pdf_name.endswith(".pdf")

        # Exportar Excel (.xlsx)
        xlsx_bytes, xlsx_mime, xlsx_name = ReportesIaServicio.exportar_solicitud(
            db,
            id_solicitud=55,
            formato="excel",
            usuario=_usuario_admin_empresa(10),
        )
        assert xlsx_bytes.startswith(b"PK")
        assert "spreadsheetml" in xlsx_mime
        assert xlsx_name.endswith(".xlsx")
        assert mock_repo.registrar_exportacion_en_solicitud.call_count == 2

    @patch("modules.comercial.cu21_reportes_ia.servicio.ReportesIaRepositorio")
    @patch("modules.comercial.cu21_reportes_ia.servicio.SuscripcionServicio.validar")
    def test_ac08_cu21_reporte_desconocido_rechaza_sin_caer_en_reservas(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        """Auditoría Parcial 2 (Punto 6): un código de reporte no reconocido debe rechazarse explícitamente."""
        from modules.comercial.cu21_reportes_ia.esquemas import InterpretacionReporteIaOut

        ahora = datetime.now(timezone.utc)
        rep_nuevo = SimpleNamespace(
            id_reporte_catalogo=99,
            codigo="reporte_sin_ejecutor",
            nombre="Reporte no implementado",
            descripcion="Reporte de prueba sin handler SQL.",
            vista_origen="vw_desconocida",
            metricas=[],
            dimensiones=[],
            filtros_permitidos=[],
            tipos_grafico=["barras"],
            ejemplos_consulta=[],
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        mock_repo.listar_catalogo_activo.return_value = [rep_nuevo]
        mock_repo.obtener_moneda_empresa.return_value = "BOB"

        interpretacion_mock = InterpretacionReporteIaOut(
            estado="completada",
            codigo_reporte="reporte_sin_ejecutor",
            nombre_reporte="Reporte no implementado",
            vista_origen="vw_desconocida",
            tipo_grafico_sugerido="barras",
            explicacion_ia="Reporte configurado en catálogo",
            origen_motor="validador_catalogo_cu22",
        )

        with patch.object(
            InterpreteReportesIA, "interpretar", return_value=interpretacion_mock
        ):
            with pytest.raises(UnprocessableEntityError) as exc:
                ReportesIaServicio.generar_reporte(
                    MagicMock(),
                    datos=GenerarReporteIaIn(
                        prompt_texto="dame el reporte sin ejecutor",
                        codigo_reporte="reporte_sin_ejecutor",
                    ),
                    usuario=_usuario_admin_empresa(10),
                )
            assert exc.value.code == "REPORTE_NO_EJECUTABLE"
            assert "reporte_sin_ejecutor" in str(exc.value)
            # Asegurar que NO se llamó a ejecutar_reservas_por_estado_sucursal
            mock_repo.ejecutar_reservas_por_estado_sucursal.assert_not_called()

