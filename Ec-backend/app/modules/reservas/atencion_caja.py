"""Atención en caja de reservas (CU31-CU32, decisión D5).

Único punto por el que el punto de venta (`compras_pagos`) opera sobre reservas: la regla de
arquitectura exige que el acceso entre paquetes vaya por el servicio, nunca por los modelos.

Invariante de inventario: las unidades de una reserva están en `cantidad_reservada` de la fila
exacta que apartó CU12 (la del movimiento `reserva` con `referencia_documento = RESERVA-{id}`). Al
cobrar, lo que el cliente se lleva sale de esa fila (`venta_confirmada`) y lo que deja vuelve a
`cantidad_disponible` (`liberacion_reserva`). Nunca se recalcula la temporada.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from core.errors import AuthorizationError, ConflictError, NotFoundError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.reservas.cu13_consultar_cancelar_reservas.repositorio import ReservaConsultaRepositorio
from modules.reservas.cu13_consultar_cancelar_reservas.servicio import (
    ESTADOS_ACTIVOS,
    ReservaConsultaServicio,
)
from modules.reservas.modelos import MovimientoInventarioORM, ReservaDetalleORM, ReservaORM
from modules.reservas.utilidades import formatear_codigo_reserva

_PATRON_CODIGO = re.compile(r"^RES-\d{4}-(\d+)$", re.IGNORECASE)


def _id_desde_referencia(referencia: str) -> Optional[int]:
    """Acepta el id numérico (`7`) o el código legible (`RES-2026-0007`)."""
    texto = referencia.strip()
    if texto.isdigit():
        return int(texto)
    coincidencia = _PATRON_CODIGO.match(texto)
    return int(coincidencia.group(1)) if coincidencia else None


class ReservaCajaServicio:
    """Operaciones de tienda sobre una reserva que se cobra en caja."""

    @staticmethod
    def codigo(reserva: ReservaORM) -> str:
        return formatear_codigo_reserva(reserva.id_reserva, reserva.creado_en)

    @staticmethod
    def obtener_para_caja(
        db: Session, referencia: str, id_sucursal: int, usuario: UsuarioORM
    ) -> ReservaORM:
        """Carga y bloquea una reserva atendible en la sucursal del punto de venta.

        Aplica antes el vencimiento perezoso de CU13: una cita pasada fuera de la tolerancia se
        vence (y libera su stock) en lugar de cobrarse.
        """
        id_reserva = _id_desde_referencia(referencia)
        reserva = (
            ReservaConsultaRepositorio.obtener_reserva_para_actualizar(db, id_reserva)
            if id_reserva is not None
            else None
        )
        if reserva is None:
            raise NotFoundError(f"No existe la reserva «{referencia}».", code="RESERVA_NO_ENCONTRADA")

        codigo = ReservaCajaServicio.codigo(reserva)
        if reserva.id_sucursal != id_sucursal:
            raise AuthorizationError(
                f"La reserva {codigo} pertenece a otra boutique.", code="SUCURSAL_AJENA"
            )

        if ReservaConsultaServicio._vencer_si_corresponde(db, reserva, usuario):
            raise ConflictError(
                f"La reserva {codigo} venció sin ser atendida y sus prendas volvieron a estar disponibles.",
                code="RESERVA_NO_ATENDIBLE",
            )
        if reserva.estado not in ESTADOS_ACTIVOS:
            raise ConflictError(
                f"La reserva {codigo} está «{reserva.estado}» y no puede cobrarse.",
                code="RESERVA_NO_ATENDIBLE",
            )
        return reserva

    @staticmethod
    def atendibles_de_cliente(db: Session, id_cliente: int, id_sucursal: int) -> List[ReservaORM]:
        """Reservas del cliente que la caja de esta sucursal puede cargar ahora, por fecha de cita.

        Solo lectura: excluye las que ya están en una orden de caja (`en_atencion`) y las que el
        vencimiento perezoso de CU13 vencería al cargarlas, sin vencerlas aquí.
        """
        reservas = ReservaConsultaRepositorio.buscar_reservas_de_cliente(db, id_cliente)
        return sorted(
            (
                r
                for r in reservas
                if r.id_sucursal == id_sucursal
                and r.estado in ("pendiente", "confirmada")
                and not ReservaConsultaServicio._es_candidata_a_vencer(r)
            ),
            key=lambda r: r.fecha_hora_atencion,
        )

    @staticmethod
    def _fila_apartada(db: Session, reserva: ReservaORM, id_variante: int):
        movimiento = ReservaConsultaRepositorio.buscar_movimiento_reserva(db, reserva.id_reserva, id_variante)
        inventario = (
            ReservaConsultaRepositorio.obtener_inventario_por_id(db, movimiento.id_inventario)
            if movimiento
            else None
        )
        if inventario is None:
            raise ConflictError(
                f"No se encontró el apartado original de la reserva {ReservaCajaServicio.codigo(reserva)}.",
                code="RESERVA_SIN_TRAZA",
            )
        return inventario

    @staticmethod
    def consolidar_linea(
        db: Session,
        reserva: ReservaORM,
        detalle: ReservaDetalleORM,
        usuario: UsuarioORM,
        id_venta: int,
        numero_comprobante: str,
    ) -> None:
        """La prenda apartada sale definitivamente del almacén (`venta_confirmada`)."""
        inventario = ReservaCajaServicio._fila_apartada(db, reserva, detalle.id_variante)
        if inventario.cantidad_reservada < detalle.cantidad:
            raise ConflictError(
                f"El inventario apartado para la reserva {ReservaCajaServicio.codigo(reserva)} es inconsistente.",
                code="RESERVA_SIN_TRAZA",
            )
        saldo_anterior = inventario.cantidad_reservada
        inventario.cantidad_reservada -= detalle.cantidad
        db.add(
            MovimientoInventarioORM(
                id_inventario=inventario.id_inventario,
                tipo_movimiento="venta_confirmada",
                cantidad=-detalle.cantidad,
                id_usuario=usuario.id_usuario,
                referencia_documento=f"VENTA-{id_venta}",
                motivo=(
                    f"Venta en caja {numero_comprobante} de la reserva "
                    f"{ReservaCajaServicio.codigo(reserva)}"
                ),
                saldo_anterior=saldo_anterior,
                saldo_nuevo=inventario.cantidad_reservada,
            )
        )

    @staticmethod
    def liberar_linea(
        db: Session,
        reserva: ReservaORM,
        detalle: ReservaDetalleORM,
        usuario: UsuarioORM,
        numero_comprobante: str,
    ) -> None:
        """La prenda que el cliente probó y no se lleva vuelve a estar disponible."""
        inventario = ReservaCajaServicio._fila_apartada(db, reserva, detalle.id_variante)
        cantidad = min(detalle.cantidad, inventario.cantidad_reservada)
        if cantidad <= 0:
            return
        saldo_anterior = inventario.cantidad_disponible
        inventario.cantidad_reservada -= cantidad
        inventario.cantidad_disponible += cantidad
        ReservaConsultaRepositorio.registrar_movimiento_liberacion(
            db=db,
            id_inventario=inventario.id_inventario,
            cantidad=cantidad,
            id_usuario=usuario.id_usuario,
            referencia=f"RESERVA-{reserva.id_reserva}",
            motivo=f"Prenda probada y no comprada (venta en caja {numero_comprobante})",
            saldo_anterior=saldo_anterior,
            saldo_nuevo=inventario.cantidad_disponible,
        )

    @staticmethod
    def bloquear(db: Session, id_reserva: int) -> Optional[ReservaORM]:
        """Reserva ya vinculada a una venta de caja, bloqueada para cobrarla o anularla."""
        return ReservaConsultaRepositorio.obtener_reserva_para_actualizar(db, id_reserva)

    @staticmethod
    def marcar_en_atencion(reserva: ReservaORM) -> None:
        """La reserva está en una orden de caja: CU13 ya no la vence ni deja cancelarla
        (`en_atencion` queda fuera de sus estados vencibles y cancelables)."""
        reserva.estado = "en_atencion"

    @staticmethod
    def devolver_a_confirmada(reserva: ReservaORM) -> None:
        """La orden de caja se anuló: la reserva sigue viva, con su stock apartado."""
        if reserva.estado == "en_atencion":
            reserva.estado = "confirmada"

    @staticmethod
    def marcar_atendida(reserva: ReservaORM, usuario: UsuarioORM) -> None:
        reserva.estado = "atendida"
        reserva.atendido_por = usuario.id_usuario
        reserva.atendido_en = datetime.now(timezone.utc)
