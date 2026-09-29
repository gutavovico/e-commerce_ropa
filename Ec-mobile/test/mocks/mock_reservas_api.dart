import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/datos/datasources/reservas_api.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/datos/modelos/reserva_dto.dart';

/// Payload literal de una respuesta real de `GET /api/v1/reservas/mias`.
///
/// Se define como JSON y no como objetos construidos a mano a propósito: los DTO deben
/// deserializarse con `fromJson` en las pruebas, porque los desajustes de nombres de clave son
/// invisibles en compilación y sólo se manifiestan como campos vacíos en pantalla.
const Map<String, dynamic> respuestaMisReservasBackend = {
  'resumen': {
    'activas': 1,
    'proxima': {
      'id_reserva': 1,
      'fecha_hora_atencion': '2026-10-02T15:30:00Z',
      'nombre_sucursal': 'Atelier Serrano - Madrid',
    },
  },
  'proximas': [
    {
      'id_reserva': 1,
      'codigo_reserva': 'RES-2026-0001',
      'estado': 'pendiente',
      'fecha_hora_atencion': '2026-10-02T15:30:00Z',
      'creado_en': '2026-09-29T10:00:00Z',
      'sucursal': {
        'id_sucursal': 1,
        'nombre': 'Atelier Serrano - Madrid',
        'direccion': 'Calle Serrano 48',
      },
      'items': [
        {
          'id_variante': 7,
          'nombre_producto': 'Blusa de satén fluido',
          'talla_codigo': '38',
          'color_nombre': 'Champagne',
          'color_hex': '#E8DFCF',
          'imagen_url': 'https://cdn.fashionstore.test/blusa.jpg',
          'cantidad': 1,
          'precio_unitario': '310.00',
        },
      ],
      'total_prendas': 1,
      'observacion': 'Prefiero probador amplio',
      'puede_cancelar': true,
    },
  ],
  'historial': [
    {
      'id_reserva': 2,
      'codigo_reserva': 'RES-2026-0002',
      'estado': 'vencida',
      'fecha_hora_atencion': '2026-09-20T15:30:00Z',
      'creado_en': '2026-09-19T10:00:00Z',
      'sucursal': {
        'id_sucursal': 1,
        'nombre': 'Atelier Serrano - Madrid',
        'direccion': 'Calle Serrano 48',
      },
      'items': [
        {
          'id_variante': 3,
          'nombre_producto': 'Vestido plisado en seda natural',
          'talla_codigo': '40',
          'color_nombre': 'Rojo Carmín',
          'color_hex': '#8C1C2B',
          'imagen_url': null,
          'cantidad': 1,
          'precio_unitario': '890.00',
        },
      ],
      'total_prendas': 1,
      'observacion': null,
      'puede_cancelar': false,
    },
  ],
};

/// Payload literal de `POST /api/v1/reservas/{id}/cancelar` aprobado.
const Map<String, dynamic> respuestaReservaCanceladaBackend = {
  'id_reserva': 1,
  'codigo_reserva': 'RES-2026-0001',
  'estado': 'cancelada',
  'fecha_hora_atencion': '2026-10-02T15:30:00Z',
  'creado_en': '2026-09-29T10:00:00Z',
  'sucursal': {
    'id_sucursal': 1,
    'nombre': 'Atelier Serrano - Madrid',
    'direccion': 'Calle Serrano 48',
  },
  'items': [],
  'total_prendas': 1,
  'observacion': null,
  'puede_cancelar': false,
};

/// Doble de [ReservasApi] que deserializa payloads reales del backend.
class MockReservasApi implements ReservasApi {
  /// Si se indica, `obtenerMisReservas` la lanza en vez de devolver la lista.
  final ReservaException? excepcionAlCargar;

  /// Si se indica, `cancelarReserva` la lanza en vez de aprobar la cancelación.
  final ReservaException? excepcionAlCancelar;

  /// Si se indica, sustituye la respuesta por defecto de `obtenerMisReservas`.
  final Map<String, dynamic>? respuestaMisReservas;

  int llamadasObtenerMisReservas = 0;
  int llamadasCancelarReserva = 0;
  int? ultimoIdReservaCancelado;
  String? ultimoMotivoEnviado;

  MockReservasApi({
    this.excepcionAlCargar,
    this.excepcionAlCancelar,
    this.respuestaMisReservas,
  });

  @override
  Future<MisReservasDto> obtenerMisReservas({required String token}) async {
    llamadasObtenerMisReservas++;
    if (excepcionAlCargar != null) throw excepcionAlCargar!;
    return MisReservasDto.fromJson(respuestaMisReservas ?? respuestaMisReservasBackend);
  }

  @override
  Future<ReservaDto> cancelarReserva(
    int idReserva,
    String motivo, {
    required String token,
  }) async {
    llamadasCancelarReserva++;
    ultimoIdReservaCancelado = idReserva;
    ultimoMotivoEnviado = motivo;
    if (excepcionAlCancelar != null) throw excepcionAlCancelar!;
    return ReservaDto.fromJson(respuestaReservaCanceladaBackend);
  }
}
