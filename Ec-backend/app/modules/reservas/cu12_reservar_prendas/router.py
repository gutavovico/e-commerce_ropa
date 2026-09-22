"""Router HTTP de FastAPI para CU12: Reservar Varias Prendas en Boutique."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu09_disponibilidad.esquemas import DisponibilidadSucursalItemOut
from modules.reservas.cu12_reservar_prendas.esquemas import (
    ReservaCreadaOut,
    ReservaCrearIn,
)
from modules.reservas.cu12_reservar_prendas.repositorio import ReservaRepositorio
from modules.reservas.cu12_reservar_prendas.servicio import ReservaServicio

router = APIRouter(tags=["Reservas en Boutique"])


@router.post(
    "/reservas",
    response_model=ReservaCreadaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Reservar cita de prueba presencial en boutique",
    description="Crea una cita de prueba en la boutique seleccionada, aparta las prendas y audita el movimiento físico.",
)
def crear_reserva_presencial(
    payload: ReservaCrearIn,
    usuario: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReservaCreadaOut:
    """Endpoint para formalizar la reserva presencial de una o más prendas."""
    return ReservaServicio.crear_reserva_presencial(db, usuario, payload)


@router.get(
    "/sucursales/activas",
    response_model=List[DisponibilidadSucursalItemOut],
    status_code=status.HTTP_200_OK,
    summary="Listar boutiques físicas activas",
    description="Retorna el directorio de boutiques insignia para selección en el modal de citas presenciales.",
)
def listar_sucursales_activas(
    db: Session = Depends(get_db),
) -> List[DisponibilidadSucursalItemOut]:
    """Endpoint para obtener el directorio de boutiques activas de FashionStore."""
    sucursales = ReservaRepositorio.obtener_sucursales_activas(db)
    if not sucursales:
        return [
            DisponibilidadSucursalItemOut(
                id_sucursal=1,
                nombre="Flagship Serrano (Madrid)",
                ciudad="Madrid",
                direccion="Calle de Serrano 44, Salamanca",
                telefono="91 555 0123",
                horario_apertura="09:00",
                horario_cierre="20:00",
                cantidad_disponible=2,
                cantidad_reservada=0,
                estado_stock="disponible",
                badge_stock="2 UDS EN STOCK",
                citas_disponibles_texto="Citas de prueba disponibles hoy y mañana",
                permite_reserva_directa=True,
            ),
            DisponibilidadSucursalItemOut(
                id_sucursal=2,
                nombre="Boutique Paris Saint-Honoré",
                ciudad="París",
                direccion="228 Rue du Faubourg Saint-Honoré",
                telefono="+33 1 42 68 0000",
                horario_apertura="09:00",
                horario_cierre="20:00",
                cantidad_disponible=1,
                cantidad_reservada=0,
                estado_stock="disponible",
                badge_stock="1 UD EN STOCK",
                citas_disponibles_texto="Horario preferente con concierge bilingüe",
                permite_reserva_directa=True,
            ),
            DisponibilidadSucursalItemOut(
                id_sucursal=3,
                nombre="Madrid Central Atelier Hub",
                ciudad="Madrid",
                direccion="Paseo de la Castellana 92",
                telefono="91 555 0199",
                horario_apertura="09:00",
                horario_cierre="20:00",
                cantidad_disponible=0,
                cantidad_reservada=0,
                estado_stock="agotada",
                badge_stock="CITA CON SASTRE JEFE",
                citas_disponibles_texto="Sesión de patronaje y ajuste personalizado (60 min)",
                permite_reserva_directa=False,
            ),
        ]

    resultado = []
    for suc in sucursales:
        resultado.append(
            DisponibilidadSucursalItemOut(
                id_sucursal=suc.id_sucursal,
                nombre=suc.nombre,
                ciudad=suc.ciudad.nombre if suc.ciudad else "Madrid",
                direccion=suc.direccion,
                telefono=suc.telefono,
                horario_apertura=suc.horario_apertura or "09:00",
                horario_cierre=suc.horario_cierre or "20:00",
                cantidad_disponible=5,
                cantidad_reservada=0,
                estado_stock="disponible",
                badge_stock="CITAS DISPONIBLES",
                citas_disponibles_texto="Citas de prueba disponibles",
                permite_reserva_directa=True,
            )
        )
    return resultado
