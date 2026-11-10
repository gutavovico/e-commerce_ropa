"""Servicio transaccional de dominio para CU12: Reservar Varias Prendas."""

from dataclasses import dataclass
from datetime import timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from core.errors import ConflictError, DomainError, NotFoundError
from core.tenant import contexto
from core.tiempo import ahora as ahora_utc
from modules.catalogo.modelos import SucursalORM
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio
from modules.reservas.modelos import ReservaORM
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.reservas.cu12_reservar_prendas.esquemas import (
    ReservaCreadaOut,
    ReservaCrearIn,
    ReservaItemOut,
)
from modules.reservas.utilidades import formatear_codigo_reserva
from modules.reservas.cu12_reservar_prendas.repositorio import ReservaRepositorio

# Tope de unidades de una misma variante por cita, alineado con `ReservaItemIn.cantidad` (le=5).
MAX_UNIDADES_POR_VARIANTE = 5

#: RN25: horas por defecto. Solo se usa con una sesión simulada (pruebas unitarias); con base de
#: datos real manda `configuracion_tenant.horas_vencimiento_reserva`.
HORAS_VENCIMIENTO_POR_DEFECTO = 24


@dataclass
class ReservaRegistrada:
    """Reserva creada y aún sin confirmar (`commit`), para quien gestiona la transacción (CU19)."""

    reserva: ReservaORM
    sucursal: SucursalORM
    items: List[ReservaItemOut]


class ReservaServicio:
    """Orquestador transaccional de reservas de citas presenciales en boutiques de alta costura."""

    @staticmethod
    def crear_reserva_presencial(
        db: Session,
        usuario: UsuarioORM,
        payload: ReservaCrearIn,
    ) -> ReservaCreadaOut:
        """Formaliza la cita de prueba en boutique, apartando inventario y registrando auditoría física."""
        registrada = ReservaServicio.registrar(db, usuario, payload)
        # Confirmación atómica de la transacción.
        # `commit()` expira la instancia, así que el refresh es obligatorio: si fallara, los
        # accesos posteriores a `reserva.*` dispararían igualmente un lazy-load contra la BD.
        # Silenciarlo solo convertiría un error diagnosticable en uno opaco.
        db.commit()
        db.refresh(registrada.reserva)
        ReservaServicio.auditar(db, usuario, registrada)
        from integrations.fcm_service import notificar_cliente
        nombre_suc = getattr(getattr(registrada, "sucursal", None), "nombre", "la boutique")
        notificar_cliente(
            db,
            id_cliente=usuario.id_usuario,
            titulo="Reserva confirmada",
            cuerpo=f"Tu cita de prueba en {nombre_suc} ha sido confirmada.",
            datos={"pantalla": "reservas", "id": str(registrada.reserva.id_reserva)},
        )
        db.commit()
        return ReservaServicio.salida(registrada)

    @staticmethod
    def horas_vencimiento(db: Session) -> int:
        """Horas de vencimiento vigentes de la empresa (RN25, CU11 C7)."""
        if contexto(db) is None:
            return HORAS_VENCIMIENTO_POR_DEFECTO
        return ParametrosEmpresaServicio.vigentes(db).horas_vencimiento_reserva

    @staticmethod
    def registrar(
        db: Session,
        usuario: UsuarioORM,
        payload: ReservaCrearIn,
        codigo_provisional: Optional[str] = None,
    ) -> ReservaRegistrada:
        """Valida, aparta el stock y crea la reserva **sin confirmar la transacción**.

        La usan la reserva en línea (que confirma a continuación) y la sincronización de CU19,
        que la confirma junto con el registro de la operación. Lanza las excepciones de dominio
        de siempre; quien llama decide si deshace.
        """
        # 1. Validar Boutique Insignia
        sucursal = ReservaRepositorio.obtener_sucursal_activa(db, payload.id_sucursal)
        if not sucursal:
            raise NotFoundError(
                f"La boutique insignia #{payload.id_sucursal} no se encuentra activa o no existe.",
                code="SUCURSAL_NO_ENCONTRADA",
            )

        # 2. Validar Fecha y Hora de Cita
        ahora = ahora_utc()
        fecha_cita = payload.fecha_hora_atencion
        if fecha_cita.tzinfo is None:
            fecha_cita = fecha_cita.replace(tzinfo=timezone.utc)

        if fecha_cita <= ahora:
            raise DomainError(
                "La fecha y hora de la cita de prueba debe ser posterior al momento actual.",
                code="FECHA_HORA_INVALIDA",
            )

        # P2-CU15 (RN25): la reserva vence a las horas de la empresa desde su creación. Una cita
        # posterior a ese instante no llegaría a atenderse: se rechaza antes de apartar nada.
        horas = ReservaServicio.horas_vencimiento(db)
        vence_en = ahora + timedelta(hours=horas)
        if fecha_cita > vence_en:
            raise DomainError(
                f"La reserva se mantiene {horas} h desde que la haces. Elige una hora de visita "
                "dentro de ese plazo.",
                code="CITA_FUERA_DE_PLAZO",
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
                # P2-CU15 A3: proponer ajustar la cantidad u otra sucursal.
                alternativas = [
                    {"id_sucursal": otra.id_sucursal, "nombre": otra.nombre}
                    for otra in ReservaRepositorio.sucursales_con_existencias(
                        db, id_variante, cantidad_total, payload.id_sucursal
                    )
                ]
                raise ConflictError(
                    f"No hay existencias suficientes de '{variante.producto.nombre}' (Talla {variante.talla.codigo}) "
                    f"en {sucursal.nombre}. Disponibles: {disp_actual}, Solicitadas: {cantidad_total}.",
                    code="STOCK_INSUFICIENTE_RESERVA",
                    datos={
                        "id_variante": id_variante,
                        "disponible": disp_actual,
                        "alternativas": alternativas,
                    },
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
            creado_en=ahora,
            vence_en=vence_en,
            codigo_provisional=codigo_provisional,
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
            ReservaRepositorio.registrar_movimiento_inventario(
                db=db,
                id_inventario=inventario.id_inventario,
                cantidad=cant,
                id_usuario=usuario.id_usuario,
                referencia=ref_doc,
                observacion=obs_mov,
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

        return ReservaRegistrada(reserva=reserva, sucursal=sucursal, items=items_procesados)

    @staticmethod
    def codigo(reserva: ReservaORM) -> str:
        return formatear_codigo_reserva(reserva.id_reserva or 1, reserva.creado_en or ahora_utc())

    @staticmethod
    def auditar(db: Session, usuario: UsuarioORM, registrada: ReservaRegistrada) -> None:
        """Bitácora (CU30) de una reserva ya confirmada."""
        reserva, sucursal, items_procesados = registrada.reserva, registrada.sucursal, registrada.items
        res_id = reserva.id_reserva or 1
        cod_reserva = ReservaServicio.codigo(reserva)

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
                "codigo_provisional": reserva.codigo_provisional,
            },
            db=db,
        )

    @staticmethod
    def salida(registrada: ReservaRegistrada) -> ReservaCreadaOut:
        reserva, sucursal, items_procesados = registrada.reserva, registrada.sucursal, registrada.items
        return ReservaCreadaOut(
            id_reserva=reserva.id_reserva or 1,
            codigo_reserva=ReservaServicio.codigo(reserva),
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
            creado_en=reserva.creado_en or ahora_utc(),
            vence_en=reserva.vence_en,
            codigo_provisional=reserva.codigo_provisional,
        )
