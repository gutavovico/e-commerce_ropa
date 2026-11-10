import 'package:flutter/foundation.dart';

/// P2-CU15 (RN25) · Horas de visita que se pueden elegir para una reserva.
///
/// La reserva vence a las horas que define la empresa desde que se crea; una cita posterior no
/// llegaría a atenderse y el servidor la rechaza (400 `CITA_FUERA_DE_PLAZO`). Solo se ofrecen horas
/// en punto entre la próxima hora completa (con al menos 1 h de margen) y el vencimiento, dentro del
/// horario de la tienda. Mismo criterio que la web (`core/sin-conexion/franjas-cita.ts`).
@immutable
class FranjaCita {
  final DateTime instante;
  final String etiqueta;

  const FranjaCita(this.instante, this.etiqueta);
}

const int _apertura = 9;
const int _cierre = 20;
const Duration _margen = Duration(minutes: 10);

List<FranjaCita> franjasDeCita(DateTime ahora, int horasVencimiento, {int maximo = 8}) {
  final limite = ahora.add(Duration(hours: horasVencimiento)).subtract(_margen);
  var cursor = DateTime(ahora.year, ahora.month, ahora.day, ahora.hour).add(const Duration(hours: 2));
  final franjas = <FranjaCita>[];
  while (!cursor.isAfter(limite) && franjas.length < maximo) {
    if (cursor.hour >= _apertura && cursor.hour < _cierre) {
      franjas.add(FranjaCita(cursor, _etiqueta(cursor, ahora)));
    }
    cursor = cursor.add(const Duration(hours: 1));
  }
  return franjas;
}

const _diasSemana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];

String _etiqueta(DateTime fecha, DateTime ahora) {
  final hoy = DateTime(ahora.year, ahora.month, ahora.day);
  final dia = DateTime(fecha.year, fecha.month, fecha.day);
  final diferencia = dia.difference(hoy).inDays;
  final nombreDia = switch (diferencia) {
    0 => 'Hoy',
    1 => 'Mañana',
    _ => '${_diasSemana[fecha.weekday - 1]} ${fecha.day}',
  };
  final hora = fecha.hour.toString().padLeft(2, '0');
  return '$nombreDia $hora:00';
}
