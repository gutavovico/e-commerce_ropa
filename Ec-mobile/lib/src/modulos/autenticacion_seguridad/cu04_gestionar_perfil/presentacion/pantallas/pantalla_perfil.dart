import 'package:flutter/material.dart';
import '../../datos/modelos/perfil_dto.dart';
import '../bloc/perfil_bloc.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/presentacion/pantallas/pantalla_buscar_productos.dart';
import 'package:ec_mobile/src/modulos/comercial/cu31_reportes_voz/presentacion/pantallas/pantalla_reportes_voz.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/bloc/mis_reservas_bloc.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/pantallas/pantalla_mis_reservas.dart';
import '../../../../../core/empresa_actual.dart';
import 'package:ec_mobile/src/core/moneda.dart';

class PantallaPerfil extends StatefulWidget {
  final String token;
  final PerfilBloc? bloc;
  final MisReservasBloc? misReservasBloc;
  final VoidCallback? alCerrarSesion;

  /// P2-CU02 (CU02 A7): vuelve a la selección de tienda sin cerrar sesión. Solo para clientes.
  final VoidCallback? alCambiarDeTienda;
  final bool habilitarImagenesRed;
  final VoidCallback? alIrAInicio;
  final VoidCallback? alIrABuscar;
  final VoidCallback? alIrACatalogo;
  final bool mostrarBottomNav;

  const PantallaPerfil({
    super.key,
    this.token = 'demo_token_haute_couture',
    this.bloc,
    this.misReservasBloc,
    this.alCerrarSesion,
    this.alCambiarDeTienda,
    this.habilitarImagenesRed = true,
    this.alIrAInicio,
    this.alIrABuscar,
    this.alIrACatalogo,
    this.mostrarBottomNav = true,
  });

  @override
  State<PantallaPerfil> createState() => _PantallaPerfilState();
}

class _PantallaPerfilState extends State<PantallaPerfil> {
  late final PerfilBloc _bloc;
  late final MisReservasBloc _reservasBloc;
  int _tabSeleccionado = 3; // Pestaña 'PERFIL' activa por defecto

  // Datos mock iniciales en caso de carga o demo sin conexión directa
  PerfilClienteDto _perfilMock = const PerfilClienteDto(
    idUsuario: 8402,
    numeroSocio: '#8402',
    email: 'ana.valenzuela@studio.es',
    rol: 'cliente',
    fechaRegistro: '2021-10-15',
    miembroDesde: 'Octubre 2021',
    nombres: 'Ana',
    apellidos: 'Valenzuela',
    telefono: '+34 612 884 901',
    tallaPreferida: '38',
    genero: 'femenino',
    aceptaMarketing: true,
    resumenAtelier: ResumenAtelierDto(
      visitasRegistradas: 32,
      boutiquesVisitadas: 4,
      preferenciaTextil: '100% Seda & Lana',
      estatusMembresia: 'Nivel Platino',
    ),
  );

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? PerfilBloc();
    _bloc.addListener(_alCambiarEstado);
    _bloc.cargarPerfil(widget.token);
    _bloc.cargarHistorialCompras(widget.token);

    _reservasBloc = widget.misReservasBloc ?? MisReservasBloc(token: widget.token);
    _reservasBloc.addListener(_alCambiarEstadoReservas);
    _reservasBloc.cargarMisReservas();
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) {
      _bloc.dispose();
    }
    _reservasBloc.removeListener(_alCambiarEstadoReservas);
    if (widget.misReservasBloc == null) {
      _reservasBloc.dispose();
    }
    super.dispose();
  }

  void _alCambiarEstadoReservas() {
    if (mounted) setState(() {});
  }

  void _abrirMisReservas() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PantallaMisReservas(
          token: widget.token,
          habilitarImagenesRed: widget.habilitarImagenesRed,
        ),
      ),
    );
  }

  int _activasReservas() {
    final estado = _reservasBloc.estado;
    return estado is ReservasListo ? estado.misReservas.resumen.activas : 0;
  }

  String _subtituloReservas() {
    final estado = _reservasBloc.estado;
    if (estado is! ReservasListo) return 'Consultando tus citas…';

    final resumen = estado.misReservas.resumen;
    if (resumen.activas == 0) return 'Sin citas agendadas';

    final proxima = resumen.proxima;
    if (proxima != null) return 'Próxima: ${proxima.nombreSucursal}';
    return resumen.activas == 1 ? '1 reserva activa' : '${resumen.activas} reservas activas';
  }

  void _alCambiarEstado() {
    if (!mounted) return;
    final estado = _bloc.estado;
    if (estado is PerfilCargado) {
      setState(() {
        _perfilMock = estado.perfil;
      });
    } else if (estado is PerfilActualizado) {
      setState(() {
        _perfilMock = estado.perfil;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Información personal actualizada correctamente.'),
          backgroundColor: Colors.black,
          duration: Duration(seconds: 3),
        ),
      );
    } else if (estado is PerfilError) {
      setState(() {});
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(estado.mensaje),
          backgroundColor: Colors.red.shade900,
          duration: const Duration(seconds: 4),
        ),
      );
    } else {
      setState(() {});
    }
  }

  String _tituloPrincipalPedido(PedidoMovilDto pedido) {
    if (pedido.items.isEmpty) {
      return 'Orden ${pedido.numeroComprobante}';
    }
    final primero = pedido.items.first.nombreProducto;
    final restantes = pedido.items.length - 1;
    return restantes > 0 ? '$primero (+$restantes más)' : primero;
  }

  String _descripcionResumenPedido(PedidoMovilDto pedido) {
    if (pedido.items.isEmpty) {
      return 'Sin desglose de artículos';
    }
    final item = pedido.items.first;
    return 'SKU ${item.sku} · Talla ${item.talla} · ${item.color} · Cant. ${item.cantidad}';
  }

  String _etiquetaEstadoPedido(String estado) {
    switch (estado) {
      case 'pagada':
        return 'PAGADO';
      case 'pendiente':
        return 'PENDIENTE DE PAGO';
      case 'anulada':
        return 'ANULADO';
      case 'devuelta':
        return 'DEVUELTO';
      default:
        return estado.toUpperCase();
    }
  }

  void _abrirComprobanteDigital(PedidoMovilDto pedido) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  '${EmpresaActual.instancia.marca.toUpperCase()} · COMPROBANTE DIGITAL',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.2,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  pedido.numeroComprobante,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'monospace',
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade50,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Estado: ${_etiquetaEstadoPedido(pedido.estado)}',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Boutique / Entrega: ${pedido.nombreSucursalRetiro ?? pedido.nombreSucursal ?? 'Atelier Digital'}',
                        style: const TextStyle(fontSize: 11, color: Colors.black87),
                      ),
                      if (pedido.metodoPago != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Método de pago: ${pedido.metodoPago}',
                          style: const TextStyle(fontSize: 11, color: Colors.black87),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                const Text(
                  'ARTÍCULOS ADQUIRIDOS',
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.grey),
                ),
                const SizedBox(height: 8),
                ...pedido.items.map(
                  (item) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item.nombreProducto,
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                              ),
                              Text(
                                'Talla ${item.talla} · ${item.color} · Cant. ${item.cantidad}',
                                style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          formatoImporte(item.subtotalLinea),
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ),
                const Divider(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Total Comprobante',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    Text(
                      formatoImporte(pedido.total),
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  height: 44,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('CERRAR COMPROBANTE'),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _abrirModalEdicion() {
    final nombresController = TextEditingController(text: _perfilMock.nombres);
    final apellidosController = TextEditingController(text: _perfilMock.apellidos);
    final telefonoController = TextEditingController(text: _perfilMock.telefono ?? '');
    String tallaSeleccionada = _perfilMock.tallaPreferida ?? '38';
    bool aceptaMarketing = _perfilMock.aceptaMarketing;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (modalContext, setModalState) {
            return Container(
              padding: EdgeInsets.only(
                top: 24,
                left: 20,
                right: 20,
                bottom: MediaQuery.of(modalContext).viewInsets.bottom + 24,
              ),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Handle superior
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.grey.shade300,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'EDITAR INFORMACIÓN PERSONAL',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.0,
                      ),
                    ),
                    const Text(
                      'Atelier VIP · Datos de Cuenta',
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 20),

                    // Nombres
                    TextField(
                      controller: nombresController,
                      decoration: InputDecoration(
                        labelText: 'Nombres',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Apellidos
                    TextField(
                      controller: apellidosController,
                      decoration: InputDecoration(
                        labelText: 'Apellidos',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Teléfono
                    TextField(
                      controller: telefonoController,
                      decoration: InputDecoration(
                        labelText: 'Teléfono',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Talla preferida
                    DropdownButtonFormField<String>(
                      initialValue: tallaSeleccionada,
                      decoration: InputDecoration(
                        labelText: 'Talla de Alta Costura',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'XS', child: Text('Talla XS')),
                        DropdownMenuItem(value: 'S', child: Text('Talla S')),
                        DropdownMenuItem(value: 'M', child: Text('Talla M')),
                        DropdownMenuItem(value: 'L', child: Text('Talla L')),
                        DropdownMenuItem(value: 'XL', child: Text('Talla XL')),
                        DropdownMenuItem(value: '36', child: Text('Talla 36')),
                        DropdownMenuItem(value: '38', child: Text('Talla 38')),
                        DropdownMenuItem(value: '40', child: Text('Talla 40')),
                        DropdownMenuItem(value: '42', child: Text('Talla 42')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => tallaSeleccionada = val);
                        }
                      },
                    ),
                    const SizedBox(height: 16),

                    // Checkbox marketing
                    Row(
                      children: [
                        Checkbox(
                          value: aceptaMarketing,
                          activeColor: Colors.black,
                          onChanged: (val) {
                            setModalState(() => aceptaMarketing = val ?? true);
                          },
                        ),
                        const Expanded(
                          child: Text(
                            'Deseo recibir avances exclusivos y cápsulas privadas.',
                            style: TextStyle(fontSize: 12, color: Colors.black87),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Botón Guardar
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        onPressed: () {
                          final updateDto = PerfilClienteUpdateDto(
                            nombres: nombresController.text.trim(),
                            apellidos: apellidosController.text.trim(),
                            telefono: telefonoController.text.trim().isNotEmpty
                                ? telefonoController.text.trim()
                                : null,
                            tallaPreferida: tallaSeleccionada,
                            aceptaMarketing: aceptaMarketing,
                          );
                          _bloc.actualizarPerfil(widget.token, updateDto);
                          Navigator.pop(ctx);
                        },
                        child: const Text(
                          'GUARDAR CAMBIOS',
                          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.0),
                        ),
                      ),
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

  @override
  Widget build(BuildContext context) {
    final perfil = _perfilMock;

    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F7),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: Colors.white,
        elevation: 0.5,
        title: Text(
          '${EmpresaActual.instancia.marca.toUpperCase()}  |  PERFIL',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.0,
            color: Colors.black,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none, color: Colors.black),
            onPressed: () {},
          ),
          Stack(
            alignment: Alignment.center,
            children: [
              IconButton(
                icon: const Icon(Icons.shopping_bag_outlined, color: Colors.black),
                onPressed: () {},
              ),
              Positioned(
                right: 8,
                top: 8,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: Colors.black,
                    shape: BoxShape.circle,
                  ),
                  child: const Text(
                    '3',
                    style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(right: 16.0, left: 4.0),
            child: CircleAvatar(
              radius: 14,
              backgroundColor: Colors.grey.shade200,
              backgroundImage: widget.habilitarImagenesRed
                  ? const NetworkImage(
                      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80',
                    )
                  : null,
              child: widget.habilitarImagenesRed
                  ? null
                  : const Icon(Icons.person, size: 14, color: Colors.black87),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Subtítulo Maison & Membresía
            const Text(
              'MAISON & MEMBRESÍA',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.5,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 4),

            // Titular Mi Cuenta + Badge Atelier VIP
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Mi Cuenta',
                  style: TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w800,
                    color: Colors.black,
                    letterSpacing: -0.5,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF5EFEB),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Text(
                    '• ATELIER VIP',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF8A6D3B),
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 1. Tarjeta Principal de Perfil
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.grey.shade200),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.02),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Avatar con botón de cámara
                      Stack(
                        children: [
                          Container(
                            width: 76,
                            height: 76,
                            decoration: BoxDecoration(
                              color: Colors.grey.shade200,
                              borderRadius: BorderRadius.circular(16),
                              image: widget.habilitarImagenesRed
                                  ? const DecorationImage(
                                      image: NetworkImage(
                                        'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
                                      ),
                                      fit: BoxFit.cover,
                                    )
                                  : null,
                            ),
                            child: widget.habilitarImagenesRed
                                ? null
                                : const Icon(Icons.person, size: 36, color: Colors.grey),
                          ),
                          Positioned(
                            bottom: 2,
                            right: 2,
                            child: Container(
                              padding: const EdgeInsets.all(4),
                              decoration: const BoxDecoration(
                                color: Colors.black,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.camera_alt, color: Colors.white, size: 12),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 14),

                      // Datos de Usuario
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'SOCIO PRIVÉ ${perfil.numeroSocio}',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.grey,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                                Text(
                                  'Desde ${perfil.miembroDesde.split(' ').last}',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: Colors.grey,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${perfil.nombres} ${perfil.apellidos}',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.black,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              perfil.email,
                              style: TextStyle(
                                fontSize: 11,
                                color: Colors.grey.shade600,
                              ),
                            ),
                            const SizedBox(height: 8),

                            // Botón Editar Información
                            InkWell(
                              onTap: _abrirModalEdicion,
                              borderRadius: BorderRadius.circular(12),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade100,
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: Colors.grey.shade300),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.tune, size: 12, color: Colors.black87),
                                    SizedBox(width: 6),
                                    Text(
                                      'Editar Información',
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                        color: Colors.black87,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Banda de Métricas en 3 Columnas
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF6F6F6),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            children: [
                              Text(
                                '${perfil.resumenAtelier.visitasRegistradas}',
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 2),
                              const Text('VISITAS', style: TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.w600)),
                            ],
                          ),
                        ),
                        Container(height: 24, width: 1, color: Colors.grey.shade300),
                        Expanded(
                          child: Column(
                            children: [
                              Text(
                                '${perfil.resumenAtelier.boutiquesVisitadas}',
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 2),
                              const Text('BOUTIQUES', style: TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.w600)),
                            ],
                          ),
                        ),
                        Container(height: 24, width: 1, color: Colors.grey.shade300),
                        const Expanded(
                          child: Column(
                            children: [
                              Text(
                                '100%',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              SizedBox(height: 2),
                              Text('SEDA & LANA', style: TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.w600)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // 2. Tarjetas Gemelas Wishlist y Bolsa
            Row(
              children: [
                // Wishlist
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF7F1E8),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(Icons.favorite_border, color: Color(0xFF8A6D3B), size: 16),
                            ),
                            const Text(
                              'WISHLIST',
                              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Colors.grey),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        const Text(
                          '12',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                        ),
                        const Text(
                          'Prendas guardadas',
                          style: TextStyle(fontSize: 11, color: Colors.grey),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'EXPLORAR PIEZAS →',
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),

                // Mis Reservas (CU13/CU14) — antes "Bolsa", con el literal fijo "3 Artículos ·
                // 1.250" que no reflejaba la bolsa real. Ver CHANGELOG.
                Expanded(
                  child: GestureDetector(
                    onTap: _abrirMisReservas,
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.black,
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Icon(Icons.calendar_today_outlined, color: Colors.white, size: 18),
                              Text(
                                'RESERVAS',
                                style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Colors.grey),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            '${_activasReservas()}',
                            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                          Text(
                            _subtituloReservas(),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 11, color: Colors.grey),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'VER MIS RESERVAS →',
                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 0.5),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // 3. Registro Histórico de Compras y Pedidos (CU17)
            const Text(
              'REGISTRO HISTÓRICO',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.5, color: Colors.grey),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Compras Anteriores y Pedidos',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black),
                ),
                Text(
                  '${_bloc.historial.pedidosCompletados} ${_bloc.historial.pedidosCompletados == 1 ? 'pedido completado' : 'pedidos completados'}',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              ],
            ),
            const SizedBox(height: 12),

            if (_bloc.cargandoHistorial)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: const Center(
                  child: Text(
                    'Consultando tu historial de compras...',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ),
              )
            else if (_bloc.pedidos.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Column(
                  children: [
                    const Text(
                      'Sin compras registradas',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.black87),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Tus adquisiciones en boutique y plataforma digital aparecerán aquí.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                    ),
                  ],
                ),
              )
            else
              // Lista de Pedidos Reales
              ..._bloc.pedidos.map((pedido) {
                final primerItem = pedido.items.isNotEmpty ? pedido.items.first : null;
                final imagenUrl = primerItem?.imagenUrl;
                final tallaEtiqueta = primerItem != null ? 'T. ${primerItem.talla}' : 'ATELIER';

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Column(
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Imagen con overlay de talla
                          Stack(
                            children: [
                              Container(
                                width: 70,
                                height: 90,
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade200,
                                  borderRadius: BorderRadius.circular(12),
                                  image: (widget.habilitarImagenesRed && imagenUrl != null && imagenUrl.isNotEmpty)
                                      ? DecorationImage(
                                          image: NetworkImage(imagenUrl),
                                          fit: BoxFit.cover,
                                        )
                                      : null,
                                ),
                                child: (widget.habilitarImagenesRed && imagenUrl != null && imagenUrl.isNotEmpty)
                                    ? null
                                    : const Icon(Icons.checkroom, color: Colors.grey, size: 28),
                              ),
                              Positioned(
                                bottom: 4,
                                right: 4,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.black87,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    tallaEtiqueta,
                                    style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(width: 12),

                          // Info del Pedido
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        _tituloPrincipalPedido(pedido),
                                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                    Text(
                                      formatoImporte(pedido.total),
                                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  _descripcionResumenPedido(pedido),
                                  style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  children: [
                                    const Icon(Icons.storefront, size: 12, color: Colors.grey),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Text(
                                        pedido.nombreSucursalRetiro ?? pedido.nombreSucursal ?? 'Atelier Digital',
                                        style: const TextStyle(fontSize: 10, color: Colors.black87),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Text(
                                      '${pedido.fechaVenta.split('T').first} · ${_etiquetaEstadoPedido(pedido.estado)}',
                                      style: const TextStyle(fontSize: 10, color: Colors.grey),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      const Divider(height: 1),
                      const SizedBox(height: 8),

                      // Fila Inferior: Referencia y Botón Factura
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            pedido.numeroComprobante,
                            style: const TextStyle(fontSize: 10, color: Colors.grey, fontFamily: 'monospace'),
                          ),
                          InkWell(
                            onTap: () => _abrirComprobanteDigital(pedido),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.grey.shade100,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Row(
                                children: [
                                  Icon(Icons.receipt_long, size: 12, color: Colors.black87),
                                  SizedBox(width: 4),
                                  Text(
                                    'VER FACTURA / TICKET',
                                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.black87),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              }),
            const SizedBox(height: 16),

            // 4. Preferencias y Configuración
            const Text(
              'Preferencias y Configuración',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black),
            ),
            const SizedBox(height: 10),

            _construirOpcionConfiguracion(
              icono: Icons.location_on_outlined,
              titulo: 'Direcciones de entrega',
              subtitulo: 'Paseo de la Castellana 112, Madrid',
            ),
            _construirOpcionConfiguracion(
              icono: Icons.credit_card_outlined,
              titulo: 'Métodos de pago',
              subtitulo: 'Mastercard Privée •••• 9214',
            ),
            _construirOpcionConfiguracion(
              icono: Icons.support_agent_outlined,
              titulo: 'Personal Shopper Asignado',
              subtitulo: 'Lucía M. · Boutique Serrano',
            ),
            _construirOpcionConfiguracion(
              icono: Icons.insights_outlined,
              titulo: 'Reportes y Consultas por Voz',
              subtitulo: 'Centro ejecutivo de analítica, filtros y comandos de voz',
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PantallaReportesVoz(token: widget.token),
                  ),
                );
              },
            ),
            const SizedBox(height: 20),

            // 4b. Cambiar de tienda (P2-CU02)
            if (widget.alCambiarDeTienda != null) ...[
              SizedBox(
                width: double.infinity,
                height: 48,
                child: OutlinedButton(
                  key: const Key('perfil_cambiar_tienda'),
                  style: OutlinedButton.styleFrom(
                    backgroundColor: Colors.white,
                    side: BorderSide(color: Colors.grey.shade300),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  onPressed: widget.alCambiarDeTienda,
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.storefront_outlined, size: 16, color: Colors.black87),
                      SizedBox(width: 8),
                      Flexible(
                        child: Text(
                          'CAMBIAR DE TIENDA',
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.0,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],

            // 5. Botón de Cierre de Sesión Seguro
            SizedBox(
              width: double.infinity,
              height: 48,
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  backgroundColor: Colors.white,
                  side: BorderSide(color: Colors.grey.shade300),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                onPressed: () {
                  if (widget.alCerrarSesion != null) {
                    widget.alCerrarSesion!();
                  } else {
                    LoginRepositorioImpl().cerrarSesion(widget.token);
                    Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(builder: (_) => const PantallaLogin()),
                      (route) => false,
                    );
                  }
                },
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.logout, size: 16, color: Colors.black87),
                    SizedBox(width: 8),
                    Text(
                      'CERRAR SESIÓN',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.0,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Metadatos de Sistema
            Center(
              child: Text(
                '${EmpresaActual.instancia.marca.toUpperCase()} • VERSIÓN 4.12 ATELIER CLIENT',
                style: TextStyle(fontSize: 9, color: Colors.grey, letterSpacing: 0.8),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: widget.mostrarBottomNav
          ? BottomNavigationBar(
              currentIndex: _tabSeleccionado,
              onTap: (index) {
                if (index == 0 && widget.alIrAInicio != null) {
                  widget.alIrAInicio!();
                } else if (index == 1) {
                  if (widget.alIrABuscar != null) {
                    widget.alIrABuscar!();
                  } else {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => PantallaBuscarProductos(
                          alIrAPerfil: () => Navigator.of(context).pop(),
                          alIrAInicio: () => Navigator.of(context).pop(),
                        ),
                      ),
                    );
                  }
                } else if (index == 2 && widget.alIrACatalogo != null) {
                  widget.alIrACatalogo!();
                } else {
                  setState(() {
                    _tabSeleccionado = index;
                  });
                }
              },
              type: BottomNavigationBarType.fixed,
              backgroundColor: Colors.white,
              selectedItemColor: Colors.black,
              unselectedItemColor: Colors.grey,
              selectedLabelStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5),
              unselectedLabelStyle: const TextStyle(fontSize: 10, letterSpacing: 0.5),
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.home_outlined),
                  label: 'INICIO',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.search),
                  label: 'BUSCAR',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.grid_view_outlined),
                  label: 'CATÁLOGO',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.person_outline),
                  label: 'PERFIL',
                ),
              ],
            )
          : null,
    );
  }

  Widget _construirOpcionConfiguracion({
    required IconData icono,
    required String titulo,
    required String subtitulo,
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icono, size: 18, color: Colors.black87),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    titulo,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    subtitulo,
                    style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, size: 18, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}
