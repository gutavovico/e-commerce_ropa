"""Excepciones de dominio para CU31: Generar reportes ejecutivos y consultas por voz."""

from core.errors import AuthorizationError, DomainError, UnprocessableEntityError


class ReportesError(DomainError):
    """Excepcion base para anomalias en el modulo de reportes."""

    def __init__(self, message: str = "Error en el modulo de reportes", code: str = "REPORTE_ERROR"):
        super().__init__(message, code=code)


class FormatoNoSoportadoError(UnprocessableEntityError):
    """Formato de archivo binario no admitido por el sistema."""

    def __init__(self, formato: str):
        super().__init__(
            message=f"El formato '{formato}' no esta soportado. Formatos validos: excel, pdf, csv.",
            code="FORMATO_NO_SOPORTADO",
        )


class ModuloReporteInvalidoError(UnprocessableEntityError):
    """Modulo de datos solicitado invalido o desconocido."""

    def __init__(self, modulo: str):
        super().__init__(
            message=f"El modulo '{modulo}' no es valido para reportes. Opciones: ventas, reservas, inventario, bitacora.",
            code="MODULO_REPORTE_INVALIDO",
        )


class ComandoVozNoReconocidoError(UnprocessableEntityError):
    """El comando de voz no contiene patrones semanticos reconocibles."""

    def __init__(self, texto: str):
        super().__init__(
            message=f"No se identifico una orden valida en: '{texto}'. Especifica el modulo (ventas, reservas, inventario, bitacora) y opcionalmente el formato (excel, pdf, csv).",
            code="COMANDO_VOZ_NO_RECONOCIDO",
        )


class AccesoReporteDenegadoError(AuthorizationError):
    """Violacion de politica RBAC al solicitar informacion restringida."""

    def __init__(self, motivo: str):
        super().__init__(
            message=f"Acceso denegado a reportes ejecutivos: {motivo}",
            code="ACCESO_REPORTE_DENEGADO",
        )
