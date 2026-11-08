"""Esquemas de P2-CU02 · Acceso por empresa."""

from pydantic import BaseModel, Field


class EmpresaOut(BaseModel):
    """Datos públicos de una empresa (tienda)."""

    codigo: str = Field(..., examples=["fashionstore"])
    nombre: str = Field(..., examples=["FASHION STORE"])


class RegistroEnTiendaOut(BaseModel):
    """Resultado de «Registrarme en esta tienda»."""

    empresa: EmpresaOut
    registrado_ahora: bool = Field(..., description="False si el cliente ya estaba registrado")
