"""Servicio de aplicación y dominio para P2-CU09 y P2-CU10 (Suscripción de la empresa + Stripe)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    PaymentRequiredError,
    ServiceUnavailableError,
)
from core.tenant import limpiar_cache_tenants, tenant_actual
from core.tiempo import hoy as hoy_bolivia
from integrations.stripe_service import ErrorPasarela, PasarelaPagos, StripeService
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu09_cu10_suscripcion_empresa.esquemas import (
    ConfirmarCambioSuscripcionIn,
    EmpresaSuscripcionInfoOut,
    FuncionalidadPlanEmpresaOut,
    HistorialMiSuscripcionOut,
    IniciarPagoSuscripcionIn,
    IntentoPagoSuscripcionOut,
    MiSuscripcionResumenOut,
    PlanDisponibleEmpresaOut,
    SucursalActivaResumenOut,
    SuscripcionEmpresaDetalleOut,
    UsoPlanEmpresaOut,
    UsoRecursoPlanOut,
)
from modules.plataforma.cu09_cu10_suscripcion_empresa.repositorio import (
    MiSuscripcionRepositorio,
)
from modules.plataforma.modelos import PlanORM, SuscripcionORM, TenantORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

DIAS_ALERTA_VENCIMIENTO = 7
DIAS_POR_MES = 30

# Registro en memoria de intentos abiertos por `iniciar_pago` para que el simulador de Stripe
# (que no persiste metadatos entre crear_intento y verificar_intento) conserve el vínculo
# con el importe, la moneda y los metadatos (id_tenant, id_plan, meses).
_INTENTOS_SUSCRIPCION_ABIERTOS: dict[str, dict[str, Any]] = {}


def registrar_intento_suscripcion(
    referencia: str,
    *,
    amount_centimos: int,
    currency: str,
    metadatos: dict[str, str],
) -> None:
    """Guarda los datos del intento abierto para verificar coherencia en `confirmar_cambio_o_renovacion`."""
    _INTENTOS_SUSCRIPCION_ABIERTOS[referencia] = {
        "amount": int(amount_centimos),
        "currency": str(currency).strip().lower(),
        "metadata": dict(metadatos),
    }


def _resolver_id_tenant_empresa(db: Session, usuario_actual: UsuarioORM) -> int:
    """Obtiene el id_tenant de la empresa del administrador autenticado.

    Nota: No invoca `SuscripcionServicio.validar()` porque `CU09 A1` y `CU10 A4` exigen que el
    administrador de la empresa pueda consultar su suscripción vencida y renovarla con Stripe.
    """
    id_tenant = getattr(usuario_actual, "id_tenant", None) or tenant_actual(db)
    if id_tenant is None:
        raise AuthorizationError(
            "Esta operación requiere pertenecer a una empresa registrada.",
            code="TENANT_REQUERIDO",
        )
    return int(id_tenant)


def _calcular_estado_y_vigencia(susc: SuscripcionORM, hoy: date) -> tuple[str, bool, int, bool]:
    """Devuelve `(estado_efectivo, vigente, dias_restantes, proxima_a_vencer)` según RN13 y RN14."""
    dias_restantes = (susc.fecha_vencimiento - hoy).days
    en_rango = susc.fecha_inicio <= hoy <= susc.fecha_vencimiento
    vigente = susc.estado in ("prueba", "activa") and en_rango

    if susc.estado in ("prueba", "activa") and hoy > susc.fecha_vencimiento:
        estado_efectivo = "vencida"
    else:
        estado_efectivo = susc.estado

    proxima_a_vencer = vigente and (0 <= dias_restantes <= DIAS_ALERTA_VENCIMIENTO)
    return estado_efectivo, vigente, dias_restantes, proxima_a_vencer


def _evaluar_compatibilidad_uso(
    *,
    plan: PlanORM,
    sucursales_activas: list[dict],
    empleados_activos: int,
) -> tuple[bool, Optional[str]]:
    """Evalúa si el uso actual cabe en los límites del plan destino (`CU10 A1`)."""
    cant_suc = len(sucursales_activas)
    motivos: list[str] = []

    if cant_suc > plan.max_sucursales_activas:
        nombres = ", ".join(s["nombre"] for s in sucursales_activas)
        motivos.append(
            f"La empresa tiene {cant_suc} sucursales activas ({nombres}) y el plan "
            f"'{plan.nombre}' permite máximo {plan.max_sucursales_activas}. "
            "Desactive las sucursales necesarias en Gestionar sucursales antes de elegir este plan."
        )
    if plan.max_empleados is not None and empleados_activos > plan.max_empleados:
        motivos.append(
            f"La empresa tiene {empleados_activos} empleados activos y el plan "
            f"'{plan.nombre}' permite máximo {plan.max_empleados}. "
            "Desactive las cuentas necesarias antes de elegir este plan."
        )

    if motivos:
        return False, " ".join(motivos)
    return True, None


def _verificar_correspondencia_intento(
    *,
    referencia_pago: str,
    payload_pasarela: dict[str, Any],
    monto_esperado: Decimal,
    moneda_esperada: str,
    id_tenant_esperado: int,
    id_plan_esperado: int,
    meses_esperados: int,
) -> None:
    """Verifica que el PaymentIntent corresponda exactamente al importe, moneda, empresa, plan y meses."""
    registrado = _INTENTOS_SUSCRIPCION_ABIERTOS.get(referencia_pago) or {}
    payload = payload_pasarela if isinstance(payload_pasarela, dict) else {}

    amount_raw = payload.get("amount", registrado.get("amount"))
    currency_raw = payload.get("currency", registrado.get("currency"))
    metadata_raw = payload.get("metadata")
    if not isinstance(metadata_raw, dict):
        metadata_raw = registrado.get("metadata")

    if amount_raw is None or currency_raw is None or not isinstance(metadata_raw, dict):
        raise ConflictError(
            "El PaymentIntent no contiene importe, moneda ni metadatos verificables para esta suscripción.",
            code="PAGO_NO_CORRESPONDE_A_SOLICITUD",
        )

    centimos_esperados = StripeService.a_centimos(monto_esperado)
    try:
        centimos_cobrados = int(amount_raw)
    except (TypeError, ValueError) as exc:
        raise ConflictError(
            "El importe del PaymentIntent es inválido.",
            code="PAGO_IMPORTE_NO_COINCIDE",
        ) from exc

    if centimos_cobrados != centimos_esperados:
        raise ConflictError(
            f"El importe del PaymentIntent ({centimos_cobrados} céntimos) no coincide con el total "
            f"recalculado del plan ({centimos_esperados} céntimos).",
            code="PAGO_IMPORTE_NO_COINCIDE",
        )

    if str(currency_raw).strip().upper() != moneda_esperada.strip().upper():
        raise ConflictError(
            f"La moneda del PaymentIntent ('{currency_raw}') no coincide con la moneda de la empresa ('{moneda_esperada}').",
            code="PAGO_MONEDA_NO_COINCIDE",
        )

    if str(metadata_raw.get("id_tenant", "")).strip() != str(id_tenant_esperado):
        raise ConflictError(
            "El PaymentIntent pertenece a otra empresa y no puede utilizarse en esta suscripción.",
            code="PAGO_EMPRESA_NO_COINCIDE",
        )

    if str(metadata_raw.get("id_plan", "")).strip() != str(id_plan_esperado):
        raise ConflictError(
            "El PaymentIntent fue emitido para un plan distinto al solicitado.",
            code="PAGO_PLAN_NO_COINCIDE",
        )

    if str(metadata_raw.get("meses", "")).strip() != str(meses_esperados):
        raise ConflictError(
            "El PaymentIntent fue emitido para una cantidad de meses distinta a la solicitada.",
            code="PAGO_MESES_NO_COINCIDEN",
        )


class MiSuscripcionServicio:
    """Casos de uso P2-CU09 (Consultar suscripción y uso) y P2-CU10 (Cambiar de plan y renovar con Stripe)."""

    @staticmethod
    def _obtener_contexto_empresa(
        db: Session, usuario_actual: UsuarioORM
    ) -> tuple[TenantORM, SuscripcionORM, PlanORM]:
        id_tenant = _resolver_id_tenant_empresa(db, usuario_actual)
        tenant = MiSuscripcionRepositorio.obtener_tenant(db, id_tenant)
        if not tenant:
            raise NotFoundError(
                f"La empresa con identificador {id_tenant} no existe.",
                code="EMPRESA_NO_ENCONTRADA",
            )
        par = MiSuscripcionRepositorio.suscripcion_actual(db, id_tenant)
        if not par:
            raise NotFoundError(
                "La empresa no tiene una suscripción registrada.",
                code="SUSCRIPCION_NO_ENCONTRADA",
            )
        return tenant, par[0], par[1]

    @staticmethod
    def consultar_mi_suscripcion(
        db: Session,
        usuario_actual: UsuarioORM,
    ) -> MiSuscripcionResumenOut:
        """Ejecuta P2-CU09: devuelve estado de suscripción, días restantes, uso, funcionalidades e historial."""
        tenant, susc, plan = MiSuscripcionServicio._obtener_contexto_empresa(db, usuario_actual)
        hoy = hoy_bolivia()
        moneda = MiSuscripcionRepositorio.obtener_moneda_empresa(db, tenant.id_tenant)

        estado_efectivo, vigente, dias_restantes, proxima_a_vencer = _calcular_estado_y_vigencia(
            susc, hoy
        )

        sucursales_lista = MiSuscripcionRepositorio.listar_sucursales_activas(db, tenant.id_tenant)
        cant_sucursales = len(sucursales_lista)
        cant_empleados = MiSuscripcionRepositorio.contar_empleados_activos(db, tenant.id_tenant)

        max_suc = plan.max_sucursales_activas
        max_emp = plan.max_empleados

        uso_sucursales = UsoRecursoPlanOut(
            usados=cant_sucursales,
            limite=max_suc,
            al_limite=cant_sucursales >= max_suc,
            excede_limite=cant_sucursales > max_suc,
        )
        uso_empleados = UsoRecursoPlanOut(
            usados=cant_empleados,
            limite=max_emp,
            al_limite=(max_emp is not None and cant_empleados >= max_emp),
            excede_limite=(max_emp is not None and cant_empleados > max_emp),
        )

        codigos_plan = set(MiSuscripcionRepositorio.funcionalidades_por_plan(db, plan.id_plan))
        catalogo_func = MiSuscripcionRepositorio.listar_catalogo_funcionalidades(db)

        incluidas: list[FuncionalidadPlanEmpresaOut] = []
        no_incluidas: list[FuncionalidadPlanEmpresaOut] = []
        for f in catalogo_func:
            if f.codigo in codigos_plan:
                incluidas.append(
                    FuncionalidadPlanEmpresaOut(
                        codigo=f.codigo,
                        nombre=f.nombre,
                        descripcion=f.descripcion,
                        planes_que_la_incluyen=[],
                    )
                )
            else:
                planes_con_f = MiSuscripcionRepositorio.planes_activos_con_funcionalidad(
                    db, f.codigo
                )
                no_incluidas.append(
                    FuncionalidadPlanEmpresaOut(
                        codigo=f.codigo,
                        nombre=f.nombre,
                        descripcion=f.descripcion,
                        planes_que_la_incluyen=planes_con_f,
                    )
                )

        historial_orm = MiSuscripcionRepositorio.listar_historial(db, tenant.id_tenant)
        precio_plan = Decimal(str(plan.precio_mensual)).quantize(Decimal("0.01"))

        return MiSuscripcionResumenOut(
            empresa=EmpresaSuscripcionInfoOut(
                id_tenant=tenant.id_tenant,
                codigo=tenant.codigo,
                nombre=tenant.nombre,
                estado=tenant.estado,
                moneda=moneda,
                simbolo_moneda="Bs." if moneda == "BOB" else "US$",
                tipo_cambio_bob=Decimal("1.00"),
            ),
            suscripcion=SuscripcionEmpresaDetalleOut(
                id_suscripcion=susc.id_suscripcion,
                id_plan=plan.id_plan,
                nombre_plan=plan.nombre,
                precio_mensual=precio_plan,
                precio_mensual_bob=precio_plan,
                estado=susc.estado,
                estado_efectivo=estado_efectivo,
                fecha_inicio=susc.fecha_inicio,
                fecha_vencimiento=susc.fecha_vencimiento,
                dias_restantes=dias_restantes,
                vigente=vigente,
                proxima_a_vencer=proxima_a_vencer,
            ),
            uso=UsoPlanEmpresaOut(
                sucursales=uso_sucursales,
                empleados=uso_empleados,
                sucursales_activas_detalle=[
                    SucursalActivaResumenOut(**s) for s in sucursales_lista
                ],
            ),
            funcionalidades_incluidas=incluidas,
            funcionalidades_no_incluidas=no_incluidas,
            historial=[HistorialMiSuscripcionOut.model_validate(h) for h in historial_orm],
        )

    @staticmethod
    def listar_planes_disponibles(
        db: Session,
        usuario_actual: UsuarioORM,
    ) -> list[PlanDisponibleEmpresaOut]:
        """Lista los planes activos evaluando su compatibilidad frente al uso actual (P2-CU10)."""
        tenant, susc, _plan_actual = MiSuscripcionServicio._obtener_contexto_empresa(
            db, usuario_actual
        )
        sucursales_lista = MiSuscripcionRepositorio.listar_sucursales_activas(db, tenant.id_tenant)
        empleados_activos = MiSuscripcionRepositorio.contar_empleados_activos(db, tenant.id_tenant)

        planes = MiSuscripcionRepositorio.listar_planes_activos(db)
        resultado: list[PlanDisponibleEmpresaOut] = []
        for p in planes:
            compatible, motivo = _evaluar_compatibilidad_uso(
                plan=p,
                sucursales_activas=sucursales_lista,
                empleados_activos=empleados_activos,
            )
            precio_plan = Decimal(str(p.precio_mensual)).quantize(Decimal("0.01"))
            resultado.append(
                PlanDisponibleEmpresaOut(
                    id_plan=p.id_plan,
                    nombre=p.nombre,
                    precio_mensual=precio_plan,
                    precio_mensual_bob=precio_plan,
                    max_sucursales_activas=p.max_sucursales_activas,
                    max_empleados=p.max_empleados,
                    funcionalidades=MiSuscripcionRepositorio.funcionalidades_por_plan(
                        db, p.id_plan
                    ),
                    es_plan_actual=(p.id_plan == susc.id_plan),
                    compatible_con_uso_actual=compatible,
                    motivo_incompatibilidad=motivo,
                )
            )
        return resultado

    @staticmethod
    def iniciar_pago(
        db: Session,
        datos: IniciarPagoSuscripcionIn,
        usuario_actual: UsuarioORM,
        pasarela: Optional[PasarelaPagos] = None,
    ) -> IntentoPagoSuscripcionOut:
        """Valida uso vs límites (`CU10 A1`) y abre un PaymentIntent en Stripe en la moneda de la empresa."""
        tenant, susc, _plan_actual = MiSuscripcionServicio._obtener_contexto_empresa(
            db, usuario_actual
        )
        plan_destino = MiSuscripcionRepositorio.obtener_plan(db, datos.id_plan)
        if not plan_destino:
            raise NotFoundError(
                f"El plan con identificador {datos.id_plan} no existe.",
                code="PLAN_NO_ENCONTRADO",
            )
        if not plan_destino.activo:
            raise ConflictError(
                f"El plan '{plan_destino.nombre}' no está disponible actualmente.",
                code="PLAN_INACTIVO",
            )

        sucursales_lista = MiSuscripcionRepositorio.listar_sucursales_activas(db, tenant.id_tenant)
        empleados_activos = MiSuscripcionRepositorio.contar_empleados_activos(db, tenant.id_tenant)
        compatible, motivo = _evaluar_compatibilidad_uso(
            plan=plan_destino,
            sucursales_activas=sucursales_lista,
            empleados_activos=empleados_activos,
        )
        if not compatible:
            raise ConflictError(
                motivo or "El uso actual de la empresa supera los límites del plan elegido.",
                code="USO_SUPERA_LIMITE_PLAN",
            )

        moneda = MiSuscripcionRepositorio.obtener_moneda_empresa(db, tenant.id_tenant)
        monto_total = (Decimal(str(plan_destino.precio_mensual)) * Decimal(datos.meses)).quantize(
            Decimal("0.01")
        )
        operacion: str = "renovacion" if plan_destino.id_plan == susc.id_plan else "cambio_plan"
        metadatos = {
            "id_tenant": str(tenant.id_tenant),
            "codigo_empresa": tenant.codigo,
            "id_plan": str(plan_destino.id_plan),
            "nombre_plan": plan_destino.nombre,
            "meses": str(datos.meses),
            "operacion": operacion,
            "moneda": moneda,
        }

        if monto_total <= Decimal("0.00"):
            ref_free = f"pi_free_{uuid.uuid4().hex[:12]}"
            registrar_intento_suscripcion(
                ref_free,
                amount_centimos=0,
                currency=moneda,
                metadatos=metadatos,
            )
            return IntentoPagoSuscripcionOut(
                referencia=ref_free,
                client_secret=f"{ref_free}_secret_free",
                estado_pago="succeeded",
                monto=monto_total,
                monto_bob=monto_total,
                moneda=moneda,
                tipo_cambio_bob=Decimal("1.00"),
                id_plan=plan_destino.id_plan,
                nombre_plan=plan_destino.nombre,
                meses=datos.meses,
                operacion=operacion,  # type: ignore[arg-type]
                requiere_cobro=False,
            )

        cliente_stripe = pasarela or StripeService(latencia_simulada_ms=0)
        try:
            intento = cliente_stripe.crear_intento(
                monto=monto_total,
                metodo_pago=datos.metodo_pago,
                descripcion=(
                    f"Suscripción FashionStore ({operacion}) - Empresa {tenant.nombre} "
                    f"- Plan {plan_destino.nombre} ({datos.meses} mes/es)"
                ),
                metadatos=metadatos,
                moneda=moneda,
            )
        except ErrorPasarela as exc:
            raise ServiceUnavailableError(str(exc), code="PASARELA_NO_DISPONIBLE") from exc

        registrar_intento_suscripcion(
            intento.referencia,
            amount_centimos=StripeService.a_centimos(monto_total),
            currency=moneda,
            metadatos=metadatos,
        )

        return IntentoPagoSuscripcionOut(
            referencia=intento.referencia,
            client_secret=intento.client_secret,
            estado_pago="requires_confirmation",
            monto=monto_total,
            monto_bob=monto_total,
            moneda=moneda,
            tipo_cambio_bob=Decimal("1.00"),
            id_plan=plan_destino.id_plan,
            nombre_plan=plan_destino.nombre,
            meses=datos.meses,
            operacion=operacion,  # type: ignore[arg-type]
            requiere_cobro=True,
        )

    @staticmethod
    def confirmar_cambio_o_renovacion(
        db: Session,
        datos: ConfirmarCambioSuscripcionIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
        pasarela: Optional[PasarelaPagos] = None,
    ) -> MiSuscripcionResumenOut:
        """Verifica el pago en Stripe (`CU10 A2`), su correspondencia con el plan/empresa/meses/importe y aplica el cambio (`RN17`)."""
        tenant, susc, plan_anterior = MiSuscripcionServicio._obtener_contexto_empresa(
            db, usuario_actual
        )
        plan_destino = MiSuscripcionRepositorio.obtener_plan(db, datos.id_plan)
        if not plan_destino:
            raise NotFoundError(
                f"El plan con identificador {datos.id_plan} no existe.",
                code="PLAN_NO_ENCONTRADO",
            )
        if not plan_destino.activo:
            raise ConflictError(
                f"El plan '{plan_destino.nombre}' no está disponible actualmente.",
                code="PLAN_INACTIVO",
            )

        # Impedir reutilización de una referencia ya registrada en historial_suscripcion
        if MiSuscripcionRepositorio.referencia_pago_ya_utilizada(db, datos.referencia_pago):
            raise ConflictError(
                f"La referencia de pago '{datos.referencia_pago}' ya fue utilizada previamente.",
                code="REFERENCIA_PAGO_YA_UTILIZADA",
            )

        # Revalidar CU10 A1 antes de confirmar
        sucursales_lista = MiSuscripcionRepositorio.listar_sucursales_activas(db, tenant.id_tenant)
        empleados_activos = MiSuscripcionRepositorio.contar_empleados_activos(db, tenant.id_tenant)
        compatible, motivo = _evaluar_compatibilidad_uso(
            plan=plan_destino,
            sucursales_activas=sucursales_lista,
            empleados_activos=empleados_activos,
        )
        if not compatible:
            raise ConflictError(
                motivo or "El uso actual de la empresa supera los límites del plan elegido.",
                code="USO_SUPERA_LIMITE_PLAN",
            )

        moneda = MiSuscripcionRepositorio.obtener_moneda_empresa(db, tenant.id_tenant)
        monto_total = (Decimal(str(plan_destino.precio_mensual)) * Decimal(datos.meses)).quantize(
            Decimal("0.01")
        )

        marca_tarjeta: Optional[str] = None
        ultimos_digitos: Optional[str] = None

        if monto_total > Decimal("0.00"):
            cliente_stripe = pasarela or StripeService(latencia_simulada_ms=0)
            try:
                resultado = cliente_stripe.verificar_intento(
                    datos.referencia_pago,
                    escenario_prueba=datos.escenario_prueba,
                )
            except ErrorPasarela as exc:
                raise ServiceUnavailableError(str(exc), code="PASARELA_NO_DISPONIBLE") from exc

            if not resultado.aprobado:
                # Curso Alterno A2 (CU10): el pago es rechazado; se mantienen el plan y vencimiento actuales
                raise PaymentRequiredError(
                    f"No se pudo completar el cobro en Stripe: {resultado.mensaje} "
                    "Se mantienen el plan y la fecha de vencimiento actuales.",
                    code="PAGO_RECHAZADO",
                )

            _verificar_correspondencia_intento(
                referencia_pago=datos.referencia_pago,
                payload_pasarela=resultado.payload if isinstance(resultado.payload, dict) else {},
                monto_esperado=monto_total,
                moneda_esperada=moneda,
                id_tenant_esperado=tenant.id_tenant,
                id_plan_esperado=plan_destino.id_plan,
                meses_esperados=datos.meses,
            )

            marca_tarjeta = resultado.marca
            ultimos_digitos = resultado.ultimos_digitos
        else:
            if datos.escenario_prueba in ("rechazado", "fondos_insuficientes"):
                raise PaymentRequiredError(
                    "El pago de verificación fue rechazado por la pasarela. "
                    "Se mantienen el plan y la fecha de vencimiento actuales.",
                    code="PAGO_RECHAZADO",
                )
            _verificar_correspondencia_intento(
                referencia_pago=datos.referencia_pago,
                payload_pasarela={},
                monto_esperado=monto_total,
                moneda_esperada=moneda,
                id_tenant_esperado=tenant.id_tenant,
                id_plan_esperado=plan_destino.id_plan,
                meses_esperados=datos.meses,
            )

        hoy = hoy_bolivia()
        es_mismo_plan = plan_destino.id_plan == susc.id_plan
        evento = "renovacion" if es_mismo_plan else "cambio_plan"
        dias_adicionales = DIAS_POR_MES * datos.meses

        vencimiento_previo = susc.fecha_vencimiento
        estado_previo = susc.estado

        if es_mismo_plan and susc.fecha_vencimiento >= hoy and susc.estado in ("prueba", "activa"):
            nueva_fecha_inicio = susc.fecha_inicio
            nueva_fecha_vencimiento = susc.fecha_vencimiento + timedelta(days=dias_adicionales)
        else:
            nueva_fecha_inicio = hoy
            nueva_fecha_vencimiento = hoy + timedelta(days=dias_adicionales)

        detalle_evento = {
            "operacion": evento,
            "plan_anterior": plan_anterior.nombre,
            "id_plan_anterior": plan_anterior.id_plan,
            "plan_nuevo": plan_destino.nombre,
            "id_plan_nuevo": plan_destino.id_plan,
            "meses_contratados": datos.meses,
            "monto_cobrado": str(monto_total),
            "monto_cobrado_bob": str(monto_total),
            "moneda": moneda,
            "referencia_pago": datos.referencia_pago,
            "pasarela": "stripe",
            "marca_tarjeta": marca_tarjeta,
            "ultimos_digitos": ultimos_digitos,
            "estado_anterior": estado_previo,
            "vencimiento_anterior": str(vencimiento_previo),
            "vencimiento_nuevo": str(nueva_fecha_vencimiento),
        }

        MiSuscripcionRepositorio.actualizar_suscripcion_y_registrar_historial(
            db,
            suscripcion=susc,
            id_tenant=tenant.id_tenant,
            id_plan=plan_destino.id_plan,
            estado="activa",
            fecha_inicio=nueva_fecha_inicio,
            fecha_vencimiento=nueva_fecha_vencimiento,
            evento=evento,
            detalle=detalle_evento,
            id_usuario=usuario_actual.id_usuario,
        )

        # Consumir el intento en memoria tras aplicarse
        _INTENTOS_SUSCRIPCION_ABIERTOS.pop(datos.referencia_pago, None)

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            db=db,
            accion=(
                "SUSCRIPCION_EMPRESA_RENOVADA"
                if es_mismo_plan
                else "SUSCRIPCION_EMPRESA_PLAN_CAMBIADO"
            ),
            modulo="plataforma",
            descripcion=(
                f"La empresa '{tenant.nombre}' ({tenant.codigo}) ejecutó '{evento}' al plan "
                f"'{plan_destino.nombre}' por {datos.meses} mes(es) con referencia Stripe "
                f"{datos.referencia_pago} ({monto_total} {moneda})."
            ),
            usuario=usuario_actual,
            direccion_ip=direccion_ip,
            datos_anteriores={
                "id_plan": plan_anterior.id_plan,
                "plan": plan_anterior.nombre,
                "estado": estado_previo,
                "fecha_vencimiento": str(vencimiento_previo),
            },
            datos_nuevos=detalle_evento,
        )
        db.commit()
        limpiar_cache_tenants()

        return MiSuscripcionServicio.consultar_mi_suscripcion(db, usuario_actual)
