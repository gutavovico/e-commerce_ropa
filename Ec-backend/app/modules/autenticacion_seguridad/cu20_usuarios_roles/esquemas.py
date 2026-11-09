"""Esquemas Pydantic v2 para el caso de uso CU20: Gestionar Usuarios y Roles."""

from datetime import datetime
from enum import Enum
import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RolUsuarioEnum(str, Enum):
    """Roles de entrada. `cliente` se acepta en el esquema para responder con un error de dominio
    claro (P2-CU03 B2, 422 `ROL_NO_PERMITIDO`): los clientes se registran por su cuenta."""

    ADMINISTRADOR = "administrador"
    ENCARGADO_SUCURSAL = "encargado_sucursal"
    CAJERO = "cajero"
    CLIENTE = "cliente"


#: P2-CU03 (RN07): roles que operan en sucursales concretas; el administrador opera en todas.
ROLES_CON_SUCURSALES = (RolUsuarioEnum.ENCARGADO_SUCURSAL, RolUsuarioEnum.CAJERO)


def _sin_repetidos(ids: Optional[List[int]]) -> Optional[List[int]]:
    if ids is None:
        return None
    vistos: List[int] = []
    for i in ids:
        if i is not None and i > 0 and i not in vistos:
            vistos.append(i)
    return vistos


def validar_complejidad_password(v: str) -> str:
    """Valida los requisitos de seguridad para contrasenas."""
    if len(v) < 8:
        raise ValueError("La contrasena debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", v):
        raise ValueError("La contrasena debe contener al menos una letra mayuscula.")
    if not re.search(r"[a-z]", v):
        raise ValueError("La contrasena debe contener al menos una letra minuscula.")
    if not re.search(r"\d", v):
        raise ValueError("La contrasena debe contener al menos un digito numerico.")
    return v


class UsuarioCrearIn(BaseModel):
    """Payload para registro y alta de un nuevo usuario corporativo o cliente."""

    email: EmailStr = Field(..., description="Correo electronico unico del usuario")
    password: str = Field(..., min_length=8, description="Contrasena en texto plano")
    nombres: str = Field(..., min_length=2, max_length=100, description="Nombres del usuario")
    apellidos: str = Field(..., min_length=2, max_length=100, description="Apellidos del usuario")
    telefono: Optional[str] = Field(None, max_length=30, description="Numero de contacto")
    rol: RolUsuarioEnum = Field(..., description="Rol RBAC asignado")
    id_sucursal: Optional[int] = Field(
        None, description="Compatibilidad: equivale a una única sucursal autorizada y principal"
    )
    sucursales_autorizadas: Optional[List[int]] = Field(
        None, description="P2-CU03 (RN07): sucursales en las que opera un encargado o cajero"
    )
    id_sucursal_principal: Optional[int] = Field(None, description="Debe estar entre las autorizadas")

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return validar_complejidad_password(v)

    @field_validator("nombres", "apellidos")
    @classmethod
    def limpiar_espacios(cls, v: str) -> str:
        v_limpio = v.strip()
        if not v_limpio:
            raise ValueError("El campo no puede estar compuesto exclusivamente por espacios en blanco.")
        return v_limpio

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def validar_sucursal_segun_rol(self) -> "UsuarioCrearIn":
        """Normaliza las sucursales: `id_sucursal` sola equivale a `[id_sucursal]` con esa principal.
        Que la principal esté en la lista lo comprueba el servicio (`SUCURSAL_PRINCIPAL_INVALIDA`)."""
        if self.rol in ROLES_CON_SUCURSALES:
            lista = _sin_repetidos(self.sucursales_autorizadas)
            if lista is None:
                lista = _sin_repetidos([self.id_sucursal] if self.id_sucursal else [])
            if not lista:
                raise ValueError(
                    f"El rol '{self.rol.value}' requiere al menos una sucursal autorizada."
                )
            principal = self.id_sucursal_principal or self.id_sucursal
            if principal is None and len(lista) == 1:
                principal = lista[0]
            self.sucursales_autorizadas = lista
            self.id_sucursal_principal = principal
            self.id_sucursal = principal
        else:
            self.sucursales_autorizadas = []
            self.id_sucursal_principal = None
            self.id_sucursal = None
        return self


class UsuarioActualizarIn(BaseModel):
    """Payload para actualizacion de datos de un usuario existente."""

    email: Optional[EmailStr] = Field(None, description="Correo electronico corporativo o cliente")
    nombres: Optional[str] = Field(None, min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=30)
    rol: Optional[RolUsuarioEnum] = None
    id_sucursal: Optional[int] = None
    #: Si llega, sustituye la lista completa. Si solo llega `id_sucursal`, equivale a `[id_sucursal]`.
    sucursales_autorizadas: Optional[List[int]] = None
    id_sucursal_principal: Optional[int] = None

    @field_validator("email")
    @classmethod
    def normalizar_email_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().lower()
        return v

    @field_validator("nombres", "apellidos")
    @classmethod
    def limpiar_espacios_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = v.strip()
            if not v_limpio:
                raise ValueError("El campo no puede estar compuesto exclusivamente por espacios en blanco.")
            return v_limpio
        return v

    @model_validator(mode="after")
    def validar_sucursal_segun_rol(self) -> "UsuarioActualizarIn":
        if self.rol in ROLES_CON_SUCURSALES:
            if self.id_sucursal is not None and self.id_sucursal <= 0:
                raise ValueError(
                    f"El campo id_sucursal debe ser un identificador valido para el rol '{self.rol.value}'."
                )
        elif self.rol in (RolUsuarioEnum.ADMINISTRADOR, RolUsuarioEnum.CLIENTE):
            self.id_sucursal = None
            self.sucursales_autorizadas = []
            self.id_sucursal_principal = None
            return self
        self.sucursales_autorizadas = _sin_repetidos(self.sucursales_autorizadas)
        if self.sucursales_autorizadas is None and self.id_sucursal:
            self.sucursales_autorizadas = [self.id_sucursal]
        if self.id_sucursal_principal is None and self.id_sucursal:
            self.id_sucursal_principal = self.id_sucursal
        return self


class UsuarioEstadoIn(BaseModel):
    """Payload para conmutacion logica del estado de la cuenta."""

    activo: bool = Field(..., description="Nuevo estado de la cuenta: True=Activo, False=Suspendido")


class ResetPasswordIn(BaseModel):
    """Payload para restablecimiento administrativo de contrasena."""

    nuevo_password: str = Field(..., min_length=8, description="Nueva contrasena segura")

    @field_validator("nuevo_password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return validar_complejidad_password(v)


class SucursalAutorizadaOut(BaseModel):
    """P2-CU03 (RN07): una sucursal autorizada del empleado."""

    id_sucursal: int
    nombre: Optional[str] = None
    es_principal: bool = False


class UsuarioResumenOut(BaseModel):
    """DTO de salida para listados y vistas resumidas."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    email: str
    nombres: str
    apellidos: str
    nombre_completo: str
    telefono: Optional[str] = None
    rol: str
    id_sucursal: Optional[int] = None
    sucursal_nombre: Optional[str] = None
    sucursal_ciudad: Optional[str] = None
    sucursales_autorizadas: List[SucursalAutorizadaOut] = Field(default_factory=list)
    activo: bool
    fecha_registro: datetime
    ultimo_acceso: Optional[datetime] = None


class UsuarioDetalleOut(BaseModel):
    """DTO de salida detallado para consultas individuales y respuestas de mutacion."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    email: str
    nombres: str
    apellidos: str
    nombre_completo: str
    telefono: Optional[str] = None
    rol: str
    id_sucursal: Optional[int] = None
    sucursal_nombre: Optional[str] = None
    sucursal_ciudad: Optional[str] = None
    sucursales_autorizadas: List[SucursalAutorizadaOut] = Field(default_factory=list)
    activo: bool
    fecha_registro: datetime
    ultimo_acceso: Optional[datetime] = None


class ListaPaginadaUsuariosOut(BaseModel):
    """Contenedor de respuesta paginada para administracion de usuarios."""

    items: List[UsuarioResumenOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int
