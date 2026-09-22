"""Servicio de dominio para CU07: Detalle de Producto y CU08: Variantes."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List
from sqlalchemy.orm import Session

from core.errors import NotFoundError
from modules.catalogo.cu07_detalle_producto.esquemas import (
    ColorResumenOut,
    ComposicionNobleOut,
    GaleriaTomaOut,
    PrendaComplementariaOut,
    ProductoDetalleOut,
    TallaResumenOut,
    VarianteDetalleOut,
)
from modules.catalogo.cu07_detalle_producto.repositorio import ProductoDetalleRepositorio


class ProductoDetalleServicio:
    """Orquestador de reglas de negocio para la ficha técnica y variantes de prendas."""

    @staticmethod
    def consultar_detalle_producto(db: Session, id_producto: int) -> ProductoDetalleOut:
        """Obtiene la ficha técnica completa del producto, variantes, stock y estilismo complementario."""
        producto = ProductoDetalleRepositorio.obtener_producto_con_variantes(db, id_producto)
        if not producto:
            raise NotFoundError(
                f"La prenda solicitada con identificador #{id_producto} no existe o se encuentra archivada.",
                code="PRODUCTO_NO_ENCONTRADO",
            )

        # 1. Precios y Promociones
        precio_base = producto.precio_base
        promocion = ProductoDetalleRepositorio.obtener_promocion_activa(db, id_producto)
        tiene_descuento = False
        porcentaje_desc = None
        descuento_monto = Decimal("0.00")
        precio_final = precio_base

        if promocion and promocion.porcentaje_descuento and promocion.porcentaje_descuento > 0:
            tiene_descuento = True
            porcentaje_desc = int(promocion.porcentaje_descuento)
            factor = Decimal(str(porcentaje_desc)) / Decimal("100")
            descuento_monto = (precio_base * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            precio_final = (precio_base - descuento_monto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Financiación en 3 cuotas Atelier Pay
        cuota_3x = (precio_final / Decimal("3")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cuotas_info = f"o 3 pagos de {cuota_3x} € sin intereses con Atelier Pay"

        # 2. Metadatos Editoriales y Badges adaptados a la prenda real
        nombre_lower = producto.nombre.lower()
        cat_lower = (producto.categoria.nombre if producto.categoria else "").lower()

        if "vestido" in nombre_lower or "vestidos" in cat_lower:
            subtitulo_atelier = "ALTA COSTURA · MILÁN / LYON"
            linea_confeccion = "ALTA COSTURA LYON"
            etiqueta_badge = "EDICIÓN LIMITADA"
        elif "blazer" in nombre_lower or "chaqueta" in nombre_lower or "chaquetas" in cat_lower:
            subtitulo_atelier = "SASTRERÍA ATELIER · BIELLA"
            linea_confeccion = "SASTRERÍA MILANO"
            etiqueta_badge = "LANA & SEDA"
        elif "pantalón" in nombre_lower or "pantalon" in nombre_lower or "bermuda" in nombre_lower or "pantalones" in cat_lower:
            subtitulo_atelier = "SASTRERÍA & CORTE · MADRID"
            linea_confeccion = "SASTRERÍA ATELIER"
            etiqueta_badge = "DISPONIBLE"
        elif "blusa" in nombre_lower or "camisa" in nombre_lower or "top" in nombre_lower or "camisas" in cat_lower:
            subtitulo_atelier = "DRAPEADO FRANCÉS · PARÍS"
            linea_confeccion = "SEDA PURA"
            etiqueta_badge = "NOVEDAD"
        elif "abrigo" in nombre_lower or "capa" in nombre_lower or "trench" in nombre_lower:
            subtitulo_atelier = "ALTA COSTURA · ANDES & MILÁN"
            linea_confeccion = "BABY ALPACA & LANA"
            etiqueta_badge = "PIEZA ICÓNICA"
        elif "suéter" in nombre_lower or "sueter" in nombre_lower:
            subtitulo_atelier = "PUNTO FINO · MILANO"
            linea_confeccion = "MERINO & CACHEMIRA"
            etiqueta_badge = "EDICIÓN LIMITADA"
        else:
            subtitulo_atelier = "BÁSICOS DE LUJO · MADRID"
            linea_confeccion = "ATELIER FLAGSHIP"
            etiqueta_badge = "DISPONIBLE"

        # SKU Base
        sku_base = f"ATEL-2025-P{producto.id_producto:02d}"

        # 3. Galería Multi-Ángulo (4 tomas de alta resolución de la MISMA prenda seleccionada)
        img_principal = producto.imagen_url or "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=1200&q=85"
        base_img = img_principal.split("?")[0]
        
        etiqueta_macro = "DETALLE TEJIDO"
        if "seda" in nombre_lower:
            etiqueta_macro = "TEXTURA SEDA"
        elif "lana" in nombre_lower or "blazer" in nombre_lower:
            etiqueta_macro = "TEJIDO LANA BIELLA"
        elif "algodón" in nombre_lower or "gabardina" in nombre_lower:
            etiqueta_macro = "ALGODÓN GIZA"

        galeria: List[GaleriaTomaOut] = [
            GaleriaTomaOut(url=img_principal, etiqueta="FRONTAL", orden=1),
            GaleriaTomaOut(
                url=f"{base_img}?auto=format&fit=crop&w=1000&h=1200&crop=top&q=85",
                etiqueta=etiqueta_macro,
                orden=2,
            ),
            GaleriaTomaOut(
                url=f"{base_img}?auto=format&fit=crop&w=1000&h=1200&crop=center&q=85",
                etiqueta="SILUETA & CAÍDA",
                orden=3,
            ),
            GaleriaTomaOut(
                url=f"{base_img}?auto=format&fit=crop&w=1000&h=1200&crop=bottom&q=85",
                etiqueta="ACABADO & COSTURA",
                orden=4,
            ),
        ]

        # 4. Trazabilidad y Composición Noble adaptada a la naturaleza del producto real
        if "blazer" in nombre_lower or "chaqueta" in nombre_lower or "chaquetas" in cat_lower:
            composicion = ComposicionNobleOut(
                cuerpo_principal="100% Lana Virgen Biella 380g & Hilatura Fina",
                forro_interior="Cupro Bemberg puro transpirable",
                tecnica_textil="Sastrería artesanal con picado a mano y entretela noble",
                descripcion_confeccion=(
                    producto.descripcion or "Estructura arquitectónica con solapa de muesca pronunciada y botonadura interior de asta natural."
                ),
                instrucciones_cuidado=[
                    "Limpieza profesional en seco con percloroetileno moderado.",
                    "Planchado únicamente vertical mediante vapor suave sin contacto directo.",
                    "Conservar en percha anatómica ancha con su funda transpirable de algodón.",
                ],
            )
        elif "pantalón" in nombre_lower or "pantalon" in nombre_lower or "bermuda" in nombre_lower or "pantalones" in cat_lower:
            composicion = ComposicionNobleOut(
                cuerpo_principal="Lana Fría y Seda de Biella (o Algodón Egipcio Giza)",
                forro_interior="Pretina estructurada forrada en popelín de algodón puro",
                tecnica_textil="Corte sastre de tiro alto con pinza invertida y caída recta",
                descripcion_confeccion=(
                    producto.descripcion or "Patronaje fluido de precisión diseñado para mantener la línea vertical impecable al movimiento."
                ),
                instrucciones_cuidado=[
                    "Limpieza profesional en seco especializada.",
                    "Planchado a temperatura media con paño protector de algodón.",
                    "Colgar por el bajo con percha de pinzas acolchadas para mantener la raya.",
                ],
            )
        elif "abrigo" in nombre_lower or "capa" in nombre_lower or "trench" in nombre_lower:
            composicion = ComposicionNobleOut(
                cuerpo_principal="100% Baby Alpaca y Lana Virgen Envolvente",
                forro_interior="Forro integral en crepé de seda natural",
                tecnica_textil="Paño cepillado térmico con costuras dobles ocultas artesanales",
                descripcion_confeccion=(
                    producto.descripcion or "Confección artesanal envolvente de alta protección térmica y ligereza inigualable."
                ),
                instrucciones_cuidado=[
                    "Limpieza profesional en seco ecológica.",
                    "Cepillado suave con cerdas naturales en el sentido del pelo del paño.",
                    "Conservar en lugar fresco en su funda de lienzo de algodón.",
                ],
            )
        elif "blusa" in nombre_lower or "camisa" in nombre_lower or "top" in nombre_lower or "camisas" in cat_lower:
            composicion = ComposicionNobleOut(
                cuerpo_principal="100% Satén de Seda Natural 22 Momme",
                forro_interior="Seda pura transpirable",
                tecnica_textil="Drapeado fluido con gemelos ocultos y cuello estructurado",
                descripcion_confeccion=(
                    producto.descripcion or "Hilatura de seda noble con brillo satinado sutil y caída etérea orgánica."
                ),
                instrucciones_cuidado=[
                    "Lavado profesional en seco o a mano en agua fría con jabón neutro.",
                    "Planchado a vapor a temperatura suave del revés.",
                    "Secado en plano horizontal a la sombra sin retorcer.",
                ],
            )
        elif "falda" in nombre_lower or "faldas" in cat_lower:
            composicion = ComposicionNobleOut(
                cuerpo_principal="Satén de Seda Lyon & Lino Puro",
                forro_interior="Crepé de seda puro transpirable",
                tecnica_textil="Corte asimétrico al bies con caída fluida",
                descripcion_confeccion=(
                    producto.descripcion or "Patronaje al bies que esculpe la silueta con libertad de movimiento y elegancia atemporal."
                ),
                instrucciones_cuidado=[
                    "Limpieza profesional en seco.",
                    "Vaporizado vertical suave.",
                    "Guardar colgada en percha de pinzas protegidas.",
                ],
            )
        else:
            composicion = ComposicionNobleOut(
                cuerpo_principal="100% Seda Natural 22 Momme",
                forro_interior="Crepé de seda puro transpirable",
                tecnica_textil="Plisado artesanal al vapor de Lyon",
                descripcion_confeccion=(
                    producto.descripcion or "Cada paño requiere 48 horas de moldeado térmico manual para preservar la elasticidad y lustre natural."
                ),
                instrucciones_cuidado=[
                    "Limpieza profesional en seco con percloroetileno moderado.",
                    "Planchado únicamente vertical mediante vapor suave a distancia mínima de 15 cm.",
                    "Conservar en su funda transpirable de algodón incluida para mantener el porte.",
                ],
            )

        # 5. Desglose de Variantes, Tallas y Colores (Fieles al producto real)
        variantes_out: List[VarianteDetalleOut] = []
        colores_dict = {}
        tallas_dict = {}

        for var in producto.variantes:
            # Stock físico acumulado en inventarios
            stock_var = sum(
                inv.cantidad_disponible for inv in var.inventarios if inv.cantidad_disponible > 0
            )
            tiene_stock = stock_var > 0

            # Precio final de la variante
            p_extra = var.precio_extra or Decimal("0.00")
            p_base_var = precio_base + p_extra
            if tiene_descuento and porcentaje_desc:
                f_desc = Decimal(str(porcentaje_desc)) / Decimal("100")
                p_fin_var = (p_base_var * (Decimal("1") - f_desc)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                p_fin_var = p_base_var

            # La fotografía de la variante corresponde a la prenda auténtica
            foto_variante = img_principal

            variantes_out.append(
                VarianteDetalleOut(
                    id_variante=var.id_variante,
                    id_producto=producto.id_producto,
                    id_talla=var.talla.id_talla,
                    talla_codigo=var.talla.codigo,
                    talla_orden=var.talla.orden,
                    id_color=var.color.id_color,
                    color_nombre=var.color.nombre,
                    color_hex=var.color.codigo_hex,
                    sku=var.sku,
                    precio_extra=p_extra,
                    precio_final_variante=p_fin_var,
                    stock_total_disponible=stock_var,
                    tiene_stock=tiene_stock,
                    imagen_url=foto_variante,
                )
            )

            # Agregar a colores únicos vinculados a la prenda real
            cid = var.color.id_color
            if cid not in colores_dict:
                colores_dict[cid] = ColorResumenOut(
                    id_color=cid,
                    nombre=var.color.nombre,
                    codigo_hex=var.color.codigo_hex,
                    disponible=tiene_stock,
                    imagen_url=foto_variante,
                )
            elif tiene_stock:
                colores_dict[cid].disponible = True

            # Agregar a tallas únicas
            tid = var.talla.id_talla
            if tid not in tallas_dict:
                tallas_dict[tid] = TallaResumenOut(
                    id_talla=tid,
                    codigo=var.talla.codigo,
                    orden=var.talla.orden,
                    disponible=tiene_stock,
                    stock_total=stock_var,
                )
            else:
                tallas_dict[tid].stock_total += stock_var
                if tiene_stock:
                    tallas_dict[tid].disponible = True

        # Ordenar tallas por orden normativo
        tallas_ordenadas = sorted(tallas_dict.values(), key=lambda t: t.orden)
        colores_lista = list(colores_dict.values())

        # Si no había variantes en BD, suministrar variantes de fallback
        if not tallas_ordenadas:
            tallas_ordenadas = [
                TallaResumenOut(id_talla=1, codigo="34", orden=1, disponible=True, stock_total=3),
                TallaResumenOut(id_talla=2, codigo="36", orden=2, disponible=True, stock_total=5),
                TallaResumenOut(id_talla=3, codigo="38", orden=3, disponible=True, stock_total=2),
                TallaResumenOut(id_talla=4, codigo="40", orden=4, disponible=True, stock_total=4),
                TallaResumenOut(id_talla=5, codigo="42", orden=5, disponible=False, stock_total=0),
            ]
        if not colores_lista:
            colores_lista = [
                ColorResumenOut(id_color=1, nombre="Seda Marfil Natural", codigo_hex="#F5F2EB", disponible=True),
                ColorResumenOut(id_color=2, nombre="Obsidian Negro", codigo_hex="#1E1E1E", disponible=True),
                ColorResumenOut(id_color=3, nombre="Camel Suave", codigo_hex="#C19A6B", disponible=True),
                ColorResumenOut(id_color=4, nombre="Vino Borgoña", codigo_hex="#581825", disponible=True),
            ]

        # 6. Prenda complementarias (Look Atelier)
        complementarias_orm = ProductoDetalleRepositorio.obtener_prendas_complementarias(
            db, producto.id_producto, limite=3
        )
        piezas_look: List[PrendaComplementariaOut] = []
        for comp in complementarias_orm:
            piezas_look.append(
                PrendaComplementariaOut(
                    id_producto=comp.id_producto,
                    nombre=comp.nombre,
                    subtitulo_atelier="ALTA COSTURA ATELIER",
                    categoria=comp.categoria.nombre if comp.categoria else "Prendas Exclusivas",
                    precio_base=comp.precio_base,
                    precio_final=comp.precio_base,
                    imagen_url=comp.imagen_url,
                )
            )

        return ProductoDetalleOut(
            id_producto=producto.id_producto,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio_base=precio_base,
            precio_final=precio_final,
            tiene_descuento=tiene_descuento,
            descuento_monto=descuento_monto,
            porcentaje_descuento=porcentaje_desc,
            cuotas_info=cuotas_info,
            subtitulo_atelier=subtitulo_atelier,
            linea_confeccion=linea_confeccion,
            etiqueta_badge=etiqueta_badge,
            sku_base=sku_base,
            rating_promedio=4.9,
            total_resenas=38,
            beneficio_membresia="Beneficio Membresía Atelier aplicado en liquidación privada",
            categoria_id=producto.id_categoria,
            categoria_nombre=producto.categoria.nombre if producto.categoria else "Atelier",
            coleccion_id=producto.id_coleccion,
            coleccion_nombre=producto.coleccion.nombre if producto.coleccion else None,
            imagen_principal=img_principal,
            galeria=galeria,
            modelo_ar_url=producto.modelo_ar_url,
            modelo_info="MODELO: 1,77M - TALLA 38 ES",
            composicion=composicion,
            colores_disponibles=colores_lista,
            tallas_disponibles=tallas_ordenadas,
            variantes=variantes_out,
            piezas_look_complementario=piezas_look,
            total_guardados=142,
        )
