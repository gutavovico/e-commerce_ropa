"""Router de P2-CU18 · Registrar cambio de prenda. Solo HTTP.

Mismos roles y alcance de sucursal que la caja (cajero, encargado y administrador). Registrar exige
la funcionalidad «ventas» del plan con la suscripción vigente.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu18_cambio_prenda.esquemas import CambioIn, CambioOut, CambioPrevioOut, VentaCambiableOut
from modules.compras_pagos.cu18_cambio_prenda.servicio import CambioPrendaServicio
from modules.compras_pagos.cu31_cu32_punto_venta.servicio import ROLES_CAJA
from modules.plataforma.cu12_validar_suscripcion.dependencias import requiere_funcionalidad

router = APIRouter(prefix="/pos/cambios", tags=["P2-CU18 Cambio de prenda"])

Cajero = Depends(require_roles(list(ROLES_CAJA)))
SucursalQuery = Query(None, gt=0, description="Solo el administrador: sucursal en la que opera.")


@router.get("/venta", response_model=VentaCambiableOut, summary="Venta pagada que se puede cambiar")
def venta_cambiable(
    comprobante: str = Query(..., min_length=3, max_length=30),
    id_sucursal: Optional[int] = SucursalQuery,
    usuario: UsuarioORM = Cajero,
    db: Session = Depends(get_db),
) -> VentaCambiableOut:
    return CambioPrendaServicio.venta_cambiable(db, usuario, comprobante, id_sucursal)


@router.post("/previsualizar", response_model=CambioPrevioOut, summary="Valores y diferencia, sin registrar")
def previsualizar(datos: CambioIn, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> CambioPrevioOut:
    return CambioPrendaServicio.previsualizar(db, usuario, datos)


@router.post(
    "",
    response_model=CambioOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_funcionalidad("ventas"))],
    summary="Registrar el cambio de prenda",
)
def registrar(datos: CambioIn, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> CambioOut:
    return CambioPrendaServicio.registrar(db, usuario, datos)


@router.get("", response_model=List[CambioOut], summary="Cambios de la sucursal")
def listar(
    id_sucursal: Optional[int] = SucursalQuery,
    solo_hoy: bool = Query(True),
    usuario: UsuarioORM = Cajero,
    db: Session = Depends(get_db),
) -> List[CambioOut]:
    return CambioPrendaServicio.listar(db, usuario, id_sucursal, solo_hoy)


@router.get("/{id_cambio}", response_model=CambioOut, summary="Comprobante de un cambio")
def obtener(id_cambio: int, usuario: UsuarioORM = Cajero, db: Session = Depends(get_db)) -> CambioOut:
    return CambioPrendaServicio.obtener(db, usuario, id_cambio)
