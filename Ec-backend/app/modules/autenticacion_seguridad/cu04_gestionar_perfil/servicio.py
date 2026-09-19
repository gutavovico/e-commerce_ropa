"""Servicio de dominio para CU04: Gestionar Perfil del Cliente."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.cu04_gestionar_perfil.esquemas import (
    PerfilClienteOut,
    PerfilClienteUpdateIn,
    ResumenAtelierOut,
)
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM

_MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


class ServicioPerfilCliente:
    """Orquesta la consulta y actualización atómica del perfil del cliente."""

    @staticmethod
    def _calcular_miembro_desde(fecha_registro: datetime) -> str:
        """Formatea la fecha de registro en texto amigable de alta costura."""
        try:
            mes = _MESES_ES[fecha_registro.month - 1]
            return f"{mes} {fecha_registro.year}"
        except Exception:
            return "Miembro Exclusivo"

    @classmethod
    def obtener_perfil(cls, db: Session, usuario: UsuarioORM) -> PerfilClienteOut:
        """Construye y devuelve el DTO consolidado de perfil del cliente."""
        # Asegurar que el registro de cliente exista de manera consistente
        cliente = usuario.cliente
        if cliente is None:
            cliente = ClienteORM(
                id_cliente=usuario.id_usuario,
                acepta_marketing=True,
            )
            db.add(cliente)
            db.commit()
            db.refresh(usuario)
            cliente = usuario.cliente

        fecha_nac = None
        if cliente.fecha_nacimiento:
            fecha_nac = (
                cliente.fecha_nacimiento.date()
                if isinstance(cliente.fecha_nacimiento, datetime)
                else cliente.fecha_nacimiento
            )

        return PerfilClienteOut(
            id_usuario=usuario.id_usuario,
            numero_socio=f"#{usuario.id_usuario:04d}",
            email=usuario.email,
            rol=str(usuario.rol),
            fecha_registro=usuario.fecha_registro,
            miembro_desde=cls._calcular_miembro_desde(usuario.fecha_registro),
            ultimo_acceso=usuario.ultimo_acceso,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            telefono=usuario.telefono,
            fecha_nacimiento=fecha_nac,
            genero=cliente.genero,
            talla_preferida=cliente.talla_preferida,
            ciudad_preferida=cliente.ciudad_preferida,
            acepta_marketing=cliente.acepta_marketing,
            resumen_atelier=ResumenAtelierOut(),
        )

    @classmethod
    def actualizar_perfil(
        cls,
        db: Session,
        usuario: UsuarioORM,
        datos: PerfilClienteUpdateIn,
    ) -> PerfilClienteOut:
        """Actualiza atómicamente los datos de usuario y cliente, persistiendo en PostgreSQL."""
        # Actualización de campos de UsuarioORM
        if datos.nombres is not None:
            usuario.nombres = datos.nombres.strip()
        if datos.apellidos is not None:
            usuario.apellidos = datos.apellidos.strip()
        if datos.telefono is not None:
            usuario.telefono = datos.telefono.strip() if datos.telefono.strip() else None

        # Asegurar entidad ClienteORM
        cliente = usuario.cliente
        if cliente is None:
            cliente = ClienteORM(
                id_cliente=usuario.id_usuario,
                acepta_marketing=True,
            )
            db.add(cliente)

        # Actualización de campos de ClienteORM
        if datos.fecha_nacimiento is not None:
            cliente.fecha_nacimiento = datetime.combine(
                datos.fecha_nacimiento,
                datetime.min.time(),
            )
        if datos.genero is not None:
            cliente.genero = datos.genero
        if datos.talla_preferida is not None:
            cliente.talla_preferida = datos.talla_preferida
        if datos.ciudad_preferida is not None:
            cliente.ciudad_preferida = datos.ciudad_preferida
        if datos.acepta_marketing is not None:
            cliente.acepta_marketing = datos.acepta_marketing

        db.add(usuario)
        if cliente is not None:
            db.add(cliente)
        db.commit()
        db.refresh(usuario)
        if usuario.cliente is not None:
            db.refresh(usuario.cliente)

        return cls.obtener_perfil(db, usuario)
