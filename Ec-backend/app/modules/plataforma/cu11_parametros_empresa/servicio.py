"""Servicio de P2-CU11 · Parámetros de la empresa.

Spec: `.specs/finalized/P2-CU11-parametros-empresa/spec.md` §2.

- CU11 configura; cada caso de uso aplica su parámetro (C1): reservas (CU15), cambios (CU18) y
  operación sin conexión (CU14, CU19) los leen con `ParametrosEmpresaServicio.vigentes(db)`.
- C7: la operación que use un parámetro guarda el valor que la rige al crearse; cambiar la
  configuración no recalcula nada ya registrado (CU11 A3).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from core.errors import AuthorizationError
from core.tenant import tenant_actual
from modules.plataforma.cu11_parametros_empresa.esquemas import ParametrosEmpresaIn, ParametrosEmpresaOut
from modules.plataforma.cu11_parametros_empresa.repositorio import ParametrosEmpresaRepositorio
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.plataforma.modelos import ConfiguracionTenantORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

#: Los parámetros que el administrador puede cambiar (C2).
EDITABLES = (
    "horas_vencimiento_reserva",
    "dias_cambio_prenda",
    "operacion_offline_habilitada",
    "dias_antiguedad_offline",
)


@dataclass(frozen=True)
class ParametrosEmpresa:
    """Parámetros vigentes de la empresa de la sesión (lectura para otros paquetes)."""

    moneda: str
    zona_horaria: str
    horas_vencimiento_reserva: int
    dias_cambio_prenda: int
    operacion_offline_habilitada: bool
    dias_antiguedad_offline: int


def _empresa(db: Session) -> int:
    empresa = tenant_actual(db)
    if empresa is None:
        raise AuthorizationError("La operación requiere una empresa identificada.", code="TENANT_REQUERIDO")
    return empresa


class ParametrosEmpresaServicio:
    @staticmethod
    def _fila(db: Session, bloquear: bool = False) -> ConfiguracionTenantORM:
        """La fila de la empresa de la sesión; si falta, se crea con los valores por defecto (C4)."""
        empresa = _empresa(db)
        fila = ParametrosEmpresaRepositorio.leer(db, empresa, bloquear)
        if fila is None:
            ParametrosEmpresaRepositorio.crear_si_falta(db)
            fila = ParametrosEmpresaRepositorio.leer(db, empresa, bloquear)
        return fila

    @staticmethod
    def vigentes(db: Session) -> ParametrosEmpresa:
        fila = ParametrosEmpresaServicio._fila(db)
        return ParametrosEmpresa(
            moneda=fila.moneda,
            zona_horaria=fila.zona_horaria,
            horas_vencimiento_reserva=fila.horas_vencimiento_reserva,
            dias_cambio_prenda=fila.dias_cambio_prenda,
            operacion_offline_habilitada=fila.operacion_offline_habilitada,
            dias_antiguedad_offline=fila.dias_antiguedad_offline,
        )

    @staticmethod
    def obtener(db: Session) -> ParametrosEmpresaOut:
        salida = ParametrosEmpresaOut.model_validate(ParametrosEmpresaServicio._fila(db))
        db.commit()  # confirma la fila creada por C4, si la hubo
        return salida

    @staticmethod
    def actualizar(
        db: Session, datos: ParametrosEmpresaIn, actor: Optional[Any] = None, ip: Optional[str] = None
    ) -> ParametrosEmpresaOut:
        SuscripcionServicio.validar(db)  # C8
        fila = ParametrosEmpresaServicio._fila(db, bloquear=True)

        anterior: dict = {}
        nuevo: dict = {}
        for campo in EDITABLES:
            valor = getattr(datos, campo)
            if getattr(fila, campo) != valor:
                anterior[campo] = getattr(fila, campo)
                nuevo[campo] = valor
                setattr(fila, campo, valor)

        if nuevo:
            fila.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(fila)

        if nuevo:  # C5: solo lo que cambió
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=getattr(actor, "id_usuario", None),
                usuario_nombre=(f"{actor.nombres} {actor.apellidos}".strip() or actor.email) if actor else None,
                accion="CONFIGURACION_MODIFICADA",
                tabla_modulo="configuracion_tenant",
                direccion_ip=ip,
                severidad="INFO",
                payload_anterior=anterior,
                payload_nuevo=nuevo,
                db=db,
            )
        return ParametrosEmpresaOut.model_validate(fila)
