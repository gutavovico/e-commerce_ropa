"""Bandeja de avisos del cliente (AC-AV.1). Sustituye a la notificación push del documento (D1)."""

from typing import Optional

from sqlalchemy.orm import Session

from core.errors import NotFoundError
from core.tiempo import ahora
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.sincronizacion.avisos_cliente.esquemas import AvisoOut, BandejaAvisosOut
from modules.sincronizacion.avisos_cliente.repositorio import AvisosRepositorio
from modules.sincronizacion.comun import exigir_cliente
from modules.sincronizacion.modelos import TIPOS_AVISO, AvisoClienteORM


class AvisosServicio:
    @staticmethod
    def crear(
        db: Session,
        *,
        id_cliente: int,
        tipo: str,
        titulo: str,
        mensaje: str,
        id_reserva: Optional[int] = None,
        id_venta: Optional[int] = None,
    ) -> AvisoClienteORM:
        """Deja un aviso en la transacción en curso (no confirma)."""
        if tipo not in TIPOS_AVISO:
            raise ValueError(f"Tipo de aviso desconocido: {tipo}")
        aviso = AvisoClienteORM(
            id_cliente=id_cliente,
            tipo=tipo,
            titulo=titulo[:120],
            mensaje=mensaje[:500],
            id_reserva=id_reserva,
            id_venta=id_venta,
        )
        db.add(aviso)
        return aviso

    @staticmethod
    def bandeja(db: Session, usuario: UsuarioORM) -> BandejaAvisosOut:
        id_cliente = exigir_cliente(db, usuario)
        avisos = AvisosRepositorio.de_cliente(db, id_cliente)
        return BandejaAvisosOut(
            no_leidos=AvisosRepositorio.no_leidos(db, id_cliente),
            avisos=[AvisosServicio._salida(a) for a in avisos],
        )

    @staticmethod
    def marcar_leido(db: Session, usuario: UsuarioORM, id_aviso: int) -> AvisoOut:
        id_cliente = exigir_cliente(db, usuario)
        aviso = AvisosRepositorio.del_cliente(db, id_cliente, id_aviso)
        if aviso is None:
            raise NotFoundError("El aviso no existe.", code="AVISO_NO_ENCONTRADO")
        if aviso.leido_en is None:
            aviso.leido_en = ahora()
            db.commit()
            db.refresh(aviso)
        return AvisosServicio._salida(aviso)

    @staticmethod
    def _salida(aviso: AvisoClienteORM) -> AvisoOut:
        return AvisoOut(
            id_aviso=aviso.id_aviso,
            tipo=aviso.tipo,
            titulo=aviso.titulo,
            mensaje=aviso.mensaje,
            id_reserva=aviso.id_reserva,
            id_venta=aviso.id_venta,
            creado_en=aviso.creado_en,
            leido=aviso.leido_en is not None,
        )
