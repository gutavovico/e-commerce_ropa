"""Esquemas de validacion Pydantic v2 para CU02: Iniciar Sesion (Login)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginIn(BaseModel):
    """Payload de entrada para autenticacion de credenciales (Login)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(
        ...,
        description="Correo electronico registrado del usuario",
        max_length=255,
        examples=["c.laurent@atelier-mode.fr"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Contrasena en texto plano para verificacion",
        examples=["PasswordSeguro123!"],
    )
    recordar_dispositivo: bool = Field(
        default=False,
        description="Indica si el usuario solicito mantener la sesion prolongada en el cliente",
    )
    codigo_empresa: Optional[str] = Field(
        default=None,
        max_length=60,
        pattern=r"^[a-z0-9-]{3,60}$",
        description=(
            "P2-CU02/RN03: código de la empresa del empleado. Opcional durante la transición "
            "(spec §1.3): sin él, un empleado entra en la empresa por defecto."
        ),
        examples=["fashionstore"],
    )


class TenantSesionOut(BaseModel):
    """Empresa en la que queda fijada la sesión (P2-CU13)."""

    codigo: str
    nombre: str


class LoginOut(BaseModel):
    """Payload de salida retornado tras autenticacion exitosa (HTTP 200)."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(
        ...,
        description="Token JWT firmado (HS256) con expiracion y claims de usuario",
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token para uso en cabecera Authorization: Bearer <token>",
    )
    id_usuario: int = Field(
        ...,
        description="Identificador primario del usuario en fashionstore.usuarios",
    )
    email: str = Field(
        ...,
        description="Correo electronico normalizado del usuario",
    )
    nombres: str = Field(
        ...,
        description="Nombres del usuario",
    )
    apellidos: str = Field(
        ...,
        description="Apellidos del usuario",
    )
    rol: str = Field(
        ...,
        description="Rol del usuario (cliente, administrador, encargado_sucursal, etc.)",
    )
    tenant: Optional[TenantSesionOut] = Field(
        default=None,
        description="Empresa de la sesión; null para el super administrador o un cliente sin empresa",
    )
