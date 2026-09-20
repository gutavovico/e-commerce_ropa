"""Esquemas Pydantic v2 para CU33 - Recuperar Acceso de Cuenta."""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class SolicitarCodigoIn(BaseModel):
    """Payload de entrada para solicitar código de recuperación."""

    email: EmailStr = Field(
        ...,
        description="Correo electrónico asociado a la cuenta de usuario.",
        examples=["ana.valenzuela@fashionstore.com"],
    )


class SolicitarCodigoOut(BaseModel):
    """Respuesta neutra anti-enumeración de usuarios."""

    mensaje: str = Field(
        default="Si el correo electrónico se encuentra registrado en nuestra plataforma, recibirás un código de verificación de 6 dígitos en los próximos instantes.",
        description="Mensaje uniforme para prevenir ataques de enumeración.",
        examples=[
            "Si el correo electrónico se encuentra registrado en nuestra plataforma, recibirás un código de verificación de 6 dígitos en los próximos instantes."
        ],
    )
    tiempo_espera_segundos: int = Field(
        default=60,
        description="Tiempo de enfriamiento (cooldown) en segundos para solicitar un nuevo código.",
        examples=[60],
    )


class RestablecerPasswordIn(BaseModel):
    """Payload para validar el código OTP y fijar la nueva contraseña."""

    email: EmailStr = Field(
        ...,
        description="Correo electrónico del usuario.",
        examples=["ana.valenzuela@fashionstore.com"],
    )
    codigo: str = Field(
        ...,
        min_length=6,
        max_length=7,
        description="Código numérico de 6 dígitos recibido por correo (admite espacio central '849 201').",
        examples=["849201"],
    )
    nueva_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nueva contraseña (mínimo 8 caracteres, al menos una letra y un dígito).",
        examples=["HauteCouture2026"],
    )
    confirmar_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Confirmación idéntica de la nueva contraseña.",
        examples=["HauteCouture2026"],
    )

    @field_validator("codigo")
    @classmethod
    def normalizar_y_validar_codigo(cls, v: str) -> str:
        clean = v.replace(" ", "").strip()
        if not clean.isdigit() or len(clean) != 6:
            raise ValueError("El código de verificación debe contener exactamente 6 dígitos numéricos.")
        return clean

    @field_validator("nueva_password")
    @classmethod
    def validar_complejidad(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La nueva contraseña debe tener al menos 8 caracteres.")
        tiene_letra = any(c.isalpha() for c in v)
        tiene_numero = any(c.isdigit() for c in v)
        if not (tiene_letra and tiene_numero):
            raise ValueError("La contraseña debe combinar al menos una letra y un número (A-Z, 0-9).")
        return v

    @model_validator(mode="after")
    def validar_coincidencia(self) -> "RestablecerPasswordIn":
        if self.nueva_password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden. Verifica la confirmación.")
        return self


class RestablecerPasswordOut(BaseModel):
    """Respuesta de confirmación tras restablecer la contraseña."""

    mensaje: str = Field(
        default="Contraseña actualizada exitosamente. Ya puedes iniciar sesión con tus nuevas credenciales.",
        description="Mensaje confirmando la actualización de contraseña.",
        examples=[
            "Contraseña actualizada exitosamente. Ya puedes iniciar sesión con tus nuevas credenciales."
        ],
    )
    exito: bool = Field(default=True, examples=[True])
    codigo_evento: str = Field(
        default="PASSWORD_RESTABLECIDA",
        description="Código de evento para trazabilidad y auditoría.",
        examples=["PASSWORD_RESTABLECIDA"],
    )
