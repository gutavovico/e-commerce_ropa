import 'package:flutter/material.dart';

import '../../datos/modelos/reserva_dto.dart';
import '../bloc/mis_reservas_bloc.dart';

/// Motivo obligatorio de CU13 (paso 4), 3-250 caracteres — espejo de `ReservaCancelarIn`.
const int _motivoMin = 3;
const int _motivoMax = 250;

/// Abre la hoja de confirmación de cancelación. Devuelve `true` si la reserva se canceló.
Future<bool?> mostrarHojaCancelarReserva({
  required BuildContext context,
  required ReservaDto reserva,
  required MisReservasBloc bloc,
}) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => _HojaCancelarReservaContenido(reserva: reserva, bloc: bloc),
  );
}

class _HojaCancelarReservaContenido extends StatefulWidget {
  final ReservaDto reserva;
  final MisReservasBloc bloc;

  const _HojaCancelarReservaContenido({required this.reserva, required this.bloc});

  @override
  State<_HojaCancelarReservaContenido> createState() =>
      _HojaCancelarReservaContenidoState();
}

class _HojaCancelarReservaContenidoState extends State<_HojaCancelarReservaContenido> {
  final _controlador = TextEditingController();

  @override
  void initState() {
    super.initState();
    widget.bloc.addListener(_alCambiar);
  }

  @override
  void dispose() {
    widget.bloc.removeListener(_alCambiar);
    _controlador.dispose();
    super.dispose();
  }

  void _alCambiar() {
    if (mounted) setState(() {});
  }

  bool get _motivoValido {
    final longitud = _controlador.text.trim().length;
    return longitud >= _motivoMin && longitud <= _motivoMax;
  }

  Future<void> _confirmar() async {
    if (!_motivoValido || widget.bloc.cancelando) return;
    final exito = await widget.bloc.cancelarReserva(
      widget.reserva.idReserva,
      _controlador.text.trim(),
    );
    // Si falló, el error queda en `widget.bloc.errorCancelacion` y `_alCambiar` repinta esta
    // misma hoja para mostrarlo; el usuario puede corregir el motivo y reintentar sin cerrarla.
    if (exito && mounted) {
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cancelando = widget.bloc.cancelando;
    final error = widget.bloc.errorCancelacion;

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
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
                widget.reserva.codigoReserva,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                  color: Colors.grey.shade500,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Cancelar esta reserva',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Text(
                '${widget.reserva.sucursal.nombre} — las prendas apartadas volverán a '
                'estar disponibles de inmediato.',
                style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 16),
              if (error != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFDAD6),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    error,
                    style: const TextStyle(fontSize: 12, color: Color(0xFF93000A)),
                  ),
                ),
                const SizedBox(height: 16),
              ],
              Text(
                'MOTIVO DE LA CANCELACIÓN',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _controlador,
                maxLength: _motivoMax,
                maxLines: 3,
                enabled: !cancelando,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  hintText: 'Cuéntanos por qué cancelas, nos ayuda a mejorar el servicio…',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: cancelando ? null : () => Navigator.of(context).pop(false),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        side: BorderSide(color: Colors.grey.shade300),
                      ),
                      child: const Text(
                        'Mantener reserva',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.black87),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: (_motivoValido && !cancelando) ? _confirmar : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF93000A),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: cancelando
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation(Colors.white),
                              ),
                            )
                          : const Text(
                              'Confirmar cancelación',
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
                            ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
