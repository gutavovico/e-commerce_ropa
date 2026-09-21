import 'package:flutter/material.dart';
import '../../datos/modelos/catalogo_dto.dart';
import '../bloc/catalogo_bloc.dart';

/// Pantalla Principal del Catálogo de Prendas (CU05) para FashionStore Móvil.
///
/// Implementa la vista de galería de alta costura exclusiva para moda femenina,
/// carrusel horizontal de chips con contadores numéricos, controles de vista,
/// cuadrícula de 2 columnas con tarjetas de lujo, paginación y sello editorial.
///
/// Conforme a la Directriz Global Hub-and-Spoke, carece estrictamente de botón
/// de retroceso (automaticallyImplyLeading: false).
class PantallaCatalogo extends StatefulWidget {
  final bool mostrarBottomNav;
  final bool habilitarImagenesRed;
  final VoidCallback? alIrAInicio;
  final VoidCallback? alIrABuscar;
  final VoidCallback? alIrAPerfil;
  final CatalogoGeneralBloc? bloc;

  const PantallaCatalogo({
    super.key,
    this.mostrarBottomNav = true,
    this.habilitarImagenesRed = true,
    this.alIrAInicio,
    this.alIrABuscar,
    this.alIrAPerfil,
    this.bloc,
  });

  @override
  State<PantallaCatalogo> createState() => _PantallaCatalogoState();
}

class _PantallaCatalogoState extends State<PantallaCatalogo> {
  late final CatalogoGeneralBloc _bloc;

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? CatalogoGeneralBloc();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _bloc.cargarCatalogo();
      }
    });
  }

  void _mostrarSnackBar(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          mensaje,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 11,
            letterSpacing: 0.8,
            fontWeight: FontWeight.w500,
          ),
        ),
        backgroundColor: const Color(0xFF1A1A1A),
        duration: const Duration(seconds: 2),
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

          if (estado is CatalogoGeneralCargando) {
            return _construirEstadoCargando();
          }

          if (estado is CatalogoGeneralError) {
            return _construirEstadoError(estado.mensaje);
          }

          if (estado is CatalogoGeneralVacio) {
            return _construirEstadoVacio(estado);
          }

          if (estado is CatalogoGeneralCargado) {
            return _construirContenidoPrincipal(estado);
          }

          return const SizedBox.shrink();
        },
      ),
    );
  }

  /// AppBar institucional sin botón de regreso (Directriz Hub-and-Spoke)
  PreferredSizeWidget _construirAppBar() {
    return AppBar(
      automaticallyImplyLeading: false,
      backgroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
      title: const Text(
        'FASHION STORE',
        style: TextStyle(
          color: Colors.black,
          fontSize: 13,
          fontWeight: FontWeight.w800,
          letterSpacing: 2.5,
        ),
      ),
      leading: IconButton(
        icon: const Icon(Icons.menu_rounded, color: Colors.black, size: 20),
        tooltip: 'Menú de Atelier',
        onPressed: () {
          _mostrarSnackBar('Fashion Store Flagship · Colección Atelier');
        },
      ),
      actions: [
        if (widget.alIrABuscar != null)
          IconButton(
            icon: const Icon(Icons.search, color: Colors.black, size: 20),
            tooltip: 'Buscar prendas',
            onPressed: widget.alIrABuscar,
          ),
        AnimatedBuilder(
          animation: _bloc,
          builder: (context, _) {
            return Stack(
              alignment: Alignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.shopping_bag_outlined,
                      color: Colors.black, size: 20),
                  tooltip: 'Cesta de compras',
                  onPressed: () {
                    _mostrarSnackBar(
                        'Cesta de compras: ${_bloc.cestaCount} prendas');
                  },
                ),
                Positioned(
                  top: 10,
                  right: 8,
                  child: Container(
                    padding: const EdgeInsets.all(3),
                    decoration: const BoxDecoration(
                      color: Colors.black,
                      shape: BoxShape.circle,
                    ),
                    constraints: const BoxConstraints(
                      minWidth: 14,
                      minHeight: 14,
                    ),
                    child: Text(
                      '${_bloc.cestaCount}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 8,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(width: 4),
      ],
    );
  }

  /// Estado de carga con indicadores elegantes
  Widget _construirEstadoCargando() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 28,
            height: 28,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
            ),
          ),
          SizedBox(height: 16),
          Text(
            'CONECTANDO CON ATELIER SERRANO...',
            style: TextStyle(
              fontSize: 10,
              letterSpacing: 1.8,
              fontWeight: FontWeight.w600,
              color: Color(0xFF666666),
            ),
          ),
        ],
      ),
    );
  }

  /// Estado de error con reintento
  Widget _construirEstadoError(String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 40, color: Color(0xFF991B1B)),
            const SizedBox(height: 16),
            const Text(
              'INCIDENCIA DE RED ATELIER',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.8,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 11, color: Color(0xFF666666)),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black,
                foregroundColor: Colors.white,
                shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.all(Radius.circular(2)),
                ),
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              ),
              onPressed: () => _bloc.cargarCatalogo(),
              child: const Text(
                'REINTENTAR',
                style: TextStyle(fontSize: 11, letterSpacing: 1.5),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Estado vacío cuando una categoría no tiene prendas activas
  Widget _construirEstadoVacio(CatalogoGeneralVacio estado) {
    return Column(
      children: [
        _construirCabeceraEditorial(),
        _construirFilaChipsCategorias(
          resumenCategorias: estado.resumenCategorias,
          categoriaSeleccionadaId: estado.categoriaSeleccionadaId,
          totalGlobal: estado.totalGlobalPrendas,
        ),
        Expanded(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: const BoxDecoration(
                      color: Color(0xFFF5F4F0),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: const Text(
                      '0',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'serif',
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'COLECCIÓN NO DISPONIBLE',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2.0,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    estado.mensaje,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF666666),
                    ),
                  ),
                  const SizedBox(height: 20),
                  TextButton(
                    onPressed: () => _bloc.seleccionarCategoria(null),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.black,
                      backgroundColor: const Color(0xFFF0EFEA),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 20, vertical: 10),
                    ),
                    child: const Text(
                      'VER TODAS LAS PRENDAS DISPONIBLES',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// Contenido principal con cabecera, chips, controles, cuadrícula y paginación
  Widget _construirContenidoPrincipal(CatalogoGeneralCargado estado) {
    return ListView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.only(bottom: 32),
      children: [
        // 1. Cabecera Editorial "Catálogo de Prendas"
        _construirCabeceraEditorial(),

        // 2. Fila Deslizable de Chips de Categorías
        _construirFilaChipsCategorias(
          resumenCategorias: estado.resumenCategorias,
          categoriaSeleccionadaId: estado.categoriaSeleccionadaId,
          totalGlobal: estado.totalGlobalPrendas,
        ),

        // 3. Barra de Control de Vista y Búsqueda
        _construirBarraControlVista(estado),

        // 4. Cuadrícula de Prendas (GridView)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: _construirCuadriculaPrendas(estado),
        ),

        // 5. Paginación y Botón "Cargar Más"
        _construirSeccionPaginacion(estado),

        // 6. Sello Editorial Inferior
        _construirSelloEditorial(),
      ],
    );
  }

  /// Cabecera editorial institucional
  Widget _construirCabeceraEditorial() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'COLECCIÓN ATELIER 2026',
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 2.0,
                  color: Color(0xFF888888),
                ),
              ),
              Row(
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: Color(0xFF10B981),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 4),
                  const Text(
                    'MADRID · PARÍS',
                    style: TextStyle(
                      fontSize: 8,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.2,
                      color: Color(0xFF666666),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Catálogo de Prendas',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.5,
              color: Colors.black,
            ),
          ),
        ],
      ),
    );
  }

  /// Fila horizontal de chips con unidades numéricas
  Widget _construirFilaChipsCategorias({
    required List<CategoriaResumenDto> resumenCategorias,
    required int? categoriaSeleccionadaId,
    required int totalGlobal,
  }) {
    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(vertical: 6),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: Color(0xFFECEAE6), width: 1),
          bottom: BorderSide(color: Color(0xFFECEAE6), width: 1),
        ),
      ),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: resumenCategorias.length + 1,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          if (index == 0) {
            final activo = categoriaSeleccionadaId == null;
            return _chipItem(
              titulo: 'Todos ($totalGlobal)',
              activo: activo,
              onTap: () => _bloc.seleccionarCategoria(null),
            );
          }

          final cat = resumenCategorias[index - 1];
          final activo = categoriaSeleccionadaId == cat.idCategoria;
          return _chipItem(
            titulo: '${cat.nombre} (${cat.totalPrendas})',
            activo: activo,
            onTap: () => _bloc.seleccionarCategoria(cat.idCategoria),
          );
        },
      ),
    );
  }

  Widget _chipItem({
    required String titulo,
    required bool activo,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: activo ? Colors.black : const Color(0xFFF5F4F0),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: activo ? Colors.black : const Color(0xFFE8E6E1),
            width: 1,
          ),
        ),
        child: Center(
          child: Text(
            titulo,
            style: TextStyle(
              fontSize: 10,
              fontWeight: activo ? FontWeight.w700 : FontWeight.w500,
              letterSpacing: 0.8,
              color: activo ? Colors.white : const Color(0xFF333333),
            ),
          ),
        ),
      ),
    );
  }

  /// Barra de control de vista (modo columnas y botón "Filtrar y Ordenar")
  Widget _construirBarraControlVista(CatalogoGeneralCargado estado) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Conmutador de Densidad de Cuadrícula
          Row(
            children: [
              const Text(
                'VISTA:',
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                  color: Color(0xFF888888),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: () => _bloc.cambiarModoColumnas(2),
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: estado.modoColumnas == 2
                        ? Colors.black
                        : const Color(0xFFF5F4F0),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Icon(
                    Icons.grid_view_sharp,
                    size: 14,
                    color: estado.modoColumnas == 2
                        ? Colors.white
                        : const Color(0xFF666666),
                  ),
                ),
              ),
              const SizedBox(width: 4),
              GestureDetector(
                onTap: () => _bloc.cambiarModoColumnas(1),
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: estado.modoColumnas == 1
                        ? Colors.black
                        : const Color(0xFFF5F4F0),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Icon(
                    Icons.view_agenda_sharp,
                    size: 14,
                    color: estado.modoColumnas == 1
                        ? Colors.white
                        : const Color(0xFF666666),
                  ),
                ),
              ),
            ],
          ),

          // Botón "Filtrar y Ordenar"
          GestureDetector(
            onTap: () {
              if (widget.alIrABuscar != null) {
                widget.alIrABuscar!();
              } else {
                _mostrarSelectorOrden();
              }
            },
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFD5D2CD)),
                borderRadius: BorderRadius.circular(2),
              ),
              child: const Row(
                children: [
                  Icon(Icons.tune, size: 12, color: Colors.black),
                  SizedBox(width: 4),
                  Text(
                    'Filtrar y Ordenar',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5,
                      color: Colors.black,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _mostrarSelectorOrden() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  child: Text(
                    'CRITERIO DE ORDENACIÓN',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                    ),
                  ),
                ),
                const Divider(),
                ListTile(
                  title: const Text('Más Recientes',
                      style: TextStyle(fontSize: 12)),
                  onTap: () {
                    Navigator.pop(ctx);
                    _bloc.cambiarOrden('recientes');
                  },
                ),
                ListTile(
                  title: const Text('Precio: Menor a Mayor',
                      style: TextStyle(fontSize: 12)),
                  onTap: () {
                    Navigator.pop(ctx);
                    _bloc.cambiarOrden('precio_asc');
                  },
                ),
                ListTile(
                  title: const Text('Precio: Mayor a Menor',
                      style: TextStyle(fontSize: 12)),
                  onTap: () {
                    Navigator.pop(ctx);
                    _bloc.cambiarOrden('precio_desc');
                  },
                ),
                ListTile(
                  title: const Text('Nombre (A - Z)',
                      style: TextStyle(fontSize: 12)),
                  onTap: () {
                    Navigator.pop(ctx);
                    _bloc.cambiarOrden('nombre_asc');
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  /// Cuadrícula de prendas adaptable (2 columnas vs 1 columna)
  Widget _construirCuadriculaPrendas(CatalogoGeneralCargado estado) {
    final productos = estado.productosAcumulados;

    if (estado.modoColumnas == 1) {
      return ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: productos.length,
        separatorBuilder: (_, _) => const SizedBox(height: 16),
        itemBuilder: (context, index) {
          return _tarjetaProductoItem(productos[index], estado.favoritos);
        },
      );
    }

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.58, // Espacio vertical generoso sin huecos blancos excesivos ni RenderFlex overflow
        mainAxisSpacing: 16,
        crossAxisSpacing: 12,
      ),
      itemCount: productos.length,
      itemBuilder: (context, index) {
        return _tarjetaProductoItem(productos[index], estado.favoritos);
      },
    );
  }

  /// Tarjeta de prenda de alta costura
  Widget _tarjetaProductoItem(
      ProductoCatalogoItemDto prod, Set<int> favoritos) {
    final esFav = favoritos.contains(prod.idProducto);

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: const Color(0xFFECEAE6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Imagen con AspectRatio 3:4 y Badges
          Stack(
            children: [
              AspectRatio(
                aspectRatio: 0.75,
                child: Container(
                  color: const Color(0xFFF5F4F0),
                  child: widget.habilitarImagenesRed &&
                          prod.imagenUrl != null &&
                          prod.imagenUrl!.isNotEmpty
                      ? Image.network(
                          prod.imagenUrl!,
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => _placeholderPrenda(),
                        )
                      : _placeholderPrenda(),
                ),
              ),

              // Badge superior izquierdo
              if (prod.etiquetaBadge != null &&
                  prod.etiquetaBadge!.isNotEmpty)
                Positioned(
                  top: 6,
                  left: 6,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 6, vertical: 3),
                    decoration: BoxDecoration(
                      color: prod.tieneDescuento
                          ? const Color(0xFF991B1B)
                          : Colors.white.withValues(alpha: 0.95),
                      borderRadius: BorderRadius.circular(1),
                    ),
                    child: Text(
                      prod.etiquetaBadge!,
                      style: TextStyle(
                        fontSize: 8,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.0,
                        color: prod.tieneDescuento
                            ? Colors.white
                            : Colors.black,
                      ),
                    ),
                  ),
                ),

              // Botón Wishlist superior derecho
              Positioned(
                top: 6,
                right: 6,
                child: GestureDetector(
                  onTap: () {
                    _bloc.toggleFavorito(prod.idProducto);
                    _mostrarSnackBar(
                      esFav
                          ? 'Retirado de Wishlist'
                          : 'Añadido a Wishlist: ${prod.nombre}',
                    );
                  },
                  child: Container(
                    width: 26,
                    height: 26,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.9),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      esFav ? Icons.favorite : Icons.favorite_border,
                      size: 15,
                      color: esFav
                          ? const Color(0xFF991B1B)
                          : const Color(0xFF333333),
                    ),
                  ),
                ),
              ),
            ],
          ),

          // 2. Metadatos de la prenda
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        prod.subtituloAtelier.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 8,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.2,
                          color: Color(0xFF777777),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        prod.nombre,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Colors.black,
                          height: 1.2,
                        ),
                      ),
                      const SizedBox(height: 4),
                      // Precios
                      Row(
                        children: [
                          if (prod.tieneDescuento) ...[
                            Text(
                              '${prod.precioFinal.toStringAsFixed(0)} €',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                color: Color(0xFF991B1B),
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '${prod.precioBase.toStringAsFixed(0)} €',
                              style: const TextStyle(
                                fontSize: 10,
                                decoration: TextDecoration.lineThrough,
                                color: Color(0xFF888888),
                              ),
                            ),
                          ] else
                            Text(
                              '${prod.precioBase.toStringAsFixed(0)} €',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                color: Colors.black,
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),

                  // Tallas y Color Dots
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          prod.tallasDisponibles.isNotEmpty
                              ? prod.tallasDisponibles.join(' · ')
                              : 'Talla Única',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 8,
                            color: Color(0xFF666666),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      if (prod.coloresDisponibles.isNotEmpty)
                        Row(
                          children: prod.coloresDisponibles
                              .take(2)
                              .map((c) => Container(
                                    width: 8,
                                    height: 8,
                                    margin: const EdgeInsets.only(left: 3),
                                    decoration: BoxDecoration(
                                      color: _colorDesdeHex(c.codigoHex),
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                          color: const Color(0xFFCCCCCC),
                                          width: 0.5),
                                    ),
                                  ))
                              .toList(),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholderPrenda() {
    return const Center(
      child: Text(
        'ATELIER',
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w700,
          letterSpacing: 2.0,
          color: Color(0xFF999999),
        ),
      ),
    );
  }

  Color _colorDesdeHex(String? hexString) {
    if (hexString == null || hexString.isEmpty) {
      return const Color(0xFF111111);
    }
    final clean = hexString.replaceAll('#', '');
    try {
      if (clean.length == 6) {
        return Color(int.parse('FF$clean', radix: 16));
      }
    } catch (_) {}
    return const Color(0xFF111111);
  }

  /// Sección de paginación con progreso y botón "Cargar Más"
  Widget _construirSeccionPaginacion(CatalogoGeneralCargado estado) {
    final cargadas = estado.productosAcumulados.length;
    final total = estado.totalArticulos;
    final restantes = estado.prendasRestantes;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
      child: Column(
        children: [
          // Progreso
          Text(
            'MOSTRANDO 1 – $cargadas DE $total PRENDAS',
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
              color: Color(0xFF666666),
            ),
          ),
          const SizedBox(height: 12),

          // Botón Expansor "Cargar Más"
          if (estado.tieneSiguiente)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.black,
                    side: const BorderSide(color: Colors.black, width: 1),
                    shape: const RoundedRectangleBorder(
                      borderRadius: BorderRadius.all(Radius.circular(2)),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  onPressed: estado.cargandoMas
                      ? null
                      : () => _bloc.cargarMas(),
                  child: estado.cargandoMas
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Colors.black),
                          ),
                        )
                      : Text(
                          'CARGAR MÁS PRENDAS ($restantes) ⌵',
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.5,
                          ),
                        ),
                ),
              ),
            ),

          // Selector de Páginas Numeradas
          if (estado.totalPaginas > 1)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (estado.tieneAnterior)
                  IconButton(
                    icon: const Icon(Icons.chevron_left, size: 18),
                    onPressed: () =>
                        _bloc.irAPagina(estado.paginaActual - 1),
                  ),
                for (int p = 1; p <= estado.totalPaginas; p++)
                  GestureDetector(
                    onTap: () => _bloc.irAPagina(p),
                    child: Container(
                      width: 28,
                      height: 28,
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      decoration: BoxDecoration(
                        color: estado.paginaActual == p
                            ? Colors.black
                            : Colors.white,
                        border: Border.all(
                          color: estado.paginaActual == p
                              ? Colors.black
                              : const Color(0xFFD5D2CD),
                        ),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        '$p',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: estado.paginaActual == p
                              ? Colors.white
                              : Colors.black,
                        ),
                      ),
                    ),
                  ),
                if (estado.tieneSiguiente)
                  IconButton(
                    icon: const Icon(Icons.chevron_right, size: 18),
                    onPressed: () =>
                        _bloc.irAPagina(estado.paginaActual + 1),
                  ),
              ],
            ),
        ],
      ),
    );
  }

  /// Sello editorial de atelier
  Widget _construirSelloEditorial() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 20, 16, 8),
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
      decoration: BoxDecoration(
        color: const Color(0xFFFAFAF8),
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: const Color(0xFFECEAE6)),
      ),
      child: const Column(
        children: [
          Text(
            'ATELIER FLAGSHIP MADRID · PARÍS',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 2.2,
              color: Colors.black,
            ),
          ),
          SizedBox(height: 6),
          Text(
            'Edición Limitada · Confección Artesanal en Tejidos Naturales',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 9,
              color: Color(0xFF777777),
              letterSpacing: 0.5,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }
}
