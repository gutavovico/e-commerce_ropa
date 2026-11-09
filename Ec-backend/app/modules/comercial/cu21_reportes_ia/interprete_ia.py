"""Intérprete semántico de solicitudes de reportes con IA (P2-CU21).

Cumple estrictamente:
- CU21 paso 3 y RN45: envía al servicio de IA únicamente el texto del administrador y el catálogo
  de reportes permitidos (CU22), sin enviar jamás filas ni datos del negocio.
- CU21 A1: detecta solicitudes ambiguas o incompletas y pide precisar lo que falta.
- CU21 A2: detecta solicitudes no soportadas fuera del catálogo y sugiere ejemplos válidos.
- Fallback determinista 0ms cuando `IA_API_KEY` no está configurada o la red no responde.
"""

from datetime import date, datetime, timedelta, timezone
import json
import logging
import re
import unicodedata
import urllib.request
from typing import Any, Optional

from core.config import settings
from modules.comercial.cu21_reportes_ia.esquemas import (
    FormatoVisualizacionIa,
    InterpretacionReporteIaOut,
)
from modules.plataforma.cu22_catalogo_reportes.modelos import CatalogoReporteIaORM

logger = logging.getLogger("fashionstore.interprete_reportes_ia")

MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

TERMINOS_NO_SOPORTADOS = (
    "clima",
    "temperatura",
    "nomina",
    "planilla salarial",
    "sueldos",
    "vacaciones",
    "impuestos nacionales",
    "contabilidad externa",
    "borrar",
    "eliminar base",
    "drop table",
    "delete from",
    "contraseñas",
    "passwords",
    "tarjetas de credito",
)

FRASES_AMBIGUAS = frozenset({
    "reporte",
    "un reporte",
    "dame un reporte",
    "dame un reporte general",
    "dame un reporte general por favor",
    "reporte general",
    "quiero un reporte",
    "generar reporte",
    "necesito un reporte",
    "informe",
    "dame un informe",
    "mostrar datos",
    "ver datos",
    "informacion",
    "resumen",
    "estadisticas",
    "grafica",
    "grafico",
})

TERMINOS_OTRO_TENANT = (
    "otra empresa",
    "otro tenant",
    "empresa competidora",
    "todas las empresas",
)


def _normalizar(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto or "")
    sin_acentos = "".join(c for c in limpio if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_acentos.lower()).strip()


def _ultimo_dia_mes(anio: int, mes: int) -> date:
    if mes == 12:
        return date(anio, 12, 31)
    return date(anio, mes + 1, 1) - timedelta(days=1)


def _extraer_rango_fechas(texto_norm: str, hoy: date) -> tuple[Optional[date], Optional[date]]:
    if "hoy" in texto_norm:
        return hoy, hoy
    if "ayer" in texto_norm:
        ayer = hoy - timedelta(days=1)
        return ayer, ayer
    if "esta semana" in texto_norm or "ultima semana" in texto_norm:
        return hoy - timedelta(days=7), hoy
    if "ultimos 30 dias" in texto_norm or "ultimo mes" in texto_norm:
        return hoy - timedelta(days=30), hoy
    if "este anio" in texto_norm or "ano actual" in texto_norm or "anio actual" in texto_norm:
        return date(hoy.year, 1, 1), date(hoy.year, 12, 31)

    for nombre_mes, num_mes in MESES_ES.items():
        if re.search(rf"\b{nombre_mes}\b", texto_norm):
            anio_match = re.search(r"\b(202[4-9])\b", texto_norm)
            anio = int(anio_match.group(1)) if anio_match else hoy.year
            return date(anio, num_mes, 1), _ultimo_dia_mes(anio, num_mes)

    if "este mes" in texto_norm or "mes actual" in texto_norm:
        return date(hoy.year, hoy.month, 1), _ultimo_dia_mes(hoy.year, hoy.month)

    return None, None


def _detectar_formato_y_grafico(
    texto_norm: str,
    formato_preferido: Optional[FormatoVisualizacionIa],
    tipos_permitidos: list[str],
) -> tuple[str, FormatoVisualizacionIa]:
    tipo_grafico = "barras"
    if "torta" in texto_norm or "pastel" in texto_norm or "circular" in texto_norm:
        tipo_grafico = "torta"
    elif "linea" in texto_norm or "tendencia" in texto_norm or "evolucion" in texto_norm:
        tipo_grafico = "linea"
    elif "barras" in texto_norm or "barra" in texto_norm:
        tipo_grafico = "barras"
    elif "solo tabla" in texto_norm or "unicamente tabla" in texto_norm:
        tipo_grafico = "tabla"

    if tipos_permitidos and tipo_grafico not in tipos_permitidos:
        tipo_grafico = next((t for t in tipos_permitidos if t != "tabla"), tipos_permitidos[0])

    if formato_preferido:
        return (
            formato_preferido if formato_preferido in ("tabla", "barras", "linea", "torta") else tipo_grafico,
            formato_preferido,
        )

    if "solo tabla" in texto_norm:
        return "tabla", "tabla"
    return tipo_grafico, "ambos"


class InterpreteReportesIA:
    """Traduce una solicitud en lenguaje natural a una especificación validada contra el catálogo CU22."""

    GEMINI_API_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent"
    )

    @classmethod
    def interpretar(
        cls,
        *,
        prompt_texto: str,
        catalogo_activo: list[CatalogoReporteIaORM],
        sucursales_empresa: list[dict[str, Any]],
        categorias_empresa: list[dict[str, Any]],
        codigo_forzado: Optional[str] = None,
        formato_preferido: Optional[FormatoVisualizacionIa] = None,
        fecha_inicio_in: Optional[date] = None,
        fecha_fin_in: Optional[date] = None,
        id_sucursal_in: Optional[int] = None,
        id_categoria_in: Optional[int] = None,
        usar_gemini: bool = False,
    ) -> InterpretacionReporteIaOut:
        texto_norm = _normalizar(prompt_texto)
        hoy = datetime.now(timezone.utc).date()

        # 0. Detectar intento de consultar datos de otra empresa en texto libre (CU21 A7, RN46)
        for termino_tenant in TERMINOS_OTRO_TENANT:
            if termino_tenant in texto_norm:
                return InterpretacionReporteIaOut(
                    estado="rechazada",
                    explicacion_ia=(
                        "Solicitud rechazada: no está permitido consultar datos de otra empresa (CU21 A7, RN46)."
                    ),
                    origen_motor="validador_aislamiento_cu13",
                )

        # 1. Detectar solicitud no soportada (CU21 A2)
        for termino in TERMINOS_NO_SOPORTADOS:
            if termino in texto_norm:
                ejemplos = cls._recopilar_ejemplos(catalogo_activo)
                return InterpretacionReporteIaOut(
                    estado="no_soportada",
                    explicacion_ia=(
                        f"La solicitud menciona '{termino}', que no corresponde a ningún reporte "
                        "del catálogo autorizado de la plataforma (CU21 A2). "
                        f"Ejemplos disponibles: {'; '.join(ejemplos[:3])}."
                    ),
                    origen_motor="validador_catalogo_cu22",
                )

        # 2. Detectar solicitud demasiado vaga o ambigua (CU21 A1)
        if not codigo_forzado and (len(texto_norm) < 5 or texto_norm in FRASES_AMBIGUAS):
            return InterpretacionReporteIaOut(
                estado="ambigua",
                explicacion_ia=(
                    "La solicitud es ambigua o incompleta (CU21 A1). Por favor, indique qué área "
                    "desea consultar (ventas por sucursal, ranking de productos más vendidos, "
                    "inventario por sucursal o estado de reservas) y opcionalmente el período o sucursal."
                ),
                origen_motor="validador_ambiguedad_cu21",
            )

        mapa_catalogo = {r.codigo: r for r in catalogo_activo}

        # 3. Identificar el reporte del catálogo
        reporte_elegido: Optional[CatalogoReporteIaORM] = None
        origen_motor = "semantico_determinista"

        if codigo_forzado:
            reporte_elegido = mapa_catalogo.get(codigo_forzado.strip().lower())
            if reporte_elegido is None:
                return InterpretacionReporteIaOut(
                    estado="rechazada",
                    explicacion_ia=(
                        f"El reporte '{codigo_forzado}' no existe o se encuentra desactivado en el catálogo permitido (CU21 A7)."
                    ),
                    origen_motor="validador_catalogo_cu22",
                )
        else:
            # Si Gemini está habilitado explícitamente y hay clave, intentamos clasificación sin enviar datos privados
            if usar_gemini and settings.IA_API_KEY:
                codigo_ia = cls._clasificar_con_gemini(prompt_texto, catalogo_activo)
                if codigo_ia and codigo_ia in mapa_catalogo:
                    reporte_elegido = mapa_catalogo[codigo_ia]
                    origen_motor = "google_gemini"

            if reporte_elegido is None:
                codigo_det = cls._clasificar_determinista(texto_norm)
                if codigo_det is None:
                    # Revisar si alguna palabra coincide con algún reporte activo del catálogo
                    for rep in catalogo_activo:
                        if _normalizar(rep.nombre) in texto_norm or rep.codigo.replace("_", " ") in texto_norm:
                            codigo_det = rep.codigo
                            break

                if codigo_det is None:
                    # Si pide algo genérico como "dame los datos de septiembre" sin decir si es ventas, inventario o reservas -> ambigua (CU21 A1)
                    if any(m in texto_norm for m in MESES_ES) or "sucursal" in texto_norm or "mes" in texto_norm:
                        return InterpretacionReporteIaOut(
                            estado="ambigua",
                            explicacion_ia=(
                                "Detectamos un filtro temporal o de sucursal, pero falta precisar qué tipo de reporte necesita "
                                "(por ejemplo: 'ventas por sucursal', 'productos más vendidos', 'inventario' o 'reservas') (CU21 A1)."
                            ),
                            origen_motor="semantico_determinista",
                        )
                    ejemplos = cls._recopilar_ejemplos(catalogo_activo)
                    return InterpretacionReporteIaOut(
                        estado="no_soportada",
                        explicacion_ia=(
                            "No se encontró un reporte compatible en el catálogo permitido para su solicitud (CU21 A2). "
                            f"Pruebe con consultas como: {'; '.join(ejemplos[:3])}."
                        ),
                        origen_motor="semantico_determinista",
                    )

                reporte_elegido = mapa_catalogo.get(codigo_det)
                if reporte_elegido is None:
                    return InterpretacionReporteIaOut(
                        estado="no_soportada",
                        explicacion_ia=(
                            f"El tipo de reporte '{codigo_det}' no se encuentra activo actualmente en el catálogo de la plataforma (CU22 A3)."
                        ),
                        origen_motor="validador_catalogo_cu22",
                    )

        # 4. Extraer fechas, sucursal y categoría dentro de la empresa del usuario
        f_ini_txt, f_fin_txt = _extraer_rango_fechas(texto_norm, hoy)
        fecha_inicio = fecha_inicio_in or f_ini_txt
        fecha_fin = fecha_fin_in or f_fin_txt

        id_sucursal = id_sucursal_in
        nombre_sucursal: Optional[str] = None
        if id_sucursal is not None:
            for s in sucursales_empresa:
                if int(s["id_sucursal"]) == int(id_sucursal):
                    nombre_sucursal = str(s["nombre"])
                    break
        else:
            for s in sucursales_empresa:
                nom_s = _normalizar(str(s["nombre"]))
                if nom_s and nom_s in texto_norm:
                    id_sucursal = int(s["id_sucursal"])
                    nombre_sucursal = str(s["nombre"])
                    break

        id_categoria = id_categoria_in
        nombre_categoria: Optional[str] = None
        if id_categoria is not None:
            for c in categorias_empresa:
                if int(c["id_categoria"]) == int(id_categoria):
                    nombre_categoria = str(c["nombre"])
                    break
        else:
            for c in categorias_empresa:
                nom_c = _normalizar(str(c["nombre"]))
                if nom_c and nom_c in texto_norm:
                    id_categoria = int(c["id_categoria"])
                    nombre_categoria = str(c["nombre"])
                    break

        tipo_grafico, formato_vis = _detectar_formato_y_grafico(
            texto_norm,
            formato_preferido,
            list(reporte_elegido.tipos_grafico or ["tabla", "barras"]),
        )

        partes_exp = [f"Reporte identificado: «{reporte_elegido.nombre}» (vista: {reporte_elegido.vista_origen})."]
        if fecha_inicio and fecha_fin:
            partes_exp.append(f"Período: {fecha_inicio.isoformat()} a {fecha_fin.isoformat()}.")
        if nombre_sucursal:
            partes_exp.append(f"Sucursal filtrada: {nombre_sucursal}.")
        if nombre_categoria:
            partes_exp.append(f"Categoría filtrada: {nombre_categoria}.")
        partes_exp.append("Montos financieros expresados en Bolivianos (Bs. / BOB).")

        return InterpretacionReporteIaOut(
            estado="completada",
            codigo_reporte=reporte_elegido.codigo,
            nombre_reporte=reporte_elegido.nombre,
            vista_origen=reporte_elegido.vista_origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_sucursal=id_sucursal,
            nombre_sucursal=nombre_sucursal,
            id_categoria=id_categoria,
            nombre_categoria=nombre_categoria,
            tipo_grafico_sugerido=tipo_grafico,  # type: ignore[arg-type]
            formato_visualizacion=formato_vis,
            explicacion_ia=" ".join(partes_exp),
            origen_motor=origen_motor,
        )

    @staticmethod
    def _clasificar_determinista(texto_norm: str) -> Optional[str]:
        if any(
            k in texto_norm
            for k in (
                "mas vendido",
                "mas vendidos",
                "top producto",
                "top prendas",
                "ranking",
                "productos estrella",
                "prendas mas vendidas",
                "diez productos",
                "10 productos",
            )
        ):
            return "top_productos_vendidos"

        if any(
            k in texto_norm
            for k in (
                "inventario",
                "existencia",
                "existencias",
                "stock",
                "almacen",
                "valorizacion",
                "unidades disponibles",
            )
        ):
            return "inventario_por_sucursal"

        if any(k in texto_norm for k in ("reserva", "reservas", "apartado", "apartados")):
            return "reservas_por_estado_sucursal"

        if any(
            k in texto_norm
            for k in (
                "venta",
                "ventas",
                "ingreso",
                "ingresos",
                "facturacion",
                "recaudacion",
                "cobros",
                "ticket promedio",
            )
        ):
            return "ventas_por_sucursal"

        return None

    @staticmethod
    def _recopilar_ejemplos(catalogo_activo: list[CatalogoReporteIaORM]) -> list[str]:
        ejemplos: list[str] = []
        for r in catalogo_activo:
            for ej in r.ejemplos_consulta or []:
                if isinstance(ej, str) and ej not in ejemplos:
                    ejemplos.append(ej)
        if not ejemplos:
            ejemplos = [
                "Ventas de este mes agrupadas por sucursal en bolivianos",
                "Top 10 productos más vendidos este mes",
                "Inventario disponible y valorizado por sucursal",
                "Reservas del mes agrupadas por sucursal y estado",
            ]
        return ejemplos

    @classmethod
    def _clasificar_con_gemini(
        cls,
        prompt_texto: str,
        catalogo_activo: list[CatalogoReporteIaORM],
    ) -> Optional[str]:
        """Envía a Gemini SOLO el texto del usuario y los códigos/nombres del catálogo permitido."""
        try:
            resumen_catalogo = [
                {"codigo": r.codigo, "nombre": r.nombre, "descripcion": r.descripcion}
                for r in catalogo_activo
            ]
            instruccion = (
                "Eres un clasificador de reportes empresariales. "
                "Elige únicamente el `codigo` del reporte más adecuado del siguiente catálogo JSON "
                "para responder a la petición del usuario, o responde 'NINGUNO'.\n"
                f"CATÁLOGO PERMITIDO: {json.dumps(resumen_catalogo, ensure_ascii=False)}\n"
                f"PETICIÓN: {prompt_texto}\n"
                "Responde solo con el código exacto:"
            )
            payload = {
                "contents": [{"parts": [{"text": instruccion}]}],
                "generationConfig": {"temperature": 0.0, "maxOutputTokens": 40},
            }
            req = urllib.request.Request(
                f"{cls.GEMINI_API_URL}?key={settings.IA_API_KEY}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    cand = data.get("candidates", [])
                    if cand:
                        txt = (
                            cand[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                            .strip()
                            .lower()
                        )
                        return txt
        except Exception as exc:
            logger.debug("Fallback determinista activado en InterpreteReportesIA: %s", exc)
        return None
