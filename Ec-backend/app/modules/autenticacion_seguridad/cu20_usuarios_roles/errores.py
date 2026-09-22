"""Excepciones de dominio semanticas para el caso de uso CU20: Gestionar Usuarios y Roles."""

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError


class UsuarioNoEncontradoError(NotFoundError):
    """Lanzada cuando un identificador de usuario no existe en el sistema (HTTP 404)."""

    def __init__(
        self,
        message: str = "Usuario no encontrado en el sistema.",
        code: str = "USUARIO_NO_ENCONTRADO",
    ):
        super().__init__(message=message, code=code)


class EmailDuplicadoError(ConflictError):
    """Lanzada ante intentos de registrar o actualizar un correo ya existente (HTTP 409)."""

    def __init__(
        self,
        message: str = "El correo electronico ya se encuentra registrado en el sistema.",
        code: str = "EMAIL_DUPLICADO",
    ):
        super().__init__(message=message, code=code)


class SucursalRequeridaError(UnprocessableEntityError):
    """Lanzada cuando un rol operativo carece de asignacion de sucursal obligatoria (HTTP 422)."""

    def __init__(
        self,
        message: str = "La asignacion de sucursal es obligatoria para roles operativos.",
        code: str = "SUCURSAL_REQUERIDA",
    ):
        super().__init__(message=message, code=code)


class SucursalInvalidaError(UnprocessableEntityError):
    """Lanzada cuando la sucursal asignada no existe o no se encuentra activa (HTTP 422)."""

    def __init__(
        self,
        message: str = "La sucursal indicada no existe o no se encuentra activa.",
        code: str = "SUCURSAL_INEXISTENTE_O_INACTIVA",
    ):
        super().__init__(message=message, code=code)


class UltimoAdministradorError(ConflictError):
    """Lanzada al intentar desactivar o degradar al unico administrador activo (HTTP 409)."""

    def __init__(
        self,
        message: str = "Operacion denegada. Debe existir al menos un administrador activo en el sistema.",
        code: str = "ULTIMO_ADMINISTRADOR_BLOQUEADO",
    ):
        super().__init__(message=message, code=code)


class AutoModificacionBloqueadaError(ConflictError):
    """Lanzada cuando el administrador en sesion intenta suspenderse o degradarse a si mismo (HTTP 409)."""

    def __init__(
        self,
        message: str = "No puede desactivar o degradar su propia cuenta de administrador en la sesion actual.",
        code: str = "AUTO_DESACTIVACION_NO_PERMITIDA",
    ):
        super().__init__(message=message, code=code)


class UsuarioConDependenciasError(ConflictError):
    """Lanzada cuando un usuario registra transacciones operativas y no puede eliminarse fisicamente (HTTP 409)."""

    def __init__(
        self,
        message: str = "El usuario registra operaciones o dependencias asociadas. Se requiere baja logica.",
        code: str = "USUARIO_CON_DEPENDENCIAS",
    ):
        super().__init__(message=message, code=code)
