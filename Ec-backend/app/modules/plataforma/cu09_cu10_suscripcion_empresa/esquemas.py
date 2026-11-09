"""Esquemas Pydantic v2 para P2-CU09 (Consultar suscripción y uso) y P2-CU10 (Cambiar de plan y renovar con Stripe)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EmpresaSuscripcionInfoOut(BaseModel):
    """Datos identificativos de la empresa a la que pertenece la suscripción."""

    id_tenant: int
    codigo: str
    nombre: str
    estado: str
    moneda: str = "BOB"
    simbolo_moneda: str = "Bs."
    tipo_cambio_bob: Decimal = Decimal("1.00")


class SuscripcionEmpresaDetalleOut(BaseModel):
    """Estado de la suscripción actual de la empresa (P2-CU09, RN13, RN14)."""

    id_suscripcion: int
    id_plan: int
    nombre_plan: str
    precio_mensual: Decimal
    precio_mensual_bob: Decimal = Decimal("0.00")
    estado: str
    estado_efectivo: str
    fecha_inicio: date
    fecha_vencimiento: date
    dias_restantes: int
    vigente: bool
    proxima_a_vencer: bool


class UsoRecursoPlanOut(BaseModel):
    """Consumo actual de un recurso frente al tope de su plan (P2-CU09, RN15, CU09 A2)."""

    usados: int
    limite: Optional[int] = None
    al_limite: bool
    excede_limite: bool


class SucursalActivaResumenOut(BaseModel):
    """Sucursal activa de la empresa (para orientar desactivaciones en CU10 A1)."""

    id_sucursal: int
    nombre: str
    direccion: Optional[str] = None


class UsoPlanEmpresaOut(BaseModel):
    """Resumen consolidado del uso de recursos de la empresa frente a su plan."""

    sucursales: UsoRecursoPlanOut
    empleados: UsoRecursoPlanOut
    sucursales_activas_detalle: list[SucursalActivaResumenOut] = Field(default_factory=list)


class FuncionalidadPlanEmpresaOut(BaseModel):
    """Funcionalidad incluida o no incluida en el plan actual de la empresa (RN16)."""

    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    planes_que_la_incluyen: list[str] = Field(default_factory=list)


class HistorialMiSuscripcionOut(BaseModel):
    """Evento del historial de suscripción de la empresa (RN17)."""

    model_config = ConfigDict(from_attributes=True)

    id_historial: int
    id_suscripcion: int
    evento: str
    detalle: Optional[dict] = None
    id_usuario: Optional[int] = None
    creado_en: datetime


class MiSuscripcionResumenOut(BaseModel):
    """Respuesta consolidada de P2-CU09: suscripción, vigencia, uso, funcionalidades e historial."""

    empresa: EmpresaSuscripcionInfoOut
    suscripcion: SuscripcionEmpresaDetalleOut
    uso: UsoPlanEmpresaOut
    funcionalidades_incluidas: list[FuncionalidadPlanEmpresaOut]
    funcionalidades_no_incluidas: list[FuncionalidadPlanEmpresaOut]
    historial: list[HistorialMiSuscripcionOut]


class PlanDisponibleEmpresaOut(BaseModel):
    """Plan activo disponible para contratación o renovación por la empresa (P2-CU10)."""

    id_plan: int
    nombre: str
    precio_mensual: Decimal
    precio_mensual_bob: Decimal = Decimal("0.00")
    max_sucursales_activas: int
    max_empleados: Optional[int] = None
    funcionalidades: list[str]
    es_plan_actual: bool
    compatible_con_uso_actual: bool
    motivo_incompatibilidad: Optional[str] = None


class IniciarPagoSuscripcionIn(BaseModel):
    """Solicitud para abrir un intento de cobro en Stripe para cambiar de plan o renovar (P2-CU10)."""

    id_plan: int = Field(..., gt=0, description="Identificador del plan elegido")
    meses: int = Field(1, ge=1, le=24, description="Cantidad de meses a contratar o renovar (1..24)")
    metodo_pago: str = Field("tarjeta", min_length=2, max_length=30)


class IntentoPagoSuscripcionOut(BaseModel):
    """Datos del PaymentIntent abierto en Stripe (o simulador determinista) para confirmar el cobro."""

    referencia: str
    client_secret: Optional[str] = None
    estado_pago: str
    monto: Decimal
    monto_bob: Decimal = Decimal("0.00")
    moneda: str
    tipo_cambio_bob: Decimal = Decimal("1.00")
    id_plan: int
    nombre_plan: str
    meses: int
    operacion: Literal["cambio_plan", "renovacion"]
    requiere_cobro: bool


class ConfirmarCambioSuscripcionIn(BaseModel):
    """Solicitud para verificar el pago en Stripe y aplicar el cambio de plan o renovación (P2-CU10)."""

    id_plan: int = Field(..., gt=0, description="Identificador del plan contratado o renovado")
    meses: int = Field(1, ge=1, le=24, description="Cantidad de meses contratados o renovados (1..24)")
    referencia_pago: str = Field(..., min_length=3, max_length=120, description="ID del PaymentIntent (pi_...)")
    escenario_prueba: Optional[Literal["exito", "rechazado", "fondos_insuficientes"]] = Field(
        None,
        description="Escenario determinista para pruebas en modo simulado (CU10 A2)",
    )
