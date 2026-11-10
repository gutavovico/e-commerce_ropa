import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../../datos/caja_api.dart';
import '../../datos/modelos_caja.dart';

/// Fase de la caja.
sealed class EstadoCaja {
  const EstadoCaja();
}

class CajaCargando extends EstadoCaja {
  const CajaCargando();
}

/// Hay que elegir sucursal (AC-3): más de una autorizada, o administrador.
class CajaEligiendoSucursal extends EstadoCaja {
  final List<SucursalCaja> sucursales;

  const CajaEligiendoSucursal(this.sucursales);
}

class CajaOperando extends EstadoCaja {
  final SucursalCaja sucursal;

  const CajaOperando(this.sucursal);
}

class CajaError extends EstadoCaja {
  final String mensaje;

  const CajaError(this.mensaje);
}

/// P2-CU16 / CU17 · Estado de la caja móvil.
///
/// La app solo envía variantes, cantidades, cliente, reserva, cupón y los datos del cobro; todos los
/// importes (totales, descuento, IVA, cambio) los devuelve el servidor y se muestran tal cual.
class CajaBloc extends ChangeNotifier {
  final CajaApi _api;
  final String _token;
  StreamSubscription<bool>? _red;

  CajaBloc({required String token, CajaApi? api, Stream<bool>? cambiosDeRed})
      : _api = api ?? CajaApi(),
        _token = token {
    _red = (cambiosDeRed ?? _redDelSistema()).listen((hayRed) {
      if (hayRed == _enLinea) return;
      _enLinea = hayRed;
      notifyListeners();
    });
  }

  EstadoCaja _estado = const CajaCargando();
  List<SucursalCaja> _sucursales = const [];
  bool _enLinea = true;

  // Venta en curso
  final Map<int, int> _lineas = {};
  final Map<int, VarianteCaja> _variantes = {};
  ClienteCaja? _cliente;
  List<ReservaCaja> _reservasDelCliente = const [];
  ReservaCaja? _reserva;
  final Set<int> _excluidas = {};
  String? _cupon;
  PrevisualizacionCaja? _previsualizacion;
  bool _calculando = false;
  bool _registrando = false;
  String? _mensaje;

  // Cobro y listados
  VentaCaja? _ventaEnCobro;
  bool _cobrando = false;
  List<VentaCaja> _ventasDelDia = const [];
  List<PedidoWebEfectivo> _pedidosWeb = const [];

  EstadoCaja get estado => _estado;

  /// Cliente de la API de la caja, compartido con las hojas que abre (P2-CU18, cambio de prenda).
  CajaApi get api => _api;
  List<SucursalCaja> get sucursales => _sucursales;
  bool get enLinea => _enLinea;
  bool get puedeCambiarSucursal => _sucursales.length > 1;
  SucursalCaja? get sucursal => switch (_estado) {
        CajaOperando(:final sucursal) => sucursal,
        _ => null,
      };
  Map<int, int> get lineas => Map.unmodifiable(_lineas);
  ClienteCaja? get cliente => _cliente;
  List<ReservaCaja> get reservasDelCliente => _reservasDelCliente;
  ReservaCaja? get reserva => _reserva;
  Set<int> get excluidas => Set.unmodifiable(_excluidas);
  String? get cupon => _cupon;
  PrevisualizacionCaja? get previsualizacion => _previsualizacion;
  bool get calculando => _calculando;
  bool get registrando => _registrando;
  String? get mensaje => _mensaje;
  VentaCaja? get ventaEnCobro => _ventaEnCobro;
  bool get cobrando => _cobrando;
  List<VentaCaja> get ventasDelDia => _ventasDelDia;
  List<VentaCaja> get pendientes => _ventasDelDia.where((v) => v.pendiente).toList();
  List<PedidoWebEfectivo> get pedidosWeb => _pedidosWeb;
  bool get hayContenido => _lineas.isNotEmpty || _reserva != null;

  /// CU16 A4: sin conexión no se registra (y CU17 A4: no se cobra).
  bool get puedeRegistrar =>
      _enLinea && _previsualizacion != null && hayContenido && !_calculando && !_registrando;

  int? get _idSucursal => sucursal?.idSucursal;

  // --------------------------------------------------------------------------- sucursal

  Future<void> iniciar() async {
    _estado = const CajaCargando();
    notifyListeners();
    try {
      _sucursales = await _api.misSucursales(token: _token);
    } on CajaException catch (e) {
      _estado = CajaError(e.mensaje);
      notifyListeners();
      return;
    }
    if (_sucursales.isEmpty) {
      _estado = const CajaError('No tienes sucursales autorizadas para vender. Pide acceso al administrador.');
    } else if (_sucursales.length == 1) {
      await elegirSucursal(_sucursales.single);
      return;
    } else {
      _estado = CajaEligiendoSucursal(_sucursales);
    }
    notifyListeners();
  }

  Future<void> elegirSucursal(SucursalCaja sucursal) async {
    limpiarVenta(notificar: false);
    _ventaEnCobro = null;
    _estado = CajaOperando(sucursal);
    notifyListeners();
    await cargarVentas();
  }

  void volverASucursales() {
    if (!puedeCambiarSucursal) return;
    limpiarVenta(notificar: false);
    _estado = CajaEligiendoSucursal(_sucursales);
    notifyListeners();
  }

  // --------------------------------------------------------------------------- CU16

  Future<List<VarianteCaja>> buscarPrendas(String texto) async {
    if (texto.trim().length < 2) return const [];
    return _api.buscarVariantes(texto.trim(), idSucursal: _idSucursal, token: _token);
  }

  /// A1: una prenda sin existencias en la sucursal no se añade.
  Future<void> agregar(VarianteCaja variante) async {
    final actual = _lineas[variante.idVariante] ?? 0;
    if (variante.disponible <= actual) {
      _mensaje = variante.disponible == 0
          ? 'No hay existencias de ${variante.nombreProducto} (${variante.talla}) en esta sucursal.'
          : 'Solo hay ${variante.disponible} unidades de ${variante.nombreProducto} (${variante.talla}).';
      notifyListeners();
      return;
    }
    _variantes[variante.idVariante] = variante;
    _lineas[variante.idVariante] = actual + 1;
    _mensaje = null;
    await previsualizar();
  }

  Future<void> cambiarCantidad(int idVariante, int cantidad) async {
    final variante = _variantes[idVariante];
    if (cantidad <= 0) {
      _lineas.remove(idVariante);
    } else if (variante != null && cantidad > variante.disponible) {
      _mensaje = 'Solo hay ${variante.disponible} unidades en esta sucursal.';
      notifyListeners();
      return;
    } else {
      _lineas[idVariante] = cantidad;
    }
    await previsualizar();
  }

  Future<List<ClienteCaja>> buscarClientes(String texto) async {
    if (texto.trim().length < 2) return const [];
    return _api.buscarClientes(texto.trim(), token: _token);
  }

  /// AC-7: al elegir cliente se ofrecen sus reservas activas cargables en esta caja.
  Future<void> elegirCliente(ClienteCaja cliente) async {
    _cliente = cliente;
    _reservasDelCliente = const [];
    notifyListeners();
    try {
      _reservasDelCliente = await _api.reservasDeCliente(cliente.idCliente, idSucursal: _idSucursal, token: _token);
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
    }
    await previsualizar();
  }

  Future<void> quitarCliente() async {
    _cliente = null;
    _reservasDelCliente = const [];
    _reserva = null;
    _excluidas.clear();
    await previsualizar();
  }

  Future<void> cargarReserva(ReservaCaja reserva) async {
    _reserva = reserva;
    _excluidas.clear();
    if (reserva.cliente != null) _cliente = reserva.cliente;
    await previsualizar();
  }

  Future<bool> cargarReservaPorCodigo(String referencia) async {
    if (referencia.trim().isEmpty) return false;
    try {
      final reserva = await _api.reserva(referencia.trim(), idSucursal: _idSucursal, token: _token);
      await cargarReserva(reserva);
      return true;
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
      notifyListeners();
      return false;
    }
  }

  Future<void> alternarExclusion(int idVariante) async {
    if (!_excluidas.remove(idVariante)) _excluidas.add(idVariante);
    await previsualizar();
  }

  Future<void> quitarReserva() async {
    _reserva = null;
    _excluidas.clear();
    await previsualizar();
  }

  Future<List<CuponCaja>> buscarCupones(String texto) => _api.cupones(texto, token: _token);

  Future<void> aplicarCupon(String? codigo) async {
    _cupon = (codigo == null || codigo.trim().isEmpty) ? null : codigo.trim();
    await previsualizar();
  }

  VentaCajaIn _ventaIn() => VentaCajaIn(
        idSucursal: _idSucursal,
        idCliente: _cliente?.idCliente,
        reserva: _reserva?.codigo,
        codigoCupon: _cupon,
        lineas: Map.of(_lineas),
        lineasReservaExcluidas: _excluidas.toList(),
      );

  /// AC-5: los totales siempre los calcula el servidor. A2: un cupón inválido se quita y se sigue
  /// sin descuento, con el motivo del servidor.
  Future<void> previsualizar() async {
    if (!hayContenido) {
      _previsualizacion = null;
      notifyListeners();
      return;
    }
    _calculando = true;
    notifyListeners();
    try {
      _previsualizacion = await _api.previsualizar(_ventaIn(), token: _token);
    } on CajaException catch (e) {
      if (_cupon != null && (e.codigo?.startsWith('CUPON') ?? false)) {
        _mensaje = e.mensaje;
        _cupon = null;
        _calculando = false;
        return previsualizar();
      }
      _mensaje = e.mensaje;
      _previsualizacion = null;
    } finally {
      _calculando = false;
      notifyListeners();
    }
  }

  /// AC-9: registra la venta `pendiente` y la deja lista para cobrar.
  Future<VentaCaja?> registrar() async {
    if (!puedeRegistrar) return null;
    _registrando = true;
    _mensaje = null;
    notifyListeners();
    try {
      final venta = await _api.registrar(_ventaIn(), token: _token);
      _ventaEnCobro = venta;
      limpiarVenta(notificar: false);
      return venta;
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
      return null;
    } finally {
      _registrando = false;
      notifyListeners();
    }
  }

  /// A3: descartar la venta antes de confirmarla no registra nada.
  void limpiarVenta({bool notificar = true}) {
    _lineas.clear();
    _variantes.clear();
    _cliente = null;
    _reservasDelCliente = const [];
    _reserva = null;
    _excluidas.clear();
    _cupon = null;
    _previsualizacion = null;
    if (notificar) notifyListeners();
  }

  void descartarMensaje() {
    _mensaje = null;
    notifyListeners();
  }

  // --------------------------------------------------------------------------- CU17

  void abrirCobro(VentaCaja venta) {
    _ventaEnCobro = venta;
    _mensaje = null;
    notifyListeners();
  }

  /// Cobra la venta en curso. Devuelve la venta actualizada: `pagada` (comprobante) o, si el
  /// datáfono la rechazó, todavía `pendiente`. `null` si el servidor la rechazó con un error.
  Future<VentaCaja?> cobrar({
    required String metodoPago,
    String? montoRecibido,
    String? referencia,
    bool aprobado = true,
  }) async {
    final venta = _ventaEnCobro;
    if (venta == null || _cobrando || !_enLinea) return null;
    _cobrando = true;
    _mensaje = null;
    notifyListeners();
    try {
      final resultado = await _api.cobrar(
        venta.idVenta,
        metodoPago: metodoPago,
        montoRecibido: montoRecibido,
        referencia: referencia,
        aprobado: aprobado,
        token: _token,
      );
      _ventaEnCobro = resultado.pendiente ? resultado : null;
      if (!aprobado) _mensaje = 'Cobro rechazado por el datáfono: la venta sigue pendiente. Prueba otro medio.';
      unawaited(cargarVentas());
      return resultado;
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
      return null;
    } finally {
      _cobrando = false;
      notifyListeners();
    }
  }

  void cerrarCobro() {
    _ventaEnCobro = null;
    notifyListeners();
  }

  Future<bool> anular(int idVenta, String motivo) async {
    try {
      await _api.anular(idVenta, motivo.trim(), token: _token);
      if (_ventaEnCobro?.idVenta == idVenta) _ventaEnCobro = null;
      await cargarVentas();
      return true;
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
      notifyListeners();
      return false;
    }
  }

  Future<VentaCaja> obtenerVenta(int idVenta) => _api.venta(idVenta, token: _token);

  Future<void> cargarVentas() async {
    if (_idSucursal == null) return;
    try {
      final resultados = await Future.wait([
        _api.ventas(idSucursal: _idSucursal, soloHoy: true, token: _token),
        _api.pedidosWebEfectivo(idSucursal: _idSucursal, token: _token),
      ]);
      _ventasDelDia = resultados[0] as List<VentaCaja>;
      _pedidosWeb = resultados[1] as List<PedidoWebEfectivo>;
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
    }
    notifyListeners();
  }

  /// E3: cobro en mostrador de un pedido web pagado en efectivo.
  Future<bool> resolverPedidoWeb(PedidoWebEfectivo pedido, {required bool confirmar}) async {
    try {
      if (confirmar) {
        await _api.confirmarPedidoWeb(pedido.idPago, token: _token);
      } else {
        await _api.cancelarPedidoWeb(pedido.idPago, token: _token);
      }
      await cargarVentas();
      return true;
    } on CajaException catch (e) {
      _mensaje = e.mensaje;
      notifyListeners();
      return false;
    }
  }

  // --------------------------------------------------------------------------- red

  Stream<bool> _redDelSistema() => Connectivity()
      .onConnectivityChanged
      .map((r) => r.any((c) => c != ConnectivityResult.none))
      .handleError((Object _) {});

  bool _liberado = false;

  /// Una petición puede terminar después de cerrar la caja (p. ej. al cerrar sesión): sin esta
  /// guarda, notificar lanzaría «used after being disposed».
  @override
  void notifyListeners() {
    if (!_liberado) super.notifyListeners();
  }

  @override
  void dispose() {
    _liberado = true;
    _red?.cancel();
    super.dispose();
  }
}
