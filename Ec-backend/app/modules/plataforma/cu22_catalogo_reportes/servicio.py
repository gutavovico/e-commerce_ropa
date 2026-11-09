"""Servicio de aplicación y dominio para P2-CU22: Gestionar catálogo de reportes permitidos."""

from typing import Optional

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu22_catalogo_reportes.esquemas import (
    CatalogoReporteGuardarIn,
    CatalogoReporteOut,
    FILTROS_CATALOGO_PERMITIDOS,
    MetadatosCatalogoReportesOut,
    TIPOS_GRAFICO_PERMITIDOS,
    VISTAS_DATOS_PERMITIDAS,
)
from modules.plataforma.cu22_catalogo_reportes.repositorio import (
    CatalogoReportesRepositorio,
)
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class CatalogoReportesServicio:
    """Lógica de negocio de P2-CU22 para administrar el catálogo cerrado de reportes IA (RN45)."""

    @staticmethod
    def _validar_definicion(datos: CatalogoReporteGuardarIn) -> None:
        """Valida vista de origen (CU22 A1) y elementos del reporte (CU22 A2)."""
        vista = datos.vista_origen.strip()
        if vista not in VISTAS_DATOS_PERMITIDAS:
            raise UnprocessableEntityError(
                f"La vista de datos '{vista}' no está permitida (CU22 A1). "
                f"Vistas autorizadas: {', '.join(sorted(VISTAS_DATOS_PERMITIDAS))}.",
                code="VISTA_DATOS_NO_PERMITIDA",
            )

        for m in datos.metricas:
            if not m.expresion or not m.expresion.strip():
                raise UnprocessableEntityError(
                    f"La métrica '{m.codigo}' no tiene expresión definida (CU22 A2).",
                    code="ELEMENTO_REPORTE_INVALIDO",
                )

        for d in datos.dimensiones:
            if not d.expresion or not d.expresion.strip():
                raise UnprocessableEntityError(
                    f"La dimensión '{d.codigo}' no tiene expresión definida (CU22 A2).",
                    code="ELEMENTO_REPORTE_INVALIDO",
                )

        graficos_invalidos = [
            g for g in datos.tipos_grafico if g.strip().lower() not in TIPOS_GRAFICO_PERMITIDOS
        ]
        if graficos_invalidos:
            raise UnprocessableEntityError(
                f"Tipos de gráfico no permitidos: {', '.join(graficos_invalidos)} (CU22 A2). "
                f"Valores válidos: {', '.join(sorted(TIPOS_GRAFICO_PERMITIDOS))}.",
                code="ELEMENTO_REPORTE_INVALIDO",
            )

        filtros_invalidos = [
            f for f in datos.filtros_permitidos if f.strip().lower() not in FILTROS_CATALOGO_PERMITIDOS
        ]
        if filtros_invalidos:
            raise UnprocessableEntityError(
                f"Filtros no permitidos en el catálogo: {', '.join(filtros_invalidos)}.",
                code="ELEMENTO_REPORTE_INVALIDO",
            )

    @staticmethod
    def listar_catalogo(
        db: Session, *, solo_activos: bool = False
    ) -> MetadatosCatalogoReportesOut:
        items = CatalogoReportesRepositorio.listar(db, solo_activos=solo_activos)
        return MetadatosCatalogoReportesOut(
            vistas_permitidas=sorted(VISTAS_DATOS_PERMITIDAS),
            tipos_grafico_permitidos=sorted(TIPOS_GRAFICO_PERMITIDOS),
            filtros_permitidos=sorted(FILTROS_CATALOGO_PERMITIDOS),
            reportes=[CatalogoReporteOut.model_validate(i) for i in items],
        )

    @staticmethod
    def crear_reporte(
        db: Session,
        datos: CatalogoReporteGuardarIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> CatalogoReporteOut:
        CatalogoReportesServicio._validar_definicion(datos)

        codigo_norm = datos.codigo.strip().lower()
        existente = CatalogoReportesRepositorio.obtener_por_codigo(db, codigo_norm)
        if existente:
            raise ConflictError(
                f"Ya existe un reporte en el catálogo con el código '{codigo_norm}'.",
                code="REPORTE_CATALOGO_DUPLICADO",
            )

        payload = {
            "codigo": codigo_norm,
            "nombre": datos.nombre.strip(),
            "descripcion": datos.descripcion.strip() if datos.descripcion else None,
            "vista_origen": datos.vista_origen.strip(),
            "metricas": [m.model_dump() for m in datos.metricas],
            "dimensiones": [d.model_dump() for d in datos.dimensiones],
            "filtros_permitidos": [f.strip().lower() for f in datos.filtros_permitidos],
            "tipos_grafico": [g.strip().lower() for g in datos.tipos_grafico],
            "ejemplos_consulta": [e.strip() for e in datos.ejemplos_consulta if e.strip()],
            "activo": datos.activo,
        }
        creado = CatalogoReportesRepositorio.crear(db, payload)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="CREAR_REPORTE_CATALOGO_IA",
            tabla_modulo="plataforma.catalogo_reportes_ia",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo=payload,
            db=db,
        )
        return CatalogoReporteOut.model_validate(creado)

    @staticmethod
    def actualizar_reporte(
        db: Session,
        id_reporte: int,
        datos: CatalogoReporteGuardarIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> CatalogoReporteOut:
        item = CatalogoReportesRepositorio.obtener_por_id(db, id_reporte)
        if not item:
            raise NotFoundError(
                f"El reporte del catálogo #{id_reporte} no existe.",
                code="REPORTE_CATALOGO_NO_ENCONTRADO",
            )

        CatalogoReportesServicio._validar_definicion(datos)

        codigo_norm = datos.codigo.strip().lower()
        duplicado = CatalogoReportesRepositorio.obtener_por_codigo(db, codigo_norm)
        if duplicado and duplicado.id_reporte_catalogo != id_reporte:
            raise ConflictError(
                f"Ya existe otro reporte en el catálogo con el código '{codigo_norm}'.",
                code="REPORTE_CATALOGO_DUPLICADO",
            )

        payload = {
            "codigo": codigo_norm,
            "nombre": datos.nombre.strip(),
            "descripcion": datos.descripcion.strip() if datos.descripcion else None,
            "vista_origen": datos.vista_origen.strip(),
            "metricas": [m.model_dump() for m in datos.metricas],
            "dimensiones": [d.model_dump() for d in datos.dimensiones],
            "filtros_permitidos": [f.strip().lower() for f in datos.filtros_permitidos],
            "tipos_grafico": [g.strip().lower() for g in datos.tipos_grafico],
            "ejemplos_consulta": [e.strip() for e in datos.ejemplos_consulta if e.strip()],
            "activo": datos.activo,
        }
        actualizado = CatalogoReportesRepositorio.actualizar(db, item, payload)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTUALIZAR_REPORTE_CATALOGO_IA",
            tabla_modulo="plataforma.catalogo_reportes_ia",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={"id_reporte_catalogo": id_reporte, **payload},
            db=db,
        )
        return CatalogoReporteOut.model_validate(actualizado)

    @staticmethod
    def cambiar_estado_reporte(
        db: Session,
        id_reporte: int,
        activo: bool,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> CatalogoReporteOut:
        """Activa o desactiva un reporte del catálogo (CU22 A3: conserva solicitudes anteriores)."""
        item = CatalogoReportesRepositorio.obtener_por_id(db, id_reporte)
        if not item:
            raise NotFoundError(
                f"El reporte del catálogo #{id_reporte} no existe.",
                code="REPORTE_CATALOGO_NO_ENCONTRADO",
            )
        actualizado = CatalogoReportesRepositorio.cambiar_estado(db, item, activo)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ESTADO_REPORTE_CATALOGO_IA",
            tabla_modulo="plataforma.catalogo_reportes_ia",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo={
                "id_reporte_catalogo": id_reporte,
                "codigo": actualizado.codigo,
                "activo": activo,
            },
            db=db,
        )
        return CatalogoReporteOut.model_validate(actualizado)

