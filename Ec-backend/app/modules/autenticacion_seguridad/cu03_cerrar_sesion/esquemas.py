"""Esquemas Pydantic para el caso de uso CU03: Cerrar Sesión (Logout)."""

from pydantic import BaseModel, Field


class LogoutOut(BaseModel):
    """Esquema de salida confirmando la revocación del token y cierre de sesión."""

    mensaje: str = Field(
        default="Sesión finalizada exitosamente.",
        description="Mensaje confirmando el cierre de sesión seguro.",
        json_schema_extra={"example": "Sesión finalizada exitosamente."},
    )
    revocado: bool = Field(
        default=True,
        description="Indicador de que el token ha sido revocado en el servidor.",
        json_schema_extra={"example": True},
    )
    codigo: str = Field(
        default="SESION_FINALIZADA",
        description="Código de evento para trazabilidad y auditoría.",
        json_schema_extra={"example": "SESION_FINALIZADA"},
    )
