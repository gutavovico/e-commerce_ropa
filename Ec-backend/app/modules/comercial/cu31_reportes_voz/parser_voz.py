"""Parser determinista y lexico-semantico para interpretacion de comandos de voz."""

import re
import unicodedata
from typing import List, Optional, Tuple

from modules.comercial.cu31_reportes_voz.errores import ComandoVozNoReconocidoError
from modules.comercial.cu31_reportes_voz.esquemas import (
    ComandoVozOut,
    FormatoReporteEnum,
    IntencionVozEnum,
    ModuloReporteEnum,
    RangoTemporalEnum,
)


class ParserComandosVoz:
    """Interpreta ordenes verbales dictadas para configurar o ejecutar reportes ejecutivos."""

    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Limpia tildes, signos y normaliza a minusculas para analisis lexico."""
        texto_limpio = texto.lower().strip()
        # Eliminar diacriticos (tildes)
        texto_sin_tildes = "".join(
            c for c in unicodedata.normalize("NFD", texto_limpio)
            if unicodedata.category(c) != "Mn"
        )
        # Sustituir caracteres no alfanumericos por espacios
        texto_normalizado = re.sub(r"[^\w\s]", " ", texto_sin_tildes)
        return re.sub(r"\s+", " ", texto_normalizado).strip()

    @classmethod
    def interpretar(
        cls,
        texto_original: str,
        sucursales_conocidas: Optional[List[Tuple[int, str]]] = None,
    ) -> ComandoVozOut:
        """Parsea una transcripcion y extrae intencion, modulo, formato, periodo y sucursal.

        Args:
            texto_original: Transcripcion textual en lenguaje natural.
            sucursales_conocidas: Lista de tuplas (id_sucursal, nombre_sucursal) para matching.

        Returns:
            ComandoVozOut estructurado.

        Raises:
            ComandoVozNoReconocidoError: Si el texto no especifica un modulo o contexto inteligible.
        """
        texto_norm = cls.normalizar_texto(texto_original)

        if not texto_norm or len(texto_norm) < 3:
            raise ComandoVozNoReconocidoError(texto_original)

        # 1. Deteccion de Modulo
        modulo: Optional[ModuloReporteEnum] = None

        if any(w in texto_norm for w in ["venta", "ventas", "facturacion", "ingreso", "ingresos", "pedidos"]):
            modulo = ModuloReporteEnum.VENTAS
        elif any(w in texto_norm for w in ["reserva", "reservas", "apartado", "apartados", "cita", "citas", "fitting"]):
            modulo = ModuloReporteEnum.RESERVAS
        elif any(w in texto_norm for w in ["inventario", "stock", "existencia", "existencias", "kardex", "prenda", "prendas"]):
            modulo = ModuloReporteEnum.INVENTARIO
        elif any(w in texto_norm for w in ["bitacora", "auditoria", "acceso", "accesos", "seguridad", "logs", "log"]):
            modulo = ModuloReporteEnum.BITACORA

        # Si no se detecto modulo explicitamente, verificar si menciona palabras clave generales
        if modulo is None:
            if "reporte" in texto_norm or "descargar" in texto_norm or "exportar" in texto_norm:
                # Por defecto contextual si dice 'reporte general' asumimos ventas
                modulo = ModuloReporteEnum.VENTAS
            else:
                raise ComandoVozNoReconocidoError(texto_original)

        # 2. Deteccion de Formato
        formato = FormatoReporteEnum.EXCEL
        formato_mencionado = False

        if any(w in texto_norm for w in ["excel", "xlsx", "planilla", "hoja de calculo"]):
            formato = FormatoReporteEnum.EXCEL
            formato_mencionado = True
        elif any(w in texto_norm for w in ["pdf", "documento", "imprimir"]):
            formato = FormatoReporteEnum.PDF
            formato_mencionado = True
        elif any(w in texto_norm for w in ["csv", "texto plano", "delimitado"]):
            formato = FormatoReporteEnum.CSV
            formato_mencionado = True

        # 3. Deteccion de Rango Temporal
        periodo = RangoTemporalEnum.ESTE_MES

        if "hoy" in texto_norm or "del dia" in texto_norm:
            periodo = RangoTemporalEnum.HOY
        elif "ayer" in texto_norm:
            periodo = RangoTemporalEnum.AYER
        elif any(w in texto_norm for w in ["esta semana", "semana actual", "semanal"]):
            periodo = RangoTemporalEnum.ESTA_SEMANA
        elif any(w in texto_norm for w in ["este mes", "mes actual", "mensual"]):
            periodo = RangoTemporalEnum.ESTE_MES
        elif any(w in texto_norm for w in ["este anio", "este ano", "anual", "anio actual", "ano actual"]):
            periodo = RangoTemporalEnum.ANIO_ACTUAL

        # 4. Deteccion de Sucursal
        id_sucursal: Optional[int] = None
        nombre_sucursal: Optional[str] = None

        if sucursales_conocidas:
            for s_id, s_nombre in sucursales_conocidas:
                nombre_norm = cls.normalizar_texto(s_nombre)
                # Busqueda de coincidencia total o palabras significativas (longitud > 3)
                tokens_sucursal = [t for t in nombre_norm.split() if len(t) > 3]
                if nombre_norm in texto_norm or any(tok in texto_norm for tok in tokens_sucursal):
                    id_sucursal = s_id
                    nombre_sucursal = s_nombre
                    break

        # Si el usuario dice "todas", "global" o "consolidado", anular seleccion de sucursal
        if any(w in texto_norm for w in ["todas", "todos", "global", "consolidado", "general"]):
            id_sucursal = None
            nombre_sucursal = None

        # 5. Deteccion de Intencion Operativa
        intencion = IntencionVozEnum.EXPORTAR if formato_mencionado else IntencionVozEnum.CONSULTAR

        if any(w in texto_norm for w in ["descargar", "exportar", "bajar", "generar", "guardar", "emitir"]):
            intencion = IntencionVozEnum.EXPORTAR
        elif any(w in texto_norm for w in ["consultar", "ver", "mostrar", "previsualizar", "cuanto", "cuantos"]):
            intencion = IntencionVozEnum.CONSULTAR
        elif any(w in texto_norm for w in ["filtrar", "buscar"]):
            intencion = IntencionVozEnum.FILTRAR

        accion_sugerida = "ejecutar_exportacion" if intencion == IntencionVozEnum.EXPORTAR else "actualizar_filtros"

        return ComandoVozOut(
            texto_dictado=texto_original,
            intencion=intencion,
            modulo=modulo,
            formato=formato,
            periodo=periodo,
            id_sucursal=id_sucursal,
            nombre_sucursal=nombre_sucursal,
            confianza=0.95 if formato_mencionado else 0.85,
            accion_recomendada=accion_sugerida,
        )
