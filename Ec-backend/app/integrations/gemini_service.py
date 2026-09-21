"""Servicio de integración con IA para FashionStore (Google Gemini Flash + Fallback Determinista).

Provee explicabilidad estilística y motivos de recomendación para CU18.
Si `IA_API_KEY` está configurada, utiliza la API de Google Gemini Flash (vía HTTP REST).
Si la clave está ausente o la API externa no responde en el tiempo límite (timeout 3s),
conmuta de forma automática y transparente a una síntesis determinista de alta costura
sin costo y sin interrupción del servicio.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from core.config import settings

logger = logging.getLogger("fashionstore.gemini_service")


class GeminiService:
    """Cliente ligero y desacoplado para servicios de IA y explicabilidad."""

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.IA_API_KEY

    def generar_motivo_recomendacion(
        self,
        categoria_principal: str,
        coleccion_principal: Optional[str] = None,
        sucursal_nombre: Optional[str] = "Flagship Serrano (Madrid)",
        nombre_prenda_reciente: Optional[str] = None,
    ) -> str:
        """Genera un motivo editorial para la sección 'Recomendado para ti'.

        Ejemplo esperado:
        'Basado en tu última adquisición de sastrería y seda en Flagship Serrano (Madrid).'
        """
        if self.api_key:
            try:
                motivo_ia = self._consultar_gemini(
                    categoria_principal=categoria_principal,
                    coleccion_principal=coleccion_principal,
                    sucursal_nombre=sucursal_nombre,
                    nombre_prenda_reciente=nombre_prenda_reciente,
                )
                if motivo_ia:
                    return motivo_ia
            except Exception as e:
                logger.warning(
                    "Fallo al consultar Google Gemini Flash (%s). Conmutando a fallback determinista.",
                    str(e),
                )

        return self.generar_motivo_fallback(
            categoria_principal=categoria_principal,
            coleccion_principal=coleccion_principal,
            sucursal_nombre=sucursal_nombre,
        )

    def _consultar_gemini(
        self,
        categoria_principal: str,
        coleccion_principal: Optional[str],
        sucursal_nombre: Optional[str],
        nombre_prenda_reciente: Optional[str],
    ) -> Optional[str]:
        """Envía solicitud a Google Gemini Flash con timeout estricto."""
        url = f"{self.GEMINI_API_URL}?key={self.api_key}"

        prompt = (
            "Eres el director de estilo de 'FASHION STORE', una firma europea de alta costura, "
            "sastrería artesanal y tejidos nobles. "
            "Genera UNA SOLA frase breve y sofisticada (máximo 16 palabras) para el encabezado 'Recomendado para ti'. "
            f"El cliente adquirió recientemente prendas de categoría '{categoria_principal}' "
            f"{f'en la colección {coleccion_principal}' if coleccion_principal else ''} "
            f"en la boutique '{sucursal_nombre or 'Flagship Serrano (Madrid)'}'. "
            "Empieza con 'Basado en tu última adquisición de...' o 'Inspirado en tu selección de...'. "
            "Responde únicamente con la frase, sin comillas ni texto adicional."
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 40,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                body = json.loads(response.read().decode("utf-8"))
                candidates = body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        texto = parts[0]["text"].strip()
                        if texto:
                            return texto.strip('"').strip("'")

        return None

    @staticmethod
    def generar_motivo_fallback(
        categoria_principal: str,
        coleccion_principal: Optional[str] = None,
        sucursal_nombre: Optional[str] = None,
    ) -> str:
        """Generador determinista con copy editorial de alta costura a costo cero."""
        boutique = sucursal_nombre or "Flagship Serrano (Madrid)"
        cat_lower = categoria_principal.lower().strip()

        if "vestid" in cat_lower or "seda" in cat_lower:
            return f"Basado en tu última adquisición de sastrería y seda en {boutique}."
        elif "blazer" in cat_lower or "chaqueta" in cat_lower or "traje" in cat_lower:
            return f"Basado en tu última selección de sastrería y lana virgen en {boutique}."
        elif "abrigo" in cat_lower:
            return f"Inspirado en tu última adquisición de prendas de abrigo y paño noble en {boutique}."
        elif "pantalon" in cat_lower or "falda" in cat_lower:
            return f"Basado en tu preferencia por siluetas depuradas y corte artesanal en {boutique}."
        else:
            if coleccion_principal:
                return f"Basado en tu afinidad por la colección {coleccion_principal} en {boutique}."
            return f"Basado en tu última adquisición de {cat_lower} en {boutique}."


# Instancia singleton accesible para el módulo
gemini_service = GeminiService()
