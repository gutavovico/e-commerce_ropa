"""Servicio de dominio para el caso de uso CU21: Gestionar Sucursales y Ciudades.

Encapsula la logica de negocio, invariantes y proteccion de integridad
relacional para la infraestructura fisica de FashionStore.
"""

from datetime import time
from typing import List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from modules.gestion_operativa.cu21_sucursales_ciudades.errores import (
    CiudadConDependenciasError,
    CiudadDuplicadaError,
    CiudadNoEncontradaError,
    HorarioSucursalInvalidoError,
    SucursalConOperacionesPendientesError,
    SucursalDuplicadaError,
    SucursalNoEncontradaError,
)
from modules.gestion_operativa.cu21_sucursales_ciudades.esquemas import (
    CiudadActualizarIn,
    CiudadCrearIn,
    CiudadOut,
    SucursalActualizarIn,
    SucursalAdminOut,
    SucursalCrearIn,
    SucursalPublicaOut,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM


class ServicioGestionSucursal:
    """Servicio de negocio para administrar ciudades y sucursales fisicas."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # OPERACIONES SOBRE CIUDADES
    # -------------------------------------------------------------------------

    def crear_ciudad(self, datos: CiudadCrearIn) -> CiudadOut:
        """Registra una nueva ciudad previa verificacion de unicidad."""
        stmt_existente = select(CiudadORM).where(
            func.lower(CiudadORM.nombre) == func.lower(datos.nombre)
        )
        if self.db.execute(stmt_existente).scalar_one_or_none():
            raise CiudadDuplicadaError(datos.nombre)

        nueva_ciudad = CiudadORM(
            nombre=datos.nombre,
            pais=datos.pais,
        )
        self.db.add(nueva_ciudad)
        self.db.commit()
        self.db.refresh(nueva_ciudad)

        return CiudadOut(
            id_ciudad=nueva_ciudad.id_ciudad,
            nombre=nueva_ciudad.nombre,
            pais=nueva_ciudad.pais,
            creado_en=nueva_ciudad.creado_en,
            total_sucursales=0,
        )

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

    def actualizar_ciudad(self, id_ciudad: int, datos: CiudadActualizarIn) -> CiudadOut:
        """Actualiza el nombre o pais de una ciudad registrada."""
        ciudad = self.db.get(CiudadORM, id_ciudad)
        if not ciudad:
            raise CiudadNoEncontradaError(id_ciudad)

        if datos.nombre and datos.nombre.lower() != ciudad.nombre.lower():
            stmt_dup = select(CiudadORM).where(
                func.lower(CiudadORM.nombre) == func.lower(datos.nombre),
                CiudadORM.id_ciudad != id_ciudad,
            )
            if self.db.execute(stmt_dup).scalar_one_or_none():
                raise CiudadDuplicadaError(datos.nombre)
            ciudad.nombre = datos.nombre

        if datos.pais:
            ciudad.pais = datos.pais

        self.db.commit()
        self.db.refresh(ciudad)

        conteo_stmt = select(func.count(SucursalORM.id_sucursal)).where(
            SucursalORM.id_ciudad == id_ciudad
        )
        total_suc = self.db.execute(conteo_stmt).scalar() or 0

        return CiudadOut(
            id_ciudad=ciudad.id_ciudad,
            nombre=ciudad.nombre,
            pais=ciudad.pais,
            creado_en=ciudad.creado_en,
            total_sucursales=total_suc,
        )

    def eliminar_ciudad(self, id_ciudad: int) -> None:
        """Elimina una ciudad si no cuenta con sucursales o clientes asignados."""
        ciudad = self.db.get(CiudadORM, id_ciudad)
        if not ciudad:
            raise CiudadNoEncontradaError(id_ciudad)

        # 1. Verificar sucursales asignadas
        conteo_sucursales = (
            self.db.execute(
                select(func.count(SucursalORM.id_sucursal)).where(
                    SucursalORM.id_ciudad == id_ciudad
                )
            ).scalar()
            or 0
        )
        if conteo_sucursales > 0:
            raise CiudadConDependenciasError(
                id_ciudad,
                f"la ciudad tiene {conteo_sucursales} sucursal(es) asociada(s)",
            )

        # 2. Verificar clientes con ciudad preferida
        conteo_clientes = (
            self.db.execute(
                text(
                    "SELECT COUNT(*) FROM fashionstore.clientes WHERE ciudad_preferida = :id_ciudad"
                ),
                {"id_ciudad": id_ciudad},
            ).scalar()
            or 0
        )
        if conteo_clientes > 0:
            raise CiudadConDependenciasError(
                id_ciudad,
                f"existen {conteo_clientes} cliente(s) con esta ciudad asignada como preferida",
            )

        self.db.delete(ciudad)
        self.db.commit()

    # -------------------------------------------------------------------------
    # OPERACIONES SOBRE SUCURSALES
    # -------------------------------------------------------------------------

    def crear_sucursal(self, datos: SucursalCrearIn) -> SucursalAdminOut:
        """Crea una nueva sucursal verificando ciudad, unicidad y franja horaria."""
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

        sucursal.activa = activa
        self.db.commit()
        self.db.refresh(sucursal)

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

        self.db.delete(sucursal)
        self.db.commit()

    # -------------------------------------------------------------------------
    # METODOS AUXILIARES DE AGREGACION
    # -------------------------------------------------------------------------

    def _construir_sucursal_admin_out(
        self, suc: SucursalORM, ciudad_nombre: str
    ) -> SucursalAdminOut:
        """Calcula estadisticas auxiliares para la visualizacion administrativa."""
        # Total empleados
        total_empleados = (
            self.db.execute(
                text(
                    "SELECT COUNT(*) FROM fashionstore.usuarios WHERE id_sucursal = :id AND activo = true"
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
