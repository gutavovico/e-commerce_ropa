"""Servicio de dominio para CU09: Disponibilidad por Sucursal."""

from typing import List, Optional
from sqlalchemy.orm import Session

from core.errors import NotFoundError
from modules.catalogo.cu09_disponibilidad.esquemas import (
    DisponibilidadSucursalItemOut,
    DisponibilidadSucursalesOut,
)
from modules.catalogo.cu09_disponibilidad.repositorio import DisponibilidadRepositorio


class DisponibilidadServicio:
    """Orquestador de disponibilidad física en boutiques de alta costura."""

    @staticmethod
    def consultar_disponibilidad(
        db: Session, id_producto: int, id_variante: Optional[int] = None
    ) -> DisponibilidadSucursalesOut:
        """Calcula el stock disponible en cada boutique física para la prenda o variante especificada."""
        producto = DisponibilidadRepositorio.obtener_producto_con_variantes(db, id_producto)
        if not producto:
            raise NotFoundError(
                f"La prenda con identificador #{id_producto} no existe o no está activa.",
                code="PRODUCTO_NO_ENCONTRADO",
            )

        variante_activa = None
        if id_variante is not None:
            variante_activa = next(
                (v for v in producto.variantes if v.id_variante == id_variante), None
            )
            if not variante_activa:
                raise NotFoundError(
                    f"La variante #{id_variante} no corresponde a la prenda #{id_producto}.",
                    code="VARIANTE_NO_ENCONTRADA",
                )
        elif producto.variantes:
            variante_activa = producto.variantes[0]

        sucursales = DisponibilidadRepositorio.obtener_sucursales_activas(db)

        # Mapa de existencias por id_sucursal
        if variante_activa:
            invs = DisponibilidadRepositorio.obtener_inventario_variante(db, variante_activa.id_variante)
        else:
            invs = DisponibilidadRepositorio.obtener_inventario_producto(db, id_producto)

        stock_por_sucursal = {}
        reservado_por_sucursal = {}
        for inv in invs:
            stock_por_sucursal[inv.id_sucursal] = stock_por_sucursal.get(inv.id_sucursal, 0) + inv.cantidad_disponible
            reservado_por_sucursal[inv.id_sucursal] = reservado_por_sucursal.get(inv.id_sucursal, 0) + inv.cantidad_reservada

        items_sucursal: List[DisponibilidadSucursalItemOut] = []
        total_global = 0

        # Si no hay sucursales en BD, proveer las boutiques insignia de FashionStore por defecto
        if not sucursales:
            sucursales_mock = [
                (1, "Flagship Serrano (Madrid)", "Madrid", "Calle de Serrano 44, Salamanca", "91 555 0123", 2, 0),
                (2, "Boutique Saint-Honoré (París)", "París", "228 Rue du Faubourg Saint-Honoré", "+33 1 42 68 0000", 1, 0),
                (3, "Madrid Central Atelier Hub", "Madrid", "Paseo de la Castellana 92", "91 555 0199", 0, 0),
            ]
            for sid, nom, ciu, dir_str, tel, disp, res in sucursales_mock:
                cant_disp = stock_por_sucursal.get(sid, disp)
                cant_res = reservado_por_sucursal.get(sid, res)
                total_global += cant_disp

                if cant_disp >= 3:
                    estado_stk = "disponible"
                    badge_stk = f"{cant_disp} UDS EN STOCK"
                elif cant_disp > 0:
                    estado_stk = "ultimas_unidades"
                    badge_stk = f"{cant_disp} UD EN STOCK" if cant_disp == 1 else f"{cant_disp} UDS EN STOCK"
                else:
                    estado_stk = "agotada"
                    badge_stk = "CITA CON SASTRE JEFE"

                items_sucursal.append(
                    DisponibilidadSucursalItemOut(
                        id_sucursal=sid,
                        nombre=nom,
                        ciudad=ciu,
                        direccion=dir_str,
                        telefono=tel,
                        horario_apertura="09:00",
                        horario_cierre="20:00",
                        cantidad_disponible=cant_disp,
                        cantidad_reservada=cant_res,
                        estado_stock=estado_stk,
                        badge_stock=badge_stk,
                        citas_disponibles_texto="Citas de prueba disponibles hoy y mañana",
                        permite_reserva_directa=cant_disp > 0,
                    )
                )
        else:
            for suc in sucursales:
                cant_disp = stock_por_sucursal.get(suc.id_sucursal, 0)
                cant_res = reservado_por_sucursal.get(suc.id_sucursal, 0)
                total_global += cant_disp

                if cant_disp >= 3:
                    estado_stk = "disponible"
                    badge_stk = f"{cant_disp} UDS EN STOCK"
                elif cant_disp > 0:
                    estado_stk = "ultimas_unidades"
                    badge_stk = f"{cant_disp} UD EN STOCK" if cant_disp == 1 else f"{cant_disp} UDS EN STOCK"
                else:
                    estado_stk = "agotada"
                    badge_stk = "CITA CON SASTRE JEFE"

                items_sucursal.append(
                    DisponibilidadSucursalItemOut(
                        id_sucursal=suc.id_sucursal,
                        nombre=suc.nombre,
                        ciudad=suc.ciudad.nombre if suc.ciudad else "Madrid",
                        direccion=suc.direccion,
                        telefono=suc.telefono,
                        horario_apertura=suc.horario_apertura or "09:00",
                        horario_cierre=suc.horario_cierre or "20:00",
                        cantidad_disponible=cant_disp,
                        cantidad_reservada=cant_res,
                        estado_stock=estado_stk,
                        badge_stock=badge_stk,
                        citas_disponibles_texto="Citas de prueba disponibles hoy y mañana",
                        permite_reserva_directa=cant_disp > 0,
                    )
                )

        return DisponibilidadSucursalesOut(
            id_producto=id_producto,
            id_variante=variante_activa.id_variante if variante_activa else None,
            sku=variante_activa.sku if variante_activa else None,
            sucursales=items_sucursal,
            total_disponible_global=total_global,
        )
