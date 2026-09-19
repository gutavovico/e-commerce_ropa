"""Esquemas Pydantic v2 para CU04: Gestionar Perfil del Cliente."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ResumenAtelierOut(BaseModel):
    """Métricas y resumen de alta costura para el panel Mi Cuenta."""

    visitas_registradas: int = Field(default=32, description="Visitas privadas registradas en ateliers")
    boutiques_visitadas: int = Field(default=4, description="Número de boutiques exclusivas frecuentadas")
    preferencia_textil: str = Field(default="100% Seda & Lana", description="Preferencia de fibras textiles puras")
    estatus_membresia: str = Field(default="Nivel Platino", description="Nivel de membresía de alta costura")


class PerfilClienteOut(BaseModel):
    """DTO de salida para la consulta y confirmación de actualización de perfil."""

    model_config = ConfigDict(from_attributes=True)

    # Identidad y Cuenta (Solo Lectura)
    id_usuario: int = Field(..., description="ID primario del usuario")
    numero_socio: str = Field(..., description="Número de socio formateado (ej. #8402)")
    email: EmailStr = Field(..., description="Correo electrónico registrado")
    rol: str = Field(default="cliente", description="Rol del usuario en la plataforma")
    fecha_registro: datetime = Field(..., description="Fecha y hora de creación de la cuenta")
    miembro_desde: str = Field(..., description="Texto legible de antigüedad (ej. Octubre 2021)")
    ultimo_acceso: Optional[datetime] = Field(None, description="Última sesión registrada")

    # Datos Personales (fashionstore.usuarios)
    nombres: str = Field(..., min_length=1, max_length=100, description="Nombres del cliente")
    apellidos: str = Field(..., min_length=1, max_length=100, description="Apellidos del cliente")
    telefono: Optional[str] = Field(None, max_length=30, description="Teléfono de contacto")

    # Datos Específicos del Cliente (fashionstore.clientes)
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento del cliente")
    genero: Optional[str] = Field(None, description="femenino, masculino, no_binario, prefiero_no_decir")
    talla_preferida: Optional[str] = Field(None, description="Talla de alta costura (XS, S, M, L, XL, XXL, etc.)")
    ciudad_preferida: Optional[int] = Field(None, description="ID de ciudad preferida")
    acepta_marketing: bool = Field(default=True, description="Preferencia de notificaciones y cápsulas privadas")

    # Resumen Haute Couture
    resumen_atelier: ResumenAtelierOut = Field(default_factory=ResumenAtelierOut)


class PerfilClienteUpdateIn(BaseModel):
    """DTO de entrada para la actualización parcial o total de datos del cliente."""

    nombres: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombres actualizados")
    apellidos: Optional[str] = Field(None, min_length=1, max_length=100, description="Apellidos actualizados")
    telefono: Optional[str] = Field(None, max_length=30, description="Teléfono de contacto")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    genero: Optional[str] = Field(
        None,
        pattern=r"^(femenino|masculino|no_binario|prefiero_no_decir)$",
        description="Género con valores normalizados",
    )
    talla_preferida: Optional[str] = Field(
        None,
        pattern=r"^(XS|S|M|L|XL|XXL|[0-9]{2})$",
        description="Talla preferida estándar o numérica europea",
    )
    ciudad_preferida: Optional[int] = Field(None, description="ID de ciudad preferida")
    acepta_marketing: Optional[bool] = Field(None, description="Preferencia de comunicaciones de marketing")
