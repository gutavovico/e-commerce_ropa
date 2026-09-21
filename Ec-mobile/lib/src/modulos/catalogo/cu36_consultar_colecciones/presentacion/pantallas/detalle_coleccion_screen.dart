import 'package:flutter/material.dart';
import '../../datos/modelos/coleccion_dto.dart';
import '../bloc/colecciones_bloc.dart';

class DetalleColeccionScreen extends StatefulWidget {
  final int idColeccion;
  final String? nombreColeccionInicial;
  final ColeccionesBloc? bloc;
  final void Function(ProductoColeccionItemDto)? alSeleccionarProducto;

  const DetalleColeccionScreen({
    super.key,
    required this.idColeccion,
    this.nombreColeccionInicial,
    this.bloc,
    this.alSeleccionarProducto,
  });

  @override
  State<DetalleColeccionScreen> createState() => _DetalleColeccionScreenState();
}

class _DetalleColeccionScreenState extends State<DetalleColeccionScreen> {
  late final ColeccionesBloc _bloc;

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? ColeccionesBloc();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _bloc.cargarPrendasColeccion(widget.idColeccion);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) {
        final detalle = _bloc.detalleActual;
        final cargando = _bloc.cargandoDetalle;
        final error = _bloc.errorDetalle;

        return Scaffold(
          backgroundColor: Colors.white,
          appBar: AppBar(
            backgroundColor: Colors.white,
            elevation: 0,
            scrolledUnderElevation: 0,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.black),
              onPressed: () => Navigator.of(context).pop(),
              tooltip: 'Volver a colecciones',
            ),
            centerTitle: false,
            title: Text(
              (detalle?.nombre ?? widget.nombreColeccionInicial ?? 'COLECCIÓN')
                  .toUpperCase(),
              style: const TextStyle(
                fontFamily: 'Outfit',
                color: Colors.black,
                fontSize: 12,
                fontWeight: FontWeight.w700,
                letterSpacing: 2.0,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.share_outlined, color: Colors.black),
                onPressed: () {},
                tooltip: 'Compartir colección',
              ),
            ],
          ),
          body: cargando
              ? const Center(
                  child: CircularProgressIndicator(color: Colors.black),
                )
              : error != null
                  ? _construirError(context, error)
                  : detalle == null
                      ? const SizedBox.shrink()
                      : _construirContenido(context, detalle),
        );
      },
    );
  }

  Widget _construirError(BuildContext context, String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.info_outline, size: 48, color: Color(0xFF888888)),
            const SizedBox(height: 16),
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 14,
                color: Color(0xFF444444),
                height: 1.4,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => _bloc.cargarPrendasColeccion(widget.idColeccion),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
              child: const Text(
                'REINTENTAR',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirContenido(BuildContext context, ColeccionDetalleDto detalle) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Temporada & Origen artesanal
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF5EFE6),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  detalle.temporadaNombre.toUpperCase(),
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                    color: Color(0xFF675D4E),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  detalle.tallerOrigen,
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    color: Color(0xFF71717A),
                    fontStyle: FontStyle.italic,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),

          const SizedBox(height: 10),

          // Título de la colección
          Text(
            detalle.nombre,
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F1116),
              letterSpacing: -0.5,
              height: 1.2,
            ),
          ),

          if (detalle.descripcion != null &&
              detalle.descripcion!.trim().isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              detalle.descripcion!,
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 13,
                color: Color(0xFF52525B),
                height: 1.45,
              ),
            ),
          ],

          const SizedBox(height: 18),

          // Encabezado de prendas
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Text(
                  'PIEZAS DE ALTA COSTURA (${detalle.totalPrendas})',
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                    color: Color(0xFF0F1116),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'Edición Exclusiva',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 11,
                  color: Color(0xFF71717A),
                ),
              ),
            ],
          ),

          const Divider(height: 24, thickness: 1, color: Color(0xFFEEEEEE)),

          // Grilla 2x2 de Prendas o Empty State
          if (detalle.productos.isEmpty)
            _construirEmptyState(context, detalle.mensajeEmptyState)
          else
            _construirGrillaPrendas(context, detalle.productos),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _construirEmptyState(BuildContext context, String? mensaje) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: const Color(0xFFFAF9F6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFECE7DE)),
      ),
      child: Column(
        children: [
          const Icon(Icons.hourglass_empty, size: 40, color: Color(0xFFAD8C63)),
          const SizedBox(height: 16),
          const Text(
            'PRÓXIMO LANZAMIENTO',
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 2.0,
              color: Color(0xFF0F1116),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            mensaje ??
                'Las piezas de esta colección están en proceso de confección artesanal en el Atelier.',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 13,
              color: Color(0xFF52525B),
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirGrillaPrendas(
    BuildContext context,
    List<ProductoColeccionItemDto> productos,
  ) {
    return GridView.builder(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: productos.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 10,
        mainAxisSpacing: 12,
        childAspectRatio: 0.65,
      ),
      itemBuilder: (context, index) {
        final item = productos[index];
        final esGuardado = _bloc.esBookmark(item.idProducto);

        return Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFFECECEC)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Foto vertical con badges que llena el área superior sin dejar espacio blanco
              Expanded(
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: ClipRRect(
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(7)),
                        child: item.imagenUrl != null &&
                                item.imagenUrl!.trim().isNotEmpty
                            ? Image.network(
                                item.imagenUrl!,
                                fit: BoxFit.cover,
                                errorBuilder: (ctx, err, stack) =>
                                    _construirPlaceholderFoto(),
                              )
                            : _construirPlaceholderFoto(),
                      ),
                    ),

                    // Badge Superior (Edición / Serrano)
                    Positioned(
                      top: 6,
                      left: 6,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.8),
                          borderRadius: BorderRadius.circular(3),
                        ),
                        child: Text(
                          item.badgeEditorial,
                          style: const TextStyle(
                            fontFamily: 'Outfit',
                            color: Colors.white,
                            fontSize: 7.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                          ),
                        ),
                      ),
                    ),

                    // Botón Bookmark / Guardar
                    Positioned(
                      top: 4,
                      right: 4,
                      child: GestureDetector(
                        onTap: () => _bloc.alternarBookmark(item.idProducto),
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.9),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            esGuardado ? Icons.bookmark : Icons.bookmark_border,
                            size: 14,
                            color: esGuardado
                                ? const Color(0xFFAD8C63)
                                : Colors.black87,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Metadatos de la prenda
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Subtítulo Textil
                    Text(
                      item.subtituloTextil.toUpperCase(),
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 8,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 1.1,
                        color: Color(0xFF71717A),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),

                    const SizedBox(height: 2),

                    // Nombre de la prenda
                    Text(
                      item.nombre,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF0F1116),
                        letterSpacing: -0.2,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),

                    const SizedBox(height: 4),

                    // Precio en EUR
                    Text(
                      '${item.precioBase.toStringAsFixed(0)} €',
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF0F1116),
                        letterSpacing: -0.2,
                      ),
                    ),

                    const SizedBox(height: 6),

                    // Fila de swatches y botón VER →
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Swatches de color
                        if (item.coloresDisponibles.isNotEmpty)
                          Row(
                            children: item.coloresDisponibles.take(3).map((hex) {
                              return Container(
                                margin: const EdgeInsets.only(right: 3),
                                width: 8,
                                height: 8,
                                decoration: BoxDecoration(
                                  color: _parseHexColor(hex),
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: const Color(0xFFDDDDDD),
                                    width: 0.5,
                                  ),
                                ),
                              );
                            }).toList(),
                          )
                        else
                          const SizedBox.shrink(),

                        // Botón VER →
                        GestureDetector(
                          onTap: () {
                            if (widget.alSeleccionarProducto != null) {
                              widget.alSeleccionarProducto!(item);
                            }
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.black,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  'VER',
                                  style: TextStyle(
                                    fontFamily: 'Outfit',
                                    color: Colors.white,
                                    fontSize: 8,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.8,
                                  ),
                                ),
                                SizedBox(width: 2),
                                Icon(
                                  Icons.arrow_forward,
                                  size: 8,
                                  color: Colors.white,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _construirPlaceholderFoto() {
    return Container(
      color: const Color(0xFFF3EFEA),
      child: const Center(
        child: Text(
          'FS',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 18,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.0,
            color: Color(0xFFC5A880),
          ),
        ),
      ),
    );
  }

  Color _parseHexColor(String hex) {
    try {
      final buffer = StringBuffer();
      if (hex.length == 6 || hex.length == 7) buffer.write('ff');
      buffer.write(hex.replaceFirst('#', ''));
      return Color(int.parse(buffer.toString(), radix: 16));
    } catch (_) {
      return const Color(0xFF1A1A1A);
    }
  }
}
