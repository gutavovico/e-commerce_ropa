import 'package:flutter/material.dart';
import '../modulos/autenticacion_seguridad/cu04_gestionar_perfil/dominio/repositorios/perfil_repositorio.dart';
import '../modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart';
import '../modulos/catalogo/cu05_consultar_catalogo/presentacion/pantallas/pantalla_catalogo.dart';
import '../modulos/catalogo/cu06_buscar_filtrar/presentacion/pantallas/pantalla_buscar_productos.dart';
import '../modulos/catalogo/cu18_recomendaciones/presentacion/pantallas/pantalla_inicio.dart';
import '../modulos/catalogo/cu07_detalle_producto/presentacion/pantallas/pantalla_producto_detalle.dart';
import '../modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/colecciones_screen.dart';
import '../modulos/catalogo/cu19_asistente_chatbot/presentacion/bloc/chatbot_bloc.dart';
import '../modulos/catalogo/cu19_asistente_chatbot/presentacion/pantallas/pantalla_asistente_estilo.dart';
import '../modulos/compras_pagos/cu11_gestionar_carrito/presentacion/pantallas/shopping_bag_screen.dart';

/// Contenedor Principal (Hub) que orquesta las 4 pantallas raíz del sistema FashionStore:
/// - Índice 0: Inicio (/inicio - Atelier & Recomendaciones)
/// - Índice 1: Buscar (/buscar - Catálogo Búsqueda y Filtros)
/// - Índice 2: Catálogo (/catalogo - Catálogo canónico CU05 en preparación)
/// - Índice 3: Perfil (/perfil - Mi Cuenta & Pedidos)
///
/// Conforme a la Directriz Arquitectónica Global Hub-and-Spoke, el Scaffold de este Hub
/// posee de forma exclusiva la barra de navegación inferior persistente (BottomNavigationBar),
/// permitiendo alternar instantáneamente entre las 4 vistas sin corromper la pila de rutas.
class PantallaPrincipalHub extends StatefulWidget {
  final String token;
  final String? nombreUsuario;
  final VoidCallback? alCerrarSesion;

  /// P2-CU02: vuelve a la selección de tienda (solo clientes).
  final VoidCallback? alCambiarDeTienda;
  final int indiceInicial;
  final bool habilitarImagenesRed;

  const PantallaPrincipalHub({
    super.key,
    required this.token,
    this.nombreUsuario,
    this.alCerrarSesion,
    this.alCambiarDeTienda,
    this.indiceInicial = 0,
    this.habilitarImagenesRed = true,
  });

  @override
  State<PantallaPrincipalHub> createState() => _PantallaPrincipalHubState();
}

class _PantallaPrincipalHubState extends State<PantallaPrincipalHub> {
  late int _indiceActual;
  late String _nombreUsuarioActual;
  late final ChatbotBloc _chatbotBloc;

  @override
  void initState() {
    super.initState();
    _indiceActual = widget.indiceInicial;
    _nombreUsuarioActual = widget.nombreUsuario ?? '';
    _chatbotBloc = ChatbotBloc.obtenerInstanciaCompartida(token: widget.token);

    if (_nombreUsuarioActual.isEmpty && widget.token.isNotEmpty) {
      _cargarNombreUsuario(widget.token);
    }
  }

  @override
  void dispose() {
    ChatbotBloc.purgarSesion();
    super.dispose();
  }

  Future<void> _cargarNombreUsuario(String token) async {
    try {
      final repo = PerfilRepositorioImpl();
      final perfil = await repo.obtenerPerfil(token);
      final nombreCompleto = '${perfil.nombres} ${perfil.apellidos}'.trim();
      if (nombreCompleto.isNotEmpty && mounted) {
        setState(() {
          _nombreUsuarioActual = nombreCompleto;
        });
      }
    } catch (_) {
      // Si falla o no hay conectividad, conserva el valor actual
    }
  }

  void _cambiarTab(int nuevoIndice) {
    if (nuevoIndice != _indiceActual) {
      setState(() {
        _indiceActual = nuevoIndice;
      });
    }
  }

  /// Abre la Bolsa de Compra como pantalla hoja (`Navigator.push`).
  ///
  /// Se apila sobre el hub en lugar de ocupar una pestaña: conforme a la directriz
  /// Hub-and-Spoke sólo existen 4 pantallas raíz, y la bolsa es una vista secundaria.
  void _abrirBolsa() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ShoppingBagScreen(
          token: widget.token,
          habilitarImagenesRed: widget.habilitarImagenesRed,
        ),
      ),
    );
  }

  Future<void> _abrirAsistente() async {
    _chatbotBloc.marcarChatAbierto();
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PantallaAsistenteEstilo(
          token: widget.token,
          habilitarImagenesRed: widget.habilitarImagenesRed,
          bloc: _chatbotBloc,
        ),
      ),
    );
    _chatbotBloc.marcarChatCerrado();
  }

  void _abrirColecciones() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ColeccionesScreen(
          token: widget.token,
          alIrAInicio: () => Navigator.of(context).pop(),
          alSeleccionarProducto: (prod) {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => PantallaProductoDetalle(
                  idProducto: prod.idProducto,
                  token: widget.token,
                  habilitarImagenesRed: widget.habilitarImagenesRed,
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pestanas = <Widget>[
      // 0. Inicio
      PantallaInicio(
        token: widget.token,
        nombreUsuario: _nombreUsuarioActual,
        mostrarBottomNav: false,
        habilitarImagenesRed: widget.habilitarImagenesRed,
        alIrABuscar: () => _cambiarTab(1),
        alIrACatalogo: () => _cambiarTab(2),
        alIrAPerfil: () => _cambiarTab(3),
        alIrAColecciones: _abrirColecciones,
        alIrABolsa: _abrirBolsa,
      ),

      // 1. Buscar
      PantallaBuscarProductos(
        token: widget.token,
        mostrarBottomNav: false,
        habilitarImagenesRed: widget.habilitarImagenesRed,
        alIrAInicio: () => _cambiarTab(0),
        alIrACatalogo: () => _cambiarTab(2),
        alIrAPerfil: () => _cambiarTab(3),
      ),

      // 2. Catálogo (CU05: Consultar Catálogo de Prendas)
      PantallaCatalogo(
        token: widget.token,
        mostrarBottomNav: false,
        habilitarImagenesRed: widget.habilitarImagenesRed,
        alIrAInicio: () => _cambiarTab(0),
        alIrABuscar: () => _cambiarTab(1),
        alIrAPerfil: () => _cambiarTab(3),
      ),

      // 3. Perfil
      PantallaPerfil(
        token: widget.token,
        mostrarBottomNav: false,
        habilitarImagenesRed: widget.habilitarImagenesRed,
        alIrAInicio: () => _cambiarTab(0),
        alIrABuscar: () => _cambiarTab(1),
        alIrACatalogo: () => _cambiarTab(2),
        alCerrarSesion: () {
          ChatbotBloc.purgarSesion();
          widget.alCerrarSesion?.call();
        },
        alCambiarDeTienda: widget.alCambiarDeTienda == null
            ? null
            : () {
                ChatbotBloc.purgarSesion();
                widget.alCambiarDeTienda!.call();
              },
      ),
    ];

    return Scaffold(
      backgroundColor: Colors.white,
      body: IndexedStack(
        index: _indiceActual,
        children: pestanas,
      ),
      floatingActionButton: AnimatedBuilder(
        animation: _chatbotBloc,
        builder: (context, _) {
          return Stack(
            clipBehavior: Clip.none,
            children: [
              FloatingActionButton(
                onPressed: _abrirAsistente,
                backgroundColor: const Color(0xFF1A1A1A),
                foregroundColor: const Color(0xFFC5A880),
                elevation: 6,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(28),
                  side: const BorderSide(color: Color(0xFFC5A880), width: 1.5),
                ),
                tooltip: 'Asistente de Estilo',
                child: const Icon(Icons.auto_awesome),
              ),
              if (_chatbotBloc.mensajesNoLeidos)
                Positioned(
                  top: 0,
                  right: 0,
                  child: Container(
                    width: 14,
                    height: 14,
                    decoration: BoxDecoration(
                      color: const Color(0xFFAD8C63), // Camel dorado alta costura
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                      boxShadow: const [
                        BoxShadow(
                          color: Colors.black26,
                          blurRadius: 3,
                          offset: Offset(0, 1),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceActual,
        onTap: _cambiarTab,
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: Colors.black,
        unselectedItemColor: const Color(0xFF777777),
        selectedLabelStyle: const TextStyle(
          fontFamily: 'Outfit',
          fontSize: 10,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
        unselectedLabelStyle: const TextStyle(
          fontFamily: 'Outfit',
          fontSize: 10,
          letterSpacing: 0.5,
        ),
        elevation: 8,
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
