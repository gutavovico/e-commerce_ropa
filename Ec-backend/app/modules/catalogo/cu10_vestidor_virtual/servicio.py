"""Servicio de dominio para CU10: Utilizar Vestidor Virtual (Dos Motores)."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from core.errors import (
    AuthorizationError,
    NotFoundError,
    UnprocessableEntityError,
)
from integrations.decart_service import DecartService, decart_service
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu10_vestidor_virtual.esquemas import (
    SesionVestidorActualizarIn,
    SesionVestidorCrearIn,
    SesionVestidorOut,
    TokenVestidorDecartOut,
)
from modules.catalogo.cu10_vestidor_virtual.repositorio import VestidorRepositorio

logger = logging.getLogger("fashionstore.cu10_vestidor")


class ServicioProcesarAR:
    """Orquestador de lógica de negocio para vestidor virtual (Local e IA Decart)."""

    def __init__(
        self,
        db: Session,
        servicio_decart: Optional[DecartService] = None,
    ):
        self.db = db
        self.repositorio = VestidorRepositorio(db)
        self.decart_client = servicio_decart or decart_service

    def solicitar_token_decart(self, usuario: UsuarioORM, canal: str = "web") -> TokenVestidorDecartOut:
        """Emite un token de cliente efímero para conectar con Decart Lucy VTON.

        - Requiere cliente autenticado con perfil activo.
        - No condiciona la duración de la sesión comercial (regla de negocio de 60 s).
        - Si el servicio externo falla o no hay créditos, DecartService lanza
          ServiceUnavailableError (503) para activar el fallback automático al Motor 1.
        """
        id_cliente = self._obtener_id_cliente_valido(usuario)
        logger.info(
            "Cliente %s solicita token efímero de conexión con Decart Lucy VTON",
            id_cliente,
        )

        # El canal móvil no puede fijar origen (WebView con `file://`): ver DecartService.
        datos_token = self.decart_client.generar_token_cliente(restringir_origenes=canal != "movil")

        return TokenVestidorDecartOut(
            token=datos_token["token"],
            expira_en_segundos=datos_token.get("expira_en_segundos", 60),
            servicio=datos_token.get("servicio", "decart_lucy_vton_720p"),
        )

    def crear_sesion(
        self,
        usuario: UsuarioORM,
        datos: SesionVestidorCrearIn,
    ) -> SesionVestidorOut:
        """Registra la interacción de prueba en sesiones_vestidor_virtual (Prueba 3).

        - Valida que el producto exista en la base de datos.
        - Valida que el producto tenga un `modelo_ar_url` configurado.
        - Persiste el motor empleado ('local' o 'ia') y la duración activa.
        """
        id_cliente = self._obtener_id_cliente_valido(usuario)

        producto = self.repositorio.obtener_producto(datos.id_producto)
        if not producto:
            raise NotFoundError(
                f"La prenda con ID {datos.id_producto} no existe en el catálogo.",
                code="PRODUCTO_NO_ENCONTRADO",
            )

        # Regla de Dominio: el vestidor exige modelo_ar_url configurado
        ar_url = getattr(producto, "modelo_ar_url", None)
        if not ar_url or not str(ar_url).strip():
            raise UnprocessableEntityError(
                f"La prenda '{producto.nombre}' no cuenta con un recurso visual 2D "
                f"configurado para el vestidor virtual (modelo_ar_url ausente).",
                code="SIN_MODELO_AR",
            )

        sesion_orm = self.repositorio.crear_sesion(
            id_cliente=id_cliente,
            id_producto=datos.id_producto,
            dispositivo=datos.dispositivo,
            motor=datos.motor,
            duracion_segundos=datos.duracion_segundos,
            resultado_url=datos.resultado_url,
            genero_interes=datos.genero_interes,
        )

        logger.info(
            "Sesión de vestidor virtual %s registrada para cliente %s (motor: %s, duración: %s s)",
            sesion_orm.id_sesion_ar,
            id_cliente,
            sesion_orm.motor,
            sesion_orm.duracion_segundos,
        )

        return SesionVestidorOut.model_validate(sesion_orm)

    def actualizar_sesion(
        self,
        id_sesion_ar: int,
        datos: SesionVestidorActualizarIn,
        usuario: UsuarioORM,
    ) -> SesionVestidorOut:
        """Actualiza el interés comercial o URL de captura generada tras la sesión."""
        sesion = self.repositorio.obtener_sesion(id_sesion_ar)
        if not sesion:
            raise NotFoundError(
                f"La sesión de vestidor virtual con ID {id_sesion_ar} no existe.",
                code="SESION_NO_ENCONTRADA",
            )

        id_cliente = self._obtener_id_cliente_valido(usuario)
        if sesion.id_cliente != id_cliente and usuario.rol != "administrador":
            raise AuthorizationError(
                "No tiene autorización para modificar esta sesión de vestidor virtual.",
                code="ACCESO_DENEGADO",
            )

        sesion_actualizada = self.repositorio.actualizar_sesion(
            sesion=sesion,
            resultado_url=datos.resultado_url,
            genero_interes=datos.genero_interes,
        )

        return SesionVestidorOut.model_validate(sesion_actualizada)

    def _obtener_id_cliente_valido(self, usuario: UsuarioORM) -> int:
        """Garantiza que el usuario autenticado cuente con perfil de cliente."""
        cliente = getattr(usuario, "cliente", None)
        if not cliente:
            raise UnprocessableEntityError(
                "El usuario autenticado no posee un perfil de cliente registrado.",
                code="CLIENTE_NO_REGISTRADO",
            )
        return cliente.id_cliente

