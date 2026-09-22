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
    # Se sirven únicamente boutiques reales de `fashionstore.sucursales`. Hasta el 2026-09-22
    # este endpoint inventaba tres sedes (Serrano, Saint-Honoré y un hub de Madrid) cuando la
    # tabla venía vacía, y asignaba `cantidad_disponible = 5` fijo a cualquier boutique real.
    # Eso hacía que la interfaz ofreciese existencias que la reserva rechazaba después, además
    # de incumplir la regla de dominio «cero datos inventados». Una lista vacía es una respuesta
    # legítima: el cliente debe mostrar su estado vacío.
    sucursales = ReservaRepositorio.obtener_sucursales_activas(db)

    resultado = []
    for suc in sucursales:
        resultado.append(
            DisponibilidadSucursalItemOut(
                id_sucursal=suc.id_sucursal,
                nombre=suc.nombre,
                ciudad=suc.ciudad.nombre if suc.ciudad else "",
                direccion=suc.direccion,
                telefono=suc.telefono,
                horario_apertura=suc.horario_apertura or "09:00",
                horario_cierre=suc.horario_cierre or "20:00",
                # Este endpoint es un directorio de boutiques, no una consulta de inventario:
                # las existencias por prenda se obtienen de
                # `GET /api/v1/productos/{id}/disponibilidad`, que sí las lee de la base.
                cantidad_disponible=0,
                cantidad_reservada=0,
                estado_stock="disponible",
                badge_stock="CITAS DISPONIBLES",
                citas_disponibles_texto="Citas de prueba disponibles",
                permite_reserva_directa=True,
            )
        )
    return resultado
