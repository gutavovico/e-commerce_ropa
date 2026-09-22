import 'package:ec_mobile/src/modulos/compras_pagos/cu11_gestionar_carrito/datos/datasources/carrito_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu11_gestionar_carrito/datos/modelos/carrito_dto.dart';

/// Payload literal de una respuesta real de `GET /api/v1/carrito`.
///
/// Se define como JSON y no como objetos construidos a mano a propósito: los DTO deben
/// deserializarse con `fromJson` en las pruebas, porque los desajustes de nombres de clave son
/// invisibles en compilación y sólo se manifiestan como campos vacíos en pantalla. Fue
/// exactamente lo que ocultó los defectos de contrato de CU07 y CU12.
const Map<String, dynamic> respuestaCarritoBackend = {
  'id_carrito': 77,
  'items': [
    {
      'id_carrito_detalle': 44,
      'id_variante': 3,
      'id_producto': 1,
      'nombre_producto': 'Vestido plisado en seda natural',
      'linea_confeccion': null,
      'sku': 'VES-PLI-40-ROJ',
      'talla_codigo': '40',
      'color_nombre': 'Rojo Carmín',
      'color_hex': '#8C1C2B',
      'imagen_url': 'https://cdn.fashionstore.test/vestido.jpg',
      'precio_lista': '890.00',
      'precio_unitario': '756.50',
      'descuento_linea': '133.50',
      'motivo_descuento': 'Membresia Prive',
      'cantidad': 2,
      'id_sucursal': 1,
      'nombre_sucursal': 'Atelier Serrano - Madrid',
      'stock_disponible': 15,
      'cantidad_maxima': 15,
      'subtotal_linea': '1513.00',
    },
  ],
  'resumen': {
    'total_prendas': 2,
    'total_lineas': 1,
    'subtotal': '1780.00',
    'descuento': '267.00',
    'total': '1513.00',
    'iva_incluido': '262.62',
    'moneda': 'EUR',
  },
  'expira_en': null,
  'sucursales_expedicion': [
    {'id_sucursal': 1, 'nombre': 'Atelier Serrano - Madrid', 'total_lineas': 1},
  ],
};

/// Payload literal de `POST /api/v1/ventas/checkout`.
const Map<String, dynamic> respuestaVentaBackend = {
  'id_venta': 1,
  'numero_comprobante': 'FS-2026-000001',
  'estado': 'pendiente',
  'tipo_venta': 'digital_movil',
  'tipo_entrega': 'domicilio',
  'direccion_envio': 'Calle de Claudio Coello 48, 28001 Madrid',
  'id_sucursal_retiro': null,
  'nombre_sucursal_retiro': null,
  'subtotal': '1780.00',
  'descuento': '267.00',
  'total': '1513.00',
  'iva_incluido': '262.62',
  'moneda': 'EUR',
  'cupon_aplicado': null,
  'nombre_promocion': 'Membresia Prive',
  'items': [
    {
      'id_venta_detalle': 1,
      'id_variante': 3,
      'sku': 'VES-PLI-40-ROJ',
      'nombre_producto': 'Vestido plisado en seda natural',
      'talla_codigo': '40',
      'color_nombre': 'Rojo Carmín',
      'imagen_url': null,
      'cantidad': 2,
      'precio_unitario': '756.50',
      'subtotal_linea': '1513.00',
      'id_sucursal': 1,
      'nombre_sucursal': 'Atelier Serrano - Madrid',
    },
  ],
  'total_prendas': 2,
  'fecha_venta': '2026-09-22T10:00:00Z',
  'expira_en': '2026-09-22T10:25:00Z',
  'mensaje_confirmacion':
      'Tu orden ha sido registrada. Dispones de 25 minutos para completar el pago.',
};

const Map<String, dynamic> respuestaCarritoVacioBackend = {
  'id_carrito': 77,
  'items': [],
  'resumen': {
    'total_prendas': 0,
    'total_lineas': 0,
    'subtotal': '0.00',
    'descuento': '0.00',
    'total': '0.00',
    'iva_incluido': '0.00',
    'moneda': 'EUR',
  },
  'expira_en': null,
  'sucursales_expedicion': [],
};

/// Doble de [CarritoApi] que deserializa payloads reales del backend.
class MockCarritoApi implements CarritoApi {
  /// Si se indica, toda operación de escritura la lanza.
  final CarritoException? excepcion;

  /// Cuando es cierto, `obtenerCarrito` devuelve una bolsa sin prendas.
  final bool bolsaVacia;

  int llamadasAgregar = 0;
  int llamadasActualizar = 0;
  int llamadasEliminar = 0;
  int llamadasCheckout = 0;

  /// Último payload enviado a `tramitarPedido`, para verificar el contrato.
  Map<String, dynamic>? ultimoPayloadCheckout;

  /// Última cantidad enviada a `actualizarCantidad`.
  int? ultimaCantidadEnviada;

  MockCarritoApi({this.excepcion, this.bolsaVacia = false});

  @override
  Future<CarritoDto> obtenerCarrito({required String token}) async {
    return CarritoDto.fromJson(
      bolsaVacia ? respuestaCarritoVacioBackend : respuestaCarritoBackend,
    );
  }

  @override
  Future<CarritoDto> agregarItem(ItemAgregarInDto datos, {required String token}) async {
    llamadasAgregar++;
    if (excepcion != null) throw excepcion!;
    return CarritoDto.fromJson(respuestaCarritoBackend);
  }

  @override
  Future<CarritoDto> actualizarCantidad(
    int idCarritoDetalle,
    int cantidad, {
    required String token,
  }) async {
    llamadasActualizar++;
    ultimaCantidadEnviada = cantidad;
    if (excepcion != null) throw excepcion!;
    return CarritoDto.fromJson(respuestaCarritoBackend);
  }

  @override
  Future<CarritoDto> eliminarItem(int idCarritoDetalle, {required String token}) async {
    llamadasEliminar++;
    if (excepcion != null) throw excepcion!;
    return CarritoDto.fromJson(respuestaCarritoVacioBackend);
  }

  @override
  Future<VentaCreadaDto> tramitarPedido(
    CheckoutInDto datos, {
    required String token,
  }) async {
    llamadasCheckout++;
    ultimoPayloadCheckout = datos.toJson();
    if (excepcion != null) throw excepcion!;
    return VentaCreadaDto.fromJson(respuestaVentaBackend);
  }

  @override
  Future<List<BoutiqueRecogidaDto>> obtenerBoutiques() async {
    return [
      BoutiqueRecogidaDto.fromJson(const {
        'id_sucursal': 1,
        'nombre': 'Atelier Serrano - Madrid',
        'ciudad': 'Madrid',
        'direccion': 'Calle Serrano 48',
      }),
    ];
  }
}
