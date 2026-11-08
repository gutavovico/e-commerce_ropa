"""Servicio de aplicacion y logica de dominio para CU20: Gestionar Usuarios y Roles (RBAC)."""

from datetime import datetime, timezone
import math
from typing import Optional

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from core.security import hash_password
from modules.autenticacion_seguridad.cu20_usuarios_roles.errores import (
    CambioRolNoPermitidoError,
    AutoModificacionBloqueadaError,
    EmailDuplicadoError,
    SucursalInvalidaError,
    SucursalRequeridaError,
    UltimoAdministradorError,
    UsuarioConDependenciasError,
    UsuarioNoEncontradoError,
)
from modules.autenticacion_seguridad.cu20_usuarios_roles.esquemas import (
    ListaPaginadaUsuariosOut,
    ResetPasswordIn,
    RolUsuarioEnum,
    UsuarioActualizarIn,
    UsuarioCrearIn,
    UsuarioDetalleOut,
    UsuarioEstadoIn,
    UsuarioResumenOut,
)
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.gestion_operativa.modelos import SucursalORM
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.plataforma.servicio_tenants import TenantServicio, es_rol_sin_empresa


#: Roles de personal: su usuario debe tener ficha en `fashionstore.empleados`, porque
#: `ventas.id_cajero` la referencia (CU31-CU32, decisión D3).
CARGOS_PERSONAL = {
    "administrador": "Administrador",
    "encargado_sucursal": "Encargado de Sucursal",
    "cajero": "Cajero",
}


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


def _to_usuario_out(usuario: UsuarioORM, out_cls=UsuarioDetalleOut):
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
        rol=str(usuario.rol),
        id_sucursal=usuario.id_sucursal,
        sucursal_nombre=sucursal_nombre,
        sucursal_ciudad=sucursal_ciudad,
        activo=usuario.activo,
        fecha_registro=fecha_reg,
        ultimo_acceso=usuario.ultimo_acceso,
    )


class ServicioGestionUsuarios:
    """Orquesta las operaciones administrativas de usuarios y privilegios RBAC."""

    def crear_usuario(self, db: Session, datos: UsuarioCrearIn) -> UsuarioDetalleOut:
        """Crea una nueva cuenta de usuario con credenciales seguras y validacion de roles."""
        email_norm = datos.email.strip().lower()

        # P2-CU13: un empleado pertenece a la empresa de la sesión; un cliente no pertenece a ninguna
        id_tenant = TenantServicio.empresa_para_rol(db, datos.rol)

        # 1. Comprobar unicidad de correo electronico (RN05, F8): entre los empleados de la empresa
        #    o entre las cuentas globales, según el rol
        stmt_dup = select(UsuarioORM).where(
            func.lower(UsuarioORM.email) == email_norm,
            UsuarioORM.id_tenant.is_(None) if id_tenant is None else UsuarioORM.id_tenant == id_tenant,
        )
        if db.scalars(stmt_dup).first():
            raise EmailDuplicadoError(
                f"El correo electronico '{datos.email}' ya se encuentra registrado en el sistema."
            )

        # 2. Validar sucursal si corresponde
        if datos.id_sucursal:
            suc = db.scalar(
                select(SucursalORM).where(SucursalORM.id_sucursal == datos.id_sucursal)
            )
            if not suc or not suc.activa:
                raise SucursalInvalidaError(
                    "La sucursal seleccionada no existe o se encuentra inactiva."
                )

        # P2-CU12: límite de empleados del plan (F17)
        if not es_rol_sin_empresa(datos.rol):
            SuscripcionServicio.validar(db, recurso="empleados")

        # 3. Hashing de contrasena
        hashed_password = hash_password(datos.password)

        # 4. Asignacion condicional de sucursal segun rol
        id_sucursal = (
            datos.id_sucursal
            if datos.rol in (RolUsuarioEnum.ENCARGADO_SUCURSAL, RolUsuarioEnum.CAJERO)
            else None
        )

        usuario = UsuarioORM(
            email=email_norm,
            password_hash=hashed_password,
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            telefono=datos.telefono,
            rol=datos.rol.value,
            id_sucursal=id_sucursal,
            id_tenant=id_tenant,
            activo=True,
            fecha_registro=datetime.now(timezone.utc),
        )
        db.add(usuario)
        db.flush()
        asegurar_ficha_empleado(db, usuario.id_usuario, datos.rol.value)
        TenantServicio.sincronizar_sucursal_principal(db, usuario.id_usuario, id_sucursal)
        db.commit()
        db.refresh(usuario)

        # Si el rol es cliente, instanciar perfil base en fashionstore.clientes y registrarlo en la
        # empresa de la sesión (F9)
        if datos.rol == RolUsuarioEnum.CLIENTE:
            cliente = ClienteORM(id_cliente=usuario.id_usuario)
            db.add(cliente)
            db.flush()
            TenantServicio.registrar_cliente(db, usuario.id_usuario)
            db.commit()
            db.refresh(usuario)

        return _to_usuario_out(usuario, UsuarioDetalleOut)

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
        """Retorna el listado paginado de usuarios aplicando filtros multicriterio."""
        stmt = select(UsuarioORM).options(
            joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad)
        )
        count_stmt = select(func.count(UsuarioORM.id_usuario))

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
            conditions.append(UsuarioORM.id_sucursal == id_sucursal)
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
        items = [_to_usuario_out(u, UsuarioResumenOut) for u in usuarios]

        return ListaPaginadaUsuariosOut(
            items=items,
            total=total,
            pagina=pagina,
            limite=limite,
            total_paginas=total_paginas,
        )

    def obtener_usuario_por_id(self, db: Session, id_usuario: int) -> UsuarioDetalleOut:
        """Obtiene la ficha detallada de un usuario por su identificador primario."""
        stmt = (
            select(UsuarioORM)
            .options(joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad))
            .where(UsuarioORM.id_usuario == id_usuario)
        )
        usuario = db.scalars(stmt).unique().first()
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")
        return _to_usuario_out(usuario, UsuarioDetalleOut)

    def actualizar_usuario(
        self,
        db: Session,
        id_usuario: int,
        datos: UsuarioActualizarIn,
        id_admin_sesion: int,
    ) -> UsuarioDetalleOut:
        """Actualiza los datos institucionales y de rol de un usuario."""
        stmt = (
            select(UsuarioORM)
            .options(joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad))
            .where(UsuarioORM.id_usuario == id_usuario)
        )
        usuario = db.scalars(stmt).unique().first()
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        # Validar colision de email si se intenta modificar
        if datos.email is not None:
            email_norm = datos.email.strip().lower()
            stmt_dup = select(UsuarioORM).where(
                func.lower(UsuarioORM.email) == email_norm,
                UsuarioORM.id_usuario != id_usuario,
                UsuarioORM.id_tenant.is_(None)
                if getattr(usuario, "id_tenant", None) is None
                else UsuarioORM.id_tenant == usuario.id_tenant,
            )
            if db.scalars(stmt_dup).first():
                raise EmailDuplicadoError(
                    f"El correo electronico '{datos.email}' ya pertenece a otro usuario."
                )
            usuario.email = email_norm

        # Salvaguarda: El administrador en sesion no puede degradar su propio rol
        if (
            id_usuario == id_admin_sesion
            and datos.rol is not None
            and datos.rol.value != "administrador"
        ):
            raise AutoModificacionBloqueadaError(
                "No puede modificar o degradar su propio rol de administrador en sesion."
            )

        # Salvaguarda: Comprobar que quede al menos un administrador activo
        if (
            str(usuario.rol) == "administrador"
            and datos.rol is not None
            and datos.rol.value != "administrador"
        ):
            conteo_admins = db.scalar(
                select(func.count(UsuarioORM.id_usuario)).where(
                    UsuarioORM.rol == "administrador",
                    UsuarioORM.activo.is_(True),
                    UsuarioORM.id_usuario != id_usuario,
                )
            ) or 0
            if conteo_admins == 0:
                raise UltimoAdministradorError(
                    "No es posible degradar al unico administrador activo del sistema."
                )

        # Validar y asignar rol y sucursal
        target_rol = datos.rol.value if datos.rol is not None else str(usuario.rol)
        # P2-CU13: cliente (cuenta global) y empleado (cuenta de una empresa) no se convierten
        if es_rol_sin_empresa(target_rol) != es_rol_sin_empresa(usuario.rol):
            raise CambioRolNoPermitidoError()
        if target_rol in ("encargado_sucursal", "cajero"):
            target_sucursal = (
                datos.id_sucursal if datos.id_sucursal is not None else usuario.id_sucursal
            )
            if not target_sucursal or target_sucursal <= 0:
                raise SucursalRequeridaError(
                    f"El rol '{target_rol}' requiere una sucursal asignada valida."
                )
            suc = db.scalar(
                select(SucursalORM).where(SucursalORM.id_sucursal == target_sucursal)
            )
            if not suc or not suc.activa:
                raise SucursalInvalidaError(
                    "La sucursal seleccionada no existe o se encuentra inactiva."
                )
            usuario.id_sucursal = target_sucursal
        elif target_rol in ("administrador", "cliente"):
            usuario.id_sucursal = None

        if datos.nombres is not None:
            usuario.nombres = datos.nombres
        if datos.apellidos is not None:
            usuario.apellidos = datos.apellidos
        if datos.telefono is not None:
            usuario.telefono = datos.telefono
        if datos.rol is not None:
            usuario.rol = datos.rol.value
            asegurar_ficha_empleado(db, usuario.id_usuario, datos.rol.value)
        if not es_rol_sin_empresa(target_rol):
            db.flush()
            TenantServicio.sincronizar_sucursal_principal(db, usuario.id_usuario, usuario.id_sucursal)

        db.commit()
        db.refresh(usuario)
        return _to_usuario_out(usuario, UsuarioDetalleOut)

    def cambiar_estado_usuario(
        self,
        db: Session,
        id_usuario: int,
        datos: UsuarioEstadoIn,
        id_admin_sesion: int,
    ) -> UsuarioDetalleOut:
        """Activa o suspende el acceso de un usuario al sistema."""
        stmt = (
            select(UsuarioORM)
            .options(joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad))
            .where(UsuarioORM.id_usuario == id_usuario)
        )
        usuario = db.scalars(stmt).unique().first()
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        # Salvaguardas ante suspension (activo=False)
        if not datos.activo:
            if id_usuario == id_admin_sesion:
                raise AutoModificacionBloqueadaError(
                    "No puede desactivar su propia cuenta de administrador en la sesion actual."
                )
            if str(usuario.rol) == "administrador":
                conteo_admins = db.scalar(
                    select(func.count(UsuarioORM.id_usuario)).where(
                        UsuarioORM.rol == "administrador",
                        UsuarioORM.activo.is_(True),
                        UsuarioORM.id_usuario != id_usuario,
                    )
                ) or 0
                if conteo_admins == 0:
                    raise UltimoAdministradorError(
                        "No es posible desactivar al unico administrador activo del sistema."
                    )

        usuario.activo = datos.activo
        db.commit()
        db.refresh(usuario)
        return _to_usuario_out(usuario, UsuarioDetalleOut)

    def reset_password(
        self,
        db: Session,
        id_usuario: int,
        datos: ResetPasswordIn,
    ) -> UsuarioDetalleOut:
        """Actualiza la contrasena de un usuario estableciendo un nuevo hash seguro."""
        stmt = (
            select(UsuarioORM)
            .options(joinedload(UsuarioORM.sucursal).joinedload(SucursalORM.ciudad))
            .where(UsuarioORM.id_usuario == id_usuario)
        )
        usuario = db.scalars(stmt).unique().first()
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        usuario.password_hash = hash_password(datos.nuevo_password)
        db.commit()
        db.refresh(usuario)
        return _to_usuario_out(usuario, UsuarioDetalleOut)

    def eliminar_usuario(
        self,
        db: Session,
        id_usuario: int,
        id_admin_sesion: int,
    ) -> None:
        """Elimina fisicamente un usuario si no registra dependencias historicas u operativas."""
        usuario = db.scalar(
            select(UsuarioORM).where(UsuarioORM.id_usuario == id_usuario)
        )
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        if id_usuario == id_admin_sesion:
            raise AutoModificacionBloqueadaError(
                "No puede eliminar su propia cuenta de administrador en la sesion actual."
            )

        if str(usuario.rol) == "administrador":
            conteo_admins = db.scalar(
                select(func.count(UsuarioORM.id_usuario)).where(
                    UsuarioORM.rol == "administrador",
                    UsuarioORM.activo.is_(True),
                    UsuarioORM.id_usuario != id_usuario,
                )
            ) or 0
            if conteo_admins == 0:
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

        # 2. Pedidos asociados
        pedidos = db.execute(
            text("SELECT 1 FROM fashionstore.pedidos WHERE id_cliente = :uid LIMIT 1"),
            {"uid": id_usuario},
        ).first()
        if pedidos:
            raise UsuarioConDependenciasError(
                "El usuario registra pedidos comerciales vinculados. Utilice la baja logica."
            )

        # 3. Empleados
        empleados = db.execute(
            text("SELECT 1 FROM fashionstore.empleados WHERE id_empleado = :uid LIMIT 1"),
            {"uid": id_usuario},
        ).first()
        if empleados:
            raise UsuarioConDependenciasError(
                "El usuario se encuentra registrado en la nomina de empleados. Utilice la baja logica."
            )

        try:
            db.delete(usuario)
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise UsuarioConDependenciasError(
                "El usuario no puede eliminarse fisicamente debido a dependencias referenciales activas."
            ) from exc
