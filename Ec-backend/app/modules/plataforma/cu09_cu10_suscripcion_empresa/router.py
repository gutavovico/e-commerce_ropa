"""Router FastAPI para P2-CU09 (Consultar suscripción y uso) y P2-CU10 (Cambiar de plan y renovar con Stripe)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu09_cu10_suscripcion_empresa.esquemas import (
    ConfirmarCambioSuscripcionIn,
    IniciarPagoSuscripcionIn,
    IntentoPagoSuscripcionOut,
    MiSuscripcionResumenOut,
    PlanDisponibleEmpresaOut,
)
from modules.plataforma.cu09_cu10_suscripcion_empresa.servicio import (
    MiSuscripcionServicio,
)

router = APIRouter(
    prefix="/mi-suscripcion",
    tags=["Plataforma · P2-CU09 y P2-CU10 · Suscripción de la Empresa y Stripe"],
)

exigir_administrador_empresa = require_roles(["administrador", "admin"])


@router.get(
    "",
    response_model=MiSuscripcionResumenOut,
    summary="Consultar el estado de suscripción, días restantes, uso del plan, funcionalidades e historial (P2-CU09)",
)
def consultar_mi_suscripcion(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> MiSuscripcionResumenOut:
    return MiSuscripcionServicio.consultar_mi_suscripcion(db, usuario)


@router.get(
    "/planes",
    response_model=list[PlanDisponibleEmpresaOut],
    summary="Listar planes activos con evaluación de compatibilidad frente al uso actual (P2-CU10)",
)
def listar_planes_disponibles(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> list[PlanDisponibleEmpresaOut]:
    return MiSuscripcionServicio.listar_planes_disponibles(db, usuario)


@router.post(
    "/iniciar-pago",
    response_model=IntentoPagoSuscripcionOut,
    summary="Validar uso vs límites del plan elegido (CU10 A1) y abrir PaymentIntent en Stripe (P2-CU10)",
)
def iniciar_pago_suscripcion(
    datos: IniciarPagoSuscripcionIn,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> IntentoPagoSuscripcionOut:
    return MiSuscripcionServicio.iniciar_pago(db, datos, usuario)


@router.post(
    "/confirmar",
    response_model=MiSuscripcionResumenOut,
    summary="Verificar pago en Stripe (CU10 A2) y confirmar cambio de plan o renovación de suscripción (P2-CU10)",
)
def confirmar_cambio_o_renovacion(
    datos: ConfirmarCambioSuscripcionIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> MiSuscripcionResumenOut:
    ip = request.client.host if request.client else None
    return MiSuscripcionServicio.confirmar_cambio_o_renovacion(
        db, datos, usuario, direccion_ip=ip
    )

