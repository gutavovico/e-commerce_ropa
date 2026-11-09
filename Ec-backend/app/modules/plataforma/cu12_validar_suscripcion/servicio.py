"""P2-CU12 · Validar suscripción y límites del plan.

Spec: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.4 (F14, F17) y CU12 de
`SI2-Parcial2.md`. Lo incluyen otros casos de uso; no modifica datos.

- Suscripción en prueba o activa y dentro de sus fechas; si no → 403 SUSCRIPCION_NO_VIGENTE (RN14).
  Una vigencia vencida se detecta al consultar: no hay proceso programado.
- Funcionalidad no incluida en el plan → 403 FUNCIONALIDAD_NO_INCLUIDA, indicando qué plan la incluye (RN16).
- Recurso con límite (sucursales activas, empleados) → 409 LIMITE_PLAN_ALCANZADO con límite y uso (RN15).
  Un límite nulo significa «sin límite» (F14).
- El super administrador (modo plataforma) no se valida (CU12 A4).
- P2-CU04 B8: al validar un recurso con límite se toma un bloqueo por empresa y recurso que dura
  hasta el `commit` de la operación; dos altas simultáneas con un solo cupo no pasan las dos.
- `uso()` (P2-CU04 B7, lo reutiliza P2-CU09): uso y límite de un recurso, sin validar nada.
"""

from typing import Any, Optional, TypedDict

from core.errors import AuthorizationError, ConflictError
from core.tenant import CLAVE_PLATAFORMA, contexto, tenant_actual
from modules.plataforma.cu12_validar_suscripcion.repositorio import SuscripcionRepositorio
from core.tiempo import hoy as hoy_empresa

FUNCIONALIDADES = (
    "productos", "ventas", "reservas", "operacion_offline", "reportes_convencionales", "reportes_ia",
)
RECURSOS = {
    "sucursales": ("sucursales activas", "max_sucursales_activas", SuscripcionRepositorio.sucursales_activas),
    "empleados": ("empleados", "max_empleados", SuscripcionRepositorio.empleados_activos),
}


class UsoRecurso(TypedDict):
    uso: int
    limite: Optional[int]
    plan: Optional[str]


class SuscripcionServicio:
    @staticmethod
    def validar(
        db: Any,
        *,
        funcionalidad: Optional[str] = None,
        recurso: Optional[str] = None,
        id_tenant: Optional[int] = None,
    ) -> None:
        """Devuelve sin más si la operación está permitida; si no, lanza el error de dominio."""
        if funcionalidad is not None and funcionalidad not in FUNCIONALIDADES:
            raise ValueError(f"Funcionalidad desconocida: {funcionalidad}")
        if recurso is not None and recurso not in RECURSOS:
            raise ValueError(f"Recurso con límite desconocido: {recurso}")

        info = contexto(db)
        if info is None:  # sesión simulada de los tests unitarios
            return
        if info.get(CLAVE_PLATAFORMA):
            return
        empresa = id_tenant if id_tenant is not None else tenant_actual(db)
        if empresa is None:
            raise AuthorizationError(
                "La operación requiere una empresa identificada.", code="TENANT_REQUERIDO"
            )

        hoy = hoy_empresa()  # Bolivia (fix P2-CU11, M5)
        suscripcion = SuscripcionRepositorio.suscripcion_vigente(db, empresa, hoy)
        if suscripcion is None:
            raise AuthorizationError(
                "La suscripción de la empresa no está vigente. Renueve el plan para continuar.",
                code="SUSCRIPCION_NO_VIGENTE",
            )
        plan = SuscripcionRepositorio.plan(db, suscripcion.id_plan)

        if funcionalidad is not None and not SuscripcionRepositorio.plan_incluye(db, plan.id_plan, funcionalidad):
            planes = SuscripcionRepositorio.planes_con(db, funcionalidad)
            sugerencia = f" Disponible en: {', '.join(planes)}." if planes else ""
            raise AuthorizationError(
                f"El plan {plan.nombre} no incluye «{funcionalidad}».{sugerencia}",
                code="FUNCIONALIDAD_NO_INCLUIDA",
            )

        if recurso is not None:
            descripcion, atributo, contar = RECURSOS[recurso]
            limite = getattr(plan, atributo)
            if limite is not None:
                SuscripcionRepositorio.bloquear_recurso(db, empresa, recurso)
                uso = contar(db, empresa)
                if uso >= limite:
                    raise ConflictError(
                        f"El plan {plan.nombre} permite {limite} {descripcion} y la empresa ya usa {uso}. "
                        "Cambie de plan o libere alguno.",
                        code="LIMITE_PLAN_ALCANZADO",
                    )

    @staticmethod
    def uso(db: Any, recurso: str) -> Optional[UsoRecurso]:
        """Uso actual y límite del plan vigente (`limite=None`: sin límite; `plan=None`: sin
        suscripción vigente). `None` con una sesión simulada o sin empresa en el contexto."""
        if recurso not in RECURSOS:
            raise ValueError(f"Recurso con límite desconocido: {recurso}")
        if contexto(db) is None:
            return None
        empresa = tenant_actual(db)
        if empresa is None:
            return None
        _, atributo, contar = RECURSOS[recurso]
        hoy = hoy_empresa()  # Bolivia (fix P2-CU11, M5)
        suscripcion = SuscripcionRepositorio.suscripcion_vigente(db, empresa, hoy)
        plan = SuscripcionRepositorio.plan(db, suscripcion.id_plan) if suscripcion else None
        return UsoRecurso(
            uso=contar(db, empresa),
            limite=getattr(plan, atributo) if plan else None,
            plan=plan.nombre if plan else None,
        )
