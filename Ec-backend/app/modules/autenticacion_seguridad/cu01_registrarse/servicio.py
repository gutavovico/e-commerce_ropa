"""Servicio de dominio transaccional para CU01: Registrarse."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.errors import ConflictError
from core.security import create_access_token, hash_password
from modules.autenticacion_seguridad.cu01_registrarse.esquemas import (
    RegistroClienteIn,
    RegistroClienteOut,
)
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM


class ServicioRegistroUsuario:
    """Gestiona la logica de negocio y persistencia para el registro de clientes."""

    def registrar_cliente(self, db: Session, datos: RegistroClienteIn) -> RegistroClienteOut:
        """Registra un nuevo cliente con verificacion de unicidad y emision de token JWT.

        Args:
            db: Sesion activa de base de datos SQLAlchemy.
            datos: Datos validados del cliente.

        Returns:
            RegistroClienteOut con datos del usuario registrado y token de acceso.

        Raises:
            ConflictError: Si el correo electronico ya se encuentra registrado.
        """
        # 1. Normalizar y verificar unicidad de email
        email_normalizado = str(datos.email).strip().lower()
        stmt = select(UsuarioORM).where(UsuarioORM.email == email_normalizado)
        usuario_existente = db.scalars(stmt).first()

        if usuario_existente is not None:
            raise ConflictError(
                message="El correo electronico ya se encuentra registrado en la plataforma.",
                code="USUARIO_YA_EXISTE",
            )

        # 2. Cifrado criptografico seguro de la contrasena
        hash_seguro = hash_password(datos.password)

        # 3. Transaccion atomica: insercion simultanea en usuarios y clientes
        nuevo_usuario = UsuarioORM(
            email=email_normalizado,
            password_hash=hash_seguro,
            nombres=datos.nombres.strip(),
            apellidos=datos.apellidos.strip(),
            telefono=datos.telefono.strip() if datos.telefono else None,
            rol="cliente",
            id_sucursal=None,
            activo=True,
        )
        db.add(nuevo_usuario)
        db.flush()  # Obtener id_usuario generado para la clave primaria foranea

        nuevo_cliente = ClienteORM(
            id_cliente=nuevo_usuario.id_usuario,
            talla_preferida=datos.talla_preferida,
            ciudad_preferida=datos.ciudad_preferida,
            acepta_marketing=True,
        )
        db.add(nuevo_cliente)
        db.commit()
        db.refresh(nuevo_usuario)

        # 4. Emision del token de acceso JWT
        payload_token = {
            "sub": str(nuevo_usuario.id_usuario),
            "email": nuevo_usuario.email,
            "rol": nuevo_usuario.rol,
        }
        token_acceso = create_access_token(data=payload_token)

        return RegistroClienteOut(
            id_usuario=nuevo_usuario.id_usuario,
            email=nuevo_usuario.email,
            nombres=nuevo_usuario.nombres,
            apellidos=nuevo_usuario.apellidos,
            rol=nuevo_usuario.rol,
            token_acceso=token_acceso,
            tipo_token="bearer",
        )
