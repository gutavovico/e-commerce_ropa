"""Servicio de aplicacion y logica de dominio para CU20: Gestionar Usuarios y Roles (RBAC).

P2-CU03 (`.specs/finalized/P2-CU03-CU04-usuarios-sucursales/spec.md`):
- B1: el administrador solo ve y modifica a los **empleados de su empresa**. La RLS de `usuarios`
  deja ver a toda cuenta sin empresa (clientes y super administrador, necesario para el login), así
  que el alcance se impone aquí; cualquier otra cuenta responde 404.
- B2: solo se asignan roles de empleado.
- B3: encargado y cajero tienen varias sucursales autorizadas y una principal (`usuarios.id_sucursal`).
- B8: reactivar un empleado respeta el límite de empleados del plan.
- B9: cada cambio queda en la bitácora (sin contraseñas).
"""

from datetime import datetime, timezone
import math
from typing import Any, Iterable, Optional

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from core.security import hash_password
from core.tenant import tenant_actual
from modules.autenticacion_seguridad.cuentas import correo_ocupado
from modules.autenticacion_seguridad.cu20_usuarios_roles.errores import (
    AutoModificacionBloqueadaError,
    EmailDuplicadoError,
    RolNoPermitidoError,
    SucursalInvalidaError,
    SucursalPrincipalInvalidaError,
    SucursalRequeridaError,
    UltimoAdministradorError,
    UsuarioConDependenciasError,
    UsuarioNoEncontradoError,
)
from modules.autenticacion_seguridad.cu20_usuarios_roles.esquemas import (
    ROLES_CON_SUCURSALES,
    ListaPaginadaUsuariosOut,
    ResetPasswordIn,
    RolUsuarioEnum,
    SucursalAutorizadaOut,
    UsuarioActualizarIn,
    UsuarioCrearIn,
    UsuarioDetalleOut,
    UsuarioEstadoIn,
    UsuarioResumenOut,
)
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.gestion_operativa.modelos import SucursalORM
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio
from modules.plataforma.servicio_tenants import TenantServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


#: Roles de personal: su usuario debe tener ficha en `fashionstore.empleados`, porque
#: `ventas.id_cajero` la referencia (CU31-CU32, decisión D3).
CARGOS_PERSONAL = {
    "administrador": "Administrador",
    "encargado_sucursal": "Encargado de Sucursal",
    "cajero": "Cajero",
}

#: P2-CU03 B1/B2: los únicos roles que gestiona el administrador de una empresa.
ROLES_GESTIONABLES = tuple(CARGOS_PERSONAL)
ROLES_OPERATIVOS = tuple(r.value for r in ROLES_CON_SUCURSALES)


def asegurar_ficha_empleado(db: Session, id_usuario: int, rol: str) -> None:
    """Crea la ficha de empleado de un usuario de personal si no existe (idempotente).

    Se usa SQL directo, igual que la comprobación de nómina de `eliminar_usuario`, para no
    depender del modelo `EmpleadoORM` de otro paquete. No toca la transacción: la confirma
    quien llama.
    """
    cargo = CARGOS_PERSONAL.get(rol)
    if cargo is None:
        return
    db.execute(
        text(
            "INSERT INTO fashionstore.empleados (id_empleado, codigo_empleado, cargo) "
            "VALUES (:uid, :codigo, :cargo) ON CONFLICT (id_empleado) DO NOTHING"
        ),
        {"uid": id_usuario, "codigo": f"EMP-{id_usuario}", "cargo": cargo},
    )


def _rol(valor: Any) -> str:
    return str(getattr(valor, "value", valor))


def _alcance(stmt, db: Session):
    """B1: empleados de la empresa de la sesión (nunca clientes ni el super administrador)."""
    stmt = stmt.where(UsuarioORM.rol.in_(ROLES_GESTIONABLES), UsuarioORM.id_tenant.is_not(None))
    empresa = tenant_actual(db)
    if empresa is not None:
        stmt = stmt.where(UsuarioORM.id_tenant == empresa)
    return stmt


def _es_gestionable(usuario: UsuarioORM) -> bool:
    """Defensa adicional a `_alcance` sobre el objeto ya cargado."""
    return _rol(usuario.rol) in ROLES_GESTIONABLES and usuario.id_tenant is not None


def _nombres_sucursales(db: Session, ids: Iterable[int]) -> dict[int, str]:
    ids = sorted(set(ids))
    if not ids:
        return {}
    filas = db.execute(
        select(SucursalORM.id_sucursal, SucursalORM.nombre).where(SucursalORM.id_sucursal.in_(ids))
    ).all()
    try:
        return {int(fila[0]): fila[1] for fila in filas}
    except (TypeError, ValueError, IndexError):  # sesión simulada
        return {}


def _autorizadas_out(db: Session, usuario: UsuarioORM) -> list[SucursalAutorizadaOut]:
    """Sucursales autorizadas del empleado; con una sesión simulada, solo la principal."""
    if _rol(usuario.rol) not in ROLES_OPERATIVOS:
        return []
    pares = SucursalesEmpleadoServicio.de_empleado(db, usuario.id_usuario)
    if not pares:
        if not usuario.id_sucursal:
            return []
        nombre = usuario.sucursal.nombre if usuario.sucursal else None
        return [SucursalAutorizadaOut(id_sucursal=usuario.id_sucursal, nombre=nombre, es_principal=True)]
    nombres = _nombres_sucursales(db, [p[0] for p in pares])
    return [
        SucursalAutorizadaOut(id_sucursal=id_suc, nombre=nombres.get(id_suc), es_principal=principal)
        for id_suc, principal in pares
    ]


def _to_usuario_out(db: Session, usuario: UsuarioORM, out_cls=UsuarioDetalleOut):
    """Mapea una entidad UsuarioORM a su respectivo DTO enriquecido."""
    sucursal_nombre = usuario.sucursal.nombre if usuario.sucursal else None
    sucursal_ciudad = (
        usuario.sucursal.ciudad.nombre
        if usuario.sucursal and getattr(usuario.sucursal, "ciudad", None)
        else None
    )
    nombre_completo = f"{usuario.nombres} {usuario.apellidos}".strip()
    id_usuario = usuario.id_usuario if usuario.id_usuario is not None else 1
    fecha_reg = (
        usuario.fecha_registro
        if usuario.fecha_registro is not None
        else datetime.now(timezone.utc)
    )
    return out_cls(
        id_usuario=id_usuario,
        email=usuario.email,
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        nombre_completo=nombre_completo,
        telefono=usuario.telefono,
        rol=_rol(usuario.rol),
        id_sucursal=usuario.id_sucursal,
        sucursal_nombre=sucursal_nombre,
        sucursal_ciudad=sucursal_ciudad,
        sucursales_autorizadas=_autorizadas_out(db, usuario),
        activo=usuario.activo,
        fecha_registro=fecha_reg,
        ultimo_acceso=usuario.ultimo_acceso,
    )


def _resumen_bitacora(usuario: UsuarioORM, sucursales: Optional[list[int]] = None) -> dict:
    datos = {
        "id_usuario": usuario.id_usuario,
        "email": usuario.email,
        "rol": _rol(usuario.rol),
        "activo": usuario.activo,
        "id_sucursal_principal": usuario.id_sucursal,
    }
    if sucursales is not None:
        datos["sucursales_autorizadas"] = sucursales
    return datos


def _registrar(db: Session, actor: Optional[UsuarioORM], accion: str, ip: Optional[str], **payloads) -> None:
    """B9: evento de bitácora tras confirmar la operación (nunca incluye contraseñas)."""
    ServicioBitacoraAuditoria.registrar_evento_seguro(
        id_usuario=getattr(actor, "id_usuario", None),
        usuario_nombre=(f"{actor.nombres} {actor.apellidos}".strip() or actor.email) if actor else None,
        accion=accion,
        tabla_modulo="usuarios",
        direccion_ip=ip,
        severidad="INFO",
        db=db,
        **payloads,
    )


class ServicioGestionUsuarios:
    """Orquesta las operaciones administrativas de usuarios y privilegios RBAC."""

    # ------------------------------------------------------------------
    # Apoyo
    # ------------------------------------------------------------------

    @staticmethod
    def _cargar(db: Session, id_usuario: int) -> UsuarioORM:
        stmt = _alcance(
            select(UsuarioORM)
            .options(joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad))
            .where(UsuarioORM.id_usuario == id_usuario),
            db,
        )
        usuario = db.scalars(stmt).unique().first()
        if not usuario or not _es_gestionable(usuario):
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")
        return usuario

    @staticmethod
    def _validar_sucursales(db: Session, ids: list[int], principal: Optional[int]) -> None:
        """B3: al menos una, todas activas y visibles (la RLS oculta las de otra empresa), y la
        principal entre ellas."""
        if not ids:
            raise SucursalRequeridaError("El rol requiere al menos una sucursal autorizada.")
        for id_sucursal in ids:
            suc = db.scalar(select(SucursalORM).where(SucursalORM.id_sucursal == id_sucursal))
            if not suc or not suc.activa:
                raise SucursalInvalidaError(
                    f"La sucursal {id_sucursal} no existe o se encuentra inactiva."
                )
        if principal is None or principal not in ids:
            raise SucursalPrincipalInvalidaError()

    @staticmethod
    def _otros_admins_activos(db: Session, id_usuario: int) -> int:
        return db.scalar(
            _alcance(
                select(func.count(UsuarioORM.id_usuario)).where(
                    UsuarioORM.rol == "administrador",
                    UsuarioORM.activo.is_(True),
                    UsuarioORM.id_usuario != id_usuario,
                ),
                db,
            )
        ) or 0

    # ------------------------------------------------------------------
    # Casos de uso
    # ------------------------------------------------------------------

    def crear_usuario(
        self,
        db: Session,
        datos: UsuarioCrearIn,
        actor: Optional[UsuarioORM] = None,
        ip: Optional[str] = None,
    ) -> UsuarioDetalleOut:
        """Crea una cuenta de empleado de la empresa del administrador (P2-CU02 A9)."""
        if datos.rol.value not in ROLES_GESTIONABLES:
            raise RolNoPermitidoError()
        email_norm = datos.email.strip().lower()
        id_tenant = TenantServicio.empresa_para_rol(db, datos.rol)

        # 1. Correo único en toda la plataforma (RN05, P2-CU02 A2)
        if correo_ocupado(db, email_norm):
            raise EmailDuplicadoError(
                f"El correo electronico '{datos.email}' ya se encuentra registrado en el sistema."
            )

        # 2. Sucursales autorizadas (B3)
        sucursales = list(datos.sucursales_autorizadas or [])
        principal = datos.id_sucursal_principal
        if datos.rol in ROLES_CON_SUCURSALES:
            self._validar_sucursales(db, sucursales, principal)
        else:
            sucursales, principal = [], None

        # 3. Límite de empleados del plan (P2-CU12, F17)
        SuscripcionServicio.validar(db, recurso="empleados")

        usuario = UsuarioORM(
            email=email_norm,
            password_hash=hash_password(datos.password),
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            telefono=datos.telefono,
            rol=datos.rol.value,
            id_sucursal=principal,
            id_tenant=id_tenant,
            activo=True,
            fecha_registro=datetime.now(timezone.utc),
        )
        db.add(usuario)
        db.flush()
        asegurar_ficha_empleado(db, usuario.id_usuario, datos.rol.value)
        SucursalesEmpleadoServicio.reemplazar(db, usuario.id_usuario, sucursales, principal)
        db.commit()
        db.refresh(usuario)

        _registrar(db, actor, "USUARIO_CREADO", ip, payload_nuevo=_resumen_bitacora(usuario, sucursales))
        return _to_usuario_out(db, usuario, UsuarioDetalleOut)

    def listar_usuarios_admin(
        self,
        db: Session,
        q: Optional[str] = None,
        rol: Optional[str] = None,
        id_sucursal: Optional[int] = None,
        activo: Optional[bool] = None,
        pagina: int = 1,
        limite: int = 10,
    ) -> ListaPaginadaUsuariosOut:
        """Empleados de la empresa, paginados y filtrados (B1)."""
        stmt = _alcance(
            select(UsuarioORM).options(
                joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad)
            ),
            db,
        )
        count_stmt = _alcance(select(func.count(UsuarioORM.id_usuario)), db)

        conditions = []
        if q:
            patron = f"%{q.strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(UsuarioORM.nombres).like(patron),
                    func.lower(UsuarioORM.apellidos).like(patron),
                    func.lower(UsuarioORM.email).like(patron),
                )
            )
        if rol:
            conditions.append(UsuarioORM.rol == rol)
        if id_sucursal:
            # B3: autorizados en la sucursal, no solo los que la tienen como principal
            conditions.append(
                or_(
                    UsuarioORM.id_sucursal == id_sucursal,
                    UsuarioORM.id_usuario.in_(
                        SucursalesEmpleadoServicio.empleados_de_sucursal(id_sucursal)
                    ),
                )
            )
        if activo is not None:
            conditions.append(UsuarioORM.activo.is_(activo))

        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = db.scalar(count_stmt) or 0
        offset = (pagina - 1) * limite
        stmt = stmt.order_by(UsuarioORM.id_usuario.desc()).offset(offset).limit(limite)
        usuarios = db.scalars(stmt).unique().all()

        total_paginas = max(1, math.ceil(total / limite)) if total > 0 else 1
        items = [_to_usuario_out(db, u, UsuarioResumenOut) for u in usuarios]

        return ListaPaginadaUsuariosOut(
            items=items,
            total=total,
            pagina=pagina,
            limite=limite,
            total_paginas=total_paginas,
        )

    def obtener_usuario_por_id(self, db: Session, id_usuario: int) -> UsuarioDetalleOut:
        """Ficha de un empleado de la empresa (B1)."""
        return _to_usuario_out(db, self._cargar(db, id_usuario), UsuarioDetalleOut)

    def actualizar_usuario(
        self,
        db: Session,
        id_usuario: int,
        datos: UsuarioActualizarIn,
        id_admin_sesion: int,
        actor: Optional[UsuarioORM] = None,
        ip: Optional[str] = None,
    ) -> UsuarioDetalleOut:
        """Actualiza datos, rol y sucursales de un empleado de la empresa."""
        usuario = self._cargar(db, id_usuario)
        if datos.rol is not None and datos.rol.value not in ROLES_GESTIONABLES:
            raise RolNoPermitidoError()

        antes_sucursales = [p[0] for p in SucursalesEmpleadoServicio.de_empleado(db, id_usuario)]
        anterior = _resumen_bitacora(usuario, antes_sucursales)

        # Validar colision de email si se intenta modificar
        if datos.email is not None:
            email_norm = datos.email.strip().lower()
            if correo_ocupado(db, email_norm, excluir_id=id_usuario):
                raise EmailDuplicadoError(
                    f"El correo electronico '{datos.email}' ya pertenece a otro usuario."
                )
            usuario.email = email_norm

        target_rol = datos.rol.value if datos.rol is not None else _rol(usuario.rol)

        # Salvaguarda: El administrador en sesion no puede degradar su propio rol
        if id_usuario == id_admin_sesion and target_rol != "administrador":
            raise AutoModificacionBloqueadaError(
                "No puede modificar o degradar su propio rol de administrador en sesion."
            )

        # Salvaguarda: Comprobar que quede al menos un administrador activo
        if _rol(usuario.rol) == "administrador" and target_rol != "administrador":
            if self._otros_admins_activos(db, id_usuario) == 0:
                raise UltimoAdministradorError(
                    "No es posible degradar al unico administrador activo del sistema."
                )

        # Sucursales autorizadas (B3)
        if target_rol in ROLES_OPERATIVOS:
            actuales = antes_sucursales or ([usuario.id_sucursal] if usuario.id_sucursal else [])
            sucursales = (
                list(datos.sucursales_autorizadas)
                if datos.sucursales_autorizadas is not None
                else actuales
            )
            principal = datos.id_sucursal_principal
            if principal is None:
                if usuario.id_sucursal in sucursales:
                    principal = usuario.id_sucursal
                elif len(sucursales) == 1:
                    principal = sucursales[0]
            if not sucursales:
                raise SucursalRequeridaError(
                    f"El rol '{target_rol}' requiere al menos una sucursal autorizada."
                )
            self._validar_sucursales(db, sucursales, principal)
        else:
            sucursales, principal = [], None
        usuario.id_sucursal = principal

        if datos.nombres is not None:
            usuario.nombres = datos.nombres
        if datos.apellidos is not None:
            usuario.apellidos = datos.apellidos
        if datos.telefono is not None:
            usuario.telefono = datos.telefono
        if datos.rol is not None:
            usuario.rol = datos.rol.value
            asegurar_ficha_empleado(db, usuario.id_usuario, datos.rol.value)
        db.flush()
        SucursalesEmpleadoServicio.reemplazar(db, usuario.id_usuario, sucursales, principal)

        db.commit()
        db.refresh(usuario)
        _registrar(
            db, actor, "USUARIO_MODIFICADO", ip,
            payload_anterior=anterior, payload_nuevo=_resumen_bitacora(usuario, sucursales),
        )
        return _to_usuario_out(db, usuario, UsuarioDetalleOut)

    def cambiar_estado_usuario(
        self,
        db: Session,
        id_usuario: int,
        datos: UsuarioEstadoIn,
        id_admin_sesion: int,
        actor: Optional[UsuarioORM] = None,
        ip: Optional[str] = None,
    ) -> UsuarioDetalleOut:
        """Activa o suspende el acceso de un empleado de la empresa."""
        usuario = self._cargar(db, id_usuario)

        if not datos.activo:
            if id_usuario == id_admin_sesion:
                raise AutoModificacionBloqueadaError(
                    "No puede desactivar su propia cuenta de administrador en la sesion actual."
                )
            if _rol(usuario.rol) == "administrador" and self._otros_admins_activos(db, id_usuario) == 0:
                raise UltimoAdministradorError(
                    "No es posible desactivar al unico administrador activo del sistema."
                )
        elif not usuario.activo:
            # B8: reactivar cuenta para el límite de empleados del plan
            SuscripcionServicio.validar(db, recurso="empleados")

        anterior = usuario.activo
        usuario.activo = datos.activo
        db.commit()
        db.refresh(usuario)
        _registrar(
            db, actor, "USUARIO_ESTADO", ip,
            payload_anterior={"id_usuario": id_usuario, "activo": anterior},
            payload_nuevo={"id_usuario": id_usuario, "activo": usuario.activo},
        )
        return _to_usuario_out(db, usuario, UsuarioDetalleOut)

    def reset_password(
        self,
        db: Session,
        id_usuario: int,
        datos: ResetPasswordIn,
        actor: Optional[UsuarioORM] = None,
        ip: Optional[str] = None,
    ) -> UsuarioDetalleOut:
        """Restablece la contraseña de un empleado de la empresa."""
        usuario = self._cargar(db, id_usuario)
        usuario.password_hash = hash_password(datos.nuevo_password)
        db.commit()
        db.refresh(usuario)
        _registrar(
            db, actor, "USUARIO_PASSWORD_RESET", ip,
            payload_nuevo={"id_usuario": id_usuario, "email": usuario.email},
        )
        return _to_usuario_out(db, usuario, UsuarioDetalleOut)

    def eliminar_usuario(
        self,
        db: Session,
        id_usuario: int,
        id_admin_sesion: int,
        actor: Optional[UsuarioORM] = None,
        ip: Optional[str] = None,
    ) -> None:
        """Elimina fisicamente un empleado si no registra dependencias historicas u operativas."""
        usuario = db.scalar(_alcance(select(UsuarioORM).where(UsuarioORM.id_usuario == id_usuario), db))
        if not usuario or not _es_gestionable(usuario):
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        if id_usuario == id_admin_sesion:
            raise AutoModificacionBloqueadaError(
                "No puede eliminar su propia cuenta de administrador en la sesion actual."
            )

        if _rol(usuario.rol) == "administrador" and self._otros_admins_activos(db, id_usuario) == 0:
            raise UltimoAdministradorError(
                "No es posible eliminar al unico administrador activo del sistema."
            )

        # Verificacion de dependencias operativas conocidas
        # 1. Movimientos de inventario
        movs = db.execute(
            text(
                "SELECT 1 FROM fashionstore.movimientos_inventario WHERE id_usuario_responsable = :uid LIMIT 1"
            ),
            {"uid": id_usuario},
        ).first()
        if movs:
            raise UsuarioConDependenciasError(
                "El usuario registra movimientos de inventario asociados. Utilice la baja logica."
            )

        # 2. Empleados (nómina)
        empleados = db.execute(
            text("SELECT 1 FROM fashionstore.empleados WHERE id_empleado = :uid LIMIT 1"),
            {"uid": id_usuario},
        ).first()
        if empleados:
            raise UsuarioConDependenciasError(
                "El usuario se encuentra registrado en la nomina de empleados. Utilice la baja logica."
            )

        resumen = _resumen_bitacora(usuario)
        try:
            db.delete(usuario)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise UsuarioConDependenciasError(
                "El usuario no puede eliminarse fisicamente debido a dependencias referenciales activas."
            ) from exc
        _registrar(db, actor, "USUARIO_ELIMINADO", ip, payload_anterior=resumen)
