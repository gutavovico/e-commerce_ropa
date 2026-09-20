import 'package:flutter/material.dart';
import '../../datos/modelos/producto_item_dto.dart';
import '../bloc/catalogo_bloc.dart';

/// Paleta de 16 colores textiles de confección para el catálogo de FashionStore.
class SwatchColorTextil {
  final String nombre;
  final Color color;
  final Color borde;

  const SwatchColorTextil(this.nombre, this.color, [Color? borde])
      : borde = borde ?? color;
}

const List<SwatchColorTextil> kColoresTextiles = [
  SwatchColorTextil('Marfil', Color(0xFFFCFBF8), Color(0xFFE5E5E5)),
  SwatchColorTextil('Camel', Color(0xFFC2A688)),
  SwatchColorTextil('Ébano', Color(0xFF1A1A1A)),
  SwatchColorTextil('Champagne', Color(0xFFE8DFC8)),
  SwatchColorTextil('Rojo Carmín', Color(0xFF991B1B)),
  SwatchColorTextil('Azul Marino', Color(0xFF1E3A8A)),
  SwatchColorTextil('Blanco Puro', Color(0xFFFFFFFF), Color(0xFFE5E5E5)),
  SwatchColorTextil('Beige Arena', Color(0xFFD4C5B9)),
  SwatchColorTextil('Borgoña', Color(0xFF800020)),
  SwatchColorTextil('Terracota', Color(0xFFC86D51)),
  SwatchColorTextil('Verde Oliva', Color(0xFF556B2F)),
  SwatchColorTextil('Esmeralda', Color(0xFF046307)),
  SwatchColorTextil('Rosa Palo', Color(0xFFDDA7A5)),
  SwatchColorTextil('Malva', Color(0xFF9370DB)),
  SwatchColorTextil('Gris Perla', Color(0xFFD1D5DB)),
  SwatchColorTextil('Ocre', Color(0xFFCC7722)),
];

class PantallaBuscarProductos extends StatefulWidget {
  final CatalogoBloc? bloc;
  final VoidCallback? alIrAPerfil;
  final VoidCallback? alIrAInicio;
  final VoidCallback? alIrACatalogo;

  const PantallaBuscarProductos({
    super.key,
    this.bloc,
    this.alIrAPerfil,
    this.alIrAInicio,
    this.alIrACatalogo,
  });

  @override
  State<PantallaBuscarProductos> createState() => _PantallaBuscarProductosState();
}

class _PantallaBuscarProductosState extends State<PantallaBuscarProductos> {
  late final CatalogoBloc _bloc;
  final TextEditingController _searchController = TextEditingController();

  final List<String> _temporadas = const [
    'Todas las temporadas',
    'Otoño / Invierno 2024',
    'Primavera / Verano 2025',
    'Cápsula Edición Limitada',
  ];

  final List<String> _colecciones = const [
    'Sastrería Atelier',
    'Esenciales',
    'Alta Costura',
    'Seda Natural Pura',
  ];

  final List<String> _tallas = const [
    '36',
    '38',
    '40',
    '42',
    '44',
    'Única',
  ];

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? CatalogoBloc();
    _bloc.inicializar();
  }

  @override
  void dispose() {
    _searchController.dispose();
    if (widget.bloc == null) {
      _bloc.dispose();
    }
    super.dispose();
  }

  void _ejecutarConfirmacion() {
    final query = _searchController.text.trim();
    _searchController.clear();
    _bloc.confirmarBusqueda(nuevoTermino: query.isNotEmpty ? query : null);
  }

  void _abrirModalFiltrosAvanzados() {
    double tempMin = _bloc.precioMin;
    double tempMax = _bloc.precioMax;
    String tempOrden = _bloc.ordenSeleccionado;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (modalCtx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                top: 24,
                left: 20,
                right: 20,
                bottom: MediaQuery.of(modalCtx).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'FILTROS AVANZADOS ATELIER',
                        style: TextStyle(
                          fontFamily: 'Outfit',
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                          color: Colors.black,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, size: 20),
                        onPressed: () => Navigator.of(modalCtx).pop(),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'RANGO DE INVERSIÓN',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      color: Color(0xFF666666),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${tempMin.toStringAsFixed(0)} €',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      Text(
                        '${tempMax.toStringAsFixed(0)} €',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ],
                  ),
                  RangeSlider(
                    values: RangeValues(tempMin, tempMax),
                    min: 0,
                    max: 2500,
                    divisions: 50,
                    activeColor: Colors.black,
                    inactiveColor: const Color(0xFFE5E5E5),
                    onChanged: (vals) {
                      setModalState(() {
                        tempMin = vals.start;
                        tempMax = vals.end;
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'ORDENAR POR',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      color: Color(0xFF666666),
                    ),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: tempOrden,
                    decoration: InputDecoration(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(color: Color(0xFFE5E5E5)),
                      ),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'recientes', child: Text('Más recientes')),
                      DropdownMenuItem(value: 'precio_asc', child: Text('Precio: Menor a Mayor')),
                      DropdownMenuItem(value: 'precio_desc', child: Text('Precio: Mayor a Menor')),
                      DropdownMenuItem(value: 'nombre_asc', child: Text('Nombre: A - Z')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setModalState(() {
                          tempOrden = val;
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            side: const BorderSide(color: Colors.black),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          onPressed: () {
                            Navigator.of(modalCtx).pop();
                            _bloc.restablecerFiltros();
                          },
                          child: const Text(
                            'LIMPIAR TODO',
                            style: TextStyle(
                              color: Colors.black,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.black,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          onPressed: () {
                            Navigator.of(modalCtx).pop();
                            _bloc.setRangoPrecios(tempMin, tempMax);
                            _bloc.cambiarOrden(tempOrden);
                          },
                          child: const Text(
                            'APLICAR FILTROS',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) {
        return Scaffold(
          backgroundColor: Colors.white,
          appBar: _construirAppBar(),
          body: _construirCuerpo(),
          bottomNavigationBar: _construirBottomNav(),
        );
      },
    );
  }

  PreferredSizeWidget _construirAppBar() {
    return AppBar(
      elevation: 0,
      backgroundColor: Colors.white,
      foregroundColor: Colors.black,
      titleSpacing: 16,
      title: Row(
        children: [
          const Text(
            'FASHION STORE',
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: 13,
              fontWeight: FontWeight.w700,
              letterSpacing: 2.0,
              color: Colors.black,
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            '/',
            style: TextStyle(fontSize: 12, color: Color(0xFF888888)),
          ),
          const SizedBox(width: 8),
          const Text(
            'Buscar',
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: 13,
              fontWeight: FontWeight.w400,
              color: Color(0xFF555555),
            ),
          ),
        ],
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 16),
          child: GestureDetector(
            onTap: widget.alIrAPerfil,
            child: Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFFD5D2CD)),
              ),
              child: ClipOval(
                child: Image.network(
                  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => const Icon(Icons.person, size: 20),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _construirCuerpo() {
    return RefreshIndicator(
      color: Colors.black,
      onRefresh: () => _bloc.confirmarBusqueda(),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Barra de búsqueda superior
            _construirBarraBusqueda(),

            // 2. Fila horizontal de temporadas
            _construirFilaTemporadas(),

            // 3. Sección de Filtros Refinados
            _construirFiltrosRefinados(),

            // 4. Cabecera de resultados "Visto recientemente"
            _construirCabeceraResultados(),

            // 5. Grilla de productos
            _construirGrillaProductos(),

            // 6. Búsquedas frecuentes
            _construirBusquedasFrecuentes(),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _construirBarraBusqueda() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: const Color(0xFFF7F7F7),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFEBEBEB)),
        ),
        child: Row(
          children: [
            const Icon(Icons.search, color: Color(0xFF777777), size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _searchController,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _ejecutarConfirmacion(),
                decoration: const InputDecoration(
                  hintText: 'Buscar vestidos, blazers, tejidos...',
                  hintStyle: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 13,
                    color: Color(0xFF888888),
                  ),
                  border: InputBorder.none,
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            if (_searchController.text.isNotEmpty)
              IconButton(
                icon: const Icon(Icons.close, size: 18, color: Color(0xFF777777)),
                onPressed: () {
                  setState(() {
                    _searchController.clear();
                  });
                },
              ),
            // Botón de confirmación explícito BUSCAR
            GestureDetector(
              onTap: _ejecutarConfirmacion,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  'BUSCAR',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.0,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 6),
            // Botón modal de filtros avanzados
            IconButton(
              icon: Stack(
                children: [
                  const Icon(Icons.tune, size: 20, color: Colors.black),
                  if (_bloc.tieneFiltrosActivos)
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        width: 7,
                        height: 7,
                        decoration: const BoxDecoration(
                          color: Color(0xFF991B1B),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                ],
              ),
              onPressed: _abrirModalFiltrosAvanzados,
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirFilaTemporadas() {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        itemCount: _temporadas.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, idx) {
          final temp = _temporadas[idx];
          final activa = _bloc.temporadaSeleccionada == temp;
          return GestureDetector(
            onTap: () {
              _bloc.seleccionarTemporada(temp);
              _bloc.confirmarBusqueda();
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: activa ? Colors.black : const Color(0xFFF4F4F4),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: activa ? Colors.black : const Color(0xFFE5E5E5),
                ),
              ),
              alignment: Alignment.center,
              child: Text(
                temp.toUpperCase(),
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.1,
                  color: activa ? Colors.white : const Color(0xFF333333),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _construirFiltrosRefinados() {
    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título de sección y botón Restablecer
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'FILTROS REFINADOS',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.5,
                    color: Color(0xFF222222),
                  ),
                ),
                GestureDetector(
                  onTap: () {
                    _bloc.restablecerFiltros();
                  },
                  child: const Text(
                    'RESTABLECER',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      color: Color(0xFF777777),
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Fila 1: Líneas / Colección
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                const Text(
                  'Línea:',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    color: Color(0xFF666666),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: SizedBox(
                    height: 32,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _colecciones.length,
                      separatorBuilder: (context, index) => const SizedBox(width: 6),
                      itemBuilder: (ctx, i) {
                        final col = _colecciones[i];
                        final activa = _bloc.coleccionSeleccionada == col;
                        return GestureDetector(
                          onTap: () {
                            _bloc.alternarColeccion(col);
                            _bloc.confirmarBusqueda();
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: activa ? Colors.black : const Color(0xFFF9F9F8),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: activa ? Colors.black : const Color(0xFFE2E2E0),
                              ),
                            ),
                            child: Text(
                              col,
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 11,
                                fontWeight: activa ? FontWeight.bold : FontWeight.w500,
                                color: activa ? Colors.white : Colors.black,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Fila 2: Tallas
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                const Text(
                  'Tallas:',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    color: Color(0xFF666666),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: SizedBox(
                    height: 32,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _tallas.length,
                      separatorBuilder: (context, index) => const SizedBox(width: 6),
                      itemBuilder: (ctx, i) {
                        final talla = _tallas[i];
                        final activa = _bloc.tallaSeleccionada == talla;
                        return GestureDetector(
                          onTap: () {
                            _bloc.seleccionarTalla(talla);
                            _bloc.confirmarBusqueda();
                          },
                          child: Container(
                            width: 36,
                            height: 32,
                            decoration: BoxDecoration(
                              color: activa ? Colors.black : Colors.white,
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(
                                color: activa ? Colors.black : const Color(0xFFDCDAD5),
                              ),
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              talla,
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 11,
                                fontWeight: activa ? FontWeight.bold : FontWeight.w500,
                                color: activa ? Colors.white : Colors.black,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Fila 3: Colores textiles (16 tonalidades)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                const Text(
                  'Colores:',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    color: Color(0xFF666666),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: SizedBox(
                    height: 32,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: kColoresTextiles.length,
                      separatorBuilder: (context, index) => const SizedBox(width: 6),
                      itemBuilder: (ctx, i) {
                        final swatch = kColoresTextiles[i];
                        final activa = _bloc.colorSeleccionado == swatch.nombre;
                        return GestureDetector(
                          onTap: () {
                            _bloc.seleccionarColor(swatch.nombre);
                            _bloc.confirmarBusqueda();
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: activa ? const Color(0xFFF2EFE9) : Colors.white,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: activa ? Colors.black : const Color(0xFFE2E2E0),
                              ),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 14,
                                  height: 14,
                                  decoration: BoxDecoration(
                                    color: swatch.color,
                                    shape: BoxShape.circle,
                                    border: Border.all(color: swatch.borde),
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  swatch.nombre,
                                  style: TextStyle(
                                    fontFamily: 'Outfit',
                                    fontSize: 11,
                                    fontWeight: activa ? FontWeight.bold : FontWeight.w500,
                                    color: Colors.black,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirCabeceraResultados() {
    final estado = _bloc.estado;
    final total = estado is CatalogoCargado ? estado.paginacion.totalRegistros : 0;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  // Tipografía Outfit estándar según el Design System
                  const Text(
                    'Visto recientemente',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.2,
                      color: Color(0xFF111111),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '($total prendas)',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 12,
                      fontWeight: FontWeight.w400,
                      color: Color(0xFF777777),
                    ),
                  ),
                ],
              ),
              GestureDetector(
                onTap: () => _bloc.limpiarHistorial(),
                child: const Row(
                  children: [
                    Icon(Icons.delete_outline, size: 14, color: Color(0xFF666666)),
                    SizedBox(width: 4),
                    Text(
                      'LIMPIAR HISTORIAL',
                      style: TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.1,
                        color: Color(0xFF666666),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Badge de término de búsqueda activo
          if (_bloc.terminoBusquedaActivo.isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'BÚSQUEDA: "${_bloc.terminoBusquedaActivo}"',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.8,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 6),
                  GestureDetector(
                    onTap: () => _bloc.quitarTerminoBusqueda(),
                    child: const Icon(Icons.close, size: 14, color: Colors.white70),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _construirGrillaProductos() {
    final estado = _bloc.estado;

    if (estado is CatalogoCargando) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 40),
        child: Center(
          child: CircularProgressIndicator(color: Colors.black),
        ),
      );
    }

    if (estado is CatalogoError) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Column(
            children: [
              const Icon(Icons.error_outline, size: 36, color: Color(0xFF991B1B)),
              const SizedBox(height: 8),
              Text(
                estado.mensaje,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF666666)),
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.black),
                onPressed: () => _bloc.confirmarBusqueda(),
                child: const Text('Reintentar', style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ),
      );
    }

    if (estado is CatalogoCargado) {
      final productos = estado.productos;
      if (productos.isEmpty) {
        return const Padding(
          padding: EdgeInsets.symmetric(vertical: 48, horizontal: 24),
          child: Center(
            child: Column(
              children: [
                Icon(Icons.inventory_2_outlined, size: 40, color: Color(0xFF888888)),
                SizedBox(height: 12),
                Text(
                  'No se hallaron prendas con estos criterios.',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Intenta cambiar la temporada, color o término de búsqueda.',
                  style: TextStyle(color: Color(0xFF777777), fontSize: 12),
                ),
              ],
            ),
          ),
        );
      }

      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: productos.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 0.52,
            crossAxisSpacing: 12,
            mainAxisSpacing: 16,
          ),
          itemBuilder: (ctx, i) {
            return _construirTarjetaProducto(productos[i]);
          },
        ),
      );
    }

    return const SizedBox.shrink();
  }

  Widget _construirTarjetaProducto(ProductoItemDto item) {
    final esFav = _bloc.favoritosIds.contains(item.idProducto);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Contenedor de Fotografía con Badges y Corazón
        Expanded(
          child: Stack(
            children: [
              Positioned.fill(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: Image.network(
                    item.imagenUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) => Container(
                      color: const Color(0xFFF0EFEB),
                      child: const Center(
                        child: Icon(Icons.image_outlined, color: Color(0xFF888888)),
                      ),
                    ),
                  ),
                ),
              ),
              // Badge Superior (Edición Limitada / En Serrano)
              if (item.badgeEditorial.isNotEmpty)
                Positioned(
                  top: 8,
                  left: 8,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.85),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      item.badgeEditorial.toUpperCase(),
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 8,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.8,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              // Botón de Favorito / Wishlist
              Positioned(
                top: 8,
                right: 8,
                child: GestureDetector(
                  onTap: () => _bloc.alternarFavorito(item.idProducto),
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.9),
                      shape: BoxShape.circle,
                      boxShadow: const [
                        BoxShadow(
                          color: Colors.black12,
                          blurRadius: 4,
                          offset: Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Icon(
                      esFav ? Icons.favorite : Icons.favorite_border,
                      size: 16,
                      color: esFav ? const Color(0xFF991B1B) : Colors.black87,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),

        // Subtítulo Atelier (Alta Costura)
        Text(
          item.subtituloAtelier.toUpperCase(),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontFamily: 'Outfit',
            fontSize: 9,
            fontWeight: FontWeight.bold,
            letterSpacing: 1.0,
            color: Color(0xFF777777),
          ),
        ),
        const SizedBox(height: 2),

        // Título de la prenda
        Text(
          item.nombre,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontFamily: 'Outfit',
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: Colors.black,
          ),
        ),
        const SizedBox(height: 2),

        // Talla y Color sugerido
        Text(
          '${item.tallaSugerida} · ${item.colorSugerido}',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontSize: 11,
            color: Color(0xFF666666),
          ),
        ),
        const SizedBox(height: 6),

        // Fila de Precio y Botón + CESTA
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '${item.precioBase.toStringAsFixed(0)} €',
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 14,
                fontWeight: FontWeight.w800,
                color: Colors.black,
              ),
            ),
            GestureDetector(
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    backgroundColor: Colors.black,
                    content: Text(
                      '${item.nombre} añadida a la cesta',
                      style: const TextStyle(fontSize: 12, color: Colors.white),
                    ),
                    duration: const Duration(seconds: 2),
                  ),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF2F2F2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  '+ CESTA',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.8,
                    color: Colors.black,
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _construirBusquedasFrecuentes() {
    final busquedas = _bloc.busquedasFrecuentes;
    if (busquedas.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.trending_up, size: 16, color: Colors.black),
              SizedBox(width: 6),
              Text(
                'BÚSQUEDAS MÁS FRECUENTES',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.4,
                  color: Colors.black,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: busquedas.map((item) {
              return GestureDetector(
                onTap: () => _bloc.aplicarBusquedaFrecuente(item),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF7F7F7),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFFEBEBEB)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.search, size: 12, color: Color(0xFF777777)),
                      const SizedBox(width: 4),
                      Text(
                        item,
                        style: const TextStyle(
                          fontFamily: 'Outfit',
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: Color(0xFF333333),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _construirBottomNav() {
    return BottomNavigationBar(
      currentIndex: 1, // 'Buscar' seleccionado
      type: BottomNavigationBarType.fixed,
      backgroundColor: Colors.white,
      selectedItemColor: Colors.black,
      unselectedItemColor: const Color(0xFF777777),
      selectedLabelStyle: const TextStyle(fontFamily: 'Outfit', fontSize: 10, fontWeight: FontWeight.bold),
      unselectedLabelStyle: const TextStyle(fontFamily: 'Outfit', fontSize: 10),
      onTap: (index) {
        if (index == 0 && widget.alIrAInicio != null) {
          widget.alIrAInicio!();
        } else if (index == 2 && widget.alIrACatalogo != null) {
          widget.alIrACatalogo!();
        } else if (index == 3 && widget.alIrAPerfil != null) {
          widget.alIrAPerfil!();
        }
      },
      items: const [
        BottomNavigationBarItem(
          icon: Icon(Icons.home_outlined),
          activeIcon: Icon(Icons.home),
          label: 'Inicio',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.search),
          label: 'Buscar',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.grid_view_outlined),
          activeIcon: Icon(Icons.grid_view),
          label: 'Catálogo',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline),
          activeIcon: Icon(Icons.person),
          label: 'Perfil',
        ),
      ],
    );
  }
}
