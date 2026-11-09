"""Servicio de dominio para el caso de uso CU21: Gestionar Sucursales y Ciudades.

Encapsula la logica de negocio, invariantes y proteccion de integridad
relacional para la infraestructura fisica de FashionStore.

P2-CU04 (`.specs/finalized/P2-CU03-CU04-usuarios-sucursales/spec.md`):
- B6: el administrador solo consulta las ciudades (catálogo global de P2-CU08).
- B7: uso del límite de sucursales del plan.
- B9: altas, cambios, activaciones y bajas de sucursales en la bitácora.
- P2-CU03 B5: sucursales en las que opera el empleado de la sesión.
"""

from datetime import time
from typing import Any, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from modules.gestion_operativa.cu21_sucursales_ciudades.errores import (
    CiudadNoEncontradaError,
    HorarioSucursalInvalidoError,
    SucursalConOperacionesPendientesError,
    SucursalDuplicadaError,
    SucursalNoEncontradaError,
)
from modules.gestion_operativa.cu21_sucursales_ciudades.esquemas import (
    CiudadOut,
    MiSucursalOut,
    SucursalActualizarIn,
    SucursalAdminOut,
    SucursalCrearIn,
    SucursalPublicaOut,
    UsoPlanSucursalesOut,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


def _resumen(suc: SucursalORM) -> dict:
    return {
        "id_sucursal": suc.id_sucursal,
        "nombre": suc.nombre,
        "id_ciudad": suc.id_ciudad,
        "activa": suc.activa,
    }


class ServicioGestionSucursal:
    """Servicio de negocio para administrar ciudades y sucursales fisicas."""

    def __init__(self, db: Session, actor: Optional[Any] = None, ip: Optional[str] = None):
        self.db = db
        self.actor = actor
        self.ip = ip

    def _registrar(self, accion: str, **payloads) -> None:
        """B9: evento de bitácora tras confirmar la operación."""
        actor = self.actor
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=getattr(actor, "id_usuario", None),
            usuario_nombre=(f"{actor.nombres} {actor.apellidos}".strip() or actor.email) if actor else None,
            accion=accion,
            tabla_modulo="sucursales",
            direccion_ip=self.ip,
            severidad="INFO",
            db=self.db,
            **payloads,
        )

    # -------------------------------------------------------------------------
    # OPERACIONES SOBRE CIUDADES
    # -------------------------------------------------------------------------

    def listar_ciudades(self) -> List[CiudadOut]:
        """Consulta el catalogo de ciudades con conteo de boutiques asociadas."""
        stmt = (
            select(
                CiudadORM,
                func.count(SucursalORM.id_sucursal).label("total_sucursales"),
            )
            .outerjoin(SucursalORM, SucursalORM.id_ciudad == CiudadORM.id_ciudad)
            .group_by(CiudadORM.id_ciudad)
            .order_by(CiudadORM.nombre.asc())
        )
        resultados = self.db.execute(stmt).all()

        salida = []
        for ciudad_orm, total_sucursales in resultados:
            salida.append(
                CiudadOut(
                    id_ciudad=ciudad_orm.id_ciudad,
                    nombre=ciudad_orm.nombre,
                    pais=ciudad_orm.pais,
                    creado_en=ciudad_orm.creado_en,
                    total_sucursales=total_sucursales or 0,
                )
            )
        return salida

    # -------------------------------------------------------------------------
    # OPERACIONES SOBRE SUCURSALES
    # -------------------------------------------------------------------------

    def crear_sucursal(self, datos: SucursalCrearIn) -> SucursalAdminOut:
        """Crea una nueva sucursal verificando ciudad, unicidad y franja horaria."""
        # P2-CU12 (RN15): la sucursal nace activa, así que cuenta para el límite del plan
        SuscripcionServicio.validar(self.db, recurso="sucursales")
        # 1. Verificar existencia de ciudad
        ciudad = self.db.get(CiudadORM, datos.id_ciudad)
        if not ciudad:
            raise CiudadNoEncontradaError(datos.id_ciudad)

        # 2. Verificar unicidad compuesta (id_ciudad, nombre)
        stmt_dup = select(SucursalORM).where(
            SucursalORM.id_ciudad == datos.id_ciudad,
            func.lower(SucursalORM.nombre) == func.lower(datos.nombre),
        )
        if self.db.execute(stmt_dup).scalar_one_or_none():
            raise SucursalDuplicadaError(datos.nombre, datos.id_ciudad)

        # 3. Validar horario
        if datos.horario_cierre <= datos.horario_apertura:
            raise HorarioSucursalInvalidoError()

        nueva_sucursal = SucursalORM(
            id_ciudad=datos.id_ciudad,
            nombre=datos.nombre,
            direccion=datos.direccion,
            telefono=datos.telefono,
            horario_apertura=datos.horario_apertura,
            horario_cierre=datos.horario_cierre,
            activa=True,
        )
        self.db.add(nueva_sucursal)
        self.db.commit()
        self.db.refresh(nueva_sucursal)
        self._registrar("SUCURSAL_CREADA", payload_nuevo=_resumen(nueva_sucursal))

        return self._construir_sucursal_admin_out(nueva_sucursal, ciudad.nombre)

    def listar_sucursales_publicas(
        self, id_ciudad: Optional[int] = None
    ) -> List[SucursalPublicaOut]:
        """Consulta publica de boutiques operativas y activas."""
        stmt = (
            select(SucursalORM, CiudadORM.nombre.label("ciudad_nombre"))
            .join(CiudadORM, CiudadORM.id_ciudad == SucursalORM.id_ciudad)
            .where(SucursalORM.activa.is_(True))
        )
        if id_ciudad:
            stmt = stmt.where(SucursalORM.id_ciudad == id_ciudad)

        stmt = stmt.order_by(CiudadORM.nombre.asc(), SucursalORM.nombre.asc())
        filas = self.db.execute(stmt).all()

        salida = []
        for suc, ciudad_nombre in filas:
            salida.append(
                SucursalPublicaOut(
                    id_sucursal=suc.id_sucursal,
                    id_ciudad=suc.id_ciudad,
                    ciudad_nombre=ciudad_nombre,
                    nombre=suc.nombre,
                    direccion=suc.direccion,
                    telefono=suc.telefono,
                    horario_apertura=suc.horario_apertura.strftime("%H:%M"),
                    horario_cierre=suc.horario_cierre.strftime("%H:%M"),
                )
            )
        return salida

    def listar_sucursales_admin(
        self,
        id_ciudad: Optional[int] = None,
        activa: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> List[SucursalAdminOut]:
        """Consulta administrativa consolidada con metricas de personal e inventario."""
        stmt = select(SucursalORM, CiudadORM.nombre.label("ciudad_nombre")).join(
            CiudadORM, CiudadORM.id_ciudad == SucursalORM.id_ciudad
        )

        if id_ciudad is not None:
            stmt = stmt.where(SucursalORM.id_ciudad == id_ciudad)
        if activa is not None:
            stmt = stmt.where(SucursalORM.activa.is_(activa))
        if q:
            patron = f"%{q.strip().lower()}%"
            stmt = stmt.where(
                (func.lower(SucursalORM.nombre).like(patron))
                | (func.lower(SucursalORM.direccion).like(patron))
                | (func.lower(CiudadORM.nombre).like(patron))
            )

        stmt = stmt.order_by(SucursalORM.id_sucursal.desc())
        filas = self.db.execute(stmt).all()

        salida = []
        for suc, ciudad_nombre in filas:
            salida.append(self._construir_sucursal_admin_out(suc, ciudad_nombre))
        return salida

    def obtener_sucursal(self, id_sucursal: int) -> SucursalAdminOut:
        """Obtiene la ficha técnica completa de una sucursal."""
        stmt = (
            select(SucursalORM, CiudadORM.nombre.label("ciudad_nombre"))
            .join(CiudadORM, CiudadORM.id_ciudad == SucursalORM.id_ciudad)
            .where(SucursalORM.id_sucursal == id_sucursal)
        )
        fila = self.db.execute(stmt).first()
        if not fila:
            raise SucursalNoEncontradaError(id_sucursal)

        suc, ciudad_nombre = fila
        return self._construir_sucursal_admin_out(suc, ciudad_nombre)

    def actualizar_sucursal(
        self, id_sucursal: int, datos: SucursalActualizarIn
    ) -> SucursalAdminOut:
        """Actualiza la direccion, nombre, horarios o ciudad de una sucursal."""
        sucursal = self.db.get(SucursalORM, id_sucursal)
        if not sucursal:
            raise SucursalNoEncontradaError(id_sucursal)
        anterior = _resumen(sucursal)

        nueva_ciudad_id = datos.id_ciudad or sucursal.id_ciudad
        if datos.id_ciudad and datos.id_ciudad != sucursal.id_ciudad:
            ciudad_nueva = self.db.get(CiudadORM, datos.id_ciudad)
            if not ciudad_nueva:
                raise CiudadNoEncontradaError(datos.id_ciudad)
            sucursal.id_ciudad = datos.id_ciudad

        nuevo_nombre = datos.nombre or sucursal.nombre
        if (datos.nombre and datos.nombre.lower() != sucursal.nombre.lower()) or (
            datos.id_ciudad and datos.id_ciudad != sucursal.id_ciudad
        ):
            stmt_dup = select(SucursalORM).where(
                SucursalORM.id_ciudad == nueva_ciudad_id,
                func.lower(SucursalORM.nombre) == func.lower(nuevo_nombre),
                SucursalORM.id_sucursal != id_sucursal,
            )
            if self.db.execute(stmt_dup).scalar_one_or_none():
                raise SucursalDuplicadaError(nuevo_nombre, nueva_ciudad_id)
            sucursal.nombre = nuevo_nombre

        if datos.direccion:
            sucursal.direccion = datos.direccion
        if datos.telefono is not None:
            sucursal.telefono = datos.telefono

        nueva_apertura = datos.horario_apertura or sucursal.horario_apertura
        nuevo_cierre = datos.horario_cierre or sucursal.horario_cierre
        if nuevo_cierre <= nueva_apertura:
            raise HorarioSucursalInvalidoError()

        sucursal.horario_apertura = nueva_apertura
        sucursal.horario_cierre = nuevo_cierre

        self.db.commit()
        self.db.refresh(sucursal)
        self._registrar("SUCURSAL_MODIFICADA", payload_anterior=anterior, payload_nuevo=_resumen(sucursal))

        ciudad_actual = self.db.get(CiudadORM, sucursal.id_ciudad)
        ciudad_nombre = ciudad_actual.nombre if ciudad_actual else ""
        return self._construir_sucursal_admin_out(sucursal, ciudad_nombre)

    def cambiar_estado_sucursal(
        self, id_sucursal: int, activa: bool
    ) -> SucursalAdminOut:
        """Activa o desactiva la boutique fisica protegiendo reservas y stock activo."""
        sucursal = self.db.get(SucursalORM, id_sucursal)
        if not sucursal:
            raise SucursalNoEncontradaError(id_sucursal)

        # P2-CU12 (RN15): reactivar una sucursal cuenta para el límite del plan
        if activa and not sucursal.activa:
            SuscripcionServicio.validar(self.db, recurso="sucursales")

        # Si se pretende desactivar y estaba activa, verificar operaciones pendientes
        if not activa and sucursal.activa:
            # 1. Reservas activas pendientes
            reservas_pendientes = (
                self.db.execute(
                    text(
                        "SELECT COUNT(*) FROM fashionstore.reservas "
                        "WHERE id_sucursal = :id_sucursal "
                        "AND estado IN ('pendiente', 'confirmada', 'en_atencion')"
                    ),
                    {"id_sucursal": id_sucursal},
                ).scalar()
                or 0
            )
            if reservas_pendientes > 0:
                raise SucursalConOperacionesPendientesError(
                    id_sucursal,
                    f"mantiene {reservas_pendientes} reserva(s) pendiente(s) de atencion fisica",
                )

            # 2. Stock fisico disponible
            stock_disponible = (
                self.db.execute(
                    text(
                        "SELECT COALESCE(SUM(cantidad_disponible), 0) "
                        "FROM fashionstore.inventario_sucursal "
                        "WHERE id_sucursal = :id_sucursal"
                    ),
                    {"id_sucursal": id_sucursal},
                ).scalar()
                or 0
            )
            if stock_disponible > 0:
                raise SucursalConOperacionesPendientesError(
                    id_sucursal,
                    f"mantiene {stock_disponible} prendas con inventario disponible en custodia",
                )

        anterior = sucursal.activa
        sucursal.activa = activa
        self.db.commit()
        self.db.refresh(sucursal)
        if anterior != activa:
            self._registrar(
                "SUCURSAL_ACTIVADA" if activa else "SUCURSAL_DESACTIVADA", payload_nuevo=_resumen(sucursal)
            )

        ciudad = self.db.get(CiudadORM, sucursal.id_ciudad)
        ciudad_nombre = ciudad.nombre if ciudad else ""
        return self._construir_sucursal_admin_out(sucursal, ciudad_nombre)

    def eliminar_sucursal(self, id_sucursal: int) -> None:
        """Elimina fisicamente una sucursal si nunca registro operaciones historicas."""
        sucursal = self.db.get(SucursalORM, id_sucursal)
        if not sucursal:
            raise SucursalNoEncontradaError(id_sucursal)

        # 1. Comprobar ventas historicas
        ventas_cnt = (
            self.db.execute(
                text("SELECT COUNT(*) FROM fashionstore.ventas WHERE id_sucursal = :id"),
                {"id": id_sucursal},
            ).scalar()
            or 0
        )
        if ventas_cnt > 0:
            raise SucursalConOperacionesPendientesError(
                id_sucursal,
                "cuenta con historial de ventas presenciales registradas. Debe desactivarse mediante baja logica.",
            )

        # 2. Comprobar reservas
        reservas_cnt = (
            self.db.execute(
                text("SELECT COUNT(*) FROM fashionstore.reservas WHERE id_sucursal = :id"),
                {"id": id_sucursal},
            ).scalar()
            or 0
        )
        if reservas_cnt > 0:
            raise SucursalConOperacionesPendientesError(
                id_sucursal,
                "cuenta con historial de reservas registrado. Debe desactivarse mediante baja logica.",
            )

        # 3. Comprobar inventario
        inv_cnt = (
            self.db.execute(
                text("SELECT COUNT(*) FROM fashionstore.inventario_sucursal WHERE id_sucursal = :id"),
                {"id": id_sucursal},
            ).scalar()
            or 0
        )
        if inv_cnt > 0:
            raise SucursalConOperacionesPendientesError(
                id_sucursal,
                "cuenta con registros de inventario vinculados. Debe desactivarse mediante baja logica.",
            )

        # 4. Comprobar empleados asignados
        emp_cnt = (
            self.db.execute(
                text("SELECT COUNT(*) FROM fashionstore.usuarios WHERE id_sucursal = :id"),
                {"id": id_sucursal},
            ).scalar()
            or 0
        )
        if emp_cnt > 0:
            raise SucursalConOperacionesPendientesError(
                id_sucursal,
                f"tiene {emp_cnt} empleado(s) actualmente asignado(s). Reubique al personal antes de eliminar.",
            )

        resumen = _resumen(sucursal)
        self.db.delete(sucursal)
        self.db.commit()
        self._registrar("SUCURSAL_ELIMINADA", payload_anterior=resumen)

    def uso_plan(self) -> UsoPlanSucursalesOut:
        """B7: sucursales activas frente al límite del plan vigente."""
        uso = SuscripcionServicio.uso(self.db, "sucursales")
        if uso is None:
            activas = self.db.execute(
                select(func.count(SucursalORM.id_sucursal)).where(SucursalORM.activa.is_(True))
            ).scalar() or 0
            return UsoPlanSucursalesOut(uso=int(activas))
        return UsoPlanSucursalesOut(**uso)

    def mis_sucursales(self, usuario: Any) -> List[MiSucursalOut]:
        """P2-CU03 B5: activas y autorizadas para el empleado (todas para el administrador), con la
        principal primero."""
        stmt = (
            select(SucursalORM, CiudadORM.nombre.label("ciudad_nombre"))
            .join(CiudadORM, CiudadORM.id_ciudad == SucursalORM.id_ciudad)
            .where(SucursalORM.activa.is_(True))
        )
        autorizadas = SucursalesEmpleadoServicio.autorizadas(usuario)
        if autorizadas is not None:
            if not autorizadas:
                return []
            stmt = stmt.where(SucursalORM.id_sucursal.in_(sorted(autorizadas)))
        principal = getattr(usuario, "id_sucursal", None)
        salida = [
            MiSucursalOut(
                id_sucursal=suc.id_sucursal,
                nombre=suc.nombre,
                ciudad=ciudad_nombre,
                es_principal=suc.id_sucursal == principal,
            )
            for suc, ciudad_nombre in self.db.execute(stmt.order_by(SucursalORM.nombre.asc())).all()
        ]
        return sorted(salida, key=lambda s: not s.es_principal)

    # -------------------------------------------------------------------------
    # METODOS AUXILIARES DE AGREGACION
    # -------------------------------------------------------------------------

    def _construir_sucursal_admin_out(
        self, suc: SucursalORM, ciudad_nombre: str
    ) -> SucursalAdminOut:
        """Calcula estadisticas auxiliares para la visualizacion administrativa."""
        # Total empleados autorizados en la sucursal (principal o adicional, P2-CU03 B3)
        total_empleados = (
            self.db.execute(
                text(
                    "SELECT COUNT(*) FROM fashionstore.usuarios u WHERE u.activo AND u.id_tenant IS NOT NULL "
                    "AND (u.id_sucursal = :id OR EXISTS (SELECT 1 FROM fashionstore.empleado_sucursal es "
                    "WHERE es.id_empleado = u.id_usuario AND es.id_sucursal = :id))"
                ),
                {"id": suc.id_sucursal},
            ).scalar()
            or 0
        )

        # Total prendas stock disponible
        total_prendas_stock = (
            self.db.execute(
                text(
                    "SELECT COALESCE(SUM(cantidad_disponible), 0) "
                    "FROM fashionstore.inventario_sucursal WHERE id_sucursal = :id"
                ),
                {"id": suc.id_sucursal},
            ).scalar()
            or 0
        )

        # Reservas activas
        reservas_activas = (
            self.db.execute(
                text(
                    "SELECT COUNT(*) FROM fashionstore.reservas "
                    "WHERE id_sucursal = :id AND estado IN ('pendiente', 'confirmada', 'en_atencion')"
                ),
                {"id": suc.id_sucursal},
            ).scalar()
            or 0
        )

        return SucursalAdminOut(
            id_sucursal=suc.id_sucursal,
            id_ciudad=suc.id_ciudad,
            ciudad_nombre=ciudad_nombre,
            nombre=suc.nombre,
            direccion=suc.direccion,
            telefono=suc.telefono,
            horario_apertura=suc.horario_apertura.strftime("%H:%M"),
            horario_cierre=suc.horario_cierre.strftime("%H:%M"),
            activa=suc.activa,
            creado_en=suc.creado_en,
            total_empleados=total_empleados,
            total_prendas_stock=total_prendas_stock,
            reservas_activas_conteo=reservas_activas,
        )
