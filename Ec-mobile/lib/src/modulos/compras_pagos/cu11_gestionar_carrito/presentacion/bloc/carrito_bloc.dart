import 'package:flutter/foundation.dart';

import '../../datos/datasources/carrito_api.dart';
import '../../datos/modelos/carrito_dto.dart';

// ---------------------------------------------------------------------------
// Estados
// ---------------------------------------------------------------------------

sealed class CarritoEstado {
  const CarritoEstado();
}

class CarritoInicial extends CarritoEstado {
  const CarritoInicial();
}

class CarritoCargando extends CarritoEstado {
  const CarritoCargando();
}

class CarritoError extends CarritoEstado {
  final String mensaje;
  const CarritoError(this.mensaje);
}

/// Bolsa sin prendas. Es un estado legítimo, no un error: el backend responde 200.
class CarritoVacio extends CarritoEstado {
  const CarritoVacio();
}

class CarritoCargado extends CarritoEstado {
  final CarritoDto carrito;
  final TipoEntrega tipoEntrega;
  final String direccionEnvio;
  final int? idSucursalRetiro;
  final String? cuponAplicado;
  final List<BoutiqueRecogidaDto> boutiques;

  /// Línea sobre la que hay una operación en vuelo, para atenuarla en pantalla.
  final int? lineaEnCurso;
  final bool procesando;
  final String? mensajeNotificacion;
  final VentaCreadaDto? ordenConfirmada;

  const CarritoCargado({
    required this.carrito,
    this.tipoEntrega = TipoEntrega.domicilio,
    this.direccionEnvio = '',
    this.idSucursalRetiro,
    this.cuponAplicado,
    this.boutiques = const [],
    this.lineaEnCurso,
    this.procesando = false,
    this.mensajeNotificacion,
    this.ordenConfirmada,
  });

  CarritoResumenDto get resumen => carrito.resumen;
  List<CarritoItemDto> get items => carrito.items;

  /// Tramitar exige prendas y los datos de entrega completos para la modalidad elegida.
  bool get puedeTramitar {
    if (carrito.estaVacia || procesando) return false;
    if (tipoEntrega == TipoEntrega.domicilio) {
      return direccionEnvio.trim().isNotEmpty;
    }
    return idSucursalRetiro != null;
  }

  CarritoCargado copyWith({
    CarritoDto? carrito,
    TipoEntrega? tipoEntrega,
    String? direccionEnvio,
    int? idSucursalRetiro,
    bool limpiarSucursalRetiro = false,
    String? cuponAplicado,
    bool limpiarCupon = false,
    List<BoutiqueRecogidaDto>? boutiques,
    int? lineaEnCurso,
    bool limpiarLineaEnCurso = false,
    bool? procesando,
    String? mensajeNotificacion,
    bool limpiarNotificacion = false,
    VentaCreadaDto? ordenConfirmada,
  }) {
    return CarritoCargado(
      carrito: carrito ?? this.carrito,
      tipoEntrega: tipoEntrega ?? this.tipoEntrega,
      direccionEnvio: direccionEnvio ?? this.direccionEnvio,
      idSucursalRetiro:
          limpiarSucursalRetiro ? null : (idSucursalRetiro ?? this.idSucursalRetiro),
      cuponAplicado: limpiarCupon ? null : (cuponAplicado ?? this.cuponAplicado),
      boutiques: boutiques ?? this.boutiques,
      lineaEnCurso: limpiarLineaEnCurso ? null : (lineaEnCurso ?? this.lineaEnCurso),
      procesando: procesando ?? this.procesando,
      mensajeNotificacion:
          limpiarNotificacion ? null : (mensajeNotificacion ?? this.mensajeNotificacion),
      ordenConfirmada: ordenConfirmada ?? this.ordenConfirmada,
    );
  }
}

// ---------------------------------------------------------------------------
// BLoC
// ---------------------------------------------------------------------------

/// Orquesta la Bolsa de Compra (CU11) y la tramitación del pedido (CU15).
///
/// Los importes nunca se calculan aquí: cada operación devuelve la bolsa completa recalculada
/// por el servidor y el estado se reemplaza con ella. Derivar totales en el cliente crearía una
/// segunda fuente de verdad que acabaría discrepando de la orden real.
class CarritoBloc extends ChangeNotifier {
  final CarritoApi _api;
  final String _token;

  CarritoEstado _estado = const CarritoInicial();

  CarritoBloc({CarritoApi? api, required String token})
      : _api = api ?? CarritoApiImpl(),
        _token = token;

  CarritoEstado get estado => _estado;

  /// Número de prendas, accesible aunque la bolsa esté vacía o cargando.
  int get totalPrendas {
    final actual = _estado;
    return actual is CarritoCargado ? actual.resumen.totalPrendas : 0;
  }

  // -------------------------------------------------------------------
  // Carga
  // -------------------------------------------------------------------

  Future<void> cargarCarrito() async {
    _estado = const CarritoCargando();
    notifyListeners();

    try {
      final carrito = await _api.obtenerCarrito(token: _token);
      final boutiques = await _cargarBoutiquesSeguro();

      _estado = carrito.estaVacia
          ? const CarritoVacio()
          : CarritoCargado(carrito: carrito, boutiques: boutiques);
    } on CarritoException catch (e) {
      _estado = CarritoError(e.mensaje);
    }
    notifyListeners();
  }

  /// El directorio de boutiques es accesorio: su fallo no debe tumbar la bolsa.
  Future<List<BoutiqueRecogidaDto>> _cargarBoutiquesSeguro() async {
    try {
      return await _api.obtenerBoutiques();
    } on CarritoException {
      return const [];
    }
  }

  // -------------------------------------------------------------------
  // CU11: modificación de la bolsa
  // -------------------------------------------------------------------

  Future<bool> incrementar(CarritoItemDto item) {
    // El tope procede de las existencias reales de la boutique de expedición.
    if (item.alcanzoElMaximo) {
      _notificar(
        'Has alcanzado las existencias disponibles de esta prenda en '
        '${item.nombreSucursal}.',
      );
      return Future.value(false);
    }
    return _fijarCantidad(item, item.cantidad + 1);
  }

  Future<bool> decrementar(CarritoItemDto item) {
    // Para retirar una prenda se usa la papelera, no una cantidad de cero.
    if (item.cantidad <= 1) return Future.value(false);
    return _fijarCantidad(item, item.cantidad - 1);
  }

  Future<bool> _fijarCantidad(CarritoItemDto item, int cantidad) async {
    final actual = _estado;
    if (actual is! CarritoCargado) return false;

    // Actualización optimista: la cifra cambia al instante y se revierte si el backend la
    // rechaza, de modo que el control responde sin esperar al viaje de red.
    final carritoPrevio = actual.carrito;
    _estado = actual.copyWith(
      carrito: _conCantidadLocal(carritoPrevio, item.idCarritoDetalle, cantidad),
      lineaEnCurso: item.idCarritoDetalle,
      procesando: true,
      limpiarNotificacion: true,
    );
    notifyListeners();

    try {
      final carrito = await _api.actualizarCantidad(
        item.idCarritoDetalle,
        cantidad,
        token: _token,
      );
      _estado = (_estado as CarritoCargado).copyWith(
        carrito: carrito,
        procesando: false,
        limpiarLineaEnCurso: true,
      );
      notifyListeners();
      return true;
    } on CarritoException catch (e) {
      // Reversión al estado previo: la bolsa del servidor no cambió.
      _estado = (_estado as CarritoCargado).copyWith(
        carrito: carritoPrevio,
        procesando: false,
        limpiarLineaEnCurso: true,
        mensajeNotificacion: e.mensaje,
      );
      notifyListeners();
      return false;
    }
  }

  /// Aplica la cantidad en memoria sin tocar los importes.
  ///
  /// Los totales se dejan intactos a propósito: recalcularlos aquí implicaría duplicar las
  /// reglas de promoción del backend. El resumen definitivo llega con la respuesta.
  CarritoDto _conCantidadLocal(CarritoDto carrito, int idLinea, int cantidad) {
    return CarritoDto(
      idCarrito: carrito.idCarrito,
      items: carrito.items.map((i) {
        if (i.idCarritoDetalle != idLinea) return i;
        return CarritoItemDto(
          idCarritoDetalle: i.idCarritoDetalle,
          idVariante: i.idVariante,
          idProducto: i.idProducto,
          nombreProducto: i.nombreProducto,
          lineaConfeccion: i.lineaConfeccion,
          sku: i.sku,
          tallaCodigo: i.tallaCodigo,
          colorNombre: i.colorNombre,
          colorHex: i.colorHex,
          imagenUrl: i.imagenUrl,
          precioLista: i.precioLista,
          precioUnitario: i.precioUnitario,
          descuentoLinea: i.descuentoLinea,
          motivoDescuento: i.motivoDescuento,
          cantidad: cantidad,
          idSucursal: i.idSucursal,
          nombreSucursal: i.nombreSucursal,
          stockDisponible: i.stockDisponible,
          cantidadMaxima: i.cantidadMaxima,
          subtotalLinea: i.subtotalLinea,
        );
      }).toList(),
      resumen: carrito.resumen,
      expiraEn: carrito.expiraEn,
      sucursalesExpedicion: carrito.sucursalesExpedicion,
    );
  }

  Future<bool> eliminar(CarritoItemDto item) async {
    final actual = _estado;
    if (actual is! CarritoCargado) return false;

    _estado = actual.copyWith(
      lineaEnCurso: item.idCarritoDetalle,
      procesando: true,
      limpiarNotificacion: true,
    );
    notifyListeners();

    try {
      final carrito = await _api.eliminarItem(item.idCarritoDetalle, token: _token);

      _estado = carrito.estaVacia
          ? const CarritoVacio()
          : actual.copyWith(
              carrito: carrito,
              procesando: false,
              limpiarLineaEnCurso: true,
              mensajeNotificacion: 'Prenda retirada de tu bolsa.',
            );
      notifyListeners();
      return true;
    } on CarritoException catch (e) {
      _estado = actual.copyWith(
        procesando: false,
        limpiarLineaEnCurso: true,
        mensajeNotificacion: e.mensaje,
      );
      notifyListeners();
      return false;
    }
  }

  // -------------------------------------------------------------------
  // CU15: entrega, cupón y tramitación
  // -------------------------------------------------------------------

  void seleccionarEntrega(TipoEntrega tipo) {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    _estado = actual.copyWith(tipoEntrega: tipo, limpiarNotificacion: true);
    notifyListeners();
  }

  void actualizarDireccion(String direccion) {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    _estado = actual.copyWith(direccionEnvio: direccion);
    notifyListeners();
  }

  void seleccionarBoutique(int idSucursal) {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    _estado = actual.copyWith(idSucursalRetiro: idSucursal);
    notifyListeners();
  }

  /// Registra el cupón. Su validez la dicta el backend al tramitar: duplicar aquí las reglas
  /// de vigencia, tope y límite de usos crearía dos fuentes de verdad.
  void aplicarCupon(String codigo) {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    final limpio = codigo.trim();
    if (limpio.isEmpty) return;
    _estado = actual.copyWith(cuponAplicado: limpio, limpiarNotificacion: true);
    notifyListeners();
  }

  void retirarCupon() {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    _estado = actual.copyWith(limpiarCupon: true);
    notifyListeners();
  }

  Future<bool> tramitarPedido() async {
    final actual = _estado;
    if (actual is! CarritoCargado || !actual.puedeTramitar) return false;

    _estado = actual.copyWith(procesando: true, limpiarNotificacion: true);
    notifyListeners();

    try {
      final venta = await _api.tramitarPedido(
        CheckoutInDto(
          tipoEntrega: actual.tipoEntrega,
          direccionEnvio: actual.direccionEnvio,
          idSucursalRetiro: actual.idSucursalRetiro,
          codigoCupon: actual.cuponAplicado,
        ),
        token: _token,
      );

      _estado = actual.copyWith(
        carrito: CarritoDto.vacio,
        procesando: false,
        ordenConfirmada: venta,
      );
      notifyListeners();
      return true;
    } on CarritoException catch (e) {
      // Si el cupón fue el motivo del rechazo se retira, para que el cliente pueda reintentar
      // sin quedar atrapado en un código que el backend no acepta.
      _estado = actual.copyWith(
        procesando: false,
        limpiarCupon: e.esCuponInvalido,
        mensajeNotificacion: e.mensaje,
      );
      notifyListeners();
      return false;
    }
  }

  // -------------------------------------------------------------------
  // Utilidades
  // -------------------------------------------------------------------

  void limpiarNotificacion() {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    _estado = actual.copyWith(limpiarNotificacion: true);
    notifyListeners();
  }

  void _notificar(String mensaje) {
    final actual = _estado;
    if (actual is! CarritoCargado) return;
    _estado = actual.copyWith(mensajeNotificacion: mensaje);
    notifyListeners();
  }
}
