"""Esquemas Pydantic v2 para CU25: Gestionar Proveedores."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# --- Esquemas de Entrada (Requests) ---

class ProveedorCrearIn(BaseModel):
    """Payload para registro de un nuevo socio comercial en el padron."""
    razon_social: str = Field(..., min_length=3, max_length=150, description="Denominacion legal de la empresa")
    nit_rut: str = Field(..., min_length=5, max_length=30, description="Identificacion fiscal tributaria unica")
    contacto_nombre: str = Field(..., min_length=3, max_length=120, description="Nombre y apellido del enlace comercial")
    telefono: str = Field(..., min_length=7, max_length=30, description="Numero telefonico institucional")
    email: EmailStr = Field(..., description="Correo electronico corporativo de contacto")
    direccion: str = Field(..., min_length=5, max_length=255, description="Direccion fisica o domicilio legal")
    ciudad: str = Field(..., min_length=2, max_length=80, description="Ciudad de operacion del proveedor")
    rubro: str = Field(..., min_length=3, max_length=80, description="Especialidad textil o tipo de insumo provisto")

    @field_validator("razon_social", "nit_rut", "contacto_nombre", "telefono", "direccion", "ciudad", "rubro")
    @classmethod
    def sanitizar_cadenas(cls, valor: str) -> str:
        saneado = valor.strip()
        if not saneado:
            raise ValueError("El campo no puede estar compuesto exclusivamente por espacios en blanco.")
        return saneado


class ProveedorActualizarIn(BaseModel):
    """Payload para actualizacion parcial o total de la ficha del proveedor."""
    razon_social: Optional[str] = Field(None, min_length=3, max_length=150)
    nit_rut: Optional[str] = Field(None, min_length=5, max_length=30)
    contacto_nombre: Optional[str] = Field(None, min_length=3, max_length=120)
    telefono: Optional[str] = Field(None, min_length=7, max_length=30)
    email: Optional[EmailStr] = Field(None)
    direccion: Optional[str] = Field(None, min_length=5, max_length=255)
    ciudad: Optional[str] = Field(None, min_length=2, max_length=80)
    rubro: Optional[str] = Field(None, min_length=3, max_length=80)

    @field_validator("razon_social", "nit_rut", "contacto_nombre", "telefono", "direccion", "ciudad", "rubro")
    @classmethod
    def sanitizar_opcionales(cls, valor: Optional[str]) -> Optional[str]:
        if valor is not None:
            saneado = valor.strip()
            if not saneado:
                raise ValueError("El campo no puede ser una cadena vacia.")
            return saneado
        return valor


class ProveedorEstadoIn(BaseModel):
    """Payload para conmutacion del estado operativo (baja logica o reactivacion)."""
    estado_activo: bool = Field(..., description="True para habilitar, False para baja logica")


class ProveedorFiltrosIn(BaseModel):
    """Parametros de consulta y filtrado multicriterio."""
    q: Optional[str] = Field(None, max_length=100, description="Busqueda por razon social, NIT o contacto")
    estado_activo: Optional[bool] = Field(None, description="Filtro por estado booleano")
    rubro: Optional[str] = Field(None, max_length=80, description="Filtro por rubro comercial")
    pagina: int = Field(default=1, ge=1)
    limite: int = Field(default=20, ge=1, le=100)


# --- Esquemas de Salida (Responses) ---

class ProveedorItemOut(BaseModel):
    """Representacion publica y tipada de la entidad Proveedor."""
    model_config = ConfigDict(from_attributes=True)

    id_proveedor: int
    id_usuario: Optional[int] = None
    razon_social: str
    nit_rut: str
    contacto_nombre: Optional[str] = "Contacto no registrado"
    telefono: Optional[str] = "No registrado"
    email: Optional[str] = ""
    direccion: Optional[str] = "Direccion no registrada"
    ciudad: Optional[str] = "La Paz"
    rubro: Optional[str] = "Confeccion Textil"
    estado_activo: bool = True
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    @field_validator("contacto_nombre", "telefono", "email", "direccion", "ciudad", "rubro", mode="before")
    @classmethod
    def normalizar_nulos_texto(cls, valor: Optional[str]) -> str:
        if valor is None:
            return ""
        return str(valor)

    @field_validator("actualizado_en", mode="before")
    @classmethod
    def normalizar_actualizado_en(cls, valor: Optional[datetime]) -> Optional[datetime]:
        return valor


class ListaPaginadaProveedoresOut(BaseModel):
    """Contenedor paginado para respuestas del padron de proveedores."""
    items: List[ProveedorItemOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int
