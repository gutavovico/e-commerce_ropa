from pathlib import Path
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.gestion_operativa.cu22_prendas_productos.esquemas import (
    ImagenSubidaOut,
    MatrizGenerarIn,
    ProductoActualizarIn,
    ProductoCrearIn,
    ProductoDetalleOut,
    ProductoEstadoIn,
    ProductoResumenOut,
    VarianteActualizarIn,
    VarianteItemIn,
    VarianteOut,
)
from modules.gestion_operativa.cu22_prendas_productos.servicio import (
    ServicioGestionProductos,
    ServicioGestionVariantes,
)

FORMATOS_IMAGEN_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_TAMANO_IMAGEN_BYTES = 5 * 1024 * 1024  # 5 MB
DIRECTORIO_UPLOADS = (
    Path(__file__).resolve().parents[4] / "static" / "uploads" / "productos"
)

router = APIRouter()


# =============================================================================
# ENDPOINTS PUBLICOS: FICHA TECNICA DE PRODUCTO
# =============================================================================


@router.get(
    "/productos/{id_producto}",
    response_model=ProductoDetalleOut,
    status_code=status.HTTP_200_OK,
    tags=["Catalogo Publico"],
    summary="Obtener ficha tecnica de producto activo con sus variantes (Publico)",
)
def obtener_producto_publico(
    id_producto: int,
    db: Session = Depends(get_db),
) -> ProductoDetalleOut:
    """Retorna los datos comerciales, descripciones y variantes activas de una prenda."""
    return ServicioGestionProductos.obtener_producto_por_id(db, id_producto, solo_activos=True)


# =============================================================================
# ENDPOINTS ADMINISTRATIVOS: GESTION DE PRENDAS (ROL ADMINISTRADOR)
# =============================================================================


@router.get(
    "/admin/productos",
    response_model=List[ProductoResumenOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Prendas y Productos"],
    summary="Listar prendas con filtros administrativos (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def listar_productos_admin(
    q: Optional[str] = Query(None, description="Termino de busqueda por nombre o descripcion"),
    id_categoria: Optional[int] = Query(None, description="Filtrar por ID de categoria"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado de publicacion"),
    pagina: int = Query(1, ge=1, description="Numero de pagina"),
    limite: int = Query(50, ge=1, le=100, description="Cantidad por pagina"),
    db: Session = Depends(get_db),
) -> List[ProductoResumenOut]:
    """Retorna el listado de prendas enriquecido con metricas consolidadas de variantes y stock."""
    items, _ = ServicioGestionProductos.listar_productos_admin(
        db, q=q, id_categoria=id_categoria, activo=activo, pagina=pagina, limite=limite
    )
    return items


@router.post(
    "/admin/productos",
    response_model=ProductoResumenOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Prendas y Productos"],
    summary="Alta de prenda o producto base (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_producto(
    payload: ProductoCrearIn,
    db: Session = Depends(get_db),
) -> ProductoResumenOut:
    """Registra una nueva prenda en el catalogo maestro tras validar unicidad y reglas comerciales."""
    return ServicioGestionProductos.crear_producto(db, payload)


@router.post(
    "/admin/productos/upload-imagen",
    response_model=ImagenSubidaOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Prendas y Productos"],
    summary="Cargar imagen local de prenda (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
async def upload_imagen_producto(
    archivo: UploadFile = File(...),
) -> ImagenSubidaOut:
    """Valida y almacena una imagen en el almacenamiento local estatico para prendas."""
    content_type = archivo.content_type.lower() if archivo.content_type else ""
    if content_type not in FORMATOS_IMAGEN_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen no admitido. Solo se admiten formatos JPEG, PNG y WebP.",
        )

    contenido = await archivo.read()
    if len(contenido) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo proporcionado esta vacio.",
        )

    if len(contenido) > MAX_TAMANO_IMAGEN_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tamano de la imagen excede el limite maximo permitido de 5 MB.",
        )

    extension = FORMATOS_IMAGEN_PERMITIDOS[content_type]
    nombre_archivo = f"prod_{uuid.uuid4().hex[:12]}{extension}"

    DIRECTORIO_UPLOADS.mkdir(parents=True, exist_ok=True)
    ruta_guardado = DIRECTORIO_UPLOADS / nombre_archivo

    with open(ruta_guardado, "wb") as buffer:
        buffer.write(contenido)

    return ImagenSubidaOut(url=f"/static/uploads/productos/{nombre_archivo}")


@router.get(
    "/admin/productos/{id_producto}",
    response_model=ProductoDetalleOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Prendas y Productos"],
    summary="Consultar ficha tecnica completa de producto con variantes (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def obtener_producto_admin(
    id_producto: int,
    db: Session = Depends(get_db),
) -> ProductoDetalleOut:
    """Retorna la informacion editorial y todas las variantes (activas e inactivas) de la prenda."""
    return ServicioGestionProductos.obtener_producto_por_id(db, id_producto, solo_activos=False)


@router.put(
    "/admin/productos/{id_producto}",
    response_model=ProductoResumenOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Prendas y Productos"],
    summary="Modificar datos comerciales y taxonomicos de una prenda (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_producto(
    id_producto: int,
    payload: ProductoActualizarIn,
    db: Session = Depends(get_db),
) -> ProductoResumenOut:
    """Actualiza la denominacion, precio base, descripcion y categoria de un producto existente."""
    return ServicioGestionProductos.actualizar_producto(db, id_producto, payload)


@router.patch(
    "/admin/productos/{id_producto}/estado",
    response_model=ProductoResumenOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Prendas y Productos"],
    summary="Conmutar visibilidad comercial de una prenda - Baja/Alta logica (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def cambiar_estado_producto(
    id_producto: int,
    payload: ProductoEstadoIn,
    db: Session = Depends(get_db),
) -> ProductoResumenOut:
    """Conmuta el campo activo de una prenda para retirarla o publicarla en vitrina."""
    return ServicioGestionProductos.cambiar_estado_producto(db, id_producto, payload.activo)


@router.delete(
    "/admin/productos/{id_producto}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Prendas y Productos"],
    summary="Eliminar fisicamente una prenda sin dependencias operativas (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_producto(
    id_producto: int,
    db: Session = Depends(get_db),
) -> Response:
    """Elimina una prenda si y solo si carece de existencias en inventario, ventas o reservas."""
    ServicioGestionProductos.eliminar_producto(db, id_producto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# ENDPOINTS ADMINISTRATIVOS: GESTION DE VARIANTES (SKUs Y MATRIZ)
# =============================================================================


@router.post(
    "/admin/productos/{id_producto}/variantes/matriz",
    response_model=List[VarianteOut],
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Variantes y SKUs"],
    summary="Generar matriz cartesiana de variantes por lote (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def generar_matriz_variantes(
    id_producto: int,
    payload: MatrizGenerarIn,
    db: Session = Depends(get_db),
) -> List[VarianteOut]:
    """Genera de forma masiva y atomica variantes combinando tallas y colores seleccionados con SKUs corporativos."""
    return ServicioGestionVariantes.generar_matriz_variantes(db, id_producto, payload)


@router.post(
    "/admin/productos/{id_producto}/variantes",
    response_model=VarianteOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Variantes y SKUs"],
    summary="Crear una variante individual para una prenda (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def crear_variante_individual(
    id_producto: int,
    payload: VarianteItemIn,
    db: Session = Depends(get_db),
) -> VarianteOut:
    """Registra una variante especifica de talla y color con SKU opcional personalizado."""
    return ServicioGestionVariantes.crear_variante_individual(db, id_producto, payload)


@router.get(
    "/admin/productos/{id_producto}/variantes",
    response_model=List[VarianteOut],
    status_code=status.HTTP_200_OK,
    tags=["Admin - Variantes y SKUs"],
    summary="Listar variantes de una prenda (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def listar_variantes_producto(
    id_producto: int,
    db: Session = Depends(get_db),
) -> List[VarianteOut]:
    """Retorna todas las variantes registradas para una prenda especifica."""
    return ServicioGestionVariantes.listar_variantes_producto(db, id_producto)


@router.put(
    "/admin/variantes/{id_variante}",
    response_model=VarianteOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Variantes y SKUs"],
    summary="Actualizar SKU o recargo de precio de una variante (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def actualizar_variante(
    id_variante: int,
    payload: VarianteActualizarIn,
    db: Session = Depends(get_db),
) -> VarianteOut:
    """Modifica el SKU, recargo de precio o estado comercial de una variante."""
    return ServicioGestionVariantes.actualizar_variante(db, id_variante, payload)


@router.patch(
    "/admin/variantes/{id_variante}/estado",
    response_model=VarianteOut,
    status_code=status.HTTP_200_OK,
    tags=["Admin - Variantes y SKUs"],
    summary="Conmutar disponibilidad logica de una variante (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def cambiar_estado_variante(
    id_variante: int,
    payload: ProductoEstadoIn,
    db: Session = Depends(get_db),
) -> VarianteOut:
    """Conmuta el estado activo de una variante fisica sin destruirla."""
    return ServicioGestionVariantes.cambiar_estado_variante(db, id_variante, payload.activo)


@router.delete(
    "/admin/variantes/{id_variante}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin - Variantes y SKUs"],
    summary="Eliminar fisicamente una variante sin dependencias operativas (Admin)",
    dependencies=[Depends(require_roles(["administrador"]))],
)
def eliminar_variante(
    id_variante: int,
    db: Session = Depends(get_db),
) -> Response:
    """Elimina una variante fisica si no posee inventario asociado ni registros transaccionales."""
    ServicioGestionVariantes.eliminar_variante(db, id_variante)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
