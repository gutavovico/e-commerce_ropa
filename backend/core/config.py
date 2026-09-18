"""Configuracion centralizada del backend de FashionStore.

Todos los valores se leen de variables de entorno (o de un archivo .env).
Los campos sin default son obligatorios; si faltan, Pydantic lanza
ValidationError al iniciar la aplicacion (AC-17).
"""

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
    JWT_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    IA_API_KEY: str = ""


settings = Settings()
