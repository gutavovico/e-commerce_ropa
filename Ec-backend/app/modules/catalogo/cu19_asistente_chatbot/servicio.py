"""Servicio de dominio para CU19: Asistente Inteligente / Chatbot."""

from typing import List, Optional

from sqlalchemy.orm import Session

from integrations.gemini_service import gemini_service
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu19_asistente_chatbot.esquemas import (
    InteraccionChatbotHistorialOut,
    MensajeChatbotIn,
    ProductoChatbotOut,
    RespuestaChatbotOut,
    SucursalChatbotOut,
)
from modules.catalogo.cu19_asistente_chatbot.repositorio import ChatbotRepositorio
from modules.gestion_operativa.modelos import SucursalORM


class ServicioAsistenteChatbot:
    """Orquestador del asistente inteligente con RAG sobre catálogo y fallback de lujo."""

    @classmethod
    def procesar_mensaje(
        cls,
        db: Session,
        payload: MensajeChatbotIn,
        usuario: Optional[UsuarioORM] = None,
    ) -> RespuestaChatbotOut:
        """Procesa una consulta del usuario, recupera contexto real y persiste el intercambio."""
        id_cliente = usuario.id_usuario if usuario else None

        # 1. Recuperar contexto verídico de la base de datos (RAG)
        productos_raw = ChatbotRepositorio.buscar_contexto_productos(
            db=db,
            consulta=payload.mensaje,
            id_sucursal=payload.id_sucursal_preferida,
            limite=3,
        )
        sucursales_raw = ChatbotRepositorio.buscar_contexto_sucursales(
            db=db,
            consulta=payload.mensaje,
            limite=2,
        )

        # 2. Intentar generación con Google Gemini Flash
        respuesta_texto = gemini_service.generar_respuesta_chat(
            mensaje_usuario=payload.mensaje,
            contexto_prendas=productos_raw,
            contexto_sucursales=sucursales_raw,
        )

        # 3. Fallback determinista editorial si Gemini no está disponible o timeout
        if not respuesta_texto:
            respuesta_texto = cls._generar_respuesta_fallback(
                mensaje=payload.mensaje,
                productos=productos_raw,
                sucursales=sucursales_raw,
            )

        # 4. Persistir interacción en PostgreSQL (fashionstore.interacciones_chatbot)
        interaccion = ChatbotRepositorio.guardar_interaccion(
            db=db,
            id_cliente=id_cliente,
            mensaje_usuario=payload.mensaje,
            respuesta_ia=respuesta_texto,
            canal=payload.canal,
        )

        # 5. Formatear productos y sucursales sugeridas
        productos_out = [
            ProductoChatbotOut(
                id_producto=p["id_producto"],
                nombre=p["nombre"],
                precio=p["precio"],
                categoria=p.get("categoria"),
                imagen_url=p.get("imagen_url"),
                disponible=p.get("disponible", True),
                sucursal_nombre=p.get("sucursal_nombre"),
            )
            for p in productos_raw
        ]

        sucursales_out = [
            SucursalChatbotOut(
                id_sucursal=s.id_sucursal,
                nombre=s.nombre,
                direccion=s.direccion,
                horario=f"{s.horario_apertura.strftime('%H:%M')} - {s.horario_cierre.strftime('%H:%M')}",
            )
            for s in sucursales_raw
        ]

        # 6. Sugerencias rápidas dinámicas
        sugerencias = cls._generar_sugerencias_rapidas(payload.mensaje, bool(productos_out))

        return RespuestaChatbotOut(
            id_interaccion=interaccion.id_interaccion,
            respuesta=respuesta_texto,
            productos_sugeridos=productos_out,
            sucursales_sugeridas=sucursales_out,
            sugerencias_rapidas=sugerencias,
        )

    @classmethod
    def obtener_historial(
        cls,
        db: Session,
        id_cliente: int,
        limite: int = 15,
    ) -> List[InteraccionChatbotHistorialOut]:
        """Recupera el historial de chat del cliente autenticado."""
        interacciones = ChatbotRepositorio.obtener_historial_cliente(
            db=db,
            id_cliente=id_cliente,
            limite=limite,
        )
        return [
            InteraccionChatbotHistorialOut.model_validate(it)
            for it in interacciones
        ]

    @staticmethod
    def _generar_respuesta_fallback(
        mensaje: str,
        productos: List[dict],
        sucursales: List[SucursalORM],
    ) -> str:
        """Motor editorial determinista con tono de alta costura a costo cero."""
        m_lower = mensaje.lower().strip()

        # Intención 1: Horarios o sucursales
        if any(w in m_lower for w in ["horario", "sucursal", "tienda", "boutique", "donde", "direccion", "madrid", "santa cruz"]):
            if sucursales:
                primera = sucursales[0]
                horario = f"{primera.horario_apertura.strftime('%H:%M')} a {primera.horario_cierre.strftime('%H:%M')}"
                return (
                    f"Nuestra boutique '{primera.nombre}' se encuentra en {primera.direccion}, "
                    f"con atención de lunes a sábado de {horario}. Estaremos encantados de recibirte para "
                    "brindarte un asesoramiento personalizado y prueba en cabina."
                )
            return (
                "Nuestras boutiques Atelier atienden de lunes a sábado de 09:00 a 20:00. "
                "Puedes consultar la dirección exacta y disponibilidad de prendas en nuestro catálogo omnicanal."
            )

        # Intención 2: Consulta de prendas o estilos
        if any(w in m_lower for w in ["vestido", "blazer", "abrigo", "seda", "traje", "pantalon", "falda", "gala", "fiesta", "precio", "talla"]):
            if productos:
                nombres = ", ".join(f"'{p['nombre']}' (Bs. {p['precio']})" for p in productos[:2])
                return (
                    f"Para esta ocasión te recomendamos especialmente {nombres}. "
                    "Son piezas confeccionadas con materias primas nobles y corte artesanal. "
                    "Puedes explorar la ficha técnica completa o reservarlas para probártelas en boutique."
                )
            return (
                "Disponemos de exclusivas piezas de sastrería y alta costura en nuestra colección actual. "
                "Te invitamos a explorar las categorías de vestidos y blazers para descubrir siluetas a tu medida."
            )

        # Intención 3: Reserva o vestidor virtual
        if any(w in m_lower for w in ["reserva", "reservar", "probar", "probador", "vestidor", "realidad aumentada", "probador virtual"]):
            return (
                "Puedes probarte nuestras prendas directamente desde la app mediante el Vestidor Virtual de Realidad Aumentada, "
                "o bien agendar una reserva de hasta 3 piezas para que nuestro equipo las prepare en tu boutique preferida."
            )

        # Intención 4: Saludo o consulta general
        return (
            "Bienvenido a Fashion Store. Soy tu asesor de estilo personal. "
            "Puedo ayudarte a encontrar el look ideal para tu próxima gala, verificar existencias de prendas "
            "o consultar horarios y servicios en nuestras boutiques."
        )

    @staticmethod
    def _generar_sugerencias_rapidas(mensaje: str, hay_productos: bool) -> List[str]:
        """Genera chips rápidos contextuales según la última interacción."""
        m = mensaje.lower()
        if "horario" in m or "sucursal" in m:
            return [
                "¿Cómo agendar una reserva en boutique?",
                "¿Tienen probador virtual?",
                "Ver vestidos de nueva colección",
            ]
        if hay_productos:
            return [
                "¿Tienen probador virtual para estas prendas?",
                "¿Qué tallas quedan disponibles?",
                "¿Cómo llegar a la boutique más cercana?",
            ]
        return [
            "¿Tienen vestidos de gala en Madrid?",
            "¿Cuáles son los horarios de atención?",
            "¿Cómo funciona el vestidor virtual?",
        ]
