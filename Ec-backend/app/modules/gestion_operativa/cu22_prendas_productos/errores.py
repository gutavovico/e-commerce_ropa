"""Excepciones de dominio tipadas para CU22: Gestionar Prendas, Productos y Variantes (SKUs)."""

from core.errors import ConflictError, NotFoundError, UnprocessableEntityError


class ProductoNoEncontradoError(NotFoundError):
    """Lanzada cuando un producto solicitado no existe en la base de datos (HTTP 404)."""

    def __init__(self, message: str = "El producto solicitado no existe.", code: str = "PRODUCTO_NO_ENCONTRADO"):
        super().__init__(message, code=code)


class ProductoDuplicadoError(ConflictError):
    """Lanzada cuando ya existe un producto con la misma denominacion comercial (HTTP 409)."""

    def __init__(
        self,
        message: str = "Ya existe un producto con el mismo nombre comercial.",
        code: str = "PRODUCTO_DUPLICADO",
    ):
        super().__init__(message, code=code)


class CategoriaInexistenteError(UnprocessableEntityError):
    """Lanzada cuando la categoria especificada no existe en el sistema (HTTP 422)."""

    def __init__(
        self,
        message: str = "La categoria seleccionada no existe en el catalogo.",
        code: str = "CATEGORIA_INEXISTENTE",
    ):
        super().__init__(message, code=code)


class VarianteNoEncontradaError(NotFoundError):
    """Lanzada cuando una variante de producto solicitada no existe (HTTP 404)."""

    def __init__(
        self,
        message: str = "La variante de producto solicitada no existe.",
        code: str = "VARIANTE_NO_ENCONTRADA",
    ):
        super().__init__(message, code=code)


class SkuDuplicadoError(ConflictError):
    """Lanzada cuando un SKU propuesto ya se encuentra asignado en el sistema (HTTP 409)."""

    def __init__(
        self,
        message: str = "El codigo SKU ya se encuentra registrado en otra prenda o variante.",
        code: str = "SKU_DUPLICADO",
    ):
        super().__init__(message, code=code)


class VarianteDuplicadaError(ConflictError):
    """Lanzada cuando ya existe la combinacion (producto, talla, color) (HTTP 409)."""

    def __init__(
        self,
        message: str = "Ya existe una variante registrada para la misma prenda, talla y color.",
        code: str = "VARIANTE_DUPLICADA",
    ):
        super().__init__(message, code=code)


class ProductoConDependenciasError(ConflictError):
    """Lanzada cuando un producto tiene dependencias operativas de inventario o pedidos (HTTP 409)."""

    def __init__(
        self,
        message: str = (
            "El producto cuenta con inventario registrado, pedidos historicos o reservas. "
            "No se puede eliminar fisicamente; debe utilizar la baja logica (activo = False)."
        ),
        code: str = "PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS",
    ):
        super().__init__(message, code=code)


class VarianteConDependenciasError(ConflictError):
    """Lanzada cuando una variante especifica tiene dependencias operativas activas (HTTP 409)."""

    def __init__(
        self,
        message: str = (
            "La variante cuenta con existencias en inventario, reservas o movimientos. "
            "No se puede eliminar fisicamente; desactive la variante para suspender su comercializacion."
        ),
        code: str = "VARIANTE_CON_DEPENDENCIAS_OPERATIVAS",
    ):
        super().__init__(message, code=code)
