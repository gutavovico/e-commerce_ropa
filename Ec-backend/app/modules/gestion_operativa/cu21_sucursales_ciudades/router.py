"""Router HTTP para el caso de uso CU21: Gestionar Sucursales y Ciudades."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.gestion_operativa.cu21_sucursales_ciudades.esquemas import (
    CiudadActualizarIn,
    CiudadCrearIn,
    CiudadOut,
    SucursalActualizarIn,
    SucursalAdminOut,
    SucursalCrearIn,
    SucursalEstadoIn,
    SucursalPublicaOut,
)
from modules.gestion_operativa.cu21_sucursales_ciudades.servicio import (
    ServicioGestionSucursal,
)

router = APIRouter()


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
# ENDPOINTS ADMINISTRATIVOS: CIUDADES
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


@router.post(
    "/admin/ciudades",
    response_model=CiudadOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Ubicaciones"],
    summary="Registrar nueva ciudad (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_ciudad(
    datos: CiudadCrearIn,
    db: Session = Depends(get_db),
) -> CiudadOut:
    """Crea una nueva ciudad en el catalogo de operaciones territoriales."""
    servicio = ServicioGestionSucursal(db)
    return servicio.crear_ciudad(datos)


@router.put(
    "/admin/ciudades/{id_ciudad}",
    response_model=CiudadOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Ubicaciones"],
    summary="Actualizar ciudad (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_ciudad(
    id_ciudad: int,
    datos: CiudadActualizarIn,
    db: Session = Depends(get_db),
) -> CiudadOut:
    """Actualiza los datos de una ciudad existente."""
    servicio = ServicioGestionSucursal(db)
    return servicio.actualizar_ciudad(id_ciudad, datos)


@router.delete(
    "/admin/ciudades/{id_ciudad}",
    status_code=status.HTTP_200_OK,
    tags=["Admin - Ubicaciones"],
    summary="Eliminar ciudad (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_ciudad(
    id_ciudad: int,
    db: Session = Depends(get_db),
) -> dict:
    """Elimina una ciudad si no tiene dependencias activas (sucursales o clientes)."""
    servicio = ServicioGestionSucursal(db)
    servicio.eliminar_ciudad(id_ciudad)
    return {"mensaje": f"Ciudad con ID {id_ciudad} eliminada exitosamente."}


# -----------------------------------------------------------------------------
# ENDPOINTS ADMINISTRATIVOS: SUCURSALES
# -----------------------------------------------------------------------------


@router.get(
    "/admin/sucursales",
    response_model=List[SucursalAdminOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Listado administrativo de sucursales (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
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
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_sucursal(
    datos: SucursalCrearIn,
    db: Session = Depends(get_db),
) -> SucursalAdminOut:
    """Registra una nueva sucursal verificando ciudad, unicidad y franja horaria."""
    servicio = ServicioGestionSucursal(db)
    return servicio.crear_sucursal(datos)


@router.put(
    "/admin/sucursales/{id_sucursal}",
    response_model=SucursalAdminOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Actualizar sucursal (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_sucursal(
    id_sucursal: int,
    datos: SucursalActualizarIn,
    db: Session = Depends(get_db),
) -> SucursalAdminOut:
    """Actualiza datos, ubicacion o franja horaria de la sucursal."""
    servicio = ServicioGestionSucursal(db)
    return servicio.actualizar_sucursal(id_sucursal, datos)


@router.patch(
    "/admin/sucursales/{id_sucursal}/estado",
    response_model=SucursalAdminOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Cambiar estado activo/inactivo (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def cambiar_estado_sucursal(
    id_sucursal: int,
    datos: SucursalEstadoIn,
    db: Session = Depends(get_db),
) -> SucursalAdminOut:
    """Activa o desactiva la sucursal validando que no tenga reservas o stock pendiente."""
    servicio = ServicioGestionSucursal(db)
    return servicio.cambiar_estado_sucursal(id_sucursal, datos.activa)


@router.delete(
    "/admin/sucursales/{id_sucursal}",
    status_code=status.HTTP_200_OK,
    tags=["Admin - Sucursales"],
    summary="Eliminar sucursal (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_sucursal(
    id_sucursal: int,
    db: Session = Depends(get_db),
) -> dict:
    """Eliminacion fisica permitida unicamente si nunca registro operaciones historicas."""
    servicio = ServicioGestionSucursal(db)
    servicio.eliminar_sucursal(id_sucursal)
    return {"mensaje": f"Sucursal con ID {id_sucursal} eliminada exitosamente."}
