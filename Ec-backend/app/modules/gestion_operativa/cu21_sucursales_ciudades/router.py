"""Router HTTP para el caso de uso CU21: Gestionar Sucursales y Ciudades."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.gestion_operativa.cu21_sucursales_ciudades.esquemas import (
    CiudadOut,
    MiSucursalOut,
    SucursalActualizarIn,
    SucursalAdminOut,
    SucursalCrearIn,
    SucursalEstadoIn,
    SucursalPublicaOut,
    UsoPlanSucursalesOut,
)
from modules.gestion_operativa.cu21_sucursales_ciudades.servicio import (
    ServicioGestionSucursal,
)

router = APIRouter()

#: P2-CU04 B9: el administrador que opera y su IP, para la bitácora.
_admin = require_roles(["administrador"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# -----------------------------------------------------------------------------
# ENDPOINTS PUBLICOS
# -----------------------------------------------------------------------------


@router.get(
    "/sucursales",
    response_model=List[SucursalPublicaOut],
    status_code=status.HTTP_200_OK,
    tags=["Sucursales"],
    summary="Listar sucursales activas (Publico)",
)
def listar_sucursales_publicas(
    id_ciudad: Optional[int] = Query(None, description="Filtrar por identificador de ciudad"),
    db: Session = Depends(get_db),
) -> List[SucursalPublicaOut]:
    """Retorna la lista de boutiques y sucursales fisicas activas en la cadena."""
    servicio = ServicioGestionSucursal(db)
    return servicio.listar_sucursales_publicas(id_ciudad=id_ciudad)


# -----------------------------------------------------------------------------
# ENDPOINTS ADMINISTRATIVOS: CIUDADES (P2-CU04 B6: solo lectura; las gestiona P2-CU08)
# -----------------------------------------------------------------------------


@router.get(
    "/admin/ciudades",
    response_model=List[CiudadOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Ubicaciones"],
    summary="Listar ciudades operativas (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def listar_ciudades(
    db: Session = Depends(get_db),
) -> List[CiudadOut]:
    """Retorna todas las ciudades registradas con estadisticas de sucursales."""
    servicio = ServicioGestionSucursal(db)
    return servicio.listar_ciudades()


# -----------------------------------------------------------------------------
# ENDPOINTS ADMINISTRATIVOS: SUCURSALES
# -----------------------------------------------------------------------------


@router.get(
    "/admin/sucursales",
    response_model=List[SucursalAdminOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Listado administrativo de sucursales (Admin)",
    dependencies=[Depends(require_roles(["administrador", "admin", "encargado_sucursal"]))],
)
def listar_sucursales_admin(
    id_ciudad: Optional[int] = Query(None, description="Filtrar por ciudad"),
    activa: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    q: Optional[str] = Query(None, description="Termino de busqueda (nombre, direccion o ciudad)"),
    db: Session = Depends(get_db),
) -> List[SucursalAdminOut]:
    """Retorna todas las sucursales con metricas de empleados y existencias."""
    servicio = ServicioGestionSucursal(db)
    return servicio.listar_sucursales_admin(id_ciudad=id_ciudad, activa=activa, q=q)


@router.get(
    "/admin/sucursales/uso-plan",
    response_model=UsoPlanSucursalesOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Sucursales activas frente al límite del plan (Admin)",
    dependencies=[Depends(_admin)],
)
def uso_plan_sucursales(db: Session = Depends(get_db)) -> UsoPlanSucursalesOut:
    """P2-CU04 B7. Declarada antes de `/{id_sucursal}` para que no la capture."""
    return ServicioGestionSucursal(db).uso_plan()


@router.get(
    "/mis-sucursales",
    response_model=List[MiSucursalOut],
    status_code=status.HTTP_200_OK,
    tags=["Sucursales"],
    summary="Sucursales en las que opera el empleado de la sesión",
)
def mis_sucursales(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal", "cajero"])),
) -> List[MiSucursalOut]:
    """P2-CU03 B5: la caja ofrece estas sucursales al empleado."""
    return ServicioGestionSucursal(db).mis_sucursales(usuario)


@router.get(
    "/admin/sucursales/{id_sucursal}",
    response_model=SucursalAdminOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Detalle completo de sucursal (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def obtener_sucursal(
    id_sucursal: int,
    db: Session = Depends(get_db),
) -> SucursalAdminOut:
    """Retorna la ficha descriptiva de una sucursal especifica."""
    servicio = ServicioGestionSucursal(db)
    return servicio.obtener_sucursal(id_sucursal)


@router.post(
    "/admin/sucursales",
    response_model=SucursalAdminOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Sucursales"],
    summary="Registrar nueva sucursal (Admin)",
)
def crear_sucursal(
    datos: SucursalCrearIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(_admin),
) -> SucursalAdminOut:
    """Registra una nueva sucursal verificando ciudad, unicidad y franja horaria."""
    servicio = ServicioGestionSucursal(db, actor=admin, ip=_ip(request))
    return servicio.crear_sucursal(datos)


@router.put(
    "/admin/sucursales/{id_sucursal}",
    response_model=SucursalAdminOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Actualizar sucursal (Admin)",
)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalActualizarIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(_admin),
) -> SucursalAdminOut:
    """Actualiza datos, ubicacion o franja horaria de la sucursal."""
    servicio = ServicioGestionSucursal(db, actor=admin, ip=_ip(request))
    return servicio.actualizar_sucursal(id_sucursal, datos)


@router.patch(
    "/admin/sucursales/{id_sucursal}/estado",
    response_model=SucursalAdminOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Cambiar estado activo/inactivo (Admin)",
)
def cambiar_estado_sucursal(
    id_sucursal: int,
    datos: SucursalEstadoIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(_admin),
) -> SucursalAdminOut:
    """Activa o desactiva la sucursal validando que no tenga reservas o stock pendiente."""
    servicio = ServicioGestionSucursal(db, actor=admin, ip=_ip(request))
    return servicio.cambiar_estado_sucursal(id_sucursal, datos.activa)


@router.delete(
    "/admin/sucursales/{id_sucursal}",
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Eliminar sucursal (Admin)",
)
def eliminar_sucursal(
    id_sucursal: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(_admin),
) -> dict:
    """Eliminacion fisica permitida unicamente si nunca registro operaciones historicas."""
    servicio = ServicioGestionSucursal(db, actor=admin, ip=_ip(request))
    servicio.eliminar_sucursal(id_sucursal)
    return {"mensaje": f"Sucursal con ID {id_sucursal} eliminada exitosamente."}
