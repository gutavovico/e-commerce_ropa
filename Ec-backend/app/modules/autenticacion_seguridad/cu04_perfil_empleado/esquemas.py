"""Esquemas del perfil del empleado (fix: el panel usaba el perfil del cliente y daba 403).

Administrador, encargado de sucursal y cajero consultan sus datos, su empresa y sus sucursales,
cambian nombre, apellidos y teléfono, y cambian su propia contraseña.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from modules.autenticacion_seguridad.cu20_usuarios_roles.esquemas import validar_complejidad_password


class EmpresaPerfilOut(BaseModel):
    codigo: str
    nombre: str
    moneda: str


class SucursalPerfilOut(BaseModel):
    id_sucursal: int
    nombre: Optional[str] = None
    es_principal: bool = False


class PerfilEmpleadoOut(BaseModel):
    id_usuario: int
    email: str
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    rol: str
    empresa: Optional[EmpresaPerfilOut] = None
    #: El administrador opera en todas las sucursales de su empresa (RN07): lista vacía y `True`.
    todas_las_sucursales: bool = False
    sucursales: List[SucursalPerfilOut] = Field(default_factory=list)
    ultimo_acceso: Optional[datetime] = None


class PerfilEmpleadoActualizarIn(BaseModel):
    nombres: Optional[str] = Field(None, min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=30)

    @field_validator("nombres", "apellidos")
    @classmethod
    def sin_espacios_sueltos(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("Debe tener al menos 2 caracteres.")
        return limpio

    @field_validator("telefono")
    @classmethod
    def telefono_limpio(cls, valor: Optional[str]) -> Optional[str]:
        return valor.strip() or None if valor is not None else None


class CambioContrasenaIn(BaseModel):
    contrasena_actual: str = Field(..., min_length=1)
    contrasena_nueva: str = Field(..., min_length=8)

    @field_validator("contrasena_nueva")
    @classmethod
    def politica(cls, valor: str) -> str:
        return validar_complejidad_password(valor)
