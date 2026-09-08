import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = FastAPI(
    title="Ecommerce API",
    description="Backend API con FastAPI para el sistema Ecommerce",
    version="1.0.0",
)

# Configuración de CORS
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:4200")
allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str = Field(default="online", description="Estado del servicio")
    service: str = Field(default="Ec-backend", description="Identificador del servicio")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Fecha y hora UTC actual",
    )


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """Endpoint de comprobación de estado de salud del backend."""
    return HealthResponse(status="online")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bienvenido a Ecommerce API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
