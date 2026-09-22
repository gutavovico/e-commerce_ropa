"""Router REST de FastAPI para CU20: Gestionar Usuarios y Roles (RBAC)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.cu20_usuarios_roles.esquemas import (
    ListaPaginadaUsuariosOut,
    ResetPasswordIn,
    UsuarioActualizarIn,
    UsuarioCrearIn,
    UsuarioDetalleOut,
    UsuarioEstadoIn,
)
from modules.autenticacion_seguridad.cu20_usuarios_roles.servicio import (
    ServicioGestionUsuarios,
)
from modules.autenticacion_seguridad.modelos import UsuarioORM

router = APIRouter(
    prefix="/admin/usuarios",
    tags=["Administracion de Usuarios y Roles"],
)
servicio_usuarios = ServicioGestionUsuarios()


@router.get(
    "",
    response_model=ListaPaginadaUsuariosOut,
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios con filtros y paginacion",
)
@router.get(
    "/",
    response_model=ListaPaginadaUsuariosOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def listar_usuarios(
    q: Optional[str] = Query(None, description="Busqueda por nombre, apellido o correo"),
    rol: Optional[str] = Query(None, description="Filtro por rol de usuario"),
    id_sucursal: Optional[int] = Query(None, description="Filtro por sucursal asignada"),
    activo: Optional[bool] = Query(None, description="Filtro por estado de cuenta"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(10, ge=1, le=100, description="Cantidad de registros por pagina"),
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(require_roles(["administrador"])),
) -> ListaPaginadaUsuariosOut:
    """Retorna la lista de usuarios paginada segun los filtros especificados."""
    return servicio_usuarios.listar_usuarios_admin(
        db=db,
        q=q,
        rol=rol,
        id_sucursal=id_sucursal,
        activo=activo,
        pagina=pagina,
        limite=limite,
    )


@router.post(
    "",
    response_model=UsuarioDetalleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva cuenta corporativa o cliente",
)
@router.post(
    "/",
    response_model=UsuarioDetalleOut,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def crear_usuario(
    datos: UsuarioCrearIn,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(require_roles(["administrador"])),
) -> UsuarioDetalleOut:
    """Registra un nuevo usuario con roles y sucursales validados."""
    return servicio_usuarios.crear_usuario(db=db, datos=datos)


@router.get(
    "/{id_usuario}",
    response_model=UsuarioDetalleOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar ficha de usuario por ID",
)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(require_roles(["administrador"])),
) -> UsuarioDetalleOut:
    """Obtiene los detalles tecnicos de una cuenta de usuario."""
    return servicio_usuarios.obtener_usuario_por_id(db=db, id_usuario=id_usuario)


@router.put(
    "/{id_usuario}",
    response_model=UsuarioDetalleOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos y rol de usuario",
)
def actualizar_usuario(
    id_usuario: int,
    datos: UsuarioActualizarIn,
    db: Session = Depends(get_db),
    admin_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> UsuarioDetalleOut:
    """Modifica atributos, rol o sucursal de un usuario con salvaguardas RBAC."""
    return servicio_usuarios.actualizar_usuario(
        db=db,
        id_usuario=id_usuario,
        datos=datos,
        id_admin_sesion=admin_sesion.id_usuario,
    )


@router.patch(
    "/{id_usuario}/estado",
    response_model=UsuarioDetalleOut,
    status_code=status.HTTP_200_OK,
    summary="Conmutar estado activo / suspendido",
)
def cambiar_estado(
    id_usuario: int,
    datos: UsuarioEstadoIn,
    db: Session = Depends(get_db),
    admin_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> UsuarioDetalleOut:
    """Activa o suspende el acceso al sistema para un usuario."""
    return servicio_usuarios.cambiar_estado_usuario(
        db=db,
        id_usuario=id_usuario,
        datos=datos,
        id_admin_sesion=admin_sesion.id_usuario,
    )


@router.post(
    "/{id_usuario}/reset-password",
    response_model=UsuarioDetalleOut,
    status_code=status.HTTP_200_OK,
    summary="Restablecer contrasena administrativamente",
)
def reset_password(
    id_usuario: int,
    datos: ResetPasswordIn,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(require_roles(["administrador"])),
) -> UsuarioDetalleOut:
    """Asigna una nueva contrasena segura con hash criptografico."""
    return servicio_usuarios.reset_password(
        db=db,
        id_usuario=id_usuario,
        datos=datos,
    )


@router.delete(
    "/{id_usuario}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario o requerir baja logica",
)
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    admin_sesion: UsuarioORM = Depends(require_roles(["administrador"])),
) -> None:
    """Elimina permanentemente al usuario si no registra dependencias operativas."""
    servicio_usuarios.eliminar_usuario(
        db=db,
        id_usuario=id_usuario,
        id_admin_sesion=admin_sesion.id_usuario,
    )
