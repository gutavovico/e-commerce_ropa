"""Router centralizador del paquete de dominio reservas."""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from modules.reservas.cu12_reservar_prendas.router import (
    router as cu12_router,
)
from modules.reservas.cu13_consultar_cancelar_reservas.router import (
    router as cu13_router,
)

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de reservas
router.include_router(cu12_router)
router.include_router(cu13_router)


class VencerExpiradasOut(BaseModel):
    ok: bool = True
    vencidas_total: int
    empresas_procesadas: int


@router.post(
    "/reservas/vencer-expiradas",
    response_model=VencerExpiradasOut,
    summary="Tarea programada: vencer reservas expiradas (AC-C7)",
)
def vencer_reservas_expiradas_cron(
    x_tareas_token: Optional[str] = Header(None, alias="X-Tareas-Token"),
    db: Session = Depends(get_db),
) -> VencerExpiradasOut:
    token_esperado = (settings.TAREAS_TOKEN or "").strip()
    if not token_esperado or x_tareas_token != token_esperado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de tareas programadas inválido o ausente.",
        )

    from core.tenant import empresas_disponibles, fijar_contexto
    from modules.reservas.cu13_consultar_cancelar_reservas.servicio import ReservaConsultaServicio

    empresas = empresas_disponibles(db)
    total_vencidas = 0
    empresas_conteo = 0

    if empresas:
        for emp in empresas:
            fijar_contexto(db, emp.id_tenant)
            vencidas = ReservaConsultaServicio.vencer_todas_expiradas(db)
            total_vencidas += vencidas
            empresas_conteo += 1
    else:
        total_vencidas += ReservaConsultaServicio.vencer_todas_expiradas(db)
        empresas_conteo = 1

    return VencerExpiradasOut(
        ok=True,
        vencidas_total=total_vencidas,
        empresas_procesadas=empresas_conteo,
    )

