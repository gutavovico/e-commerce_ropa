import 'package:flutter/material.dart';
import '../../datos/modelos/producto_detalle_dto.dart';
import '../bloc/producto_detalle_bloc.dart';

/// Pantalla Completa de Detalle de Prenda de Alta Costura (CU07, CU08, CU09, CU12, CU10)
///
/// Conforme a la Directriz Global Hub-and-Spoke:
/// - Es una pantalla secundaria (hoja) abierta a pantalla completa.
/// - Oculta estrictamente la BottomNavigationBar del contenedor Hub.
/// - Incluye botón funcional de retorno contextual `← VOLVER` (Navigator.pop).
/// - Tipografía 100% Outfit (sin tipografías serif).
/// - Galería multiángulo de la MISMA prenda auténtica (cero modelos ajenos ni masculinos).
/// - Selector cromático y selector de tallas en cascada con validación de existencias.
/// - Sección continua de disponibilidad física por boutique con botón directo de reserva.
class PantallaProductoDetalle extends StatefulWidget {
  final int idProducto;
  final String? token;
  final bool habilitarImagenesRed;
  final ProductoDetalleBloc? bloc;

  const PantallaProductoDetalle({
    super.key,
    required this.idProducto,
    this.token,
    this.habilitarImagenesRed = true,
    this.bloc,
  });

  @override
  State<PantallaProductoDetalle> createState() => _PantallaProductoDetalleState();
}

class _PantallaProductoDetalleState extends State<PantallaProductoDetalle> {
  late final ProductoDetalleBloc _bloc;

  // Estado de acordeones expandibles
  bool _acordeonComposicionAbierto = true;
  bool _acordeonBoutiquesAbierto = true;
  bool _acordeonCitaInfoAbierto = false;

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? ProductoDetalleBloc();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _bloc.cargarDetalle(widget.idProducto);
      }
    });
  }

  void _mostrarSnackBar(String mensaje, {bool esError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          mensaje,
          style: const TextStyle(
            fontFamily: 'Outfit',
            color: Colors.white,
            fontSize: 12,
            letterSpacing: 0.5,
            fontWeight: FontWeight.w500,
          ),
        ),
        backgroundColor: esError ? const Color(0xFF991B1B) : const Color(0xFF0F1116),
        duration: const Duration(seconds: 3),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: _construirAppBar(),
      body: AnimatedBuilder(
        animation: _bloc,
        builder: (context, _) {
          final estado = _bloc.estado;

          if (estado is ProductoDetalleCargando) {
            return const Center(
              child: CircularProgressIndicator(color: Colors.black),
            );
          }

          if (estado is ProductoDetalleError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, size: 40, color: Color(0xFF991B1B)),
                    const SizedBox(height: 12),
                    Text(
                      estado.mensaje,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 13,
                        color: Color(0xFF666666),
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.black,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      onPressed: () => _bloc.cargarDetalle(widget.idProducto),
                      child: const Text(
                        'Reintentar',
                        style: TextStyle(
                          fontFamily: 'Outfit',
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          if (estado is ProductoDetalleCargado) {
            return Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 1. Galería de alta costura multiángulo (4 fotos de la misma prenda)
                        _construirGaleria(estado),

                        // 2. Información técnica, nombre, rating y precios
                        Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _construirHeaderYPrecios(estado),
                              const SizedBox(height: 16),
                              const Divider(height: 1, color: Color(0xFFECEAE6)),
                              const SizedBox(height: 16),

                              // 3. Selector Cromático (CU08)
                              _construirSelectorColor(estado),
                              const SizedBox(height: 16),

                              // 4. Selector de Tallas en Cascada (CU08)
                              _construirSelectorTallas(estado),
                              const SizedBox(height: 12),

                              // 5. Píldora de stock en tiempo real
                              _construirPildoraStock(estado),
                              const SizedBox(height: 24),

                              // 6. Sección de Especificaciones & Acordeones
                              _construirSeccionAcordeones(estado),
                              const SizedBox(height: 24),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // 7. Barra Inferior Persistente de Compra (con botón AR y Añadir a Bolsa)
                _construirBarraInferiorCompra(estado),
              ],
            );
          }

          return const SizedBox.shrink();
        },
      ),
    );
  }

  // ==========================================
  // APP BAR CON RETORNO CONTEXTUAL (Hub-and-Spoke)
  // ==========================================
  PreferredSizeWidget _construirAppBar() {
    return AppBar(
      automaticallyImplyLeading: false,
      backgroundColor: Colors.white,
      elevation: 0,
      scrolledUnderElevation: 0,
      titleSpacing: 0,
      leadingWidth: 120,
      leading: GestureDetector(
        onTap: () => Navigator.of(context).pop(),
        behavior: HitTestBehavior.opaque,
        child: Padding(
          padding: const EdgeInsets.only(left: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: const [
              Icon(Icons.arrow_back, color: Colors.black, size: 18),
              SizedBox(width: 4),
              Text(
                'VOLVER',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  color: Colors.black,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                ),
              ),
            ],
          ),
        ),
      ),
      title: const Center(
        child: Text(
          'FASHION STORE',
          style: TextStyle(
            fontFamily: 'Outfit',
            color: Colors.black,
            fontSize: 13,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.4,
          ),
        ),
      ),
      actions: [
        AnimatedBuilder(
          animation: _bloc,
          builder: (context, _) {
            final esFav = (_bloc.estado is ProductoDetalleCargado) &&
                (_bloc.estado as ProductoDetalleCargado).esFavorito;
            return IconButton(
              icon: Icon(
                esFav ? Icons.favorite : Icons.favorite_border,
                color: esFav ? const Color(0xFF991B1B) : Colors.black,
                size: 20,
              ),
              onPressed: () {
                _bloc.toggleFavorito();
                if (_bloc.estado is ProductoDetalleCargado) {
                  final notif =
                      (_bloc.estado as ProductoDetalleCargado).mensajeNotificacion;
                  if (notif != null) _mostrarSnackBar(notif);
                }
              },
              tooltip: 'Deseos Atelier',
            );
          },
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  // ==========================================
  // 1. GALERÍA MULTIÁNGULO (CU07 + CU10 AR)
  // ==========================================
  Widget _construirGaleria(ProductoDetalleCargado estado) {
    final imagenes = estado.imagenesGaleria;
    final index = estado.indiceGaleria.clamp(0, imagenes.length - 1);
    final imagenActual = imagenes[index];

    return Column(
      children: [
        // Imagen Principal en ratio 3:4 con Badges flotantes
        AspectRatio(
          aspectRatio: 0.75,
          child: Stack(
            fit: StackFit.expand,
            children: [
              Container(
                color: const Color(0xFFF7F5F2),
                child: widget.habilitarImagenesRed && imagenActual.url.isNotEmpty
                    ? Image.network(
                        imagenActual.url,
                        fit: BoxFit.cover,
                        alignment: Alignment.topCenter,
                        errorBuilder: (_, _, _) => _placeholderGaleria(),
                      )
                    : _placeholderGaleria(),
              ),

              // Badges Superiores Izquierdos
              Positioned(
                top: 12,
                left: 12,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.9),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: Text(
                        (estado.producto.etiquetaBadge ?? 'EDICIÓN LIMITADA').toUpperCase(),
                        style: const TextStyle(
                          fontFamily: 'Outfit',
                          color: Colors.white,
                          fontSize: 8,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.92),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: Text(
                        estado.producto.subtituloAtelier.toUpperCase(),
                        style: const TextStyle(
                          fontFamily: 'Outfit',
                          color: Colors.black,
                          fontSize: 8,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.1,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Contador de imagen inferior izquierdo "1 / 4"
              Positioned(
                bottom: 12,
                left: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.9),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${index + 1} / ${imagenes.length}',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      color: Colors.black,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ),

              // Botón Flotante CU10: [ 👁 PROBAR EN AR ]
              Positioned(
                bottom: 12,
                right: 12,
                child: GestureDetector(
                  onTap: () => _abrirModalVestidorAr(),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: const [
                        BoxShadow(
                          color: Colors.black26,
                          blurRadius: 6,
                          offset: Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Icon(Icons.view_in_ar, size: 14, color: Colors.white),
                        SizedBox(width: 6),
                        Text(
                          'PROBAR EN AR',
                          style: TextStyle(
                            fontFamily: 'Outfit',
                            color: Colors.white,
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 10),

        // Tira de miniaturas multiángulo (4 encuadres)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: List.generate(imagenes.length, (i) {
              final img = imagenes[i];
              final activa = i == index;
              return Expanded(
                child: GestureDetector(
                  onTap: () => _bloc.cambiarIndiceGaleria(i),
                  child: Container(
                    margin: EdgeInsets.only(
                      right: i < imagenes.length - 1 ? 8 : 0,
                    ),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: activa ? Colors.black : const Color(0xFFE4E4E7),
                        width: activa ? 2 : 1,
                      ),
                      borderRadius: BorderRadius.circular(2),
                    ),
                    child: Column(
                      children: [
                        AspectRatio(
                          aspectRatio: 1.0,
                          child: widget.habilitarImagenesRed && img.url.isNotEmpty
                              ? Image.network(
                                  img.url,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, _, _) => _placeholderGaleria(),
                                )
                              : _placeholderGaleria(),
                        ),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(vertical: 3),
                          color: activa ? Colors.black : const Color(0xFFF9F9F8),
                          child: Text(
                            img.etiqueta.toUpperCase(),
                            textAlign: TextAlign.center,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontFamily: 'Outfit',
                              fontSize: 7.5,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.5,
                              color: activa ? Colors.white : const Color(0xFF71717A),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ],
    );
  }

  Widget _placeholderGaleria() {
    return Container(
      color: const Color(0xFFF2EFEB),
      child: const Center(
        child: Icon(Icons.checkroom, color: Color(0xFFC0BDB8), size: 36),
      ),
    );
  }

  // ==========================================
  // 2. HEADER Y PRECIOS
  // ==========================================
  Widget _construirHeaderYPrecios(ProductoDetalleCargado estado) {
    final prod = estado.producto;
    final precio = estado.precioActual;
    final sku = estado.skuActual;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Subtítulo y SKU
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                prod.subtituloAtelier.toUpperCase(),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 9.5,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                  color: Color(0xFF71717A),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              'SKU: $sku',
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 9.5,
                fontWeight: FontWeight.w500,
                letterSpacing: 0.8,
                color: Color(0xFF71717A),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),

        // Título de la prenda (Outfit Sans-Serif)
        Text(
          prod.nombre,
          style: const TextStyle(
            fontFamily: 'Outfit',
            fontSize: 21,
            fontWeight: FontWeight.w600,
            color: Color(0xFF0F1116),
            letterSpacing: -0.3,
            height: 1.25,
          ),
        ),
        const SizedBox(height: 8),

        // Rating de reseñas VIP
        Row(
          children: const [
            Icon(Icons.star, size: 14, color: Color(0xFFC5A782)),
            Icon(Icons.star, size: 14, color: Color(0xFFC5A782)),
            Icon(Icons.star, size: 14, color: Color(0xFFC5A782)),
            Icon(Icons.star, size: 14, color: Color(0xFFC5A782)),
            Icon(Icons.star, size: 14, color: Color(0xFFC5A782)),
            SizedBox(width: 6),
            Text(
              '4.9 · 38 reseñas VIP',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: Color(0xFF71717A),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Fila de precios
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              '${precio.toStringAsFixed(0)} €',
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F1116),
                letterSpacing: -0.4,
              ),
            ),
            if (prod.tieneDescuento && prod.precioBase > precio) ...[
              const SizedBox(width: 8),
              Text(
                '${prod.precioBase.toStringAsFixed(0)} €',
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 14,
                  decoration: TextDecoration.lineThrough,
                  color: Color(0xFF888888),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFFF5EFE6),
                  borderRadius: BorderRadius.circular(2),
                ),
                child: Text(
                  'AHORRO ${(prod.precioBase - precio).toStringAsFixed(0)} €',
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                    color: Color(0xFF8E714C),
                  ),
                ),
              ),
            ],
          ],
        ),
        const SizedBox(height: 6),

        // Nota Atelier
        Row(
          children: const [
            Icon(Icons.check_circle, size: 13, color: Color(0xFF16A34A)),
            SizedBox(width: 6),
            Expanded(
              child: Text(
                'Beneficio Membresía Atelier aplicado en liquidación privada',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 10.5,
                  color: Color(0xFF52525B),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ==========================================
  // 3. SELECTOR CROMÁTICO (CU08)
  // ==========================================
  Widget _construirSelectorColor(ProductoDetalleCargado estado) {
    final colores = estado.producto.coloresDisponibles;
    final colorActivo = estado.colorSeleccionado;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'TONO SELECCIONADO',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.2,
                color: Color(0xFF0F1116),
              ),
            ),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                colorActivo?.nombre ?? 'Tono Único',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                  color: Color(0xFF71717A),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        // Muestrarios circulares de color
        Row(
          children: colores.map((c) {
            final seleccionado = colorActivo?.idColor == c.idColor;
            return GestureDetector(
              onTap: () => _bloc.seleccionarColor(c),
              child: Container(
                margin: const EdgeInsets.only(right: 12),
                padding: const EdgeInsets.all(3),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: seleccionado ? Colors.black : Colors.transparent,
                    width: 1.5,
                  ),
                ),
                child: Container(
                  width: 26,
                  height: 26,
                  decoration: BoxDecoration(
                    color: _parseColorHex(c.codigoHex),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: const Color(0xFFDDDDDD),
                      width: 0.5,
                    ),
                  ),
                  child: seleccionado
                      ? Center(
                          child: Icon(
                            Icons.check,
                            size: 13,
                            color: _iconoColorContraste(c.codigoHex),
                          ),
                        )
                      : null,
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ==========================================
  // 4. SELECTOR DE TALLAS EN CASCADA (CU08)
  // ==========================================
  Widget _construirSelectorTallas(ProductoDetalleCargado estado) {
    final tallas = estado.producto.tallasDisponibles;
    final tallaActiva = estado.tallaSeleccionada;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Flexible(
              child: Text(
                'TALLA (FR / ES)',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                  color: Color(0xFF0F1116),
                ),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: () => _mostrarGuiaTallasModal(),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Icon(Icons.straighten, size: 13, color: Color(0xFF71717A)),
                  SizedBox(width: 4),
                  Text(
                    'Guía de medidas',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10.5,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF71717A),
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        // Cajas de talla (con estilo tachado si no hay stock en el color actual)
        Row(
          children: tallas.map((t) {
            final tieneStockEnColor =
                estado.tallaTieneStockParaColorActual(t.idTalla);
            final seleccionada = tallaActiva?.idTalla == t.idTalla;

            return GestureDetector(
              onTap: () {
                if (tieneStockEnColor) {
                  _bloc.seleccionarTalla(t);
                } else {
                  _mostrarSnackBar(
                    'La talla ${t.codigo} está agotada temporalmente en este tono.',
                  );
                }
              },
              child: Container(
                margin: const EdgeInsets.only(right: 8),
                width: 44,
                height: 40,
                decoration: BoxDecoration(
                  color: seleccionada
                      ? Colors.black
                      : (!tieneStockEnColor
                          ? const Color(0xFFF4F4F5)
                          : Colors.white),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                    color: seleccionada
                        ? Colors.black
                        : const Color(0xFFD4D4D8),
                  ),
                ),
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Text(
                      t.codigo,
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: seleccionada
                            ? Colors.white
                            : (!tieneStockEnColor
                                ? const Color(0xFFA1A1AA)
                                : const Color(0xFF0F1116)),
                      ),
                    ),
                    if (!tieneStockEnColor)
                      Positioned.fill(
                        child: CustomPaint(
                          painter: _DiagonalStrikethroughPainter(
                            color: const Color(0xFFA1A1AA),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ==========================================
  // 5. PÍLDORA DE STOCK EN TIEMPO REAL
  // ==========================================
  Widget _construirPildoraStock(ProductoDetalleCargado estado) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFFBF8F4),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: const Color(0xFFEFE0CE)),
      ),
      child: Text(
        estado.stockAdvertenciaTexto,
        style: const TextStyle(
          fontFamily: 'Outfit',
          fontSize: 10.5,
          fontWeight: FontWeight.w600,
          color: Color(0xFF6F5739),
        ),
      ),
    );
  }

  // ==========================================
  // 6. ACORDEONES: COMPOSICIÓN, BOUTIQUES Y CITAS
  // ==========================================
  Widget _construirSeccionAcordeones(ProductoDetalleCargado estado) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'ESPECIFICACIONES & TRAZABILIDAD',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
            color: Color(0xFF71717A),
          ),
        ),
        const SizedBox(height: 12),

        // Acordeón 1: Composición & Confección Noble (CU07)
        _acordeonCard(
          icono: Icons.spa_outlined,
          titulo: 'Composición & Confección Noble',
          abierto: _acordeonComposicionAbierto,
          alAlternar: () => setState(() {
            _acordeonComposicionAbierto = !_acordeonComposicionAbierto;
          }),
          contenido: _contenidoComposicion(estado.producto.composicion),
        ),
        const SizedBox(height: 10),

        // Acordeón 2: Disponibilidad en Boutique & Reserva Directa (CU09, CU12)
        _acordeonCard(
          icono: Icons.storefront_outlined,
          titulo: 'Disponibilidad en Boutique',
          abierto: _acordeonBoutiquesAbierto,
          alAlternar: () => setState(() {
            _acordeonBoutiquesAbierto = !_acordeonBoutiquesAbierto;
          }),
          contenido: _contenidoBoutiques(estado),
        ),
        const SizedBox(height: 10),

        // Acordeón 3: Citas de Prueba Presencial
        _acordeonCard(
          icono: Icons.calendar_today_outlined,
          titulo: 'Reserva de Prueba Presencial',
          abierto: _acordeonCitaInfoAbierto,
          alAlternar: () => setState(() {
            _acordeonCitaInfoAbierto = !_acordeonCitaInfoAbierto;
          }),
          contenido: _contenidoCitaInfo(),
        ),
      ],
    );
  }

  Widget _acordeonCard({
    required IconData icono,
    required String titulo,
    required bool abierto,
    required VoidCallback alAlternar,
    required Widget contenido,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: const Color(0xFFE4E4E7)),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: alAlternar,
            borderRadius: BorderRadius.circular(6),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              child: Row(
                children: [
                  Icon(icono, size: 16, color: const Color(0xFF0F1116)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      titulo,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF0F1116),
                      ),
                    ),
                  ),
                  Icon(
                    abierto ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    size: 18,
                    color: const Color(0xFF71717A),
                  ),
                ],
              ),
            ),
          ),
          if (abierto) ...[
            const Divider(height: 1, color: Color(0xFFEEEEEE)),
            Padding(
              padding: const EdgeInsets.all(14),
              child: contenido,
            ),
          ],
        ],
      ),
    );
  }

  Widget _contenidoComposicion(ComposicionNobleDto comp) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _filaDetalleTecnico('Cuerpo Principal', comp.cuerpoPrincipal),
        const SizedBox(height: 6),
        _filaDetalleTecnico('Forro Interior', comp.forroInterior),
        const SizedBox(height: 6),
        _filaDetalleTecnico('Técnica Textil', comp.tecnicaTextil),
        const SizedBox(height: 10),
        Text(
          comp.descripcionConfeccion,
          style: const TextStyle(
            fontFamily: 'Outfit',
            fontSize: 11.5,
            color: Color(0xFF52525B),
            height: 1.4,
          ),
        ),
        if (comp.instruccionesCuidado.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'INSTRUCCIONES DE CUIDADO',
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: 9,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.1,
              color: Color(0xFF71717A),
            ),
          ),
          const SizedBox(height: 6),
          ...comp.instruccionesCuidado.map(
            (c) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ', style: TextStyle(color: Color(0xFF71717A))),
                  Expanded(
                    child: Text(
                      c,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 10.5,
                        color: Color(0xFF52525B),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }

  Widget _filaDetalleTecnico(String etiqueta, String valor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          etiqueta,
          style: const TextStyle(
            fontFamily: 'Outfit',
            fontSize: 11,
            color: Color(0xFF71717A),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            valor,
            textAlign: TextAlign.end,
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: Color(0xFF0F1116),
            ),
          ),
        ),
      ],
    );
  }

  /// Lista continua de boutiques con botón directo [ 🏢 RESERVAR EN ESTA BOUTIQUE ]
  Widget _contenidoBoutiques(ProductoDetalleCargado estado) {
    if (estado.cargandoDisponibilidad) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(
          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
        ),
      );
    }

    if (estado.sucursales.isEmpty) {
      return const Text(
        'No hay disponibilidad confirmada en este momento.',
        style: TextStyle(
          fontFamily: 'Outfit',
          fontSize: 11.5,
          color: Color(0xFF71717A),
        ),
      );
    }

    return Column(
      children: estado.sucursales.map((sucursal) {
        final tieneStock = sucursal.cantidadDisponible > 0;

        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFFFAFAFA),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: const Color(0xFFE4E4E7)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Nombre y Badge de Stock
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      sucursal.nombre,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF0F1116),
                      ),
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                    decoration: BoxDecoration(
                      color: tieneStock
                          ? const Color(0xFFF5EFE6)
                          : const Color(0xFFF4F4F5),
                      borderRadius: BorderRadius.circular(3),
                    ),
                    child: Text(
                      tieneStock
                          ? (sucursal.cantidadDisponible > 1
                              ? 'DISPONIBLE (${sucursal.cantidadDisponible} UDS.)'
                              : 'ÚLTIMA UNIDAD')
                          : 'AGOTADO',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 8.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                        color: tieneStock
                            ? const Color(0xFF8E714C)
                            : const Color(0xFF71717A),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),

              // Dirección y Horario
              Text(
                sucursal.direccion,
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 10.5,
                  color: Color(0xFF71717A),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Horario: ${sucursal.horarioApertura} - ${sucursal.horarioCierre}',
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 10,
                  color: Color(0xFF888888),
                ),
              ),
              const SizedBox(height: 10),

              // Botón Directo: [ 🏢 RESERVAR EN ESTA BOUTIQUE ]
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: tieneStock
                      ? () => _abrirBottomSheetReserva(estado, sucursal)
                      : null,
                  icon: const Icon(Icons.storefront_outlined, size: 14),
                  label: const Text(
                    'RESERVAR EN ESTA BOUTIQUE',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: const Color(0xFFE4E4E7),
                    disabledForegroundColor: const Color(0xFFA1A1AA),
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _contenidoCitaInfo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        Text(
          'El servicio Private Atelier incluye:',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: Color(0xFF0F1116),
          ),
        ),
        SizedBox(height: 6),
        Text(
          '• Atención exclusiva personalizada de 45 minutos con estilista sénior.\n'
          '• Cabina privada climatizada con espejo trifásico y copa de champán de cortesía.\n'
          '• Las prendas seleccionadas permanecen reservadas físicamente a tu nombre hasta 48 horas tras la cita.',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 10.5,
            color: Color(0xFF52525B),
            height: 1.45,
          ),
        ),
      ],
    );
  }

  // ==========================================
  // 7. BARRA INFERIOR PERSISTENTE (Sticky Action)
  // ==========================================
  Widget _construirBarraInferiorCompra(ProductoDetalleCargado estado) {
    final precio = estado.precioActual;

    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: Color(0xFFE4E4E7))),
          boxShadow: [
            BoxShadow(
              color: Colors.black12,
              blurRadius: 4,
              offset: Offset(0, -2),
            ),
          ],
        ),
        child: Row(
          children: [
            // Botón rápido AR
            GestureDetector(
              onTap: () => _abrirModalVestidorAr(),
              child: Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: const Color(0xFFF4F4F5),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: const Color(0xFFE4E4E7)),
                ),
                child: const Icon(Icons.center_focus_weak, size: 20, color: Colors.black),
              ),
            ),
            const SizedBox(width: 10),

            // Botón Principal de Compra: "AÑADIR A LA BOLSA · 890 €"
            Expanded(
              child: SizedBox(
                height: 44,
                child: ElevatedButton.icon(
                  onPressed: () {
                    _bloc.agregarABolsa();
                    _mostrarSnackBar('Prenda añadida a la bolsa de compras');
                  },
                  icon: const Icon(Icons.shopping_bag_outlined, size: 16),
                  label: Text(
                    'AÑADIR A LA BOLSA · ${precio.toStringAsFixed(0)} €',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // 8. BOTTOM SHEET MODAL DE RESERVA (CU12)
  // ==========================================
  void _abrirBottomSheetReserva(
    ProductoDetalleCargado estado,
    SucursalDisponibilidadDto sucursalSeleccionadaInicial,
  ) {
    int sucursalIdSeleccionada = sucursalSeleccionadaInicial.idSucursal;
    int franjaHorariaIndex = 0;
    final franjas = [
      'MAÑANA 11:30H',
      'MAÑANA 16:30H',
      'VIERNES 12:00H',
      'SÁBADO 11:00H',
    ];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final sucursalActiva = estado.sucursales.firstWhere(
              (s) => s.idSucursal == sucursalIdSeleccionada,
              orElse: () => sucursalSeleccionadaInicial,
            );

            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Cabecera del BottomSheet
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'PRIVATE ATELIER SERVICE',
                          style: TextStyle(
                            fontFamily: 'Outfit',
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.4,
                            color: Color(0xFFAD8C63),
                          ),
                        ),
                        GestureDetector(
                          onTap: () => Navigator.pop(ctx),
                          child: const Icon(Icons.close, size: 20, color: Colors.black),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'RESERVAR CITA DE PRUEBA EN BOUTIQUE',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF0F1116),
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Selecciona tu boutique insignia para coordinar tu cita privada con nuestro equipo de sastrería.',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 11,
                        color: Color(0xFF71717A),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Resumen de Prenda Seleccionada
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFAFAFA),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: const Color(0xFFE4E4E7)),
                      ),
                      child: Row(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: SizedBox(
                              width: 40,
                              height: 50,
                              child: widget.habilitarImagenesRed &&
                                      estado.producto.imagenUrl != null
                                  ? Image.network(
                                      estado.producto.imagenUrl!,
                                      fit: BoxFit.cover,
                                      errorBuilder: (_, _, _) => _placeholderGaleria(),
                                    )
                                  : _placeholderGaleria(),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'PRENDA SELECCIONADA',
                                  style: TextStyle(
                                    fontFamily: 'Outfit',
                                    fontSize: 8,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 1.0,
                                    color: Color(0xFF71717A),
                                  ),
                                ),
                                Text(
                                  estado.producto.nombre,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontFamily: 'Outfit',
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF0F1116),
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Talla: ${estado.tallaSeleccionada?.codigo ?? "38"} · Precio: ${estado.precioActual.toStringAsFixed(0)} € · Cortesía incluida',
                                  style: const TextStyle(
                                    fontFamily: 'Outfit',
                                    fontSize: 9.5,
                                    color: Color(0xFF6F5739),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 1. Selector de Boutique
                    const Text(
                      '1. SELECCIONA LA BOUTIQUE INSIGNIA',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.1,
                        color: Color(0xFF0F1116),
                      ),
                    ),
                    const SizedBox(height: 8),
                    ...estado.sucursales.map((suc) {
                      final esActiva = suc.idSucursal == sucursalIdSeleccionada;
                      final tieneStock = suc.cantidadDisponible > 0;
                      return GestureDetector(
                        onTap: tieneStock
                            ? () {
                                setModalState(() {
                                  sucursalIdSeleccionada = suc.idSucursal;
                                });
                              }
                            : null,
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: esActiva
                                ? const Color(0xFFFBF8F4)
                                : Colors.white,
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(
                              color: esActiva
                                  ? const Color(0xFF0F1116)
                                  : const Color(0xFFE4E4E7),
                              width: esActiva ? 1.5 : 1,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                esActiva
                                    ? Icons.radio_button_checked
                                    : Icons.radio_button_off,
                                size: 16,
                                color: esActiva
                                    ? Colors.black
                                    : const Color(0xFFA1A1AA),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      suc.nombre,
                                      style: TextStyle(
                                        fontFamily: 'Outfit',
                                        fontSize: 11,
                                        fontWeight: esActiva
                                            ? FontWeight.w700
                                            : FontWeight.w500,
                                        color: tieneStock
                                            ? const Color(0xFF0F1116)
                                            : const Color(0xFFA1A1AA),
                                      ),
                                    ),
                                    Text(
                                      suc.direccion,
                                      style: const TextStyle(
                                        fontFamily: 'Outfit',
                                        fontSize: 9.5,
                                        color: Color(0xFF71717A),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: tieneStock
                                      ? const Color(0xFFF5EFE6)
                                      : const Color(0xFFF4F4F5),
                                  borderRadius: BorderRadius.circular(2),
                                ),
                                child: Text(
                                  tieneStock
                                      ? '${suc.cantidadDisponible} EN STOCK'
                                      : 'AGOTADA',
                                  style: TextStyle(
                                    fontFamily: 'Outfit',
                                    fontSize: 8,
                                    fontWeight: FontWeight.w700,
                                    color: tieneStock
                                        ? const Color(0xFF8E714C)
                                        : const Color(0xFF71717A),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                    const SizedBox(height: 12),

                    // 2. Fecha y Franja Horaria
                    const Text(
                      '2. FECHA Y HORA PREFERENTE',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.1,
                        color: Color(0xFF0F1116),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: List.generate(franjas.length, (idx) {
                        final elegida = idx == franjaHorariaIndex;
                        return GestureDetector(
                          onTap: () {
                            setModalState(() {
                              franjaHorariaIndex = idx;
                            });
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 7),
                            decoration: BoxDecoration(
                              color: elegida ? Colors.black : const Color(0xFFF4F4F5),
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(
                                color: elegida ? Colors.black : const Color(0xFFE4E4E7),
                              ),
                            ),
                            child: Text(
                              franjas[idx],
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.5,
                                color: elegida ? Colors.white : const Color(0xFF52525B),
                              ),
                            ),
                          ),
                        );
                      }),
                    ),
                    const SizedBox(height: 14),

                    // Aviso cortesía
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFBF8F4),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: const Color(0xFFEFE0CE)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: const [
                          Icon(Icons.info_outline, size: 14, color: Color(0xFF8E714C)),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'La cita incluye champán de cortesía, asesoramiento de estilista sénior y ajustes de costura sin coste adicional.',
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 9.5,
                                color: Color(0xFF6F5739),
                                height: 1.3,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Botones de acción: CANCELAR / CONFIRMAR
                    Row(
                      children: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text(
                            'CANCELAR',
                            style: TextStyle(
                              fontFamily: 'Outfit',
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.0,
                              color: Color(0xFF71717A),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () async {
                              Navigator.pop(ctx);
                              final exito = await _bloc.confirmarReserva(
                                idSucursal: sucursalActiva.idSucursal,
                                fechaReserva: DateTime.now().add(const Duration(days: 1)),
                                token: widget.token,
                              );
                              if (exito && mounted) {
                                _mostrarDialogoReservaConfirmada(
                                  _bloc.estado is ProductoDetalleCargado
                                      ? (_bloc.estado as ProductoDetalleCargado).ultimaReserva
                                      : null,
                                );
                              } else if (mounted) {
                                final err = (_bloc.estado is ProductoDetalleCargado)
                                    ? (_bloc.estado as ProductoDetalleCargado).mensajeNotificacion
                                    : 'Fallo al confirmar reserva';
                                _mostrarSnackBar(err ?? 'Error', esError: true);
                              }
                            },
                            icon: const Icon(Icons.check_circle_outline, size: 16),
                            label: const Text(
                              'CONFIRMAR RESERVA EN BOUTIQUE',
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 10.5,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.8,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.black,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _mostrarDialogoReservaConfirmada(ReservaCreadaOutDto? reserva) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        title: Row(
          children: const [
            Icon(Icons.check_circle, color: Color(0xFF16A34A), size: 22),
            SizedBox(width: 8),
            Text(
              'CITA CONFIRMADA',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 14,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.0,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Código de Reserva: ${reserva?.codigoReserva ?? "RES-ATELIER"}',
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F1116),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Boutique: ${reserva?.sucursalNombre ?? "Atelier Serrano"}',
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 12,
                color: Color(0xFF52525B),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tus prendas han sido apartadas en el probador privado. Nuestro concierge te recibirá con champán de cortesía.',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 11,
                color: Color(0xFF71717A),
                height: 1.35,
              ),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.black,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
            ),
            onPressed: () => Navigator.pop(ctx),
            child: const Text(
              'ENTENDIDO',
              style: TextStyle(fontFamily: 'Outfit', fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  void _abrirModalVestidorAr() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.view_in_ar, size: 42, color: Colors.black),
              const SizedBox(height: 12),
              const Text(
                'VESTIDOR VIRTUAL AR ATELIER',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'La simulación morfológica inteligente y renderizado 3D de alta costura se encuentra en fase de calibración para esta colección.\n\nPodrás proyectar la caída de la seda y el drapeado en tu entorno en la próxima entrega.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 11.5,
                  color: Color(0xFF71717A),
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text(
                    'COMPRENDIDO',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.0,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _mostrarGuiaTallasModal() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'TABLA DE MEDIDAS ATELIER (FR / ES)',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                ),
              ),
              const SizedBox(height: 12),
              Table(
                border: TableBorder.all(color: const Color(0xFFEEEEEE)),
                children: const [
                  TableRow(
                    decoration: BoxDecoration(color: Color(0xFFF9F9F8)),
                    children: [
                      Padding(padding: EdgeInsets.all(8), child: Text('Talla', style: TextStyle(fontFamily: 'Outfit', fontWeight: FontWeight.bold, fontSize: 11))),
                      Padding(padding: EdgeInsets.all(8), child: Text('Busto (cm)', style: TextStyle(fontFamily: 'Outfit', fontWeight: FontWeight.bold, fontSize: 11))),
                      Padding(padding: EdgeInsets.all(8), child: Text('Cintura (cm)', style: TextStyle(fontFamily: 'Outfit', fontWeight: FontWeight.bold, fontSize: 11))),
                      Padding(padding: EdgeInsets.all(8), child: Text('Cadera (cm)', style: TextStyle(fontFamily: 'Outfit', fontWeight: FontWeight.bold, fontSize: 11))),
                    ],
                  ),
                  TableRow(children: [
                    Padding(padding: EdgeInsets.all(8), child: Text('34', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('80 - 84', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('60 - 64', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('86 - 90', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                  ]),
                  TableRow(children: [
                    Padding(padding: EdgeInsets.all(8), child: Text('36', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('84 - 88', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('64 - 68', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('90 - 94', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                  ]),
                  TableRow(children: [
                    Padding(padding: EdgeInsets.all(8), child: Text('38', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('88 - 92', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('68 - 72', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('94 - 98', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                  ]),
                  TableRow(children: [
                    Padding(padding: EdgeInsets.all(8), child: Text('40', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('92 - 96', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('72 - 76', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                    Padding(padding: EdgeInsets.all(8), child: Text('98 - 102', style: TextStyle(fontFamily: 'Outfit', fontSize: 11))),
                  ]),
                ],
              ),
              const SizedBox(height: 16),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('CERRAR', style: TextStyle(fontFamily: 'Outfit', fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _parseColorHex(String hexString) {
    final clean = hexString.replaceAll('#', '');
    try {
      if (clean.length == 6) {
        return Color(int.parse('FF$clean', radix: 16));
      }
    } catch (_) {}
    return Colors.black;
  }

  Color _iconoColorContraste(String hexString) {
    final color = _parseColorHex(hexString);
    final luminancia = color.computeLuminance();
    return luminancia > 0.5 ? Colors.black : Colors.white;
  }
}

/// Pintor personalizado para dibujar la línea diagonal de tachado en tallas sin existencias
class _DiagonalStrikethroughPainter extends CustomPainter {
  final Color color;

  const _DiagonalStrikethroughPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.0;
    canvas.drawLine(
      Offset(0, size.height),
      Offset(size.width, 0),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant _DiagonalStrikethroughPainter oldDelegate) {
    return oldDelegate.color != color;
  }
}
