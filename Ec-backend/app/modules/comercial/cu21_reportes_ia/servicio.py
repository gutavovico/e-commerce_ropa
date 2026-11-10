"""Servicio de aplicación y dominio para P2-CU21: Generar reporte con IA."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Optional

from sqlalchemy.orm import Session

from core.errors import AuthorizationError, NotFoundError, UnprocessableEntityError
from core.tenant import tenant_actual
from core.tiempo import ahora, ahora_local, hoy
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu21_reportes_ia.esquemas import (
    ContextoReportesIaEmpresaOut,
    GenerarReporteIaIn,
    InterpretacionReporteIaOut,
    PuntoGraficoReporteOut,
    SolicitudReporteIaHistorialOut,
    SolicitudReporteIaResultadoOut,
)
from modules.comercial.cu21_reportes_ia.interprete_ia import InterpreteReportesIA
from modules.comercial.cu21_reportes_ia.repositorio import ReportesIaRepositorio
from modules.comercial.cu31_reportes_voz.generadores.generador_excel import (
    GeneradorExcel,
)
from modules.comercial.cu31_reportes_voz.generadores.generador_pdf import GeneradorPDF
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.plataforma.cu22_catalogo_reportes.esquemas import CatalogoReporteOut
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

TASAS_CAMBIO_BOB: dict[str, Decimal] = {
    "BOB": Decimal("1.00"),
    "USD": Decimal("6.96"),
}


def _resolver_empresa_y_validar_plan(db: Session, usuario: UsuarioORM) -> int:
    """Resuelve el id_tenant del administrador y valida P2-CU12 (`reportes_ia`, RN44, CU21 A3)."""
    id_tenant = getattr(usuario, "id_tenant", None) or tenant_actual(db)
    if id_tenant is None:
        raise AuthorizationError(
            "La generación de reportes con IA requiere pertenecer a una empresa.",
            code="TENANT_REQUERIDO",
        )
    # P2-CU12 / RN44 / CU21 A3: valida suscripción vigente y que el plan incluya `reportes_ia`
    SuscripcionServicio.validar(db, funcionalidad="reportes_ia", id_tenant=int(id_tenant))
    return int(id_tenant)


def _factor_conversion_a_bob(moneda_empresa: str, tipo_cambio_bob: Decimal) -> Decimal:
    """Si los precios de la empresa están en USD o EUR, convierte a Bolivianos (Bs.); si ya están en BOB, mantiene 1.00."""
    moneda_norm = (moneda_empresa or "BOB").strip().upper()
    if moneda_norm == "BOB":
        return Decimal("1.00")
    if tipo_cambio_bob and tipo_cambio_bob > Decimal("1.00"):
        return Decimal(str(tipo_cambio_bob))
    return TASAS_CAMBIO_BOB.get(moneda_norm, Decimal("6.96"))


class ReportesIaServicio:
    """Orquesta P2-CU21: contexto del catálogo, interpretación IA, consultas controladas en Bs. (BOB) y exportación."""

    @staticmethod
    def obtener_contexto_empresa(
        db: Session,
        usuario: UsuarioORM,
    ) -> ContextoReportesIaEmpresaOut:
        id_tenant = _resolver_empresa_y_validar_plan(db, usuario)
        tenant = ReportesIaRepositorio.obtener_tenant(db, id_tenant)
        moneda = ReportesIaRepositorio.obtener_moneda_empresa(db, id_tenant)
        catalogo = ReportesIaRepositorio.listar_catalogo_activo(db)
        sucursales = ReportesIaRepositorio.listar_sucursales_empresa(db, id_tenant)
        categorias = ReportesIaRepositorio.listar_categorias_empresa(db, id_tenant)
        ejemplos = InterpreteReportesIA._recopilar_ejemplos(catalogo)

        return ContextoReportesIaEmpresaOut(
            id_tenant=id_tenant,
            nombre_empresa=tenant.nombre if tenant else "FashionStore",
            moneda_empresa="BOB",
            simbolo_moneda="Bs.",
            tipo_cambio_bob=TASAS_CAMBIO_BOB.get(moneda, Decimal("6.96"))
            if moneda != "BOB"
            else Decimal("6.96"),
            catalogo_activo=[CatalogoReporteOut.model_validate(c) for c in catalogo],
            sucursales_activas=sucursales,
            categorias_empresa=categorias,
            ejemplos_destacados=ejemplos,
        )

    @staticmethod
    def generar_reporte(
        db: Session,
        datos: GenerarReporteIaIn,
        usuario: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> SolicitudReporteIaResultadoOut:
        id_tenant = _resolver_empresa_y_validar_plan(db, usuario)
        moneda_bd = ReportesIaRepositorio.obtener_moneda_empresa(db, id_tenant)
        factor_bob = _factor_conversion_a_bob(moneda_bd, datos.tipo_cambio_bob)
        tasa_referencial = (
            datos.tipo_cambio_bob if datos.tipo_cambio_bob > Decimal("1.00") else Decimal("6.96")
        )

        catalogo_activo = ReportesIaRepositorio.listar_catalogo_activo(db)
        if not catalogo_activo:
            raise UnprocessableEntityError(
                "No existen reportes activos en el catálogo permitido de la plataforma (CU21 precondición).",
                code="CATALOGO_REPORTES_VACIO",
            )

        ejemplos_sugeridos = InterpreteReportesIA._recopilar_ejemplos(catalogo_activo)

        # Curso Alterno A7: rechazo de intento de consultar datos de otra empresa
        if datos.id_tenant_solicitado is not None and int(datos.id_tenant_solicitado) != id_tenant:
            interp_rechazo = InterpretacionReporteIaOut(
                estado="rechazada",
                explicacion_ia=(
                    "Solicitud rechazada: los filtros intentan consultar datos de otra empresa (CU21 A7, RN46)."
                ),
                origen_motor="validador_aislamiento_cu13",
            )
            solicitud_orm = ReportesIaRepositorio.registrar_solicitud(
                db,
                id_tenant=id_tenant,
                id_usuario=usuario.id_usuario,
                comando_voz_texto=datos.prompt_texto,
                tipo_reporte=None,
                estado="rechazada",
                interpretacion=interp_rechazo.model_dump(mode="json"),
                formato_visualizacion="ambos",
                mensaje_estado=interp_rechazo.explicacion_ia,
            )
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=usuario.id_usuario,
                usuario_nombre=usuario.email,
                accion="REPORTE_IA_RECHAZADO_OTRO_TENANT",
                tabla_modulo="comercial.solicitudes_reporte_ia",
                direccion_ip=direccion_ip,
                severidad="WARN",
                payload_nuevo={
                    "id_solicitud": solicitud_orm.id_solicitud,
                    "id_tenant_autenticado": id_tenant,
                    "id_tenant_solicitado": datos.id_tenant_solicitado,
                },
                db=db,
            )
            raise AuthorizationError(
                interp_rechazo.explicacion_ia,
                code="FILTRO_REPORTE_NO_AUTORIZADO",
            )

        sucursales_empresa = ReportesIaRepositorio.listar_sucursales_empresa(db, id_tenant)
        categorias_empresa = ReportesIaRepositorio.listar_categorias_empresa(db, id_tenant)

        # Si el usuario pidió un id_sucursal explícito que no pertenece a su empresa -> A7
        if datos.id_sucursal is not None:
            ids_validos = {int(s["id_sucursal"]) for s in sucursales_empresa}
            if int(datos.id_sucursal) not in ids_validos:
                raise AuthorizationError(
                    "La sucursal indicada en los filtros no pertenece a su empresa o no está activa (CU21 A7).",
                    code="FILTRO_REPORTE_NO_AUTORIZADO",
                )

        interpretacion = InterpreteReportesIA.interpretar(
            prompt_texto=datos.prompt_texto,
            catalogo_activo=catalogo_activo,
            sucursales_empresa=sucursales_empresa,
            categorias_empresa=categorias_empresa,
            codigo_forzado=datos.codigo_reporte_forzado,
            formato_preferido=datos.formato_preferido,
            fecha_inicio_in=datos.fecha_inicio,
            fecha_fin_in=datos.fecha_fin,
            id_sucursal_in=datos.id_sucursal,
            id_categoria_in=datos.id_categoria,
        )

        # Cursos Alternos A1 (ambigua), A2 (no_soportada) o A7 (rechazada)
        if interpretacion.estado != "completada" or not interpretacion.codigo_reporte:
            solicitud_orm = ReportesIaRepositorio.registrar_solicitud(
                db,
                id_tenant=id_tenant,
                id_usuario=usuario.id_usuario,
                comando_voz_texto=datos.prompt_texto,
                tipo_reporte=interpretacion.codigo_reporte,
                estado=interpretacion.estado,
                interpretacion=interpretacion.model_dump(mode="json"),
                formato_visualizacion=interpretacion.formato_visualizacion,
                mensaje_estado=interpretacion.explicacion_ia,
            )
            return SolicitudReporteIaResultadoOut(
                id_solicitud=solicitud_orm.id_solicitud,
                estado=interpretacion.estado,
                mensaje_estado=interpretacion.explicacion_ia,
                prompt_original=datos.prompt_texto,
                codigo_reporte=interpretacion.codigo_reporte,
                titulo_reporte=interpretacion.nombre_reporte,
                interpretacion=interpretacion,
                moneda="BOB",
                simbolo_moneda="Bs.",
                tipo_cambio_bob=tasa_referencial,
                formato_visualizacion=interpretacion.formato_visualizacion,
                tipo_grafico=interpretacion.tipo_grafico_sugerido,
                columnas=[],
                filas=[],
                serie_grafico=[],
                resumen_kpis_bob={},
                sin_datos=True,
                ejemplos_sugeridos=ejemplos_sugeridos,
                exportaciones=[],
                creado_en=solicitud_orm.creado_en,
            )

        # Ejecutar consulta controlada sobre los datos de la empresa (CU21 paso 6, RN45, RN46)
        columnas, filas, serie, kpis_bob = ReportesIaServicio._ejecutar_consulta_controlada(
            db,
            id_tenant=id_tenant,
            interpretacion=interpretacion,
            factor_bob=factor_bob,
            tasa_referencial=tasa_referencial,
        )

        sin_datos = len(filas) == 0
        mensaje_final = (
            "El reporte no encontró registros para los filtros seleccionados en su empresa (CU21 A6)."
            if sin_datos
            else interpretacion.explicacion_ia
        )

        solicitud_orm = ReportesIaRepositorio.registrar_solicitud(
            db,
            id_tenant=id_tenant,
            id_usuario=usuario.id_usuario,
            comando_voz_texto=datos.prompt_texto,
            tipo_reporte=interpretacion.codigo_reporte,
            estado="completada",
            interpretacion=interpretacion.model_dump(mode="json"),
            formato_visualizacion=interpretacion.formato_visualizacion,
            mensaje_estado=mensaje_final,
        )

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion="GENERAR_REPORTE_IA",
            tabla_modulo="comercial.solicitudes_reporte_ia",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_solicitud": solicitud_orm.id_solicitud,
                "codigo_reporte": interpretacion.codigo_reporte,
                "filas_generadas": len(filas),
                "moneda": "BOB",
                "tipo_cambio_bob": str(tasa_referencial),
            },
            db=db,
        )

        return SolicitudReporteIaResultadoOut(
            id_solicitud=solicitud_orm.id_solicitud,
            estado="completada",
            mensaje_estado=mensaje_final,
            prompt_original=datos.prompt_texto,
            codigo_reporte=interpretacion.codigo_reporte,
            titulo_reporte=interpretacion.nombre_reporte,
            interpretacion=interpretacion,
            moneda="BOB",
            simbolo_moneda="Bs.",
            tipo_cambio_bob=tasa_referencial,
            formato_visualizacion=interpretacion.formato_visualizacion,
            tipo_grafico=interpretacion.tipo_grafico_sugerido,
            columnas=columnas,
            filas=filas,
            serie_grafico=serie,
            resumen_kpis_bob=kpis_bob,
            sin_datos=sin_datos,
            ejemplos_sugeridos=ejemplos_sugeridos,
            exportaciones=list(solicitud_orm.exportaciones or []),
            creado_en=solicitud_orm.creado_en,
        )

    @staticmethod
    def _ejecutar_consulta_controlada(
        db: Session,
        *,
        id_tenant: int,
        interpretacion: InterpretacionReporteIaOut,
        factor_bob: Decimal,
        tasa_referencial: Decimal,
    ) -> tuple[list[str], list[list[Any]], list[PuntoGraficoReporteOut], dict[str, Any]]:
        codigo = interpretacion.codigo_reporte

        if codigo == "ventas_por_sucursal":
            datos = ReportesIaRepositorio.ejecutar_ventas_por_sucursal(
                db,
                id_tenant=id_tenant,
                fecha_inicio=interpretacion.fecha_inicio,
                fecha_fin=interpretacion.fecha_fin,
                id_sucursal=interpretacion.id_sucursal,
            )
            columnas = [
                "Sucursal",
                "Órdenes Pagadas",
                "Ingresos Totales (Bs. BOB)",
                "Ticket Promedio (Bs. BOB)",
                "Equivalente USD (T.C. 6.96)",
            ]
            filas: list[list[Any]] = []
            serie: list[PuntoGraficoReporteOut] = []
            total_ordenes = 0
            total_bob = Decimal("0.00")

            for d in datos:
                ing_bob = (d["ingresos_totales"] * factor_bob).quantize(Decimal("0.01"))
                ticket_bob = (d["ticket_promedio"] * factor_bob).quantize(Decimal("0.01"))
                eq_usd = (ing_bob / tasa_referencial).quantize(Decimal("0.01"))
                total_ordenes += d["cantidad_ventas"]
                total_bob += ing_bob

                filas.append(
                    [
                        d["sucursal"],
                        d["cantidad_ventas"],
                        float(ing_bob),
                        float(ticket_bob),
                        float(eq_usd),
                    ]
                )
                serie.append(
                    PuntoGraficoReporteOut(
                        etiqueta=d["sucursal"],
                        valor=float(ing_bob),
                        valor_secundario=float(d["cantidad_ventas"]),
                        unidad="Bs.",
                    )
                )

            kpis = {
                "ordenes_pagadas_totales": total_ordenes,
                "ingresos_totales_bob": float(total_bob),
                "equivalente_usd": float((total_bob / tasa_referencial).quantize(Decimal("0.01"))),
                "tipo_cambio_aplicado_bob": float(tasa_referencial),
            }
            return columnas, filas, serie, kpis

        if codigo == "top_productos_vendidos":
            datos = ReportesIaRepositorio.ejecutar_top_productos_vendidos(
                db,
                id_tenant=id_tenant,
                fecha_inicio=interpretacion.fecha_inicio,
                fecha_fin=interpretacion.fecha_fin,
                id_sucursal=interpretacion.id_sucursal,
                id_categoria=interpretacion.id_categoria,
            )
            columnas = [
                "Prenda",
                "Categoría",
                "Unidades Vendidas",
                "Ingresos Generados (Bs. BOB)",
                "Equivalente USD (T.C. 6.96)",
            ]
            filas = []
            serie = []
            total_unidades = 0
            total_bob = Decimal("0.00")

            for d in datos:
                ing_bob = (d["ingresos_producto"] * factor_bob).quantize(Decimal("0.01"))
                eq_usd = (ing_bob / tasa_referencial).quantize(Decimal("0.01"))
                total_unidades += d["unidades_vendidas"]
                total_bob += ing_bob

                filas.append(
                    [
                        d["producto"],
                        d["categoria"],
                        d["unidades_vendidas"],
                        float(ing_bob),
                        float(eq_usd),
                    ]
                )
                serie.append(
                    PuntoGraficoReporteOut(
                        etiqueta=d["producto"],
                        valor=float(ing_bob),
                        valor_secundario=float(d["unidades_vendidas"]),
                        unidad="Bs.",
                    )
                )

            kpis = {
                "unidades_totales_vendidas": total_unidades,
                "ingresos_totales_bob": float(total_bob),
                "equivalente_usd": float((total_bob / tasa_referencial).quantize(Decimal("0.01"))),
                "tipo_cambio_aplicado_bob": float(tasa_referencial),
            }
            return columnas, filas, serie, kpis

        if codigo == "inventario_por_sucursal":
            datos = ReportesIaRepositorio.ejecutar_inventario_por_sucursal(
                db,
                id_tenant=id_tenant,
                id_sucursal=interpretacion.id_sucursal,
                id_categoria=interpretacion.id_categoria,
            )
            columnas = [
                "Sucursal",
                "Categoría",
                "Unidades Disponibles",
                "Unidades Reservadas",
                "Valor Inventario (Bs. BOB)",
            ]
            filas = []
            serie = []
            total_disp = 0
            total_res = 0
            total_valor_bob = Decimal("0.00")

            for d in datos:
                val_bob = (d["valor_inventario"] * factor_bob).quantize(Decimal("0.01"))
                total_disp += d["stock_disponible"]
                total_res += d["stock_reservado"]
                total_valor_bob += val_bob

                filas.append(
                    [
                        d["sucursal"],
                        d["categoria"],
                        d["stock_disponible"],
                        d["stock_reservado"],
                        float(val_bob),
                    ]
                )
                serie.append(
                    PuntoGraficoReporteOut(
                        etiqueta=f"{d['sucursal']} · {d['categoria']}",
                        valor=float(d["stock_disponible"]),
                        valor_secundario=float(val_bob),
                        unidad="unid.",
                    )
                )

            kpis = {
                "unidades_disponibles_totales": total_disp,
                "unidades_reservadas_totales": total_res,
                "valor_inventario_total_bob": float(total_valor_bob),
                "tipo_cambio_aplicado_bob": float(tasa_referencial),
            }
            return columnas, filas, serie, kpis

        if codigo == "reservas_por_estado_sucursal":
            datos = ReportesIaRepositorio.ejecutar_reservas_por_estado_sucursal(
                db,
                id_tenant=id_tenant,
                fecha_inicio=interpretacion.fecha_inicio,
                fecha_fin=interpretacion.fecha_fin,
                id_sucursal=interpretacion.id_sucursal,
            )
            columnas = [
                "Sucursal",
                "Estado de Reserva",
                "Cantidad de Reservas",
                "Prendas Reservadas",
            ]
            filas = []
            serie = []
            total_reservas = 0
            total_prendas = 0

            for d in datos:
                total_reservas += d["total_reservas"]
                total_prendas += d["prendas_reservadas"]
                filas.append(
                    [
                        d["sucursal"],
                        d["estado"],
                        d["total_reservas"],
                        d["prendas_reservadas"],
                    ]
                )
                serie.append(
                    PuntoGraficoReporteOut(
                        etiqueta=f"{d['sucursal']} ({d['estado']})",
                        valor=float(d["total_reservas"]),
                        valor_secundario=float(d["prendas_reservadas"]),
                        unidad="reservas",
                    )
                )

            kpis = {
                "reservas_totales": total_reservas,
                "prendas_reservadas_totales": total_prendas,
            }
            return columnas, filas, serie, kpis

        raise UnprocessableEntityError(
            f"El reporte con código '{codigo}' no cuenta con una consulta ejecutable configurada (CU21).",
            code="REPORTE_NO_EJECUTABLE",
        )

    @staticmethod
    def listar_historial(
        db: Session,
        usuario: UsuarioORM,
    ) -> list[SolicitudReporteIaHistorialOut]:
        id_tenant = _resolver_empresa_y_validar_plan(db, usuario)
        items = ReportesIaRepositorio.listar_historial_empresa(db, id_tenant)
        return [SolicitudReporteIaHistorialOut.model_validate(i) for i in items]

    @staticmethod
    def exportar_solicitud(
        db: Session,
        *,
        id_solicitud: int,
        formato: Literal["pdf", "excel"],
        usuario: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> tuple[bytes, str, str]:
        """Re-ejecuta los datos de una solicitud completada y genera el archivo PDF o Excel (RN48)."""
        id_tenant = _resolver_empresa_y_validar_plan(db, usuario)
        solicitud = ReportesIaRepositorio.obtener_solicitud_empresa(db, id_tenant, id_solicitud)
        if not solicitud:
            raise NotFoundError(
                f"La solicitud de reporte #{id_solicitud} no existe en su empresa.",
                code="SOLICITUD_REPORTE_NO_ENCONTRADA",
            )
        if solicitud.estado != "completada" or not solicitud.tipo_reporte:
            raise UnprocessableEntityError(
                f"La solicitud #{id_solicitud} tiene estado '{solicitud.estado}' y no se puede exportar.",
                code="SOLICITUD_REPORTE_NO_EXPORTABLE",
            )

        tenant = ReportesIaRepositorio.obtener_tenant(db, id_tenant)
        moneda_bd = ReportesIaRepositorio.obtener_moneda_empresa(db, id_tenant)
        tasa_ref = Decimal("6.96")
        factor_bob = _factor_conversion_a_bob(moneda_bd, tasa_ref)

        interp_dict = solicitud.interpretacion or {
            "estado": "completada",
            "codigo_reporte": solicitud.tipo_reporte,
            "nombre_reporte": solicitud.tipo_reporte,
            "explicacion_ia": solicitud.mensaje_estado or "",
        }
        interpretacion = InterpretacionReporteIaOut.model_validate(interp_dict)

        columnas, filas, _serie, kpis = ReportesIaServicio._ejecutar_consulta_controlada(
            db,
            id_tenant=id_tenant,
            interpretacion=interpretacion,
            factor_bob=factor_bob,
            tasa_referencial=tasa_ref,
        )

        titulo_empresa = f"{tenant.nombre if tenant else 'FASHION STORE'} · REPORTES CON IA (CU21)"
        subtitulo = f"{interpretacion.nombre_reporte or solicitud.tipo_reporte} — Consulta: «{solicitud.comando_voz_texto}»"
        metadatos = {
            "Empresa": tenant.nombre if tenant else str(id_tenant),
            "Operador": usuario.email,
            "Moneda": "Bolivianos (Bs. / BOB) · T.C. 1 USD = 6.96 Bs.",
        }

        fecha_str = hoy().strftime("%Y%m%d")
        if formato == "pdf":
            contenido = GeneradorPDF.generar(
                titulo=titulo_empresa,
                subtitulo=subtitulo,
                columnas=columnas,
                filas=filas if filas else [["Sin registros para los filtros seleccionados"] + ["-"] * max(0, len(columnas) - 1)],
                metadatos=metadatos,
            )
            media_type = "application/pdf"
            nombre_archivo = f"reporte_ia_{solicitud.tipo_reporte}_{fecha_str}.pdf"
        else:
            contenido = GeneradorExcel.generar(
                titulo=titulo_empresa,
                subtitulo=subtitulo,
                columnas=columnas,
                filas=filas,
                metadatos=metadatos,
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            nombre_archivo = f"reporte_ia_{solicitud.tipo_reporte}_{fecha_str}.xlsx"

        # RN48: cada exportación queda registrada
        ReportesIaRepositorio.registrar_exportacion_en_solicitud(
            db, solicitud, formato=formato, usuario_email=usuario.email
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion=f"EXPORTAR_REPORTE_IA_{formato.upper()}",
            tabla_modulo="comercial.solicitudes_reporte_ia",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_solicitud": id_solicitud,
                "tipo_reporte": solicitud.tipo_reporte,
                "formato": formato,
                "resumen_kpis_bob": kpis,
            },
            db=db,
        )
        return contenido, media_type, nombre_archivo

