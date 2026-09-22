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

        # 1. Deteccion de Modulo (orden jerarquico con fronteras de palabra)
        modulo: Optional[ModuloReporteEnum] = None

        palabras_inventario = [
            "inventario", "inventarios", "stock", "existencia", "existencias",
            "kardex", "prenda", "prendas", "producto", "productos",
            "articulo", "articulos", "catalogo", "ropa", "disponible",
            "disponibles", "disponibilidad", "almacen", "almacenes",
        ]
        palabras_ventas = [
            "venta", "ventas", "facturacion", "factura", "facturas",
            "ingreso", "ingresos", "pedido", "pedidos", "vendido",
            "vendidos", "vendio", "vendieron", "caja", "recaudacion",
            "ganancia", "ganancias", "dinero", "cobro", "cobros",
            "ticket", "tickets", "orden", "ordenes", "transaccion", "transacciones",
        ]
        palabras_reservas = [
            "reserva", "reservas", "reservado", "reservados", "apartado",
            "apartados", "apartar", "cita", "citas", "fitting",
            "fittings", "probador", "probadores", "visita", "visitas",
            "agendado", "agendados", "agenda",
        ]
        palabras_bitacora = [
            "bitacora", "bitacoras", "auditoria", "auditorias", "acceso",
            "accesos", "seguridad", "logs", "log", "evento", "eventos",
            "historial", "trazabilidad", "actividad", "movimientos",
        ]

        if cls._contiene_palabra(texto_norm, palabras_inventario):
            modulo = ModuloReporteEnum.INVENTARIO
        elif cls._contiene_palabra(texto_norm, palabras_ventas):
            modulo = ModuloReporteEnum.VENTAS
        elif cls._contiene_palabra(texto_norm, palabras_reservas):
            modulo = ModuloReporteEnum.RESERVAS
        elif cls._contiene_palabra(texto_norm, palabras_bitacora):
            modulo = ModuloReporteEnum.BITACORA

        # Si no se detecto modulo explicitamente, verificar si menciona palabras clave generales
        if modulo is None:
            if any(w in texto_norm for w in ["reporte", "descargar", "exportar", "resumen", "balance"]):
                modulo = ModuloReporteEnum.VENTAS
            else:
                raise ComandoVozNoReconocidoError(texto_original)

        # 2. Deteccion de Formato
        formato = FormatoReporteEnum.EXCEL
        formato_mencionado = False

        if cls._contiene_palabra(texto_norm, ["excel", "xlsx", "planilla", "hoja de calculo", "hoja de calculos", "calculo", "libro"]):
            formato = FormatoReporteEnum.EXCEL
            formato_mencionado = True
        elif cls._contiene_palabra(texto_norm, ["pdf", "documento", "imprimir", "hoja", "informe"]):
            formato = FormatoReporteEnum.PDF
            formato_mencionado = True
        elif cls._contiene_palabra(texto_norm, ["csv", "texto plano", "delimitado", "plano", "datos", "valores separados"]):
            formato = FormatoReporteEnum.CSV
            formato_mencionado = True

        # 3. Deteccion de Rango Temporal
        periodo = RangoTemporalEnum.ESTE_MES

        if cls._contiene_palabra(texto_norm, ["hoy", "del dia", "de hoy", "diario", "dia actual", "en este dia", "de la fecha"]):
            periodo = RangoTemporalEnum.HOY
        elif cls._contiene_palabra(texto_norm, ["ayer", "del dia de ayer", "dia anterior", "del dia anterior"]):
            periodo = RangoTemporalEnum.AYER
        elif any(w in texto_norm for w in ["esta semana", "semana actual", "semanal", "de la semana", "ultimos 7 dias"]):
            periodo = RangoTemporalEnum.ESTA_SEMANA
        elif any(w in texto_norm for w in ["este mes", "mes actual", "mensual", "del mes", "ultimo mes", "en el mes"]):
            periodo = RangoTemporalEnum.ESTE_MES
        elif any(w in texto_norm for w in ["este anio", "este ano", "anual", "anio actual", "ano actual", "del anio", "del ano", "todo el anio", "todo el ano", "historico"]):
            periodo = RangoTemporalEnum.ANIO_ACTUAL

        # 4. Deteccion de Sucursal con scoring no ambiguo
        id_sucursal, nombre_sucursal = cls._resolver_sucursal(texto_norm, sucursales_conocidas)

        # 5. Deteccion de Intencion Operativa
        intencion = IntencionVozEnum.EXPORTAR if formato_mencionado else IntencionVozEnum.CONSULTAR

        if cls._contiene_palabra(texto_norm, ["descargar", "exportar", "bajar", "generar", "guardar", "emitir"]):
            intencion = IntencionVozEnum.EXPORTAR
        elif cls._contiene_palabra(texto_norm, ["consultar", "ver", "mostrar", "previsualizar", "cuanto", "cuantos", "cuanto se vendio", "resumen"]):
            intencion = IntencionVozEnum.CONSULTAR
        elif cls._contiene_palabra(texto_norm, ["filtrar", "buscar"]):
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

    @staticmethod
    def _contiene_palabra(texto: str, palabras: List[str]) -> bool:
        """Verifica si alguna de las palabras o frases clave coincide con limite de palabra."""
        for p in palabras:
            patron = r"\b" + re.escape(p) + r"\b"
            if re.search(patron, texto):
                return True
        return False

    @classmethod
    def _resolver_sucursal(
        cls,
        texto_norm: str,
        sucursales_conocidas: Optional[List[Tuple[int, str]]] = None,
    ) -> Tuple[Optional[int], Optional[str]]:
        """Determina la sucursal de forma desambiguada evitando falsos positivos por terminos genericos."""
        if not sucursales_conocidas:
            return None, None

        # Si el usuario dice 'todas', 'global', 'consolidado', 'general', forzar consolidado
        if cls._contiene_palabra(texto_norm, ["todas", "todos", "global", "consolidado", "general", "todas las sucursales", "todas las tiendas"]):
            return None, None

        stop_words = {"boutique", "central", "tienda", "sucursal", "de", "el", "la", "los", "las", "y", "en", "del", "al", "atelier"}
        candidatos = []

        for s_id, s_nombre in sucursales_conocidas:
            nombre_norm = cls.normalizar_texto(s_nombre)
            if nombre_norm in texto_norm:
                candidatos.append((s_id, s_nombre, 100))
                continue

            tokens_distintivos = [
                t for t in nombre_norm.split()
                if len(t) >= 3 and t not in stop_words
            ]

            score = 0
            for tok in tokens_distintivos:
                if re.search(r"\b" + re.escape(tok) + r"\b", texto_norm):
                    score += 10

            if score > 0:
                candidatos.append((s_id, s_nombre, score))

        if candidatos:
            candidatos.sort(key=lambda x: x[2], reverse=True)
            mejor = candidatos[0]
            return mejor[0], mejor[1]

        return None, None
