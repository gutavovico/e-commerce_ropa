"""Router HTTP para el caso de uso CU23: Gestionar Categorias, Tallas y Colores.

Expone endpoints publicos para consulta de catalogos y endpoints protegidos por RBAC
para operaciones de administracion editorial por usuarios con rol 'administrador'.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.gestion_operativa.cu23_categorias_tallas_colores.esquemas import (
    CategoriaActualizarIn,
    CategoriaAdminOut,
    CategoriaCrearIn,
    CategoriaOut,
    ColorActualizarIn,
    ColorAdminOut,
    ColorCrearIn,
    ColorOut,
    TallaActualizarIn,
    TallaAdminOut,
    TallaCrearIn,
    TallaOut,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.servicio import (
    ServicioGestionAtributos,
)

router = APIRouter()


# =============================================================================
# ENDPOINTS PUBLICOS: CONSULTA DE CATALOGOS Y ATRIBUTOS
# =============================================================================


@router.get(
    "/categorias",
    response_model=List[CategoriaOut],
    status_code=status.HTTP_200_OK,
    tags=["Atributos Publicos"],
    summary="Listar categorias del catalogo (Publico)",
)
def listar_categorias_publicas(
    db: Session = Depends(get_db),
) -> List[CategoriaOut]:
    """Retorna la jerarquia de categorias disponibles para navegacion en tienda y catalogo."""
    return ServicioGestionAtributos(db).listar_categorias_publicas()


@router.get(
    "/tallas",
    response_model=List[TallaOut],
    status_code=status.HTTP_200_OK,
    tags=["Atributos Publicos"],
    summary="Listar tallas comerciales ordenadas (Publico)",
)
def listar_tallas_publicas(
    db: Session = Depends(get_db),
) -> List[TallaOut]:
    """Retorna la escala de tallas comerciales ordenadas secuencialmente."""
    return ServicioGestionAtributos(db).listar_tallas_publicas()


@router.get(
    "/colores",
    response_model=List[ColorOut],
    status_code=status.HTTP_200_OK,
    tags=["Atributos Publicos"],
    summary="Listar colores textiles de diseno (Publico)",
)
def listar_colores_publicos(
    db: Session = Depends(get_db),
) -> List[ColorOut]:
    """Retorna la paleta de colores textiles con representacion hexadecimal #HEX."""
    return ServicioGestionAtributos(db).listar_colores_publicos()


# =============================================================================
# ENDPOINTS ADMINISTRATIVOS: CATEGORIAS (ROL ADMINISTRADOR)
# =============================================================================


@router.get(
    "/admin/categorias",
    response_model=List[CategoriaAdminOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Atributos"],
    summary="Listar categorias con metricas (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def listar_categorias_admin(
    db: Session = Depends(get_db),
) -> List[CategoriaAdminOut]:
    """Retorna todas las categorias con conteos de productos y subcategorias asociadas."""
    return ServicioGestionAtributos(db).listar_categorias_admin()


@router.post(
    "/admin/categorias",
    response_model=CategoriaOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Atributos"],
    summary="Crear categoria taxonomica (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_categoria(
    datos: CategoriaCrearIn,
    db: Session = Depends(get_db),
) -> CategoriaOut:
    """Crea una nueva categoria raiz o subcategoria."""
    return ServicioGestionAtributos(db).crear_categoria(datos)


@router.put(
    "/admin/categorias/{id_categoria}",
    response_model=CategoriaOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Atributos"],
    summary="Actualizar categoria (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_categoria(
    id_categoria: int,
    datos: CategoriaActualizarIn,
    db: Session = Depends(get_db),
) -> CategoriaOut:
    """Actualiza una categoria previniendo referencias circulares en el arbol."""
    return ServicioGestionAtributos(db).actualizar_categoria(id_categoria, datos)


@router.delete(
    "/admin/categorias/{id_categoria}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Atributos"],
    summary="Eliminar categoria (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_categoria(
    id_categoria: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina una categoria si no posee subcategorias ni productos asociados."""
    ServicioGestionAtributos(db).eliminar_categoria(id_categoria)


# =============================================================================
# ENDPOINTS ADMINISTRATIVOS: TALLAS (ROL ADMINISTRADOR)
# =============================================================================


@router.get(
    "/admin/tallas",
    response_model=List[TallaAdminOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Atributos"],
    summary="Listar tallas con metricas (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def listar_tallas_admin(
    db: Session = Depends(get_db),
) -> List[TallaAdminOut]:
    """Retorna la coleccion de tallas con total de variantes vinculadas."""
    return ServicioGestionAtributos(db).listar_tallas_admin()


@router.post(
    "/admin/tallas",
    response_model=TallaOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Atributos"],
    summary="Crear talla comercial (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_talla(
    datos: TallaCrearIn,
    db: Session = Depends(get_db),
) -> TallaOut:
    """Registra una nueva talla comercial con orden secuencial."""
    return ServicioGestionAtributos(db).crear_talla(datos)


@router.put(
    "/admin/tallas/{id_talla}",
    response_model=TallaOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Atributos"],
    summary="Actualizar talla comercial (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_talla(
    id_talla: int,
    datos: TallaActualizarIn,
    db: Session = Depends(get_db),
) -> TallaOut:
    """Modifica el codigo u orden secuencial de una talla existente."""
    return ServicioGestionAtributos(db).actualizar_talla(id_talla, datos)


@router.delete(
    "/admin/tallas/{id_talla}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Atributos"],
    summary="Eliminar talla comercial (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_talla(
    id_talla: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina una talla verificando que no este en uso en variantes activas."""
    ServicioGestionAtributos(db).eliminar_talla(id_talla)


# =============================================================================
# ENDPOINTS ADMINISTRATIVOS: COLORES (ROL ADMINISTRADOR)
# =============================================================================


@router.get(
    "/admin/colores",
    response_model=List[ColorAdminOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Atributos"],
    summary="Listar colores con metricas (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def listar_colores_admin(
    db: Session = Depends(get_db),
) -> List[ColorAdminOut]:
    """Retorna la coleccion de colores textiles con metricas de uso en variantes."""
    return ServicioGestionAtributos(db).listar_colores_admin()


@router.post(
    "/admin/colores",
    response_model=ColorOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Atributos"],
    summary="Crear color textil (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_color(
    datos: ColorCrearIn,
    db: Session = Depends(get_db),
) -> ColorOut:
    """Registra un nuevo color textil con codigo hexadecimal estandar #HEX."""
    return ServicioGestionAtributos(db).crear_color(datos)


@router.put(
    "/admin/colores/{id_color}",
    response_model=ColorOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Atributos"],
    summary="Actualizar color textil (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_color(
    id_color: int,
    datos: ColorActualizarIn,
    db: Session = Depends(get_db),
) -> ColorOut:
    """Actualiza la denominacion o el valor hexadecimal de un color textil."""
    return ServicioGestionAtributos(db).actualizar_color(id_color, datos)


@router.delete(
    "/admin/colores/{id_color}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Atributos"],
    summary="Eliminar color textil (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_color(
    id_color: int,
    db: Session = Depends(get_db),
) -> None:
    """Elimina un color textil verificando que no este asignado a variantes de prendas."""
    ServicioGestionAtributos(db).eliminar_color(id_color)
