import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/datasources/pago_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/modelos/pago_dto.dart';

/// Payload literal de una respuesta real de `GET /api/v1/ventas/{id}/resumen-pago`.
///
/// Se define como JSON y no como objetos construidos a mano a propósito: los DTO deben
/// deserializarse con `fromJson` en las pruebas, porque los desajustes de nombres de clave son
/// invisibles en compilación y sólo se manifiestan como campos vacíos en pantalla. Fue
/// exactamente lo que ocultó los defectos de contrato de CU07/CU12, y lo que arrastraba
/// `pago.model.ts` en Web hasta que se corrigió.
const Map<String, dynamic> respuestaResumenPagoBackend = {
  'id_venta': 1,
  'numero_comprobante': 'FS-2026-000001',
  'estado': 'pendiente',
  'subtotal': '2100.00',
  'descuento': '160.00',
  'total': '1940.00',
  'iva_incluido': '336.69',
  'moneda': 'EUR',
  'total_prendas': 3,
  'items': [
    {
      'id_variante': 3,
      'sku': 'VES-PLI-40-ROJ',
      'nombre_producto': 'Vestido plisado en seda natural',
      'talla_codigo': '38',
      'color_nombre': 'Rojo Carmín',
      'imagen_url': 'https://cdn.fashionstore.test/vestido.jpg',
      'cantidad': 1,
      'precio_unitario': '890.00',
      'subtotal_linea': '890.00',
      'nombre_sucursal': 'Atelier Serrano - Madrid',
    },
  ],
  'tipo_entrega': 'domicilio',
  'direccion_envio': 'Calle de Claudio Coello 48, 4º Derecha, 28001 Madrid',
  'nombre_sucursal_retiro': null,
  'nombre_cliente': 'Ana Valenzuela',
  'fecha_venta': '2026-09-22T10:00:00Z',
  'expira_en': '2026-09-22T10:25:00Z',
  'segundos_restantes': 1500,
  'metodos_disponibles': ['tarjeta_credito', 'tarjeta_debito', 'qr', 'pasarela_digital'],
};

/// Payload literal de `POST /api/v1/pagos/intentos`: abre el `PaymentIntent` y devuelve su
/// `client_secret`. No lleva ningún dato de tarjeta (revisado el 2026-09-28).
const Map<String, dynamic> respuestaIntentoPagoBackend = {
  'id_pago': 505,
  'client_secret': 'pi_test_123456789_secret_test',
  'ya_confirmado': false,
  'confirmacion': null,
};

/// Payload literal de `POST /api/v1/pagos/{id_pago}/confirmar` aprobado.
const Map<String, dynamic> respuestaPagoConfirmadoBackend = {
  'id_pago': 505,
  'id_venta': 1,
  'numero_comprobante': 'FS-2026-000001',
  'estado_pago': 'confirmado',
  'estado_venta': 'pagada',
  'metodo_pago': 'tarjeta_credito',
  'referencia_pasarela': 'pi_test_123456789',
  'monto': '1940.00',
  'moneda': 'EUR',
  'marca_tarjeta': 'VISA',
  'ultimos_digitos': '1111',
  'confirmado_en': '2026-09-22T10:05:00Z',
  'mensaje_confirmacion': 'Pago confirmado. Tu orden entra en preparación en el atelier.',
};

/// Doble de [PagoApi] que deserializa payloads reales del backend.
class MockPagoApi implements PagoApi {
  /// Si se indica, `iniciarPago` la lanza en vez de abrir el intento.
  final PagoException? excepcionAlIniciar;

  /// Si se indica, `confirmarPago` la lanza en vez de confirmar el cobro.
  final PagoException? excepcionAlConfirmar;

  /// Si se indica, `obtenerResumenPago` la lanza en vez de devolver el resumen.
  final PagoException? excepcionAlCargar;

  /// Si se indica, sustituye la respuesta por defecto de `iniciarPago`.
  final Map<String, dynamic>? respuestaIniciar;

  int llamadasIniciarPago = 0;
  int llamadasConfirmarPago = 0;
  Map<String, dynamic>? ultimoPayloadIniciar;
  int? ultimoIdPagoConfirmado;

  MockPagoApi({
    this.excepcionAlIniciar,
    this.excepcionAlConfirmar,
    this.excepcionAlCargar,
    this.respuestaIniciar,
  });

  @override
  Future<ResumenPagoDto> obtenerResumenPago(int idVenta, {required String token}) async {
    if (excepcionAlCargar != null) throw excepcionAlCargar!;
    return ResumenPagoDto.fromJson(respuestaResumenPagoBackend);
  }

  @override
  Future<PagoIntentoOutDto> iniciarPago(PagoIniciarInDto datos, {required String token}) async {
    llamadasIniciarPago++;
    ultimoPayloadIniciar = datos.toJson();
    if (excepcionAlIniciar != null) throw excepcionAlIniciar!;
    return PagoIntentoOutDto.fromJson(respuestaIniciar ?? respuestaIntentoPagoBackend);
  }

  @override
  Future<PagoConfirmadoDto> confirmarPago(int idPago, {required String token}) async {
    llamadasConfirmarPago++;
    ultimoIdPagoConfirmado = idPago;
    if (excepcionAlConfirmar != null) throw excepcionAlConfirmar!;
    return PagoConfirmadoDto.fromJson(respuestaPagoConfirmadoBackend);
  }
}
