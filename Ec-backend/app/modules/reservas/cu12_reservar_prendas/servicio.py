"""Servicio transaccional de dominio para CU12: Reservar Varias Prendas."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List
from sqlalchemy.orm import Session

from core.errors import ConflictError, DomainError, NotFoundError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.reservas.cu12_reservar_prendas.esquemas import (
    ReservaCreadaOut,
    ReservaCrearIn,
    ReservaItemOut,
)
from modules.reservas.cu12_reservar_prendas.repositorio import ReservaRepositorio

# Tope de unidades de una misma variante por cita, alineado con `ReservaItemIn.cantidad` (le=5).
MAX_UNIDADES_POR_VARIANTE = 5


class ReservaServicio:
    """Orquestador transaccional de reservas de citas presenciales en boutiques de alta costura."""

    @staticmethod
    def crear_reserva_presencial(
        db: Session,
        usuario: UsuarioORM,
        payload: ReservaCrearIn,
    ) -> ReservaCreadaOut:
        """Formaliza la cita de prueba en boutique, apartando inventario y registrando auditoría física."""
        # 1. Validar Boutique Insignia
        sucursal = ReservaRepositorio.obtener_sucursal_activa(db, payload.id_sucursal)
        if not sucursal:
            raise NotFoundError(
                f"La boutique insignia #{payload.id_sucursal} no se encuentra activa o no existe.",
                code="SUCURSAL_NO_ENCONTRADA",
            )

        # 2. Validar Fecha y Hora de Cita
        ahora = datetime.now(timezone.utc)
        fecha_cita = payload.fecha_hora_atencion
        if fecha_cita.tzinfo is None:
            fecha_cita = fecha_cita.replace(tzinfo=timezone.utc)

        if fecha_cita <= ahora:
            raise DomainError(
                "La fecha y hora de la cita de prueba debe ser posterior al momento actual.",
                code="FECHA_HORA_INVALIDA",
            )

        # 3. Asegurar Ficha de Cliente
        cliente = ReservaRepositorio.asegurar_cliente(db, usuario)

        # 4. Consolidar Prendas Repetidas
        # `reserva_detalle` tiene UNIQUE (id_reserva, id_variante), así que dos líneas con la
        # misma variante violarían la restricción y provocarían un IntegrityError no manejado
        # (500) tras haber descontado el inventario dos veces. Se agrupan sumando cantidades.
        cantidades_por_variante: Dict[int, int] = {}
        for item_in in payload.items:
            cantidades_por_variante[item_in.id_variante] = (
                cantidades_por_variante.get(item_in.id_variante, 0) + item_in.cantidad
            )

        # 5. Procesar Prendas y Validar Inventario
        items_procesados: List[ReservaItemOut] = []
        inventarios_afectados = []

        for id_variante, cantidad_total in cantidades_por_variante.items():
            variante = ReservaRepositorio.obtener_variante_con_prenda(db, id_variante)
            if not variante:
                raise NotFoundError(
                    f"La variante de prenda #{id_variante} no existe en catálogo.",
                    code="VARIANTE_NO_ENCONTRADA",
                )

            # El límite por línea (le=5) también debe respetarse sobre el total consolidado.
            if cantidad_total > MAX_UNIDADES_POR_VARIANTE:
                raise DomainError(
                    f"No es posible apartar más de {MAX_UNIDADES_POR_VARIANTE} unidades de "
                    f"'{variante.producto.nombre}' (Talla {variante.talla.codigo}) en una misma cita. "
                    f"Solicitadas: {cantidad_total}.",
                    code="CANTIDAD_MAXIMA_EXCEDIDA",
                )

            inventario = ReservaRepositorio.obtener_inventario_para_reserva(
                db, id_variante, payload.id_sucursal, cantidad_total
            )

            if not inventario or inventario.cantidad_disponible < cantidad_total:
                disp_actual = inventario.cantidad_disponible if inventario else 0
                raise ConflictError(
                    f"No hay existencias suficientes de '{variante.producto.nombre}' (Talla {variante.talla.codigo}) "
                    f"en {sucursal.nombre}. Disponibles: {disp_actual}, Solicitadas: {cantidad_total}.",
                    code="STOCK_INSUFICIENTE_RESERVA",
                )

            # Apartado de inventario. El saldo previo se captura ANTES del descuento: en el
            # paso 7, donde se escribe la bitácora, `cantidad_disponible` ya vale el nuevo.
            saldo_anterior = inventario.cantidad_disponible
            inventario.cantidad_disponible -= cantidad_total
            inventario.cantidad_reservada += cantidad_total
            inventarios_afectados.append(
                (inventario, variante, cantidad_total, saldo_anterior)
            )

        # 6. Crear Cabecera de Reserva
        canal = payload.canal_origen.lower()
        if canal not in ("web", "movil", "sucursal"):
            canal = "web"

        reserva = ReservaRepositorio.crear_reserva(
            db=db,
            id_cliente=cliente.id_cliente,
            id_sucursal=payload.id_sucursal,
            fecha_hora_atencion=fecha_cita,
            canal_origen=canal,
            observacion=payload.observacion,
        )

        # 7. Crear Líneas de Detalle y Movimientos de Inventario
        for inventario, variante, cant, saldo_anterior in inventarios_afectados:
            detalle = ReservaRepositorio.crear_detalle_reserva(
                db=db,
                id_reserva=reserva.id_reserva,
                id_variante=variante.id_variante,
                cantidad=cant,
            )

            # Movimiento de auditoría física inmutable
            ref_doc = f"RESERVA-{reserva.id_reserva}"
            obs_mov = f"Apartado para cita privada de fitting en {sucursal.nombre} ({fecha_cita.strftime('%d/%m/%Y %H:%M')})"
            saldo_ant = inventario.cantidad_disponible + cant
            saldo_nue = inventario.cantidad_disponible
            ReservaRepositorio.registrar_movimiento_inventario(
                db=db,
                id_inventario=inventario.id_inventario,
                cantidad=cant,
                id_usuario=usuario.id_usuario,
                referencia=ref_doc,
                observacion=obs_mov,
                saldo_anterior=saldo_ant,
                saldo_nuevo=saldo_nue,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=inventario.cantidad_disponible,
            )

            precio_unit = variante.producto.precio_base + (variante.precio_extra or Decimal("0.00"))
            items_procesados.append(
                ReservaItemOut(
                    id_reserva_detalle=detalle.id_reserva_detalle,
                    id_variante=variante.id_variante,
                    sku=variante.sku,
                    nombre_producto=variante.producto.nombre,
                    talla_codigo=variante.talla.codigo,
                    color_nombre=variante.color.nombre,
                    cantidad=cant,
                    precio_unitario=precio_unit,
                )
            )

        # Confirmación atómica de la transacción.
        # `commit()` expira la instancia, así que el refresh es obligatorio: si fallara, los
        # accesos posteriores a `reserva.*` dispararían igualmente un lazy-load contra la BD.
        # Silenciarlo solo convertiría un error diagnosticable en uno opaco.
        db.commit()
        db.refresh(reserva)

        res_id = reserva.id_reserva or 1
        res_creado = reserva.creado_en or ahora
        cod_reserva = f"RES-{res_creado.year}-{res_id:04d}"

        # 8. Persistencia en Bitacora de Auditoria (CU30)
        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

        nombre_usuario = (
            f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
            if usuario
            else "Cliente Atelier"
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario if usuario else None,
            usuario_nombre=nombre_usuario,
            accion="CREAR_RESERVA",
            tabla_modulo="reservas",
            severidad="INFO",
            payload_anterior=None,
            payload_nuevo={
                "id_reserva": res_id,
                "codigo_reserva": cod_reserva,
                "id_sucursal": sucursal.id_sucursal,
                "total_items": len(items_procesados),
                "canal_origen": reserva.canal_origen,
            },
            db=db,
        )

        return ReservaCreadaOut(
            id_reserva=res_id,
            codigo_reserva=cod_reserva,
            id_sucursal=sucursal.id_sucursal,
            nombre_sucursal=sucursal.nombre,
            direccion_sucursal=sucursal.direccion,
            fecha_hora_atencion=reserva.fecha_hora_atencion,
            estado=reserva.estado,
            canal_origen=reserva.canal_origen,
            items=items_procesados,
            mensaje_confirmacion="Cita de prueba presencial confirmada con nuestro equipo de sastrería.",
            cortesias_incluidas=[
                "Champán de cortesía o infusión artesanal de bienvenida",
                "Asesoramiento privado de estilista sénior de atelier",
                "Ajustes menores de costura y entallado sin coste adicional",
            ],
            creado_en=res_creado,
        )
