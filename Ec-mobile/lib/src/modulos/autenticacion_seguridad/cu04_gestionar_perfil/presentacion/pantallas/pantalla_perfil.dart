import 'package:flutter/material.dart';
import '../../datos/modelos/perfil_dto.dart';
import '../bloc/perfil_bloc.dart';

class PantallaPerfil extends StatefulWidget {
  final String token;
  final PerfilBloc? bloc;
  final VoidCallback? alCerrarSesion;
  final bool habilitarImagenesRed;

  const PantallaPerfil({
    super.key,
    this.token = 'demo_token_haute_couture',
    this.bloc,
    this.alCerrarSesion,
    this.habilitarImagenesRed = true,
  });

  @override
  State<PantallaPerfil> createState() => _PantallaPerfilState();
}

class _PantallaPerfilState extends State<PantallaPerfil> {
  late final PerfilBloc _bloc;
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

  final List<PedidoMovilDto> _pedidos = const [
    PedidoMovilDto(
      id: 'PED-01',
      titulo: 'Vestido plisado en seda',
      origen: 'Flagship Serrano (Madrid)',
      descripcion: 'Seda natural mora 100% · Talla 38',
      talla: 'T. 38',
      color: 'Marfil',
      precio: 890,
      fecha: '14 Oct 2024 · ENTREGADO EN TIENDA',
      estado: 'ENTREGADO',
      referencia: 'REF: MAD-77894',
      imagen: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=400&q=80',
    ),
    PedidoMovilDto(
      id: 'PED-02',
      titulo: 'Blazer estructurado lan...',
      origen: 'Boutique Saint-Honoré (París)',
      descripcion: 'Lana virgen italiana · Talla 40',
      talla: 'T. 40',
      color: 'Camel',
      precio: 740,
      fecha: '28 Sep 2024 · A DOMICILIO',
      estado: 'ENTREGADO',
      referencia: 'REF: PAR-20411',
      imagen: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=400&q=80',
    ),
    PedidoMovilDto(
      id: 'PED-03',
      titulo: 'Blusa de satén fluido ma...',
      origen: 'Madrid Central Hub (Online)',
      descripcion: 'Satén de seda marfil · Talla 38',
      talla: 'T. 38',
      color: 'Marfil',
      precio: 310,
      fecha: '10 Ago 2024 · ENTREGADO',
      estado: 'ENTREGADO',
      referencia: 'REF: ONL-09552',
      imagen: 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=400&q=80',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? PerfilBloc();
    _bloc.addListener(_alCambiarEstado);
    _bloc.cargarPerfil(widget.token);
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) {
      _bloc.dispose();
    }
    super.dispose();
  }

  void _alCambiarEstado() {
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
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(estado.mensaje),
          backgroundColor: Colors.red.shade900,
          duration: const Duration(seconds: 4),
        ),
      );
    }
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
        backgroundColor: Colors.white,
        elevation: 0.5,
        title: const Text(
          'FASHION STORE  |  PERFIL',
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

                // Bolsa
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Icon(Icons.shopping_bag_outlined, color: Colors.white, size: 20),
                            Text(
                              'BOLSA',
                              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Colors.grey),
                            ),
                          ],
                        ),
                        SizedBox(height: 10),
                        Text(
                          '3',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                        ),
                        Text(
                          'Artículos · 1.250 €',
                          style: TextStyle(fontSize: 11, color: Colors.grey),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'IR AL CHECKOUT →',
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 0.5),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // 3. Registro Histórico de Compras y Pedidos
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
                  '3 pedidos',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Lista de Pedidos
            ..._pedidos.map((pedido) {
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
                                image: widget.habilitarImagenesRed
                                    ? DecorationImage(
                                        image: NetworkImage(pedido.imagen),
                                        fit: BoxFit.cover,
                                      )
                                    : null,
                              ),
                              child: widget.habilitarImagenesRed
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
                                  pedido.talla,
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
                                      pedido.titulo,
                                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  Text(
                                    '${pedido.precio} €',
                                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 2),
                              Text(
                                pedido.descripcion,
                                style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  const Icon(Icons.storefront, size: 12, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Expanded(
                                    child: Text(
                                      pedido.origen,
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
                                    pedido.fecha,
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
                          pedido.referencia,
                          style: const TextStyle(fontSize: 10, color: Colors.grey, fontFamily: 'monospace'),
                        ),
                        InkWell(
                          onTap: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Descargando comprobante ${pedido.referencia}...'),
                                duration: const Duration(seconds: 2),
                              ),
                            );
                          },
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
            const SizedBox(height: 20),

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
                    Navigator.pop(context);
                  }
                },
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.logout, size: 16, color: Colors.black87),
                    SizedBox(width: 8),
                    Text(
                      'CERRAR SESIÓN SEGURA',
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
            const Center(
              child: Text(
                'FASHION STORE • VERSIÓN 4.12 ATELIER CLIENT',
                style: TextStyle(fontSize: 9, color: Colors.grey, letterSpacing: 0.8),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tabSeleccionado,
        onTap: (index) {
          setState(() {
            _tabSeleccionado = index;
          });
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
      ),
    );
  }

  Widget _construirOpcionConfiguracion({
    required IconData icono,
    required String titulo,
    required String subtitulo,
  }) {
    return Container(
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
    );
  }
}
