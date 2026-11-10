"""Pruebas unitarias de Fase 4: P2-CU23 (Datos y modelos ML), P2-CU24 (Predicciones) y P2-CU25 (Segmentos de clientes) en Bolivianos (Bs. / BOB)."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from core.errors import AuthorizationError, UnprocessableEntityError
from modules.comercial.cu23_cu25_aprendizaje_ml.esquemas import (
    CrearDatasetMlIn,
    EntrenarModeloMlIn,
)
from modules.comercial.cu23_cu25_aprendizaje_ml.servicio import AprendizajeMlServicio


def _usuario_admin(id_tenant: int = 10) -> SimpleNamespace:
    return SimpleNamespace(
        id_usuario=25,
        email="admin@atelierlapaz.bo",
        id_tenant=id_tenant,
    )


class TestP2CU23CU25AprendizajeAutomaticoML:
    """Pruebas unitarias para P2-CU23, P2-CU24 y P2-CU25."""

    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.ServicioBitacoraAuditoria")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.AprendizajeMlRepositorio")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.SuscripcionServicio.validar")
    def test_ac01_cu23_crear_dataset_sintetico_y_rechazar_real_insuficiente_a1(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
        mock_bitacora: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        mock_repo.obtener_moneda_empresa.return_value = "USD"
        mock_repo.contar_ventas_reales_empresa.return_value = 2
        mock_repo.listar_clientes_con_actividad_empresa.return_value = []
        mock_repo.listar_productos_empresa.return_value = [
            {"id_producto": 1, "nombre": "Vestido Gala", "precio_base": Decimal("100.00")}
        ]
        mock_repo.listar_sucursales_empresa.return_value = [
            {"id_sucursal": 10, "nombre": "Sucursal La Paz"}
        ]
        mock_repo.crear_dataset.side_effect = lambda _db, payload: SimpleNamespace(
            id_dataset=1,
            creado_en=ahora,
            **payload,
        )
        db = MagicMock()

        # Curso Alterno CU23 A1: Datos reales insuficientes (< 5 registros)
        with pytest.raises(UnprocessableEntityError) as exc_a1:
            AprendizajeMlServicio.crear_dataset(
                db,
                CrearDatasetMlIn(nombre="Dataset Real", origen="real"),
                _usuario_admin(10),
            )
        assert exc_a1.value.code == "DATOS_INSUFICIENTES_ML"

        # Flujo normal CU23: Dataset sintético con preprocesamiento y conversión a Bolivianos (100 USD * 6.96 = 696.00 Bs.)
        ds_sintetico = AprendizajeMlServicio.crear_dataset(
            db,
            CrearDatasetMlIn(
                nombre="Dataset Sintético Q4",
                origen="sintetico",
                cantidad_registros_sinteticos=60,
                horizonte_meses=6,
                tipo_cambio_bob=Decimal("6.96"),
            ),
            _usuario_admin(10),
        )
        assert ds_sintetico.id_dataset == 1
        assert ds_sintetico.origen == "sintetico"
        assert ds_sintetico.cantidad_registros == 60
        assert "limpieza_nulos" in ds_sintetico.resumen_preprocesamiento
        assert ds_sintetico.muestra_datos[0]["precio_bob"] == 696.0
        assert ds_sintetico.muestra_datos[0]["moneda"] == "BOB"
        mock_bitacora.registrar_evento_seguro.assert_called_once()

    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.ServicioBitacoraAuditoria")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.AprendizajeMlRepositorio")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.SuscripcionServicio.validar")
    def test_ac02_cu23_modelo_supervisado_exige_variable_objetivo_a2_y_guarda_metricas_rn49(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
        mock_bitacora: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        db = MagicMock()

        # Curso Alterno CU23 A2 / RN49: Modelo supervisado sin variable objetivo
        with pytest.raises(UnprocessableEntityError) as exc_a2:
            AprendizajeMlServicio.entrenar_modelo(
                db,
                EntrenarModeloMlIn(
                    id_dataset=1,
                    nombre="Modelo sin objetivo",
                    tipo_modelo="supervisado",
                    variable_objetivo="   ",
                ),
                _usuario_admin(10),
            )
        assert exc_a2.value.code == "VARIABLE_OBJETIVO_REQUERIDA"

        mock_repo.obtener_dataset.return_value = SimpleNamespace(
            id_dataset=1,
            id_tenant=10,
            origen="sintetico",
            variables_seleccionadas=["precio_bob", "frecuencia_compra"],
        )
        mock_repo.obtener_moneda_empresa.return_value = "BOB"
        mock_repo.listar_productos_empresa.return_value = [
            {"id_producto": 1, "nombre": "Abrigo Alpaca", "precio_base": Decimal("850.00")}
        ]
        mock_repo.listar_sucursales_empresa.return_value = [
            {"id_sucursal": 10, "nombre": "Sucursal Prado"}
        ]
        mock_repo.crear_modelo_con_resultados.side_effect = (
            lambda _db, *, datos_modelo, predicciones, segmentos, activar_inmediatamente: SimpleNamespace(
                id_modelo=10,
                creado_en=ahora,
                actualizado_en=ahora,
                _predicciones=predicciones,
                **datos_modelo,
            )
        )

        modelo_sup = AprendizajeMlServicio.entrenar_modelo(
            db,
            EntrenarModeloMlIn(
                id_dataset=1,
                nombre="Proyección Demanda Invierno",
                tipo_modelo="supervisado",
                variable_objetivo="demanda_unidades",
                activar_inmediatamente=True,
            ),
            _usuario_admin(10),
        )
        assert modelo_sup.id_modelo == 10
        assert modelo_sup.tipo_modelo == "supervisado"
        assert modelo_sup.variable_objetivo == "demanda_unidades"
        assert "r2" in modelo_sup.metricas_entrenamiento
        assert "r2" in modelo_sup.metricas_validacion
        assert "r2" in modelo_sup.metricas_prueba

        # Curso Alterno CU23 A3: Fallo de entrenamiento
        modelo_fallido = AprendizajeMlServicio.entrenar_modelo(
            db,
            EntrenarModeloMlIn(
                id_dataset=1,
                nombre="Modelo Fallido",
                tipo_modelo="supervisado",
                variable_objetivo="demanda_unidades",
                forzar_fallo_entrenamiento=True,
            ),
            _usuario_admin(10),
        )
        assert modelo_fallido.estado == "fallido"
        assert modelo_fallido.activo is False

    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.ServicioBitacoraAuditoria")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.AprendizajeMlRepositorio")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.SuscripcionServicio.validar")
    def test_ac03_y_ac04_entrenar_no_supervisado_activar_y_archivar_a5(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
        mock_bitacora: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        mock_repo.obtener_dataset.return_value = SimpleNamespace(
            id_dataset=2,
            id_tenant=10,
            origen="mixto",
            variables_seleccionadas=["frecuencia_compra", "monto_acumulado_bob"],
        )
        mock_repo.obtener_moneda_empresa.return_value = "BOB"
        mock_repo.listar_clientes_con_actividad_empresa.return_value = []
        mock_repo.crear_modelo_con_resultados.side_effect = (
            lambda _db, *, datos_modelo, predicciones, segmentos, activar_inmediatamente: SimpleNamespace(
                id_modelo=20,
                creado_en=ahora,
                actualizado_en=ahora,
                **datos_modelo,
            )
        )
        db = MagicMock()

        modelo_unsup = AprendizajeMlServicio.entrenar_modelo(
            db,
            EntrenarModeloMlIn(
                id_dataset=2,
                nombre="Clustering RFM Clientas",
                tipo_modelo="no_supervisado",
                numero_clusters=3,
            ),
            _usuario_admin(10),
        )
        assert modelo_unsup.tipo_modelo == "no_supervisado"
        assert "silhouette_score" in modelo_unsup.metricas_entrenamiento

        # Activar y luego Archivar (CU23 A5)
        modelo_obj = SimpleNamespace(
            id_modelo=20,
            id_tenant=10,
            id_dataset=2,
            nombre="Clustering RFM Clientas",
            tipo_modelo="no_supervisado",
            algoritmo="K-Means RFM",
            variable_objetivo=None,
            variables_entrada=["frecuencia_compra"],
            origen_datos="mixto",
            estado="evaluado",
            activo=False,
            motivo_error=None,
            metricas_entrenamiento={"silhouette_score": 0.71},
            metricas_validacion={"silhouette_score": 0.69},
            metricas_prueba={"silhouette_score": 0.68},
            creado_en=ahora,
            actualizado_en=ahora,
        )
        mock_repo.obtener_modelo.return_value = modelo_obj

        def _archivar(_db: MagicMock, m: SimpleNamespace) -> SimpleNamespace:
            m.activo = False
            m.estado = "archivado"
            return m

        mock_repo.archivar_modelo.side_effect = _archivar

        archivado = AprendizajeMlServicio.archivar_modelo(db, 20, _usuario_admin(10))
        assert archivado.estado == "archivado"
        assert archivado.activo is False
        assert archivado.metricas_entrenamiento["silhouette_score"] == 0.71  # Conserva métricas (CU23 A5)

    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.AprendizajeMlRepositorio")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.SuscripcionServicio.validar")
    def test_ac05_y_ac06_cu24_consultar_predicciones_rn50_bolivianos_y_a1_a3(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        db = MagicMock()

        # Curso Alterno CU24 A1: Sin modelo supervisado activo
        mock_repo.obtener_modelo_activo_por_tipo.return_value = None
        sin_modelo = AprendizajeMlServicio.consultar_predicciones(db, _usuario_admin(10))
        assert sin_modelo.tiene_modelo_activo is False

        # Con modelo supervisado activo entrenado con datos sintéticos (CU24 A3)
        mock_repo.obtener_modelo_activo_por_tipo.return_value = SimpleNamespace(
            id_modelo=10,
            id_tenant=10,
            id_dataset=1,
            nombre="Proyección Demanda Bs.",
            tipo_modelo="supervisado",
            algoritmo="RandomForest",
            variable_objetivo="demanda_unidades",
            variables_entrada=["precio_bob"],
            origen_datos="sintetico",
            estado="activo",
            activo=True,
            motivo_error=None,
            metricas_entrenamiento={"r2": 0.91},
            metricas_validacion={"r2": 0.89},
            metricas_prueba={"r2": 0.88},
            creado_en=ahora,
            actualizado_en=ahora,
        )
        mock_repo.listar_predicciones_modelo.return_value = [
            SimpleNamespace(
                id_prediccion=1,
                id_modelo=10,
                id_producto=1,
                nombre_producto="Vestido Seda Imperial",
                id_sucursal=101,
                nombre_sucursal="Sucursal La Paz",
                periodo="proximo_mes",
                demanda_esperada=12,
                ingresos_esperados_bob=Decimal("6960.00"),
                probabilidad=Decimal("0.8750"),
                nivel_confianza="ALTA",
            )
        ]

        res = AprendizajeMlServicio.consultar_predicciones(
            db, _usuario_admin(10), tipo_cambio_bob=Decimal("6.96")
        )
        assert res.tiene_modelo_activo is True
        assert res.aviso_datos_sinteticos is True  # CU24 A3
        assert res.moneda == "BOB"
        assert res.simbolo_moneda == "Bs."
        assert len(res.predicciones) == 1
        assert Decimal("0.0000") <= res.predicciones[0].probabilidad <= Decimal("1.0000")  # RN50
        assert res.predicciones[0].ingresos_esperados_bob == Decimal("6960.00")
        assert res.predicciones[0].equivalente_usd == Decimal("1000.00")

    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.AprendizajeMlRepositorio")
    @patch("modules.comercial.cu23_cu25_aprendizaje_ml.servicio.SuscripcionServicio.validar")
    def test_ac07_y_ac08_cu25_consultar_segmentos_clientes_y_aislamiento(
        self,
        mock_validar_susc: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        ahora = datetime.now(timezone.utc)
        db = MagicMock()

        # Curso Alterno CU25 A1: Sin modelo no supervisado activo
        mock_repo.obtener_modelo_activo_por_tipo.return_value = None
        sin_seg = AprendizajeMlServicio.consultar_segmentos(db, _usuario_admin(10))
        assert sin_seg.tiene_modelo_activo is False

        # Con modelo no supervisado activo y un grupo vacío (CU25 A2 y A3)
        mock_repo.obtener_modelo_activo_por_tipo.return_value = SimpleNamespace(
            id_modelo=20,
            id_tenant=10,
            id_dataset=2,
            nombre="Clustering RFM",
            tipo_modelo="no_supervisado",
            algoritmo="K-Means",
            variable_objetivo=None,
            variables_entrada=["frecuencia_compra"],
            origen_datos="sintetico",
            estado="activo",
            activo=True,
            motivo_error=None,
            metricas_entrenamiento={"silhouette_score": 0.72},
            metricas_validacion={"silhouette_score": 0.70},
            metricas_prueba={"silhouette_score": 0.69},
            creado_en=ahora,
            actualizado_en=ahora,
        )
        mock_repo.listar_segmentos_modelo.return_value = [
            SimpleNamespace(
                id_segmento=1,
                id_modelo=20,
                codigo_grupo="SEG-VIP",
                nombre_grupo="Clientas VIP",
                descripcion="Alta frecuencia y ticket en Bs.",
                cantidad_clientes=15,
                caracteristicas={"ticket_promedio_bob": 1480.0, "moneda": "BOB (Bs.)"},
                clientes_muestra=[{"nombre_completo": "Valeria Rojas", "monto_total_bob": 5420.0}],
            ),
            SimpleNamespace(
                id_segmento=2,
                id_modelo=20,
                codigo_grupo="SEG-VACIO",
                nombre_grupo="Segmento sin clientes",
                descripcion="Grupo vacío para prueba CU25 A2",
                cantidad_clientes=0,
                caracteristicas={"ticket_promedio_bob": 0.0, "moneda": "BOB (Bs.)"},
                clientes_muestra=[],
            ),
        ]

        res_seg = AprendizajeMlServicio.consultar_segmentos(db, _usuario_admin(10))
        assert res_seg.tiene_modelo_activo is True
        assert res_seg.aviso_datos_sinteticos is True  # CU25 A3
        assert res_seg.total_clientes_segmentados == 15
        assert res_seg.segmentos[0].sin_clientes is False
        assert res_seg.segmentos[1].sin_clientes is True  # CU25 A2

        # AC-08: Bloqueo si la suscripción de la empresa no está vigente (CU12)
        mock_validar_susc.side_effect = AuthorizationError(
            "La suscripción de la empresa está vencida.",
            code="SUSCRIPCION_NO_VIGENTE",
        )
        with pytest.raises(AuthorizationError) as exc_susc:
            AprendizajeMlServicio.consultar_segmentos(db, _usuario_admin(10))
        assert exc_susc.value.code == "SUSCRIPCION_NO_VIGENTE"

    def test_cero_datos_inventados_cuando_empresa_no_tiene_productos_o_sucursales(self) -> None:
        """Bloqueante 2 Auditoría: Si la empresa no tiene productos o sucursales, no inventa nombres."""
        from modules.comercial.cu23_cu25_aprendizaje_ml.motor_ml import MotorAprendizajeML

        # Caso dataset sin productos ni sucursales
        total, resumen, muestra = MotorAprendizajeML.construir_dataset_y_preprocesar(
            id_tenant=99,
            origen="real",
            cantidad_sinteticos=20,
            horizonte_meses=3,
            variables_seleccionadas=["precio_bob"],
            productos_empresa=[],
            sucursales_empresa=[],
            clientes_empresa=[],
            registros_reales_ventas=0,
            factor_bob=Decimal("1.00"),
        )
        assert total == 0
        assert len(muestra) == 0

        # Caso entrenamiento supervisado sin productos ni sucursales
        m_train, m_val, m_test, predicciones = MotorAprendizajeML.entrenar_modelo_supervisado(
            id_tenant=99,
            id_dataset=1,
            variable_objetivo="demanda_unidades",
            variables_entrada=["precio_bob"],
            origen_datos="real",
            productos_empresa=[],
            sucursales_empresa=[],
            factor_bob=Decimal("1.00"),
        )
        assert len(predicciones) == 0

        # Caso entrenamiento no supervisado con origen real y sin clientes
        m_train_u, m_val_u, m_test_u, segmentos = MotorAprendizajeML.entrenar_modelo_no_supervisado(
            id_tenant=99,
            id_dataset=1,
            numero_clusters=3,
            origen_datos="real",
            clientes_empresa=[],
            factor_bob=Decimal("1.00"),
        )
        assert len(segmentos) == 0


