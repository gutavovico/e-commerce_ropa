"""Configuracion centralizada del backend de FashionStore.

Todos los valores se leen de variables de entorno (o de un archivo .env).
Los campos sin default son obligatorios; si faltan, Pydantic lanza
ValidationError al iniciar la aplicacion (AC-17).
"""

import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion del backend cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Obligatorios (sin default) ---
    DATABASE_URL: str
    JWT_SECRET: str

    # --- Opcionales (con default) ---
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: list[str] | str = ["http://localhost:4200"]
    CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    IA_API_KEY: str = ""

    # --- Notificaciones SMTP Gmail ---
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "fashionstore321@gmail.com"
    SMTP_PASSWORD: str = "PasswordSegura321"
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str = "Fashion Store Atelier"

    # --- Políticas OTP Recuperación ---
    OTP_EXPIRE_MINUTES: int = 15
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Permite cargar CORS_ORIGINS como lista separada por comas o como JSON."""
        if isinstance(v, str):
            v_strip = v.strip()
            if v_strip.startswith("[") and v_strip.endswith("]"):
                try:
                    return json.loads(v_strip)
                except Exception:
                    pass
            return [origin.strip() for origin in v_strip.split(",") if origin.strip()]
        return v


settings = Settings()
