"""Repositorio de acceso a datos para CU19: Asistente Inteligente / Chatbot."""

import re
from typing import List, Optional

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, joinedload

from modules.catalogo.cu19_asistente_chatbot.modelos import InteraccionChatbotORM
from modules.catalogo.modelos import (
    CategoriaORM,
    InventarioSucursalORM,
    ProductoORM,
    VarianteProductoORM,
)
from modules.gestion_operativa.modelos import SucursalORM


class ChatbotRepositorio:
    """Acceso a datos e historial para el asistente inteligente."""

    @staticmethod
    def guardar_interaccion(
        db: Session,
        id_cliente: Optional[int],
        mensaje_usuario: str,
        respuesta_ia: str,
        canal: str,
    ) -> InteraccionChatbotORM:
        """Persiste una interacción en `fashionstore.interacciones_chatbot`."""
        interaccion = InteraccionChatbotORM(
            id_cliente=id_cliente,
            mensaje_usuario=mensaje_usuario,
            respuesta_ia=respuesta_ia,
            canal=canal,
        )
        db.add(interaccion)
        db.commit()
        db.refresh(interaccion)
        return interaccion

    @staticmethod
    def obtener_historial_cliente(
        db: Session,
        id_cliente: int,
        limite: int = 15,
    ) -> List[InteraccionChatbotORM]:
        """Obtiene las interacciones recientes de un cliente ordenadas cronológicamente."""
        stmt = (
            select(InteraccionChatbotORM)
            .where(InteraccionChatbotORM.id_cliente == id_cliente)
            .order_by(desc(InteraccionChatbotORM.creado_en))
            .limit(limite)
        )
        resultados = db.execute(stmt).scalars().all()
        # Retornar en orden cronológico ascendente para renderizar como chat
        return list(reversed(resultados))

    @staticmethod
    def buscar_contexto_productos(
        db: Session,
        consulta: str,
        id_sucursal: Optional[int] = None,
        limite: int = 5,
    ) -> List[dict]:
        """Busca productos reales que coincidan con la intención de la consulta.

        Prioriza productos activos con variantes y disponibilidad de inventario.
        """
        # Extraer palabras clave de más de 2 caracteres
        palabras = [p.lower() for p in re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}\b", consulta)]
        # Palabras comunes a ignorar
        stopwords = {
            "para", "como", "cual", "cuales", "donde", "tienen", "tiene", "hola", "buenas",
            "dias", "tardes", "noches", "quiero", "busco", "necesito", "favor", "gracias",
            "puedo", "esta", "estan", "unos", "unas", "sobre", "entre"
        }
        terminos = [p for p in palabras if p not in stopwords]

        query = (
            select(ProductoORM)
            .options(
                joinedload(ProductoORM.categoria),
                joinedload(ProductoORM.coleccion),
                joinedload(ProductoORM.variantes).joinedload(VarianteProductoORM.inventarios),
            )
            .where(ProductoORM.activo.is_(True))
        )

        if terminos:
            filtros = []
            for t in terminos:
                filtros.append(ProductoORM.nombre.ilike(f"%{t}%"))
                filtros.append(ProductoORM.descripcion.ilike(f"%{t}%"))
                filtros.append(CategoriaORM.nombre.ilike(f"%{t}%"))
            query = query.join(ProductoORM.categoria).where(or_(*filtros))

        query = query.order_by(desc(ProductoORM.id_producto)).limit(limite * 2)
        candidatos = db.execute(query).unique().scalars().all()

        if not candidatos:
            # Fallback: tomar los productos más recientes del catálogo
            fallback_query = (
                select(ProductoORM)
                .options(
                    joinedload(ProductoORM.categoria),
                    joinedload(ProductoORM.coleccion),
                    joinedload(ProductoORM.variantes).joinedload(VarianteProductoORM.inventarios),
                )
                .where(ProductoORM.activo.is_(True))
                .order_by(desc(ProductoORM.id_producto))
                .limit(limite)
            )
            candidatos = db.execute(fallback_query).unique().scalars().all()

        resultado: List[dict] = []
        for prod in candidatos:
            # Calcular si tiene stock disponible
            tiene_stock = False
            sucursal_disponible = None

            for var in prod.variantes:
                for inv in var.inventarios:
                    if id_sucursal:
                        if inv.id_sucursal == id_sucursal and inv.cantidad_disponible > 0:
                            tiene_stock = True
                            sucursal_disponible = inv.sucursal.nombre if inv.sucursal else None
                            break
                    else:
                        if inv.cantidad_disponible > 0:
                            tiene_stock = True
                            sucursal_disponible = inv.sucursal.nombre if inv.sucursal else None
                            break
                if tiene_stock:
                    break

            resultado.append(
                {
                    "id_producto": prod.id_producto,
                    "nombre": prod.nombre,
                    "precio": f"{prod.precio_base:.2f}",
                    "categoria": prod.categoria.nombre if prod.categoria else "Alta Costura",
                    "imagen_url": prod.imagen_url,
                    "disponible": tiene_stock,
                    "sucursal_nombre": sucursal_disponible,
                }
            )
            if len(resultado) >= limite:
                break

        return resultado

    @staticmethod
    def buscar_contexto_sucursales(
        db: Session,
        consulta: str,
        limite: int = 3,
    ) -> List[SucursalORM]:
        """Busca sucursales activas coincidentes con ciudades o nombres consultados."""
        palabras = [p.lower() for p in re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}\b", consulta)]

        query = select(SucursalORM).where(SucursalORM.activa.is_(True))

        filtros = []
        for p in palabras:
            filtros.append(SucursalORM.nombre.ilike(f"%{p}%"))
            filtros.append(SucursalORM.direccion.ilike(f"%{p}%"))

        if filtros:
            coincidentes = db.execute(
                query.where(or_(*filtros)).limit(limite)
            ).scalars().all()
            if coincidentes:
                return list(coincidentes)

        # Si no hubo coincidencia específica, retornar las primeras sucursales activas
        return list(db.execute(query.order_by(SucursalORM.id_sucursal).limit(limite)).scalars().all())

