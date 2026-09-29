"""Router HTTP de FastAPI para CU13 (Consultar y cancelar reservas) y CU14 (Consultar estado de
reserva)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.reservas.cu13_consultar_cancelar_reservas.esquemas import (
    MisReservasOut,
    ReservaCancelarIn,
    ReservaOut,
)
from modules.reservas.cu13_consultar_cancelar_reservas.servicio import ReservaConsultaServicio

router = APIRouter(tags=["Reservas en Boutique"])


@router.get(
    "/reservas/mias",
    response_model=MisReservasOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar mis reservas de citas presenciales",
    description=(
        "Lista las reservas del cliente autenticado, separadas en próximas e historial. "
        "Cubre CU13 (listado para cancelar) y CU14 (consulta de estado desde el panel del "
        "cliente): cada reserva ya trae su estado y prendas completos."
    ),
)
def listar_mis_reservas(
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MisReservasOut:
    """Endpoint de lectura del panel de reservas del cliente."""
    return ReservaConsultaServicio.listar_mis_reservas(db, usuario)


@router.post(
    "/reservas/{id_reserva}/cancelar",
    response_model=ReservaOut,
    status_code=status.HTTP_200_OK,
    summary="Cancelar una reserva de cita presencial",
    description=(
        "Cancela una reserva propia en estado 'pendiente' o 'confirmada', antes de la hora de "
        "la cita, y libera de inmediato las existencias apartadas."
    ),
    responses={
        403: {"description": "La reserva pertenece a otro cliente"},
        404: {"description": "La reserva no existe"},
        409: {"description": "La reserva no admite cancelación, o venció sin ser atendida"},
    },
)
def cancelar_reserva(
    id_reserva: int,
    payload: ReservaCancelarIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReservaOut:
    """Endpoint de cancelación de CU13, con motivo obligatorio."""
    return ReservaConsultaServicio.cancelar_reserva(db, usuario, id_reserva, payload)
