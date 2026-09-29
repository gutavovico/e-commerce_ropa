import 'package:flutter/material.dart';

import '../../datos/modelos/reserva_dto.dart';
import '../bloc/mis_reservas_bloc.dart';
import '../widgets/hoja_cancelar_reserva.dart';

/// Pantalla de reservas de CU13/CU14, abierta desde el Perfil.
///
/// Es una vista secundaria del patrón Hub-and-Spoke: se abre con `Navigator.push`, su `Scaffold`
/// **no declara la barra de navegación de 4 pestañas** y su `AppBar` incluye retorno explícito
/// (`BackButton`).
class PantallaMisReservas extends StatefulWidget {
  final String token;
  final MisReservasBloc? bloc;
  final bool habilitarImagenesRed;

  const PantallaMisReservas({
    super.key,
    required this.token,
    this.bloc,
    this.habilitarImagenesRed = true,
  });

  @override
  State<PantallaMisReservas> createState() => _PantallaMisReservasState();
}

class _PantallaMisReservasState extends State<PantallaMisReservas> {
  late final MisReservasBloc _bloc;
  bool _pestanaHistorial = false;

  static const Map<String, String> _etiquetasEstado = {
    'pendiente': 'Pendiente de confirmación',
    'confirmada': 'Confirmada',
    'en_atencion': 'En atención',
    'atendida': 'Atendida',
    'cancelada': 'Cancelada',
    'vencida': 'Vencida',
  };

  static const Map<String, Color> _coloresFondoBadge = {
    'pendiente': Color(0xFFEDEEF0),
    'confirmada': Color(0xFFECDECB),
    'en_atencion': Color(0xFF1B1C1D),
    'atendida': Color(0xFFE8E8EA),
    'cancelada': Color(0xFFFFDAD6),
    'vencida': Color(0xFFD9DADC),
  };

  static const Map<String, Color> _coloresTextoBadge = {
    'pendiente': Color(0xFF45474A),
    'confirmada': Color(0xFF6B6152),
    'en_atencion': Colors.white,
    'atendida': Color(0xFF1A1C1D),
    'cancelada': Color(0xFF93000A),
    'vencida': Color(0xFF75777A),
  };

  static const List<String> _dias = [
    'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
  ];
  static const List<String> _meses = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
  ];

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? MisReservasBloc(token: widget.token);
    _bloc.addListener(_alCambiarEstado);
    _bloc.cargarMisReservas();
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) _bloc.dispose();
    super.dispose();
  }

  void _alCambiarEstado() {
    if (mounted) setState(() {});
  }

  Future<void> _abrirCancelacion(ReservaDto reserva) async {
    _bloc.limpiarErrorCancelacion();
    await mostrarHojaCancelarReserva(context: context, reserva: reserva, bloc: _bloc);
  }

  String _formatearFecha(DateTime? fecha) {
    if (fecha == null) return '';
    final local = fecha.toLocal();
    final texto = '${_dias[local.weekday - 1]} ${local.day} de ${_meses[local.month - 1]}';
    return texto[0].toUpperCase() + texto.substring(1);
  }

  String _formatearHora(DateTime? fecha) {
    if (fecha == null) return '';
    final local = fecha.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  Color _colorDesdeHex(String? hexString) {
    if (hexString == null || hexString.isEmpty) return Colors.grey.shade200;
    try {
      final limpio = hexString.replaceAll('#', '');
      return Color(int.parse('FF$limpio', radix: 16));
    } catch (_) {
      return Colors.grey.shade200;
    }
  }

  String _textoResumen(ResumenReservasDto resumen) {
    final base =
        resumen.activas == 1 ? '1 reserva activa' : '${resumen.activas} reservas activas';
    final proxima = resumen.proxima;
    if (proxima != null) {
      return '$base · Próxima: ${_formatearFecha(proxima.fechaHoraAtencion)} en '
          '${proxima.nombreSucursal}';
    }
    return base;
  }

  @override
  Widget build(BuildContext context) {
    final estado = _bloc.estado;

    return Scaffold(
      backgroundColor: const Color(0xFFFAFAFB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0.5,
        leading: const BackButton(color: Colors.black),
        title: const Text(
          'MIS RESERVAS',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
            color: Colors.black,
          ),
        ),
      ),
      body: switch (estado) {
        ReservasInicial() || ReservasCargando() => _construirCargando(),
        ReservasError(:final mensaje) => _construirError(mensaje),
        ReservasListo(:final misReservas) => _construirContenido(misReservas),
      },
    );
  }

  Widget _construirCargando() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 2,
      itemBuilder: (_, _) => Container(
        margin: const EdgeInsets.only(bottom: 16),
        height: 160,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.grey.shade200),
        ),
      ),
    );
  }

  Widget _construirError(String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => _bloc.cargarMisReservas(),
              child: const Text(
                'REINTENTAR',
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirContenido(MisReservasDto datos) {
    final lista = _pestanaHistorial ? datos.historial : datos.proximas;

    return RefreshIndicator(
      onRefresh: () => _bloc.cargarMisReservas(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            _textoResumen(datos.resumen),
            style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _construirPestana(
                  'Próximas (${datos.proximas.length})',
                  !_pestanaHistorial,
                  () => setState(() => _pestanaHistorial = false),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _construirPestana(
                  'Historial (${datos.historial.length})',
                  _pestanaHistorial,
                  () => setState(() => _pestanaHistorial = true),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (lista.isEmpty) _construirVacio() else ...lista.map(_construirTarjetaReserva),
        ],
      ),
    );
  }

  Widget _construirPestana(String texto, bool activa, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: activa ? Colors.black : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: activa ? Colors.black : Colors.grey.shade200),
        ),
        child: Text(
          texto,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.6,
            color: activa ? Colors.white : Colors.grey.shade600,
          ),
        ),
      ),
    );
  }

  Widget _construirVacio() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 48, horizontal: 24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Text(
        _pestanaHistorial
            ? 'No hay reservas en tu historial todavía.'
            : 'Aún no tienes citas de probador agendadas.',
        textAlign: TextAlign.center,
        style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
      ),
    );
  }

  Widget _construirTarjetaReserva(ReservaDto reserva) {
    final colorFondoBadge = _coloresFondoBadge[reserva.estado] ?? _coloresFondoBadge['pendiente']!;
    final colorTextoBadge = _coloresTextoBadge[reserva.estado] ?? _coloresTextoBadge['pendiente']!;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  reserva.codigoReserva,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.grey.shade400,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: colorFondoBadge,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  _etiquetasEstado[reserva.estado] ?? reserva.estado,
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                    color: colorTextoBadge,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _formatearFecha(reserva.fechaHoraAtencion),
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    Text(
                      '${_formatearHora(reserva.fechaHoraAtencion)} h',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'BOUTIQUE',
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.6,
                        color: Colors.grey.shade400,
                      ),
                    ),
                    Text(
                      reserva.sucursal.nombre,
                      textAlign: TextAlign.right,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                    Text(
                      reserva.sucursal.direccion,
                      textAlign: TextAlign.right,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const Divider(height: 24),
          ...reserva.items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(12),
                      image: (widget.habilitarImagenesRed && item.imagenUrl != null)
                          ? DecorationImage(
                              image: NetworkImage(item.imagenUrl!),
                              fit: BoxFit.cover,
                            )
                          : null,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.nombreProducto,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        Row(
                          children: [
                            Flexible(
                              child: Text(
                                'Talla ${item.tallaCodigo} · ${item.colorNombre}',
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
                              ),
                            ),
                            if (item.colorHex != null) ...[
                              const SizedBox(width: 6),
                              Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  color: _colorDesdeHex(item.colorHex),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.grey.shade300),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                  Text(
                    '× ${item.cantidad}',
                    style: TextStyle(fontSize: 11, color: Colors.grey.shade400),
                  ),
                ],
              ),
            ),
          ),
          if (reserva.observacion != null && reserva.observacion!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFBF9F7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '"${reserva.observacion}"',
                style: TextStyle(
                  fontSize: 11,
                  fontStyle: FontStyle.italic,
                  color: Colors.grey.shade600,
                ),
              ),
            ),
          ],
          if (reserva.puedeCancelar) ...[
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 12),
            TextButton(
              onPressed: () => _abrirCancelacion(reserva),
              style: TextButton.styleFrom(
                padding: EdgeInsets.zero,
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text(
                'CANCELAR RESERVA',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                  color: Color(0xFF93000A),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
