"""Router FastAPI para P2-CU23, P2-CU24 y P2-CU25: Aprendizaje Automático (ML)."""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu23_cu25_aprendizaje_ml.esquemas import (
    ConsultaPrediccionesOut,
    ConsultaSegmentosOut,
    CrearDatasetMlIn,
    DatasetMlOut,
    EntrenarModeloMlIn,
    ModeloMlOut,
    ResumenAprendizajeMlOut,
)
from modules.comercial.cu23_cu25_aprendizaje_ml.servicio import AprendizajeMlServicio

router = APIRouter(
    prefix="/aprendizaje-ml",
    tags=["Comercial - Aprendizaje Automático ML (P2-CU23 a P2-CU25)"],
)

exigir_admin_empresa = require_roles(["administrador", "admin"])


@router.get(
    "/resumen",
    response_model=ResumenAprendizajeMlOut,
    status_code=status.HTTP_200_OK,
    summary="Obtiene datasets, modelos, variables y contexto de la empresa en Bolivianos (P2-CU23)",
)
def obtener_resumen_ml(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> ResumenAprendizajeMlOut:
    return AprendizajeMlServicio.obtener_resumen(db, usuario)


@router.post(
    "/datasets",
    response_model=DatasetMlOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crea y preprocesa un conjunto de datos sintético, real o mixto (P2-CU23)",
)
def crear_dataset_ml(
    datos: CrearDatasetMlIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> DatasetMlOut:
    ip = request.client.host if request.client else None
    return AprendizajeMlServicio.crear_dataset(db, datos, usuario, direccion_ip=ip)


@router.post(
    "/modelos/entrenar",
    response_model=ModeloMlOut,
    status_code=status.HTTP_201_CREATED,
    summary="Entrena y evalúa un modelo supervisado o no supervisado (P2-CU23, RN49)",
)
def entrenar_modelo_ml(
    datos: EntrenarModeloMlIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> ModeloMlOut:
    ip = request.client.host if request.client else None
    return AprendizajeMlServicio.entrenar_modelo(db, datos, usuario, direccion_ip=ip)


@router.patch(
    "/modelos/{id_modelo}/activar",
    response_model=ModeloMlOut,
    status_code=status.HTTP_200_OK,
    summary="Activa un modelo evaluado para dejarlo disponible en CU24 o CU25 (P2-CU23 paso 7)",
)
def activar_modelo_ml(
    id_modelo: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> ModeloMlOut:
    ip = request.client.host if request.client else None
    return AprendizajeMlServicio.activar_modelo(db, id_modelo, usuario, direccion_ip=ip)


@router.patch(
    "/modelos/{id_modelo}/archivar",
    response_model=ModeloMlOut,
    status_code=status.HTTP_200_OK,
    summary="Archiva un modelo conservando sus métricas de evaluación (P2-CU23 A5)",
)
def archivar_modelo_ml(
    id_modelo: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> ModeloMlOut:
    ip = request.client.host if request.client else None
    return AprendizajeMlServicio.archivar_modelo(db, id_modelo, usuario, direccion_ip=ip)


@router.get(
    "/predicciones",
    response_model=ConsultaPrediccionesOut,
    status_code=status.HTTP_200_OK,
    summary="Consulta las predicciones del modelo supervisado activo en Bolivianos (P2-CU24, RN50)",
)
def consultar_predicciones_ml(
    id_producto: Optional[int] = Query(default=None),
    id_sucursal: Optional[int] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    tipo_cambio_bob: Decimal = Query(default=Decimal("6.96"), ge=Decimal("1.00")),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> ConsultaPrediccionesOut:
    return AprendizajeMlServicio.consultar_predicciones(
        db,
        usuario,
        id_producto=id_producto,
        id_sucursal=id_sucursal,
        periodo=periodo,
        tipo_cambio_bob=tipo_cambio_bob,
    )


@router.get(
    "/segmentos",
    response_model=ConsultaSegmentosOut,
    status_code=status.HTTP_200_OK,
    summary="Consulta los segmentos de clientes del modelo no supervisado activo en Bolivianos (P2-CU25)",
)
def consultar_segmentos_ml(
    tipo_cambio_bob: Decimal = Query(default=Decimal("6.96"), ge=Decimal("1.00")),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_admin_empresa),
) -> ConsultaSegmentosOut:
    return AprendizajeMlServicio.consultar_segmentos(
        db,
        usuario,
        tipo_cambio_bob=tipo_cambio_bob,
    )
