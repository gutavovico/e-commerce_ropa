import 'package:flutter/material.dart';
import '../../datos/modelos/coleccion_dto.dart';
import '../bloc/colecciones_bloc.dart';
import 'detalle_coleccion_screen.dart';

class ColeccionesScreen extends StatefulWidget {
  final ColeccionesBloc? bloc;
  final VoidCallback? alIrAInicio;
  final void Function(ProductoColeccionItemDto)? alSeleccionarProducto;

  const ColeccionesScreen({
    super.key,
    this.bloc,
    this.alIrAInicio,
    this.alSeleccionarProducto,
  });

  @override
  State<ColeccionesScreen> createState() => _ColeccionesScreenState();
}

class _ColeccionesScreenState extends State<ColeccionesScreen> {
  late final ColeccionesBloc _bloc;

  static const List<String> _chips = [
    'COLECCIÓN DESTACADA',
    'ORIGEN CERTIFICADO',
    'ENVÍO ATELIER',
  ];

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? ColeccionesBloc();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _bloc.cargarColeccionesActivas();
      }
    });
  }

  void _navegarADetalle(ColeccionResumenDto col) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DetalleColeccionScreen(
          idColeccion: col.idColeccion,
          nombreColeccionInicial: col.nombre,
          bloc: _bloc,
          alSeleccionarProducto: widget.alSeleccionarProducto,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) {
        final estado = _bloc.estado;

        return Scaffold(
          backgroundColor: Colors.white,
          appBar: _construirAppBar(context),
          body: Stack(
            children: [
              RefreshIndicator(
                color: Colors.black,
                onRefresh: () => _bloc.cargarColeccionesActivas(),
                child: switch (estado) {
                  ColeccionesInicial() || ColeccionesCargando() =>
                    const Center(
                      child: CircularProgressIndicator(color: Colors.black),
                    ),
                  ColeccionesError(:final mensaje) =>
                    _construirVistaError(context, mensaje),
                  ColeccionesCargadas() => _construirContenido(context, estado),
                  DetalleColeccionCargado() => const SizedBox.shrink(),
                },
              ),

              // Toast flotante de cesta
              if (_bloc.mensajeToast != null)
                Positioned(
                  bottom: 16,
                  left: 16,
                  right: 16,
                  child: Material(
                    elevation: 6,
                    borderRadius: BorderRadius.circular(12),
                    color: const Color(0xFF111111),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.check_circle_outline,
                            color: Color(0xFFC5A880),
                            size: 20,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              _bloc.mensajeToast!,
                              style: const TextStyle(
                                fontFamily: 'Outfit',
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          GestureDetector(
                            onTap: () => _bloc.limpiarMensajeToast(),
                            child: const Icon(
                              Icons.close,
                              color: Colors.white70,
                              size: 18,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  PreferredSizeWidget _construirAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      scrolledUnderElevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: Colors.black),
        onPressed: () {
          if (widget.alIrAInicio != null) {
            widget.alIrAInicio!();
          } else if (Navigator.of(context).canPop()) {
            Navigator.of(context).pop();
          }
        },
        tooltip: 'Regresar',
      ),
      centerTitle: true,
      title: const Text(
        'FASHION STORE',
        style: TextStyle(
          fontFamily: 'Outfit',
          color: Colors.black,
          fontSize: 14,
          fontWeight: FontWeight.w700,
          letterSpacing: 2.2,
        ),
      ),
      actions: [
        Stack(
          alignment: Alignment.center,
          children: [
            IconButton(
              icon: const Icon(Icons.shopping_bag_outlined, color: Colors.black),
              onPressed: () {},
              tooltip: 'Cesta privada',
            ),
            if (_bloc.cestaCount > 0)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: Color(0xFFC5A880),
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    '${_bloc.cestaCount}',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(width: 4),
      ],
    );
  }

  Widget _construirVistaError(BuildContext context, String mensaje) {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: Container(
        height: MediaQuery.of(context).size.height * 0.7,
        alignment: Alignment.center,
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Color(0xFF888888)),
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
              onPressed: () => _bloc.cargarColeccionesActivas(),
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

  Widget _construirContenido(BuildContext context, ColeccionesCargadas estado) {
    final destacada = estado.destacada;
    final otras = estado.otrasColecciones;

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título H1 Colecciones
          const Text(
            'Colecciones',
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: 26,
              fontWeight: FontWeight.w700,
              color: Colors.black,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Explora y visualiza todas las colecciones disponibles de la firma, desde la colección en curso hasta piezas selectas de archivo.',
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: 12,
              color: Color(0xFF666666),
              height: 1.4,
            ),
          ),

          const SizedBox(height: 16),

          // Chips horizontales de filtro
          _construirChipsFiltro(estado.chipSeleccionado),

          const SizedBox(height: 24),

          // 1. Colección Destacada Hero (si existe)
          if (destacada != null) ...[
            _construirColeccionDestacada(context, destacada),
            const SizedBox(height: 32),
          ],

          // 2. Sección "Otras colecciones"
          _construirSeccionOtrasColecciones(context, otras),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _construirChipsFiltro(String chipActivo) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: _chips.map((chip) {
          final seleccionado = chip == chipActivo;
          return Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: ChoiceChip(
              label: Text(chip),
              selected: seleccionado,
              onSelected: (_) => _bloc.seleccionarChip(chip),
              labelStyle: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.2,
                color: seleccionado ? Colors.white : const Color(0xFF555555),
              ),
              selectedColor: Colors.black,
              backgroundColor: const Color(0xFFF6F6F6),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: BorderSide(
                  color: seleccionado
                      ? Colors.black
                      : (chip == 'ENVÍO ATELIER'
                          ? const Color(0xFFE2D6C5)
                          : const Color(0xFFEEEEEE)),
                  width: 1,
                ),
              ),
              showCheckmark: false,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _construirColeccionDestacada(
    BuildContext context,
    ColeccionResumenDto col,
  ) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFAFAFA),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFEEEEEE)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Badge Superior Hero
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.black,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    col.badgeEdicion.toUpperCase(),
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF3EFEA),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'DISPONIBLE',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    color: Color(0xFF675D4E),
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.0,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Título de la Colección Destacada
          Text(
            col.nombre,
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Colors.black,
              letterSpacing: -0.4,
              height: 1.2,
            ),
          ),

          if (col.descripcion != null) ...[
            const SizedBox(height: 6),
            Text(
              col.descripcion!,
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 12,
                color: Color(0xFF666666),
                height: 1.4,
              ),
            ),
          ],

          const SizedBox(height: 14),

          // Fila de metadatos: PIEZAS CLAVE (4) / Edición Vigente
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Text(
                  'PIEZAS CLAVE (${col.piezasClave.length})',
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.0,
                    color: Colors.black,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'Desde ${col.precioDesde.toStringAsFixed(0)} €',
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFFAD8C63),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Grilla 2x2 de piezas clave
          if (col.piezasClave.isNotEmpty)
            _construirGrillaPiezasClave(context, col.piezasClave)
          else
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: Text(
                'Piezas en confección artesanal en el Atelier.',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 12,
                  color: Color(0xFF888888),
                ),
              ),
            ),

          const SizedBox(height: 14),

          // Botón para acceder a la colección completa
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => _navegarADetalle(col),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.black,
                side: const BorderSide(color: Colors.black, width: 1.2),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(25),
                ),
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Flexible(
                    child: Text(
                      'VER COLECCIÓN COMPLETA',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.0,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  SizedBox(width: 6),
                  Icon(Icons.arrow_forward, size: 13),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirGrillaPiezasClave(
    BuildContext context,
    List<ProductoColeccionItemDto> piezas,
  ) {
    return GridView.builder(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: piezas.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 10,
        mainAxisSpacing: 12,
        childAspectRatio: 0.65,
      ),
      itemBuilder: (context, index) {
        final pieza = piezas[index];
        final esGuardado = _bloc.esBookmark(pieza.idProducto);

        return GestureDetector(
          onTap: () {
            if (widget.alSeleccionarProducto != null) {
              widget.alSeleccionarProducto!(pieza);
            }
          },
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFECECEC)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Foto vertical con badges ocupando el espacio superior
                Expanded(
                  child: Stack(
                    children: [
                      Positioned.fill(
                        child: ClipRRect(
                          borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(7)),
                          child: pieza.imagenUrl != null &&
                                  pieza.imagenUrl!.trim().isNotEmpty
                              ? Image.network(
                                  pieza.imagenUrl!,
                                  fit: BoxFit.cover,
                                  errorBuilder: (ctx, err, stack) =>
                                      _construirPlaceholderFoto(),
                                )
                              : _construirPlaceholderFoto(),
                        ),
                      ),
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
                            pieza.badgeEditorial,
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
                      Positioned(
                        top: 4,
                        right: 4,
                        child: GestureDetector(
                          onTap: () => _bloc.alternarBookmark(pieza.idProducto),
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

                // Datos de la pieza clave
                Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        pieza.subtituloTextil.toUpperCase(),
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
                      Text(
                        pieza.nombre,
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
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '${pieza.precioBase.toStringAsFixed(0)} €',
                            style: const TextStyle(
                              fontFamily: 'Outfit',
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                              color: Color(0xFF0F1116),
                              letterSpacing: -0.2,
                            ),
                          ),
                          GestureDetector(
                            onTap: () => _bloc.agregarACesta(pieza),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF3EFEA),
                                borderRadius: BorderRadius.circular(4),
                                border: Border.all(
                                    color: const Color(0xFFE2D6C5), width: 0.6),
                              ),
                              child: const Text(
                                '+ CESTA',
                                style: TextStyle(
                                  fontFamily: 'Outfit',
                                  fontSize: 8,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF675D4E),
                                  letterSpacing: 0.6,
                                ),
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
          ),
        );
      },
    );
  }

  Widget _construirSeccionOtrasColecciones(
    BuildContext context,
    List<ColeccionResumenDto> otras,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Otras colecciones',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: Colors.black,
            letterSpacing: -0.4,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Prendas y archivos de colecciones anteriores confeccionadas con hilaturas nobles.',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 12,
            color: Color(0xFF666666),
            height: 1.4,
          ),
        ),
        const SizedBox(height: 16),

        // Lista vertical de tarjetas de colecciones secundarias
        ListView.separated(
          physics: const NeverScrollableScrollPhysics(),
          shrinkWrap: true,
          itemCount: otras.length,
          separatorBuilder: (context, index) => const SizedBox(height: 14),
          itemBuilder: (context, index) {
            final col = otras[index];
            return _construirTarjetaColeccionSecundaria(context, col);
          },
        ),
      ],
    );
  }

  Widget _construirTarjetaColeccionSecundaria(
    BuildContext context,
    ColeccionResumenDto col,
  ) {
    return GestureDetector(
      onTap: () => _navegarADetalle(col),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE8E8E8)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Imagen de Portada con badges
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(11)),
              child: AspectRatio(
                aspectRatio: 1.8,
                child: col.imagenPortada != null &&
                        col.imagenPortada!.trim().isNotEmpty
                    ? Image.network(
                        col.imagenPortada!,
                        fit: BoxFit.cover,
                        errorBuilder: (ctx, err, stack) =>
                            _construirPlaceholderPortada(),
                      )
                    : _construirPlaceholderPortada(),
              ),
            ),

            // Metadatos y Acciones
            Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Fila Temporada y Precio "Desde X €"
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Flexible(
                        child: Text(
                          col.temporadaNombre.toUpperCase(),
                          style: const TextStyle(
                            fontFamily: 'Outfit',
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.0,
                            color: Color(0xFF888888),
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF5EFE6),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'Desde ${col.precioDesde.toStringAsFixed(0)} €',
                          style: const TextStyle(
                            fontFamily: 'Outfit',
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF675D4E),
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 6),

                  // Nombre de la Colección
                  Text(
                    col.nombre,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colors.black,
                      letterSpacing: -0.3,
                    ),
                  ),

                  const SizedBox(height: 4),

                  // Taller artesanal
                  Text(
                    col.tallerOrigen,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11,
                      color: Color(0xFF777777),
                      fontStyle: FontStyle.italic,
                    ),
                  ),

                  const SizedBox(height: 12),

                  // Fila Inferior: Total de Prendas y Botón VER COLECCIÓN →
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Flexible(
                        child: Text(
                          '${col.totalPrendas} prendas activas',
                          style: const TextStyle(
                            fontFamily: 'Outfit',
                            fontSize: 11,
                            color: Color(0xFF999999),
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Text(
                            'VER COLECCIÓN',
                            style: TextStyle(
                              fontFamily: 'Outfit',
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.0,
                              color: Colors.black,
                            ),
                          ),
                          SizedBox(width: 4),
                          Icon(Icons.arrow_forward,
                              size: 13, color: Colors.black),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
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

  Widget _construirPlaceholderPortada() {
    return Container(
      color: const Color(0xFF22201E),
      child: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'ATELIER ARCHIVE',
              style: TextStyle(
                fontFamily: 'Outfit',
                color: Colors.white70,
                fontSize: 12,
                fontWeight: FontWeight.w700,
                letterSpacing: 2.5,
              ),
            ),
            SizedBox(height: 4),
            Text(
              'COLECCIÓN EDITORIAL',
              style: TextStyle(
                fontFamily: 'Outfit',
                color: Color(0xFFC5A880),
                fontSize: 9,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
