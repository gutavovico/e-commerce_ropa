"""Routers REST para CU25: Gestionar Proveedores."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from .esquemas import (
    ListaPaginadaProveedoresOut,
    ProveedorActualizarIn,
    ProveedorCrearIn,
    ProveedorEstadoIn,
    ProveedorFiltrosIn,
    ProveedorItemOut,
)
from .servicio import servicio_gestion_proveedores

router = APIRouter(
    prefix="/admin/proveedores",
    tags=["Gestion Operativa - Proveedores y Fabricantes (Admin)"],
)


@router.get(
    "",
    response_model=ListaPaginadaProveedoresOut,
    status_code=status.HTTP_200_OK,
    summary="Consulta paginada del padron de proveedores con filtros",
)
def listar_proveedores(
    q: Optional[str] = Query(None, max_length=100, description="Busqueda por razon social, NIT o contacto"),
    estado_activo: Optional[bool] = Query(None, description="Filtro booleano por estado activo"),
    estado: Optional[str] = Query(None, description="Alias: 'activos', 'inactivos', 'todos'"),
    rubro: Optional[str] = Query(None, max_length=80, description="Filtro por rubro comercial"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(20, ge=1, le=100, description="Registros por pagina"),
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ListaPaginadaProveedoresOut:
    filtro_estado = estado_activo
    if filtro_estado is None and estado:
        if estado == "activos":
            filtro_estado = True
        elif estado == "inactivos":
            filtro_estado = False

    filtros = ProveedorFiltrosIn(
        q=q.strip() if q and q.strip() else None,
        estado_activo=filtro_estado,
        rubro=rubro.strip() if rubro and rubro.strip() else None,
        pagina=pagina,
        limite=limite,
    )
    return servicio_gestion_proveedores.listar_proveedores(db, filtros, usuario_sesion)


@router.get(
    "/{id_proveedor}",
    response_model=ProveedorItemOut,
    status_code=status.HTTP_200_OK,
    summary="Obtiene la ficha detallada de un proveedor por ID",
)
def obtener_proveedor(
    id_proveedor: int,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ProveedorItemOut:
    return servicio_gestion_proveedores.obtener_proveedor_por_id(db, id_proveedor, usuario_sesion)


@router.post(
    "",
    response_model=ProveedorItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra un nuevo socio comercial en el padron",
)
def crear_proveedor(
    payload: ProveedorCrearIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ProveedorItemOut:
    return servicio_gestion_proveedores.crear_proveedor(db, payload, usuario_sesion)


@router.put(
    "/{id_proveedor}",
    response_model=ProveedorItemOut,
    status_code=status.HTTP_200_OK,
    summary="Actualiza los datos fiscales, comerciales o de contacto de un proveedor",
)
def actualizar_proveedor(
    id_proveedor: int,
    payload: ProveedorActualizarIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ProveedorItemOut:
    return servicio_gestion_proveedores.actualizar_proveedor(db, id_proveedor, payload, usuario_sesion)


@router.patch(
    "/{id_proveedor}/estado",
    response_model=ProveedorItemOut,
    status_code=status.HTTP_200_OK,
    summary="Conmuta el estado operativo del proveedor (baja logica o reactivacion)",
)
def cambiar_estado_proveedor(
    id_proveedor: int,
    payload: ProveedorEstadoIn,
    db: Session = Depends(get_db),
    usuario_sesion: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ProveedorItemOut:
    return servicio_gestion_proveedores.cambiar_estado_proveedor(
        db, id_proveedor, payload.estado_activo, usuario_sesion
    )
