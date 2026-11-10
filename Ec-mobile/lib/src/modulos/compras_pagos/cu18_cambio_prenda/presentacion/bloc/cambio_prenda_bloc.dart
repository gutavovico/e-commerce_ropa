import 'package:flutter/foundation.dart';

import '../../../cu16_cu17_caja/datos/caja_api.dart';
import '../../../cu16_cu17_caja/datos/modelos_caja.dart';
import '../../datos/cambio_prenda_api.dart';

/// Fase del cambio de prenda.
sealed class EstadoCambio {
  const EstadoCambio();
}

/// Aún no hay venta: se pide el comprobante.
class CambioSinVenta extends EstadoCambio {
  const CambioSinVenta();
}

/// Venta encontrada dentro del plazo: se elige qué devuelve y qué se lleva.
class CambioEligiendo extends EstadoCambio {
  final VentaCambiable venta;

  const CambioEligiendo(this.venta);
}

/// Cambio registrado: comprobante en pantalla (AC-9).
class CambioRegistrado extends EstadoCambio {
  final CambioPrenda cambio;

  const CambioRegistrado(this.cambio);
}

/// P2-CU18 · Estado del cambio de prenda en la caja móvil.
///
/// La app solo envía la venta, qué se devuelve, qué se lleva y el cobro; el valor de lo devuelto
/// (decisión F2), el de lo nuevo y la diferencia los calcula el servidor y se muestran tal cual.
class CambioPrendaBloc extends ChangeNotifier {
  final CambioPrendaApi _api;
  final String _token;
  final int? _idSucursal;
  final Future<List<VarianteCaja>> Function(String texto) _buscarPrendas;

  CambioPrendaBloc({
    required String token,
    required int? idSucursal,
    required Future<List<VarianteCaja>> Function(String texto) buscarPrendas,
    CambioPrendaApi? api,
  })  : _api = api ?? CambioPrendaApi(),
        _token = token,
        _idSucursal = idSucursal,
        _buscarPrendas = buscarPrendas;

  EstadoCambio _estado = const CambioSinVenta();
  final Map<int, int> _devolver = {};
  final Map<int, int> _nuevas = {};
  final Map<int, VarianteCaja> _variantes = {};
  CambioPrenda? _previo;
  bool _cargando = false;
  bool _calculando = false;
  String? _error;
  int _consulta = 0;

  EstadoCambio get estado => _estado;
  Map<int, int> get devolver => Map.unmodifiable(_devolver);
  List<(VarianteCaja, int)> get nuevas => [for (final e in _nuevas.entries) (_variantes[e.key]!, e.value)];
  CambioPrenda? get previo => _previo;
  bool get cargando => _cargando;
  bool get calculando => _calculando;
  String? get error => _error;

  /// AC-13: sin conexión no se registra.
  bool puedeRegistrar({required bool enLinea}) => enLinea && _previo != null && !_calculando && !_cargando;

  Future<List<VarianteCaja>> buscarPrendas(String texto) => _buscarPrendas(texto);

  Future<void> buscarVenta(String comprobante) async {
    if (comprobante.trim().isEmpty) return;
    _cargando = true;
    _error = null;
    notifyListeners();
    try {
      final venta = await _api.ventaCambiable(comprobante, idSucursal: _idSucursal, token: _token);
      _limpiarSeleccion();
      _estado = CambioEligiendo(venta);
    } on CajaException catch (e) {
      _estado = const CambioSinVenta();
      _error = e.mensaje;
    } finally {
      _cargando = false;
      notifyListeners();
    }
  }

  /// AC-4: no se devuelve más de lo que queda por cambiar en la línea.
  void cambiarDevolucion(LineaCambiable linea, int delta) {
    final actual = _devolver[linea.idVentaDetalle] ?? 0;
    final nueva = (actual + delta).clamp(0, linea.cambiables);
    if (nueva == actual) return;
    if (nueva == 0) {
      _devolver.remove(linea.idVentaDetalle);
    } else {
      _devolver[linea.idVentaDetalle] = nueva;
    }
    _recalcular();
  }

  /// A1 de la caja: una prenda sin existencias en la sucursal no se ofrece.
  void agregarNueva(VarianteCaja variante) {
    if (variante.disponible <= 0) return;
    final actual = _nuevas[variante.idVariante] ?? 0;
    if (actual >= variante.disponible) return;
    _variantes[variante.idVariante] = variante;
    _nuevas[variante.idVariante] = actual + 1;
    _recalcular();
  }

  void quitarNueva(int idVariante) {
    _nuevas.remove(idVariante);
    _variantes.remove(idVariante);
    _recalcular();
  }

  Map<String, dynamic> _cuerpo(int idVenta) => {
        'id_venta': idVenta,
        'id_sucursal': _idSucursal,
        'devueltas': [for (final e in _devolver.entries) {'id_venta_detalle': e.key, 'cantidad': e.value}],
        'nuevas': [for (final e in _nuevas.entries) {'id_variante': e.key, 'cantidad': e.value}],
      };

  /// La diferencia la calcula el servidor; si llegan dos respuestas, solo vale la última pedida.
  Future<void> _recalcular() async {
    final estado = _estado;
    _error = null;
    if (estado is! CambioEligiendo || _devolver.isEmpty || _nuevas.isEmpty) {
      _previo = null;
      _calculando = false;
      notifyListeners();
      return;
    }
    final consulta = ++_consulta;
    _calculando = true;
    notifyListeners();
    try {
      final previo = await _api.previsualizar(_cuerpo(estado.venta.idVenta), token: _token);
      if (consulta != _consulta) return;
      _previo = previo;
    } on CajaException catch (e) {
      if (consulta != _consulta) return;
      _previo = null;
      _error = e.mensaje;
    }
    _calculando = false;
    notifyListeners();
  }

  /// AC-6 / AC-7: si paga el cliente, se envía el cobro; si se le devuelve, se entrega en efectivo.
  Future<void> registrar({String metodoPago = 'efectivo', String? montoRecibido, String? referencia}) async {
    final estado = _estado;
    final previo = _previo;
    if (estado is! CambioEligiendo || previo == null) return;
    _cargando = true;
    _error = null;
    notifyListeners();
    try {
      final efectivo = metodoPago == 'efectivo';
      final cambio = await _api.registrar({
        ..._cuerpo(estado.venta.idVenta),
        if (previo.pagaElCliente)
          'cobro': {
            'metodo_pago': metodoPago,
            'monto_recibido': efectivo ? _texto(montoRecibido) : null,
            'referencia': efectivo ? null : _texto(referencia),
          },
      }, token: _token);
      _estado = CambioRegistrado(cambio);
    } on CajaException catch (e) {
      _error = e.mensaje;
    } finally {
      _cargando = false;
      notifyListeners();
    }
  }

  String? _texto(String? v) {
    final t = v?.trim().replaceAll(',', '.');
    return t == null || t.isEmpty ? null : t;
  }

  void reiniciar() {
    _limpiarSeleccion();
    _estado = const CambioSinVenta();
    _error = null;
    notifyListeners();
  }

  void _limpiarSeleccion() {
    _consulta++;
    _devolver.clear();
    _nuevas.clear();
    _variantes.clear();
    _previo = null;
    _calculando = false;
  }

  bool _liberado = false;

  @override
  void notifyListeners() {
    if (!_liberado) super.notifyListeners();
  }

  @override
  void dispose() {
    _liberado = true;
    super.dispose();
  }
}
