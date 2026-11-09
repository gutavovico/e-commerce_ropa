"""Servicio de aplicación y dominio para P2-CU23, P2-CU24 y P2-CU25 (Aprendizaje Automático)."""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from core.errors import AuthorizationError, NotFoundError, UnprocessableEntityError
from core.tenant import tenant_actual
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu23_cu25_aprendizaje_ml.esquemas import (
    ConsultaPrediccionesOut,
    ConsultaSegmentosOut,
    CrearDatasetMlIn,
    DatasetMlOut,
    EntrenarModeloMlIn,
    ModeloMlOut,
    PrediccionItemOut,
    ResumenAprendizajeMlOut,
    SegmentoClienteItemOut,
)
from modules.comercial.cu23_cu25_aprendizaje_ml.motor_ml import (
    PERIODOS_PREDICCION,
    VARIABLES_DISPONIBLES_ML,
    VARIABLES_OBJETIVO_SUPERVISADO,
    MotorAprendizajeML,
)
from modules.comercial.cu23_cu25_aprendizaje_ml.repositorio import (
    AprendizajeMlRepositorio,
)
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

TASAS_CAMBIO_BOB: dict[str, Decimal] = {
    "BOB": Decimal("1.00"),
    "USD": Decimal("6.96"),
    "EUR": Decimal("7.50"),
}


def _resolver_empresa_y_validar_suscripcion(db: Session, usuario: UsuarioORM) -> int:
    """Resuelve el id_tenant del administrador y valida que la suscripción de la empresa esté vigente (CU12)."""
    id_tenant = getattr(usuario, "id_tenant", None) or tenant_actual(db)
    if id_tenant is None:
        raise AuthorizationError(
            "El módulo de aprendizaje automático requiere pertenecer a una empresa.",
            code="TENANT_REQUERIDO",
        )
    SuscripcionServicio.validar(db, id_tenant=int(id_tenant))
    return int(id_tenant)


def _factor_conversion_a_bob(moneda_empresa: str, tipo_cambio_bob: Decimal) -> Decimal:
    moneda_norm = (moneda_empresa or "BOB").strip().upper()
    if moneda_norm == "BOB":
        return Decimal("1.00")
    if tipo_cambio_bob and tipo_cambio_bob > Decimal("1.00"):
        return Decimal(str(tipo_cambio_bob))
    return TASAS_CAMBIO_BOB.get(moneda_norm, Decimal("6.96"))


class AprendizajeMlServicio:
    """Orquesta P2-CU23 (datasets y modelos), P2-CU24 (predicciones) y P2-CU25 (segmentos de clientes)."""

    @staticmethod
    def obtener_resumen(
        db: Session,
        usuario: UsuarioORM,
    ) -> ResumenAprendizajeMlOut:
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)
        tenant = AprendizajeMlRepositorio.obtener_tenant(db, id_tenant)
        moneda_bd = AprendizajeMlRepositorio.obtener_moneda_empresa(db, id_tenant)
        factor_bob = _factor_conversion_a_bob(moneda_bd, Decimal("6.96"))

        ventas_reales = AprendizajeMlRepositorio.contar_ventas_reales_empresa(db, id_tenant)
        clientes_reales = AprendizajeMlRepositorio.listar_clientes_con_actividad_empresa(
            db, id_tenant, factor_bob
        )
        productos = AprendizajeMlRepositorio.listar_productos_empresa(db, id_tenant)
        sucursales = AprendizajeMlRepositorio.listar_sucursales_empresa(db, id_tenant)
        datasets = AprendizajeMlRepositorio.listar_datasets(db, id_tenant)
        modelos = AprendizajeMlRepositorio.listar_modelos(db, id_tenant)

        sup_activo = AprendizajeMlRepositorio.obtener_modelo_activo_por_tipo(
            db, id_tenant, "supervisado"
        )
        unsup_activo = AprendizajeMlRepositorio.obtener_modelo_activo_por_tipo(
            db, id_tenant, "no_supervisado"
        )

        return ResumenAprendizajeMlOut(
            id_tenant=id_tenant,
            nombre_empresa=tenant.nombre if tenant else "FashionStore",
            moneda="BOB",
            simbolo_moneda="Bs.",
            tipo_cambio_bob=Decimal("6.96"),
            registros_reales_ventas=ventas_reales,
            registros_reales_clientes=len(clientes_reales),
            variables_disponibles=VARIABLES_DISPONIBLES_ML,
            variables_objetivo_supervisado=VARIABLES_OBJETIVO_SUPERVISADO,
            productos_empresa=[
                {
                    "id_producto": p["id_producto"],
                    "nombre": p["nombre"],
                    "precio_bob": float((p["precio_base"] * factor_bob).quantize(Decimal("0.01"))),
                }
                for p in productos
            ],
            sucursales_empresa=sucursales,
            datasets=[DatasetMlOut.model_validate(d) for d in datasets],
            modelos=[ModeloMlOut.model_validate(m) for m in modelos],
            modelo_supervisado_activo=ModeloMlOut.model_validate(sup_activo)
            if sup_activo
            else None,
            modelo_no_supervisado_activo=ModeloMlOut.model_validate(unsup_activo)
            if unsup_activo
            else None,
        )

    @staticmethod
    def crear_dataset(
        db: Session,
        datos: CrearDatasetMlIn,
        usuario: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> DatasetMlOut:
        """Crea un conjunto de datos (`sintetico`, `real` o `mixto`) y ejecuta su preprocesamiento (P2-CU23 pasos 1-3)."""
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)
        moneda_bd = AprendizajeMlRepositorio.obtener_moneda_empresa(db, id_tenant)
        factor_bob = _factor_conversion_a_bob(moneda_bd, datos.tipo_cambio_bob)

        ventas_reales = AprendizajeMlRepositorio.contar_ventas_reales_empresa(db, id_tenant)
        clientes_reales = AprendizajeMlRepositorio.listar_clientes_con_actividad_empresa(
            db, id_tenant, factor_bob
        )

        # Curso Alterno CU23 A1: Datos reales insuficientes
        if datos.origen == "real" and ventas_reales < 5 and len(clientes_reales) < 5:
            raise UnprocessableEntityError(
                "La empresa cuenta con datos reales insuficientes para entrenar directamente (CU23 A1). "
                "Seleccione el origen 'sintetico' o 'mixto' para generar datos de entrenamiento.",
                code="DATOS_INSUFICIENTES_ML",
            )

        productos = AprendizajeMlRepositorio.listar_productos_empresa(db, id_tenant)
        sucursales = AprendizajeMlRepositorio.listar_sucursales_empresa(db, id_tenant)

        total_registros, resumen_prep, muestra = (
            MotorAprendizajeML.construir_dataset_y_preprocesar(
                id_tenant=id_tenant,
                origen=datos.origen,
                cantidad_sinteticos=datos.cantidad_registros_sinteticos,
                horizonte_meses=datos.horizonte_meses,
                variables_seleccionadas=datos.variables_seleccionadas,
                productos_empresa=productos,
                sucursales_empresa=sucursales,
                clientes_empresa=clientes_reales,
                registros_reales_ventas=ventas_reales,
                factor_bob=factor_bob,
            )
        )

        creado = AprendizajeMlRepositorio.crear_dataset(
            db,
            {
                "id_tenant": id_tenant,
                "nombre": datos.nombre.strip(),
                "origen": datos.origen,
                "cantidad_registros": total_registros,
                "variables_seleccionadas": datos.variables_seleccionadas,
                "parametros_generacion": {
                    "cantidad_registros_sinteticos": datos.cantidad_registros_sinteticos,
                    "horizonte_meses": datos.horizonte_meses,
                    "moneda": "BOB",
                    "tipo_cambio_bob": str(datos.tipo_cambio_bob),
                },
                "resumen_preprocesamiento": resumen_prep,
                "muestra_datos": muestra,
                "creado_por": usuario.id_usuario,
            },
        )

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion="CREAR_DATASET_ML",
            tabla_modulo="comercial.datasets_ml",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_dataset": creado.id_dataset,
                "nombre": creado.nombre,
                "origen": creado.origen,
                "cantidad_registros": creado.cantidad_registros,
                "moneda": "BOB",
            },
            db=db,
        )
        return DatasetMlOut.model_validate(creado)

    @staticmethod
    def entrenar_modelo(
        db: Session,
        datos: EntrenarModeloMlIn,
        usuario: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> ModeloMlOut:
        """Entrena y evalúa un modelo supervisado o no supervisado (P2-CU23 pasos 4-8 y A2, A3, RN49)."""
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)

        # Curso Alterno CU23 A2 / RN49: Modelo supervisado exige variable objetivo
        if datos.tipo_modelo == "supervisado" and (
            not datos.variable_objetivo or not datos.variable_objetivo.strip()
        ):
            raise UnprocessableEntityError(
                "Un modelo supervisado exige obligatoriamente una variable objetivo (CU23 A2, RN49).",
                code="VARIABLE_OBJETIVO_REQUERIDA",
            )

        dataset = AprendizajeMlRepositorio.obtener_dataset(db, id_tenant, datos.id_dataset)
        if not dataset:
            raise NotFoundError(
                f"El conjunto de datos #{datos.id_dataset} no existe en su empresa.",
                code="DATASET_ML_NO_ENCONTRADO",
            )

        variables_entrada = (
            datos.variables_entrada
            if datos.variables_entrada
            else list(dataset.variables_seleccionadas or ["precio_bob", "frecuencia_compra"])
        )
        algoritmo = datos.algoritmo or (
            "RandomForestRegressor (Demanda & Ingresos Bs.)"
            if datos.tipo_modelo == "supervisado"
            else f"K-Means RFM ({datos.numero_clusters} Segmentos en Bs.)"
        )

        # Curso Alterno CU23 A3: El entrenamiento falla y el modelo queda en estado 'fallido' con el motivo
        if datos.forzar_fallo_entrenamiento:
            modelo_fallido = AprendizajeMlRepositorio.crear_modelo_con_resultados(
                db,
                datos_modelo={
                    "id_tenant": id_tenant,
                    "id_dataset": dataset.id_dataset,
                    "nombre": datos.nombre.strip(),
                    "tipo_modelo": datos.tipo_modelo,
                    "algoritmo": algoritmo,
                    "variable_objetivo": datos.variable_objetivo,
                    "variables_entrada": variables_entrada,
                    "origen_datos": dataset.origen,
                    "estado": "fallido",
                    "activo": False,
                    "motivo_error": "No se alcanzó convergencia numérica durante el ajuste de hiperparámetros (CU23 A3).",
                    "metricas_entrenamiento": {},
                    "metricas_validacion": {},
                    "metricas_prueba": {},
                    "creado_por": usuario.id_usuario,
                },
                predicciones=[],
                segmentos=[],
                activar_inmediatamente=False,
            )
            return ModeloMlOut.model_validate(modelo_fallido)

        moneda_bd = AprendizajeMlRepositorio.obtener_moneda_empresa(db, id_tenant)
        factor_bob = _factor_conversion_a_bob(moneda_bd, datos.tipo_cambio_bob)

        predicciones_generadas = []
        segmentos_generados = []

        if datos.tipo_modelo == "supervisado":
            productos = AprendizajeMlRepositorio.listar_productos_empresa(db, id_tenant)
            sucursales = AprendizajeMlRepositorio.listar_sucursales_empresa(db, id_tenant)
            m_train, m_val, m_test, predicciones_generadas = (
                MotorAprendizajeML.entrenar_modelo_supervisado(
                    id_tenant=id_tenant,
                    id_dataset=dataset.id_dataset,
                    variable_objetivo=datos.variable_objetivo or "demanda_unidades",
                    variables_entrada=variables_entrada,
                    origen_datos=dataset.origen,
                    productos_empresa=productos,
                    sucursales_empresa=sucursales,
                    factor_bob=factor_bob,
                )
            )
        else:
            clientes = AprendizajeMlRepositorio.listar_clientes_con_actividad_empresa(
                db, id_tenant, factor_bob
            )
            m_train, m_val, m_test, segmentos_generados = (
                MotorAprendizajeML.entrenar_modelo_no_supervisado(
                    id_tenant=id_tenant,
                    id_dataset=dataset.id_dataset,
                    numero_clusters=datos.numero_clusters,
                    origen_datos=dataset.origen,
                    clientes_empresa=clientes,
                    factor_bob=factor_bob,
                )
            )

        modelo_creado = AprendizajeMlRepositorio.crear_modelo_con_resultados(
            db,
            datos_modelo={
                "id_tenant": id_tenant,
                "id_dataset": dataset.id_dataset,
                "nombre": datos.nombre.strip(),
                "tipo_modelo": datos.tipo_modelo,
                "algoritmo": algoritmo,
                "variable_objetivo": datos.variable_objetivo
                if datos.tipo_modelo == "supervisado"
                else None,
                "variables_entrada": variables_entrada,
                "origen_datos": dataset.origen,
                "estado": "activo" if datos.activar_inmediatamente else "evaluado",
                "activo": datos.activar_inmediatamente,
                "motivo_error": None,
                "metricas_entrenamiento": m_train,
                "metricas_validacion": m_val,
                "metricas_prueba": m_test,
                "creado_por": usuario.id_usuario,
            },
            predicciones=predicciones_generadas,
            segmentos=segmentos_generados,
            activar_inmediatamente=datos.activar_inmediatamente,
        )

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion="ENTRENAR_MODELO_ML",
            tabla_modulo="comercial.modelos_ml",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_modelo": modelo_creado.id_modelo,
                "tipo_modelo": modelo_creado.tipo_modelo,
                "origen_datos": modelo_creado.origen_datos,
                "activo": modelo_creado.activo,
                "moneda": "BOB",
            },
            db=db,
        )
        return ModeloMlOut.model_validate(modelo_creado)

    @staticmethod
    def activar_modelo(
        db: Session,
        id_modelo: int,
        usuario: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> ModeloMlOut:
        """Activa un modelo evaluado para que quede disponible en CU24 o CU25 (CU23 paso 7)."""
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)
        modelo = AprendizajeMlRepositorio.obtener_modelo(db, id_tenant, id_modelo)
        if not modelo:
            raise NotFoundError(
                f"El modelo #{id_modelo} no existe en su empresa.",
                code="MODELO_ML_NO_ENCONTRADO",
            )
        if modelo.estado == "fallido":
            raise UnprocessableEntityError(
                "No se puede activar un modelo cuyo entrenamiento resultó fallido (CU23 A3).",
                code="MODELO_ML_FALLIDO_NO_ACTIVABLE",
            )

        activado = AprendizajeMlRepositorio.activar_modelo(db, modelo)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion="ACTIVAR_MODELO_ML",
            tabla_modulo="comercial.modelos_ml",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_modelo": activado.id_modelo,
                "nombre": activado.nombre,
                "tipo_modelo": activado.tipo_modelo,
            },
            db=db,
        )
        return ModeloMlOut.model_validate(activado)

    @staticmethod
    def archivar_modelo(
        db: Session,
        id_modelo: int,
        usuario: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> ModeloMlOut:
        """Archiva un modelo: deja de usarse pero conserva sus métricas (CU23 A5)."""
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)
        modelo = AprendizajeMlRepositorio.obtener_modelo(db, id_tenant, id_modelo)
        if not modelo:
            raise NotFoundError(
                f"El modelo #{id_modelo} no existe en su empresa.",
                code="MODELO_ML_NO_ENCONTRADO",
            )

        archivado = AprendizajeMlRepositorio.archivar_modelo(db, modelo)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion="ARCHIVAR_MODELO_ML",
            tabla_modulo="comercial.modelos_ml",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_modelo": archivado.id_modelo,
                "nombre": archivado.nombre,
                "estado": archivado.estado,
            },
            db=db,
        )
        return ModeloMlOut.model_validate(archivado)

    # =========================================================================
    # P2-CU24: CONSULTAR PREDICCIONES (MODELO SUPERVISADO ACTIVO)
    # =========================================================================

    @staticmethod
    def consultar_predicciones(
        db: Session,
        usuario: UsuarioORM,
        *,
        id_producto: Optional[int] = None,
        id_sucursal: Optional[int] = None,
        periodo: Optional[str] = None,
        tipo_cambio_bob: Decimal = Decimal("6.96"),
    ) -> ConsultaPrediccionesOut:
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)
        tasa_ref = tipo_cambio_bob if tipo_cambio_bob > Decimal("1.00") else Decimal("6.96")

        modelo_activo = AprendizajeMlRepositorio.obtener_modelo_activo_por_tipo(
            db, id_tenant, "supervisado"
        )
        # Curso Alterno CU24 A1: No hay un modelo supervisado activo
        if not modelo_activo:
            return ConsultaPrediccionesOut(
                tiene_modelo_activo=False,
                mensaje_estado=(
                    "No existe un modelo supervisado activo en su empresa (CU24 A1). "
                    "Diríjase a la pestaña 'Gestionar Datos y Modelos (CU23)' para entrenar y activar uno."
                ),
                aviso_datos_sinteticos=False,
                moneda="BOB",
                simbolo_moneda="Bs.",
                tipo_cambio_bob=tasa_ref,
                modelo_activo=None,
                periodos_disponibles=list(PERIODOS_PREDICCION),
                resumen_kpis_bob={},
                predicciones=[],
            )

        # Curso Alterno CU24 A3: Señalar si el modelo se entrenó con datos sintéticos o mixtos
        usa_sinteticos = modelo_activo.origen_datos in ("sintetico", "mixto")
        msg_sinteticos = (
            f"Aviso metodológico (CU24 A3): Este modelo fue entrenado con datos de origen '{modelo_activo.origen_datos}'. "
            "Las proyecciones reflejan patrones simulados calibrados para su empresa."
            if usa_sinteticos
            else None
        )

        filas_orm = AprendizajeMlRepositorio.listar_predicciones_modelo(
            db,
            id_tenant=id_tenant,
            id_modelo=modelo_activo.id_modelo,
            id_producto=id_producto,
            id_sucursal=id_sucursal,
            periodo=periodo,
        )

        items_out: list[PrediccionItemOut] = []
        total_unidades = 0
        total_bob = Decimal("0.00")
        suma_prob = Decimal("0.0000")

        for f in filas_orm:
            ing_bob = Decimal(str(f.ingresos_esperados_bob)).quantize(Decimal("0.01"))
            eq_usd = (ing_bob / tasa_ref).quantize(Decimal("0.01"))
            prob = max(Decimal("0.0000"), min(Decimal("1.0000"), Decimal(str(f.probabilidad))))

            total_unidades += int(f.demanda_esperada)
            total_bob += ing_bob
            suma_prob += prob

            items_out.append(
                PrediccionItemOut(
                    id_prediccion=f.id_prediccion,
                    id_modelo=f.id_modelo,
                    id_producto=f.id_producto,
                    nombre_producto=f.nombre_producto,
                    id_sucursal=f.id_sucursal,
                    nombre_sucursal=f.nombre_sucursal,
                    periodo=f.periodo,
                    demanda_esperada=f.demanda_esperada,
                    ingresos_esperados_bob=ing_bob,
                    equivalente_usd=eq_usd,
                    probabilidad=prob,
                    nivel_confianza=f.nivel_confianza,
                )
            )

        prob_media = (
            float((suma_prob / Decimal(len(items_out))).quantize(Decimal("0.0001")))
            if items_out
            else 0.0
        )

        mensaje = (
            "No se encontraron predicciones para los filtros seleccionados (CU24 A2)."
            if not items_out
            else f"Mostrando {len(items_out)} predicciones del modelo supervisado activo en Bolivianos (Bs. / BOB)."
        )

        return ConsultaPrediccionesOut(
            tiene_modelo_activo=True,
            mensaje_estado=mensaje,
            aviso_datos_sinteticos=usa_sinteticos,
            mensaje_datos_sinteticos=msg_sinteticos,
            moneda="BOB",
            simbolo_moneda="Bs.",
            tipo_cambio_bob=tasa_ref,
            modelo_activo=ModeloMlOut.model_validate(modelo_activo),
            periodos_disponibles=list(PERIODOS_PREDICCION),
            resumen_kpis_bob={
                "demanda_total_unidades": total_unidades,
                "ingresos_proyectados_bob": float(total_bob),
                "equivalente_proyectado_usd": float((total_bob / tasa_ref).quantize(Decimal("0.01"))),
                "probabilidad_media": prob_media,
                "tipo_cambio_bob": float(tasa_ref),
            },
            predicciones=items_out,
        )

    # =========================================================================
    # P2-CU25: CONSULTAR SEGMENTOS DE CLIENTES (MODELO NO SUPERVISADO ACTIVO)
    # =========================================================================

    @staticmethod
    def consultar_segmentos(
        db: Session,
        usuario: UsuarioORM,
        *,
        tipo_cambio_bob: Decimal = Decimal("6.96"),
    ) -> ConsultaSegmentosOut:
        id_tenant = _resolver_empresa_y_validar_suscripcion(db, usuario)
        tasa_ref = tipo_cambio_bob if tipo_cambio_bob > Decimal("1.00") else Decimal("6.96")

        modelo_activo = AprendizajeMlRepositorio.obtener_modelo_activo_por_tipo(
            db, id_tenant, "no_supervisado"
        )
        # Curso Alterno CU25 A1: No hay un modelo no supervisado activo
        if not modelo_activo:
            return ConsultaSegmentosOut(
                tiene_modelo_activo=False,
                mensaje_estado=(
                    "No existe un modelo no supervisado activo en su empresa (CU25 A1). "
                    "Diríjase a la pestaña 'Gestionar Datos y Modelos (CU23)' para entrenar y activar un modelo de segmentación."
                ),
                aviso_datos_sinteticos=False,
                moneda="BOB",
                simbolo_moneda="Bs.",
                tipo_cambio_bob=tasa_ref,
                modelo_activo=None,
                total_clientes_segmentados=0,
                segmentos=[],
            )

        # Curso Alterno CU25 A3: Modelo entrenado con datos sintéticos
        usa_sinteticos = modelo_activo.origen_datos in ("sintetico", "mixto")
        msg_sinteticos = (
            f"Aviso metodológico (CU25 A3): Este modelo de segmentación fue entrenado con datos de origen '{modelo_activo.origen_datos}'."
            if usa_sinteticos
            else None
        )

        filas_orm = AprendizajeMlRepositorio.listar_segmentos_modelo(
            db,
            id_tenant=id_tenant,
            id_modelo=modelo_activo.id_modelo,
        )
        total_clientes = sum(max(0, int(s.cantidad_clientes)) for s in filas_orm)
        divisor = total_clientes if total_clientes > 0 else 1

        segmentos_out: list[SegmentoClienteItemOut] = []
        for s in filas_orm:
            cant = max(0, int(s.cantidad_clientes))
            pct = round((cant / divisor) * 100.0, 1) if total_clientes > 0 else 0.0
            segmentos_out.append(
                SegmentoClienteItemOut(
                    id_segmento=s.id_segmento,
                    id_modelo=s.id_modelo,
                    codigo_grupo=s.codigo_grupo,
                    nombre_grupo=s.nombre_grupo,
                    descripcion=s.descripcion,
                    cantidad_clientes=cant,
                    porcentaje_clientes=pct,
                    sin_clientes=(cant == 0),  # CU25 A2
                    caracteristicas=dict(s.caracteristicas or {}),
                    clientes_muestra=list(s.clientes_muestra or []),
                )
            )

        return ConsultaSegmentosOut(
            tiene_modelo_activo=True,
            mensaje_estado=f"Mostrando {len(segmentos_out)} segmentos de clientes con métricas en Bolivianos (Bs. / BOB).",
            aviso_datos_sinteticos=usa_sinteticos,
            mensaje_datos_sinteticos=msg_sinteticos,
            moneda="BOB",
            simbolo_moneda="Bs.",
            tipo_cambio_bob=tasa_ref,
            modelo_activo=ModeloMlOut.model_validate(modelo_activo),
            total_clientes_segmentados=total_clientes,
            segmentos=segmentos_out,
        )

