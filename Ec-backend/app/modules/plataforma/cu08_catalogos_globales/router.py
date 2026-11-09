"""Router FastAPI para P2-CU08: Gestionar catálogos globales (ciudades, tallas, colores)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu08_catalogos_globales.esquemas import (
    CambiarEstadoCatalogoIn,
    CiudadGlobalIn,
    CiudadGlobalOut,
    ColorGlobalIn,
    ColorGlobalOut,
    EliminacionCatalogoOut,
    TallaGlobalIn,
    TallaGlobalOut,
)
from modules.plataforma.cu08_catalogos_globales.servicio import CatalogosGlobalesServicio
from modules.plataforma.dependencias import exigir_super_administrador

router = APIRouter(prefix="/catalogos", tags=["Plataforma - Catálogos Globales (P2-CU08)"])


def _ip_cliente(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


# --- Ciudades ---


@router.get(
    "/ciudades",
    response_model=list[CiudadGlobalOut],
    summary="Listar el catálogo global de ciudades (RN21)",
)
def listar_ciudades(
    solo_activas: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[CiudadGlobalOut]:
    return CatalogosGlobalesServicio.listar_ciudades(db, solo_activas=solo_activas)


@router.post(
    "/ciudades",
    response_model=CiudadGlobalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una ciudad en el catálogo global",
)
def crear_ciudad(
    datos: CiudadGlobalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> CiudadGlobalOut:
    return CatalogosGlobalesServicio.crear_ciudad(
        db, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.put(
    "/ciudades/{id_ciudad}",
    response_model=CiudadGlobalOut,
    summary="Editar una ciudad del catálogo global",
)
def actualizar_ciudad(
    id_ciudad: int,
    datos: CiudadGlobalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> CiudadGlobalOut:
    return CatalogosGlobalesServicio.actualizar_ciudad(
        db, id_ciudad, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.patch(
    "/ciudades/{id_ciudad}/estado",
    response_model=CiudadGlobalOut,
    summary="Activar o desactivar una ciudad del catálogo global (CU08 A2)",
)
def cambiar_estado_ciudad(
    id_ciudad: int,
    datos: CambiarEstadoCatalogoIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> CiudadGlobalOut:
    return CatalogosGlobalesServicio.cambiar_estado_ciudad(
        db, id_ciudad, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.delete(
    "/ciudades/{id_ciudad}",
    response_model=EliminacionCatalogoOut,
    summary="Eliminar una ciudad sin sucursales asociadas (CU08 A2)",
)
def eliminar_ciudad(
    id_ciudad: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EliminacionCatalogoOut:
    return CatalogosGlobalesServicio.eliminar_ciudad(
        db, id_ciudad, usuario, direccion_ip=_ip_cliente(request)
    )


# --- Tallas ---


@router.get(
    "/tallas",
    response_model=list[TallaGlobalOut],
    summary="Listar el catálogo global de tallas ordenadas por orden de visualización (RN21)",
)
def listar_tallas(
    solo_activas: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[TallaGlobalOut]:
    return CatalogosGlobalesServicio.listar_tallas(db, solo_activas=solo_activas)


@router.post(
    "/tallas",
    response_model=TallaGlobalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una talla en el catálogo global",
)
def crear_talla(
    datos: TallaGlobalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> TallaGlobalOut:
    return CatalogosGlobalesServicio.crear_talla(
        db, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.put(
    "/tallas/{id_talla}",
    response_model=TallaGlobalOut,
    summary="Editar una talla del catálogo global",
)
def actualizar_talla(
    id_talla: int,
    datos: TallaGlobalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> TallaGlobalOut:
    return CatalogosGlobalesServicio.actualizar_talla(
        db, id_talla, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.patch(
    "/tallas/{id_talla}/estado",
    response_model=TallaGlobalOut,
    summary="Activar o desactivar una talla del catálogo global (CU08 A2)",
)
def cambiar_estado_talla(
    id_talla: int,
    datos: CambiarEstadoCatalogoIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> TallaGlobalOut:
    return CatalogosGlobalesServicio.cambiar_estado_talla(
        db, id_talla, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.delete(
    "/tallas/{id_talla}",
    response_model=EliminacionCatalogoOut,
    summary="Eliminar una talla sin variantes asociadas (CU08 A2)",
)
def eliminar_talla(
    id_talla: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EliminacionCatalogoOut:
    return CatalogosGlobalesServicio.eliminar_talla(
        db, id_talla, usuario, direccion_ip=_ip_cliente(request)
    )


# --- Colores ---


@router.get(
    "/colores",
    response_model=list[ColorGlobalOut],
    summary="Listar el catálogo global de colores (RN21)",
)
def listar_colores(
    solo_activos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> list[ColorGlobalOut]:
    return CatalogosGlobalesServicio.listar_colores(db, solo_activos=solo_activos)


@router.post(
    "/colores",
    response_model=ColorGlobalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un color en el catálogo global",
)
def crear_color(
    datos: ColorGlobalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> ColorGlobalOut:
    return CatalogosGlobalesServicio.crear_color(
        db, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.put(
    "/colores/{id_color}",
    response_model=ColorGlobalOut,
    summary="Editar un color del catálogo global",
)
def actualizar_color(
    id_color: int,
    datos: ColorGlobalIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> ColorGlobalOut:
    return CatalogosGlobalesServicio.actualizar_color(
        db, id_color, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.patch(
    "/colores/{id_color}/estado",
    response_model=ColorGlobalOut,
    summary="Activar o desactivar un color del catálogo global (CU08 A2)",
)
def cambiar_estado_color(
    id_color: int,
    datos: CambiarEstadoCatalogoIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> ColorGlobalOut:
    return CatalogosGlobalesServicio.cambiar_estado_color(
        db, id_color, datos, usuario, direccion_ip=_ip_cliente(request)
    )


@router.delete(
    "/colores/{id_color}",
    response_model=EliminacionCatalogoOut,
    summary="Eliminar un color sin variantes asociadas (CU08 A2)",
)
def eliminar_color(
    id_color: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> EliminacionCatalogoOut:
    return CatalogosGlobalesServicio.eliminar_color(
        db, id_color, usuario, direccion_ip=_ip_cliente(request)
    )

