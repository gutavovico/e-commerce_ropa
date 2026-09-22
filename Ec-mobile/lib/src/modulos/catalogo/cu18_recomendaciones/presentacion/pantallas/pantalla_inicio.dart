import 'package:flutter/material.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/dominio/repositorios/perfil_repositorio.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/presentacion/pantallas/pantalla_producto_detalle.dart';
import '../../datos/modelos/recomendacion_item_dto.dart';
import '../bloc/inicio_bloc.dart';

class PantallaInicio extends StatefulWidget {
  final InicioBloc? bloc;
  final String? token;
  final String? nombreUsuario;
  final VoidCallback? alIrABuscar;
  final VoidCallback? alIrACatalogo;
  final VoidCallback? alIrAPerfil;
  final VoidCallback? alIrAColecciones;
  /// Abre la Bolsa de Compra como pantalla hoja.
  final VoidCallback? alIrABolsa;
  final bool mostrarBottomNav;
  final bool habilitarImagenesRed;

  const PantallaInicio({
    super.key,
    this.bloc,
    this.token,
    this.nombreUsuario,
    this.alIrABuscar,
    this.alIrACatalogo,
    this.alIrAPerfil,
    this.alIrAColecciones,
    this.alIrABolsa,
    this.mostrarBottomNav = true,
    this.habilitarImagenesRed = true,
  });

  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  late final InicioBloc _bloc;
  int _indiceNav = 0;

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? InicioBloc();
    if (widget.nombreUsuario != null && widget.nombreUsuario!.isNotEmpty) {
      _bloc.establecerNombreCliente(widget.nombreUsuario!);
    } else if (widget.token != null && widget.token!.isNotEmpty) {
      _cargarNombreDesdePerfil(widget.token!);
    }
    _bloc.cargarInicio(token: widget.token);
  }

  @override
  void didUpdateWidget(covariant PantallaInicio oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.nombreUsuario != null &&
        widget.nombreUsuario != oldWidget.nombreUsuario &&
        widget.nombreUsuario!.isNotEmpty) {
      _bloc.establecerNombreCliente(widget.nombreUsuario!);
    }
  }

  Future<void> _cargarNombreDesdePerfil(String token) async {
    try {
      final repo = PerfilRepositorioImpl();
      final perfil = await repo.obtenerPerfil(token);
      final nombreCompleto = '${perfil.nombres} ${perfil.apellidos}'.trim();
      if (nombreCompleto.isNotEmpty && mounted) {
        _bloc.establecerNombreCliente(nombreCompleto);
      }
    } catch (_) {
      // En modo sin conexión o pruebas, preserva el valor existente
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) {
        return Scaffold(
          backgroundColor: Colors.white,
          appBar: _construirAppBar(context),
          body: Stack(
            children: [
              RefreshIndicator(
                color: Colors.black,
                onRefresh: () => _bloc.cargarInicio(token: widget.token),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 1. Chip Boutique y Saludo
                      _construirBarraBoutiqueYBienvenida(),

                      const SizedBox(height: 16),

                      // 2. Banner Hero Promocional (CU36)
                      _construirHeroBanner(context),

                      const SizedBox(height: 24),

                      // 3. Módulo "Recomendado para ti" (CU18)
                      _construirModuloRecomendaciones(context),

                      const SizedBox(height: 28),

                      // 4. Sección "Experiencia Atelier"
                      _construirExperienciaAtelier(),

                      const SizedBox(height: 80),
                    ],
                  ),
                ),
              ),

              // Toast flotante cuando se añade una prenda
              if (_bloc.mensajePrendaAgregada != null)
                Positioned(
                  bottom: 16,
                  left: 16,
                  right: 16,
                  child: Material(
                    elevation: 6,
                    borderRadius: BorderRadius.circular(12),
                    color: const Color(0xFF111111),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle_outline, color: Color(0xFFC5A880), size: 20),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              _bloc.mensajePrendaAgregada!,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          GestureDetector(
                            onTap: () => _bloc.limpiarMensajeToast(),
                            child: const Icon(Icons.close, color: Colors.white70, size: 18),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
          bottomNavigationBar: widget.mostrarBottomNav ? _construirBottomNavBar() : null,
        );
      },
    );
  }

  PreferredSizeWidget _construirAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      title: const Text(
        'FASHION STORE',
        style: TextStyle(
          color: Colors.black,
          fontSize: 14,
          fontWeight: FontWeight.w700,
          letterSpacing: 2.2,
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.notifications_none_outlined, color: Colors.black),
          onPressed: () {},
          tooltip: 'Notificaciones',
        ),
        // Acceso a la Bolsa de Compra. Es una pantalla hoja, no una quinta pestaña:
        // la directriz Hub-and-Spoke fija en 4 las pantallas raíz.
        IconButton(
          icon: const Icon(Icons.shopping_bag_outlined, color: Colors.black),
          onPressed: widget.alIrABolsa,
          tooltip: 'Bolsa de compra',
        ),
        GestureDetector(
          onTap: widget.alIrAPerfil,
          child: Container(
            margin: const EdgeInsets.only(right: 16),
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFFD5D2CD)),
            ),
            child: ClipOval(
              child: widget.habilitarImagenesRed
                  ? Image.network(
                      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) => const Icon(Icons.person, size: 20),
                    )
                  : const Icon(Icons.person, size: 20),
            ),
          ),
        ),
      ],
    );
  }

  Widget _construirBarraBoutiqueYBienvenida() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Chip Boutique
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: const Color(0xFFF5F4F0),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFFE5E2DC)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Icon(Icons.storefront_outlined, size: 14, color: Color(0xFF666666)),
                    SizedBox(width: 6),
                    Text(
                      'BOUTIQUE SERRANO (MADRID)',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 1.2,
                        color: Color(0xFF444444),
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.near_me_outlined, size: 18, color: Color(0xFF666666)),
            ],
          ),

          const SizedBox(height: 16),

          // Saludo
          const Text(
            'BIENVENIDA DE NUEVO',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              letterSpacing: 2.0,
              color: Color(0xFF888888),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            _bloc.nombreCliente,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w700,
              color: Colors.black,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Novedades seleccionadas y colecciones cápsula curadas exclusivamente para tu silueta y estilo personal.',
            style: TextStyle(
              fontSize: 12,
              height: 1.4,
              color: Color(0xFF666666),
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirHeroBanner(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Container(
          height: 380,
          color: const Color(0xFF1F1E1C),
          child: Stack(
            children: [
              Positioned.fill(
                child: Image.network(
                  'https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=1200&auto=format&fit=crop&q=85',
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => Container(
                    color: const Color(0xFF22201E),
                  ),
                ),
              ),
              Positioned.fill(
                child: Container(
                  color: Colors.black.withValues(alpha: 0.45),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    // Badge Pill
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.25),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white.withValues(alpha: 0.3)),
                      ),
                      child: const Text(
                        '• NUEVA TEMPORADA',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ),

                    const SizedBox(height: 12),

                    // Titular Hero
                    const Text(
                      'Visita nuestra\ncolección más\nreciente',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 26,
                        fontWeight: FontWeight.w400,
                        height: 1.15,
                        letterSpacing: -0.5,
                      ),
                    ),

                    const SizedBox(height: 10),

                    // Subtítulo
                    const Text(
                      'Líneas puras, patronaje contemporáneo y tejidos nobles seleccionados en Biella y Lyon para una silueta atemporal.',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                        height: 1.35,
                      ),
                    ),

                    const SizedBox(height: 18),

                    // Botón CTA Hero
                    GestureDetector(
                      onTap: widget.alIrAColecciones ??
                          widget.alIrACatalogo ??
                          widget.alIrABuscar,
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(25),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Text(
                              'EXPLORAR COLECCIÓN',
                              style: TextStyle(
                                color: Colors.black,
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.5,
                              ),
                            ),
                            SizedBox(width: 8),
                            Icon(Icons.arrow_forward, size: 14, color: Colors.black),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _construirModuloRecomendaciones(BuildContext context) {
    final estado = _bloc.estado;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Cabecera de Sección
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'SELECCIÓN A MEDIDA • ATELIER RECOMMENDS',
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.8,
                        color: Color(0xFF8C6D46),
                      ),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Recomendado para ti',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Colors.black,
                        letterSpacing: -0.3,
                      ),
                    ),
                  ],
                ),
              ),
              GestureDetector(
                onTap: widget.alIrACatalogo ?? widget.alIrABuscar,
                child: Row(
                  children: const [
                    Text(
                      'Ver catálogo',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: Colors.black,
                      ),
                    ),
                    SizedBox(width: 4),
                    Icon(Icons.arrow_forward, size: 12, color: Colors.black),
                  ],
                ),
              ),
            ],
          ),

          if (estado is InicioCargado && estado.motivoGeneral != null) ...[
            const SizedBox(height: 6),
            Text(
              estado.motivoGeneral!,
              style: const TextStyle(
                fontSize: 11,
                fontStyle: FontStyle.italic,
                color: Color(0xFF666666),
              ),
            ),
          ],

          const SizedBox(height: 16),

          // Renderizado de Estados
          if (estado is InicioCargando)
            _construirSkeletonLoader()
          else if (estado is InicioCargado && estado.tieneHistorial && estado.items.isNotEmpty)
            _construirCarruselPrendas(estado.items)
          else
            _construirEmptyState(),
        ],
      ),
    );
  }

  Widget _construirSkeletonLoader() {
    return SizedBox(
      height: 310,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: 2,
        separatorBuilder: (context, index) => const SizedBox(width: 14),
        itemBuilder: (context, index) => Container(
          width: 190,
          decoration: BoxDecoration(
            color: const Color(0xFFFAF9F6),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE5E2DC)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                flex: 3,
                child: Container(
                  decoration: const BoxDecoration(
                    color: Color(0xFFEFECE6),
                    borderRadius: BorderRadius.vertical(top: Radius.circular(11)),
                  ),
                ),
              ),
              Expanded(
                flex: 2,
                child: Padding(
                  padding: const EdgeInsets.all(10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      Container(height: 8, width: 80, color: const Color(0xFFE0DDD5)),
                      Container(height: 12, width: 140, color: const Color(0xFFD5D2CD)),
                      Container(height: 14, width: 60, color: const Color(0xFFE0DDD5)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _construirCarruselPrendas(List<ProductoRecomendadoDto> items) {
    return SizedBox(
      height: 320,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        clipBehavior: Clip.none,
        itemCount: items.length,
        separatorBuilder: (context, index) => const SizedBox(width: 14),
        itemBuilder: (context, index) {
          final item = items[index];
          final esFav = _bloc.favoritos.contains(item.idProducto);

          return GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => PantallaProductoDetalle(
                    idProducto: item.idProducto,
                    token: widget.token,
                    habilitarImagenesRed: widget.habilitarImagenesRed,
                  ),
                ),
              );
            },
            child: Container(
            width: 195,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFECEAE6)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Imagen con Badges
                Stack(
                  children: [
                    ClipRRect(
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(11)),
                      child: AspectRatio(
                        aspectRatio: 1.05,
                        child: Image.network(
                          item.imagenUrl,
                          fit: BoxFit.cover,
                          alignment: Alignment.topCenter,
                          errorBuilder: (context, error, stackTrace) => Container(
                            color: const Color(0xFFF2EFEB),
                            child: const Icon(Icons.checkroom, color: Color(0xFFCCCCCC)),
                          ),
                        ),
                      ),
                    ),
                    // Badge Editorial
                    Positioned(
                      top: 8,
                      left: 8,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.8),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          item.badgeEditorial,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 8,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ),
                    ),
                    // Botón Favorito
                    Positioned(
                      top: 8,
                      right: 8,
                      child: GestureDetector(
                        onTap: () => _bloc.toggleFavorito(item.idProducto),
                        child: Container(
                          width: 28,
                          height: 28,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.9),
                          ),
                          child: Icon(
                            esFav ? Icons.favorite : Icons.favorite_border,
                            color: esFav ? const Color(0xFF991B1B) : Colors.black87,
                            size: 15,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

                // Contenido Informativo
                Padding(
                  padding: const EdgeInsets.all(10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'TONO: ${item.tonoPrincipal.toUpperCase()}',
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 1.2,
                          color: Color(0xFF777777),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        item.nombre,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: Colors.black,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${item.precioBase.toStringAsFixed(0)} €',
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          color: Colors.black,
                        ),
                      ),
                      const SizedBox(height: 8),

                      // Botones de Acción
                      Row(
                        children: [
                          Expanded(
                            child: GestureDetector(
                              onTap: () => _bloc.agregarACesta(item),
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 8),
                                decoration: BoxDecoration(
                                  color: Colors.black,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: const Center(
                                  child: Text(
                                    '+ BOLSA',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 1.0,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          GestureDetector(
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => PantallaProductoDetalle(
                                    idProducto: item.idProducto,
                                    token: widget.token,
                                    habilitarImagenesRed: widget.habilitarImagenesRed,
                                  ),
                                ),
                              );
                            },
                            child: Container(
                              width: 30,
                              height: 30,
                              decoration: BoxDecoration(
                                color: const Color(0xFFF5F4F0),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: const Color(0xFFE0DDD5)),
                              ),
                              child: const Icon(Icons.arrow_forward, size: 14, color: Colors.black),
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
      ),
    );
  }

  Widget _construirEmptyState() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFAF9F6),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE5E0D8)),
      ),
      child: Column(
        children: [
          const Icon(Icons.auto_awesome_outlined, size: 32, color: Color(0xFF8C6D46)),
          const SizedBox(height: 10),
          const Text(
            'Personalización Atelier',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12,
              height: 1.4,
              color: Color(0xFF666666),
            ),
          ),
          const SizedBox(height: 16),
          GestureDetector(
            onTap: widget.alIrACatalogo ?? widget.alIrABuscar,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'EXPLORAR CATÁLOGO COMPLETO →',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirExperienciaAtelier() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'GARANTÍA Y SERVICIOS EXCLUSIVOS',
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.8,
              color: Color(0xFF888888),
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Experiencia Atelier',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Colors.black,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(height: 14),

          // Tarjeta 1: Patronaje a Medida
          _construirTarjetaServicio(
            icono: Icons.architecture_outlined,
            titulo: 'Patronaje a Medida en Serrano',
            descripcion:
                'Ajuste de sastrería gratuito y entallado artesanal en el Flagship de Madrid con cita previa personalizada.',
          ),

          const SizedBox(height: 12),

          // Tarjeta 2: Entrega con Guante Blanco
          _construirTarjetaServicio(
            icono: Icons.local_shipping_outlined,
            titulo: 'Entrega con Guante Blanco',
            descripcion:
                'Envío exprés en 2h o servicio privado de entrega personalizada con cita a domicilio.',
          ),
        ],
      ),
    );
  }

  Widget _construirTarjetaServicio({
    required IconData icono,
    required String titulo,
    required String descripcion,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFAF9F6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFEAE7E1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFE0DDD5)),
            ),
            child: Icon(icono, size: 18, color: const Color(0xFF8C6D46)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  titulo,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Colors.black,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  descripcion,
                  style: const TextStyle(
                    fontSize: 11,
                    height: 1.35,
                    color: Color(0xFF666666),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirBottomNavBar() {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFECEAE6))),
      ),
      child: BottomNavigationBar(
        currentIndex: _indiceNav,
        onTap: (index) {
          setState(() => _indiceNav = index);
          if (index == 1 && widget.alIrABuscar != null) {
            widget.alIrABuscar!();
          } else if (index == 2 && widget.alIrACatalogo != null) {
            widget.alIrACatalogo!();
          } else if (index == 3 && widget.alIrAPerfil != null) {
            widget.alIrAPerfil!();
          }
        },
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: Colors.black,
        unselectedItemColor: const Color(0xFF888888),
        selectedFontSize: 10,
        unselectedFontSize: 10,
        elevation: 0,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: 'Inicio',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.search_outlined),
            activeIcon: Icon(Icons.search),
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
      ),
    );
  }
}
