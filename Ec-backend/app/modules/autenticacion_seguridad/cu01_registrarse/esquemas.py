"""Esquemas de validacion Pydantic v2 para CU01: Registrarse."""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegistroClienteIn(BaseModel):
    """Payload de entrada para el registro de un nuevo cliente."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(
        ...,
        description="Correo electronico del cliente (unico en el sistema)",
        max_length=255,
        examples=["cliente@fashionstore.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contrasena en texto plano (minimo 8 caracteres)",
        examples=["PasswordSeguro123!"],
    )
    nombres: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombres del cliente",
        examples=["Ana Maria"],
    )
    apellidos: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Apellidos del cliente",
        examples=["Garcia Morales"],
    )
    telefono: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Numero telefonico o de WhatsApp",
        examples=["+591 70012345"],
    )
    talla_preferida: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Talla habitual de prenda (XS, S, M, L, XL, XXL)",
        examples=["M"],
    )
    ciudad_preferida: Optional[int] = Field(
        default=None,
        description="ID de la ciudad principal de residencia",
        examples=[1],
    )

    @field_validator("talla_preferida")
    @classmethod
    def validar_talla(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            tallas_validas = {"XS", "S", "M", "L", "XL", "XXL"}
            v_normalizado = v.upper().strip()
            if v_normalizado not in tallas_validas:
                raise ValueError(f"Talla no valida. Debe ser una de: {', '.join(sorted(tallas_validas))}")
            return v_normalizado
        return v


class RegistroClienteOut(BaseModel):
    """Payload de salida retornado tras un registro exitoso (HTTP 201)."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: int = Field(..., description="Identificador unico del usuario registrado")
    email: str = Field(..., description="Correo electronico confirmado")
    nombres: str = Field(..., description="Nombres del cliente")
    apellidos: str = Field(..., description="Apellidos del cliente")
    rol: str = Field(default="cliente", description="Rol asignado en el sistema")
    token_acceso: str = Field(..., description="Token JWT de acceso emitido")
    tipo_token: str = Field(default="bearer", description="Esquema de autorizacion HTTP")
