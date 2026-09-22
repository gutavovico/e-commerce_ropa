"""Servicio de dominio para CU30: Consultar bitacora.

Contiene la logica de autorizacion estricta, filtrado dinamico, agregacion de metricas
y consulta inmutable de la tabla de auditoria.
"""

from datetime import datetime, time, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import case, distinct, func, or_, select
from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.seguridad.cu30_bitacora.errores import (
    EventoBitacoraNoEncontradoError,
    PermisoDenegadoBitacoraError,
)
from modules.seguridad.cu30_bitacora.esquemas import (
    BitacoraEventoDetalle,
    BitacoraEventoResumen,
    BitacoraFiltrosParametros,
    BitacoraListadoRespuesta,
    BitacoraMetricas,
    RegistrarEventoBitacoraIn,
)
from modules.seguridad.cu30_bitacora.modelos import Bitacora


class ServicioBitacoraAuditoria:
    """Servicio de consulta y registro de eventos en la bitacora de auditoria."""

    ROLES_PERMITIDOS = {"administrador", "admin"}

    @classmethod
    def validar_permisos_administrador(cls, usuario_actual: Optional[UsuarioORM]) -> None:
        """Valida que el usuario activo sea superadministrador."""
        if not usuario_actual:
            raise PermisoDenegadoBitacoraError("anonimo")

        rol = str(getattr(usuario_actual, "rol", "") or "").lower().strip()
        if rol not in cls.ROLES_PERMITIDOS:
            raise PermisoDenegadoBitacoraError(rol)

    @classmethod
    def listar_eventos(
        cls,
        db: Session,
        filtros: BitacoraFiltrosParametros,
        usuario_actual: Optional[UsuarioORM],
    ) -> BitacoraListadoRespuesta:
        """Retorna eventos paginados con metricas cuantitativas de auditoria."""
        cls.validar_permisos_administrador(usuario_actual)

        # Construccion de clausulas WHERE comunes
        condiciones = []

        if filtros.fecha_inicio:
            inicio_utc = datetime.combine(filtros.fecha_inicio, time.min).replace(tzinfo=timezone.utc)
            condiciones.append(Bitacora.creado_en >= inicio_utc)

        if filtros.fecha_fin:
            fin_utc = datetime.combine(filtros.fecha_fin + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
            condiciones.append(Bitacora.creado_en < fin_utc)

        if filtros.severidad:
            condiciones.append(Bitacora.severidad == filtros.severidad)

        if filtros.tabla_modulo:
            condiciones.append(Bitacora.tabla_modulo.ilike(f"%{filtros.tabla_modulo.strip()}%"))

        if filtros.accion:
            condiciones.append(Bitacora.accion.ilike(f"%{filtros.accion.strip()}%"))

        if filtros.q:
            termino = f"%{filtros.q.strip()}%"
            condiciones.append(
                or_(
                    Bitacora.usuario_nombre.ilike(termino),
                    Bitacora.accion.ilike(termino),
                    Bitacora.tabla_modulo.ilike(termino),
                    Bitacora.direccion_ip.ilike(termino),
                )
            )

        # 1. Metricas consolidadas sobre el universo filtrado
        stmt_metricas = select(
            func.count(Bitacora.id_bitacora).label("total"),
            func.count(case((Bitacora.severidad == "CRITICAL", 1))).label("criticos"),
            func.count(case((Bitacora.severidad.in_(["WARN", "ERROR"]), 1))).label("advertencias"),
            func.count(distinct(Bitacora.id_usuario)).label("usuarios_activos"),
        )
        if condiciones:
            stmt_metricas = stmt_metricas.where(*condiciones)

        row_metricas = db.execute(stmt_metricas).first()
        total = row_metricas.total if row_metricas else 0
        criticos = row_metricas.criticos if row_metricas else 0
        advertencias = row_metricas.advertencias if row_metricas else 0
        usuarios_activos = row_metricas.usuarios_activos if row_metricas else 0

        metricas = BitacoraMetricas(
            total_eventos=total,
            eventos_criticos=criticos,
            advertencias_errores=advertencias,
            usuarios_activos=usuarios_activos,
        )

        if total == 0:
            return BitacoraListadoRespuesta(
                items=[],
                total=0,
                pagina=filtros.pagina,
                limite=filtros.limite,
                total_paginas=1,
                metricas=metricas,
            )

        # 2. Ordenacion dinamica
        orden_map = {
            "creado_en_desc": Bitacora.creado_en.desc(),
            "creado_en_asc": Bitacora.creado_en.asc(),
            "severidad_desc": Bitacora.severidad.desc(),
            "accion_asc": Bitacora.accion.asc(),
        }
        columna_orden = orden_map.get(filtros.ordenar_por, Bitacora.creado_en.desc())

        # 3. Paginacion
        offset = (filtros.pagina - 1) * filtros.limite
        total_paginas = max(1, (total + filtros.limite - 1) // filtros.limite)

        stmt_paginado = select(Bitacora)
        if condiciones:
            stmt_paginado = stmt_paginado.where(*condiciones)
        stmt_paginado = stmt_paginado.order_by(columna_orden).offset(offset).limit(filtros.limite)

        registros = db.execute(stmt_paginado).scalars().all()

        items = [
            BitacoraEventoResumen(
                id_bitacora=r.id_bitacora,
                id_usuario=r.id_usuario,
                usuario_nombre=r.usuario_nombre,
                accion=r.accion,
                tabla_modulo=r.tabla_modulo,
                direccion_ip=r.direccion_ip,
                severidad=r.severidad,
                tiene_payload=bool(r.payload_anterior or r.payload_nuevo),
                creado_en=r.creado_en,
            )
            for r in registros
        ]

        return BitacoraListadoRespuesta(
            items=items,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
            metricas=metricas,
        )

    @classmethod
    def obtener_evento_por_id(
        cls,
        db: Session,
        id_bitacora: int,
        usuario_actual: Optional[UsuarioORM],
    ) -> BitacoraEventoDetalle:
        """Recupera el detalle unitario de un evento de bitacora incluyendo payloads."""
        cls.validar_permisos_administrador(usuario_actual)

        stmt = select(Bitacora).where(Bitacora.id_bitacora == id_bitacora)
        registro = db.execute(stmt).scalar_one_or_none()

        if not registro:
            raise EventoBitacoraNoEncontradoError(id_bitacora)

        return BitacoraEventoDetalle(
            id_bitacora=registro.id_bitacora,
            id_usuario=registro.id_usuario,
            usuario_nombre=registro.usuario_nombre,
            accion=registro.accion,
            tabla_modulo=registro.tabla_modulo,
            direccion_ip=registro.direccion_ip,
            severidad=registro.severidad,
            tiene_payload=bool(registro.payload_anterior or registro.payload_nuevo),
            payload_anterior=registro.payload_anterior,
            payload_nuevo=registro.payload_nuevo,
            creado_en=registro.creado_en,
        )

    @classmethod
    def registrar_evento(
        cls,
        db: Session,
        datos: RegistrarEventoBitacoraIn,
    ) -> Bitacora:
        """Crea un nuevo registro inmutable en la bitacora de auditoria."""
        nuevo = Bitacora(
            id_usuario=datos.id_usuario,
            usuario_nombre=datos.usuario_nombre,
            accion=datos.accion,
            tabla_modulo=datos.tabla_modulo,
            direccion_ip=datos.direccion_ip,
            severidad=datos.severidad,
            payload_anterior=datos.payload_anterior,
            payload_nuevo=datos.payload_nuevo,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
