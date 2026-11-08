"""Router de P2-CU02 · Acceso por empresa. Solo HTTP."""

from typing import List

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.plataforma.cu02_acceso_empresa.esquemas import EmpresaOut, RegistroEnTiendaOut
from modules.plataforma.cu02_acceso_empresa.servicio import AccesoEmpresaServicio

router = APIRouter(tags=["P2-CU02 Acceso por empresa"])


@router.get("/tenants", response_model=List[EmpresaOut], summary="Directorio de tiendas disponibles")
def directorio(db: Session = Depends(get_db)) -> List[EmpresaOut]:
    return AccesoEmpresaServicio.directorio(db)


@router.get("/tenants/{codigo}", response_model=EmpresaOut, summary="Datos públicos del portal de una tienda")
def portal(codigo: str, db: Session = Depends(get_db)) -> EmpresaOut:
    return AccesoEmpresaServicio.portal(db, codigo)


@router.get("/mis-empresas", response_model=List[EmpresaOut], summary="Tiendas en las que el cliente está registrado")
def mis_empresas(db: Session = Depends(get_db), usuario=Depends(get_current_user)) -> List[EmpresaOut]:
    return AccesoEmpresaServicio.mis_empresas(db, usuario)


@router.post(
    "/mis-empresas",
    response_model=RegistroEnTiendaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrarme en la tienda indicada en X-Tenant",
)
def registrarse_en_tienda(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
) -> RegistroEnTiendaOut:
    ip = request.client.host if request.client else None
    resultado = AccesoEmpresaServicio.registrarse_en_tienda(db, usuario, ip)
    if not resultado.registrado_ahora:
        response.status_code = status.HTTP_200_OK
    return resultado
