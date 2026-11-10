import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import 'almacen_local.dart';
import 'modelos_sin_conexion.dart';
import 'sin_conexion_api.dart';
import '../push/servicio_push.dart';

/// P2-CU14 / CU15 A1 / CU19 · Catálogo descargado, reservas sin conexión, compras interrumpidas y
/// sincronización en la app Flutter.
///
/// - Al abrir el hub de un cliente en una tienda se carga lo guardado (también sin red) y, con red,
///   se registra el dispositivo, se descarga el catálogo y se envía lo pendiente.
/// - Al volver la conexión (y responder `/health`) se sincroniza solo; si falla, se reintenta con
///   espera creciente (CU19 A1).
/// - Ninguna operación se borra al enviarse (RN37); el resultado del servidor se guarda en ella.
class SinConexionServicio extends ChangeNotifier {
  final AlmacenLocal _almacen;
  final SinConexionApi _api;
  final Stream<bool>? _cambiosDeRed;
  final Uuid _uuid;

  static const int _loteMaximo = 50;
  static const Duration _vigenciaCatalogo = Duration(hours: 1);
  static const Duration _esperaInicial = Duration(seconds: 5);
  static const Duration _esperaMaxima = Duration(minutes: 5);

  SinConexionServicio({
    AlmacenLocal? almacen,
    SinConexionApi? api,
    Stream<bool>? cambiosDeRed,
    Uuid? uuid,
    bool enLineaInicial = true,
  })  : _almacen = almacen ?? AlmacenSqlite.instancia,
        _api = api ?? SinConexionApi(),
        _cambiosDeRed = cambiosDeRed,
        _uuid = uuid ?? const Uuid(),
        _enLinea = enLineaInicial {
    _suscripcion = (_cambiosDeRed ?? _redDelSistema()).listen(_alCambiarRed);
  }

  static SinConexionServicio? _instancia;

  /// Instancia de la app (SQLite y red reales). Las pruebas crean la suya con dobles.
  static SinConexionServicio get instancia => _instancia ??= SinConexionServicio();

  /// La instancia solo si ya se creó (la crea el hub de un cliente); evita abrir SQLite y escuchar
  /// la red en sesiones de empleado o en pruebas.
  static SinConexionServicio? get instanciaSiExiste => _instancia;

  StreamSubscription<bool>? _suscripcion;
  Timer? _temporizador;
  int _reintentos = 0;

  String? _token;
  String? _clave;
  String? _codigoTienda;
  bool _enLinea;
  DispositivoLocal? _dispositivo;
  CatalogoLocal? _catalogo;
  DateTime? _guardadoEn;
  List<OperacionLocal> _operaciones = const [];
  int _avisosNoLeidos = 0;
  bool _sincronizando = false;
  bool _descargando = false;
  String? _aviso;

  bool get enLinea => _enLinea;
  String? get clave => _clave;
  DispositivoLocal? get dispositivo => _dispositivo;
  CatalogoLocal? get catalogo => _catalogo;
  DateTime? get guardadoEn => _guardadoEn;
  List<OperacionLocal> get operaciones => _operaciones;
  List<OperacionLocal> get pendientes => _operaciones.where((o) => o.pendiente).toList();
  int get avisosNoLeidos => _avisosNoLeidos;
  bool get sincronizando => _sincronizando;
  bool get descargando => _descargando;
  String? get aviso => _aviso;
  bool get preparado => _dispositivo?.codigoCorto != null;
  int get horasVencimiento => _dispositivo?.parametros?.horasVencimientoReserva ?? 24;
  bool get puedeReservarSinConexion =>
      (_dispositivo?.parametros?.operacionOfflineHabilitada ?? false) && _catalogo != null;

  // --------------------------------------------------------------------------- tienda

  /// Carga lo guardado de la tienda y, con red, la prepara para trabajar sin conexión.
  Future<void> prepararTienda({required String codigoTienda, required int idCliente, required String token}) async {
    final clave = '$codigoTienda:$idCliente';
    _token = token;
    if (_clave != clave) {
      _cancelarReintento();
      _reintentos = 0;
      _clave = clave;
      _codigoTienda = codigoTienda;
      _dispositivo = null;
      _catalogo = null;
      _guardadoEn = null;
      _operaciones = const [];
      _avisosNoLeidos = 0;
    }
    await _cargarLocal();
    if (!_enLinea) return;
    try {
      await registrarDispositivo();
      final guardado = _guardadoEn;
      if (guardado == null || DateTime.now().difference(guardado) > _vigenciaCatalogo) {
        await descargarCatalogo();
      }
      await sincronizar();
      await cargarAvisos();
    } on SinConexionException {
      // Sin red, servidor caído o cliente no registrado en la tienda: se trabaja con lo guardado.
    }
  }

  /// Al cerrar sesión: fuera el catálogo, pero nunca las operaciones pendientes (RNF03).
  Future<void> cerrarSesion() async {
    _cancelarReintento();
    _token = null;
    _clave = null;
    _codigoTienda = null;
    _dispositivo = null;
    _catalogo = null;
    _guardadoEn = null;
    _operaciones = const [];
    _avisosNoLeidos = 0;
    notifyListeners();
    await _almacen.borrarCatalogos();
  }

  Future<void> _cargarLocal() async {
    final clave = _clave;
    final codigo = _codigoTienda;
    if (clave == null || codigo == null) return;
    _dispositivo = await _almacen.dispositivo(clave);
    final catalogo = await _almacen.catalogo(codigo);
    _catalogo = catalogo?.$1;
    _guardadoEn = catalogo?.$2;
    _operaciones = await _almacen.operaciones(clave);
    notifyListeners();
  }

  // --------------------------------------------------------------------------- CU14

  Future<DispositivoLocal> registrarDispositivo() async {
    final clave = _exigirClave();
    var local = await _almacen.dispositivo(clave);
    if (local == null) {
      // El UUID se guarda antes de llamar a la API: se conserva aunque falle la red.
      local = DispositivoLocal(clave: clave, identificador: _uuid.v4());
      await _almacen.guardarDispositivo(local);
    }
    final dto = await _api.registrarDispositivo(
      local.identificador,
      token: _token ?? '',
      tokenPush: ServicioPush.instancia.tokenFCM,
    );
    final actual = await _almacen.dispositivo(clave) ?? local;
    final registrado = actual.copyWith(codigoCorto: dto.codigoCorto, parametros: dto.parametros);
    await _almacen.guardarDispositivo(registrado);

    // AC-C1: Asociar token push al dispositivo en el backend
    await ServicioPush.instancia.registrarTokenEnServidor(
      api: _api,
      identificadorDispositivo: local.identificador,
      tokenAuth: _token ?? '',
    );
    if (_clave == clave) {
      _dispositivo = registrado;
      notifyListeners();
    }
    return registrado;
  }

  /// Descarga el paquete y solo entonces reemplaza el guardado (A2). Sin espacio → indispensable (A3).
  Future<void> descargarCatalogo({String modo = 'completo'}) async {
    final clave = _exigirClave();
    final codigo = _codigoTienda!;
    final dispositivo = _dispositivo ?? await registrarDispositivo();
    _descargando = true;
    notifyListeners();
    try {
      final paquete = await _api.descargarCatalogo(dispositivo.identificador, modo, token: _token ?? '');
      final ahora = DateTime.now();
      try {
        await _almacen.guardarCatalogo(codigo, paquete, ahora);
      } on FileSystemException {
        if (modo == 'completo') {
          _aviso = 'No hay espacio suficiente en el teléfono: se descargó solo lo indispensable.';
          _descargando = false;
          return await descargarCatalogo(modo: 'indispensable');
        }
        rethrow;
      }
      if (_clave == clave) {
        _catalogo = CatalogoLocal.fromJson(paquete);
        _guardadoEn = ahora;
      }
    } finally {
      _descargando = false;
      notifyListeners();
    }
  }

  // --------------------------------------------------------------------------- CU15 A1

  /// Guarda la reserva en el teléfono con su código provisional (RN34).
  Future<OperacionLocal> reservarSinConexion({
    required int idSucursal,
    required DateTime fechaHoraAtencion,
    required List<Map<String, int>> items,
    required String titulo,
    required String detalle,
  }) async {
    final clave = _exigirClave();
    final dispositivo = _dispositivo;
    if (dispositivo?.codigoCorto == null || dispositivo?.parametros == null) {
      throw const SinConexionException('Para reservar sin conexión, abre antes la tienda con conexión.', codigoHttp: 0);
    }
    if (!dispositivo!.parametros!.operacionOfflineHabilitada) {
      throw const SinConexionException('Esta tienda no permite reservar sin conexión.', codigoHttp: 0);
    }
    final correlativo = await _almacen.siguienteCorrelativo(clave);
    final operacion = OperacionLocal(
      uuid: _uuid.v4(),
      clave: clave,
      tipo: 'reserva',
      idSucursal: idSucursal,
      registradaEn: DateTime.now(),
      codigoProvisional: 'PROV-${dispositivo.codigoCorto}-${correlativo.toString().padLeft(6, '0')}',
      datos: {'fecha_hora_atencion': fechaHoraAtencion.toUtc().toIso8601String(), 'items': items},
      estado: EstadoOperacion.registradaLocalmente,
      titulo: titulo,
      detalle: detalle,
    );
    await _almacen.guardarOperacion(operacion);
    _dispositivo = dispositivo.copyWith(correlativo: correlativo);
    _operaciones = [operacion, ..._operaciones];
    notifyListeners();
    if (_enLinea) unawaited(sincronizar());
    return operacion;
  }

  /// CU19 · Compra interrumpida: Stripe ya pudo cobrar pero la confirmación no llegó al servidor.
  /// Se guarda solo `{id_venta, id_pago}` (nunca datos de tarjeta); el servidor verifica el cobro.
  Future<OperacionLocal?> registrarCompraInterrumpida({
    required int idVenta,
    required int idPago,
    required String comprobante,
  }) async {
    final clave = _clave;
    if (clave == null) return null;
    final operacion = OperacionLocal(
      uuid: _uuid.v4(),
      clave: clave,
      tipo: 'compra_interrumpida',
      registradaEn: DateTime.now(),
      datos: {'id_venta': idVenta, 'id_pago': idPago},
      estado: EstadoOperacion.registradaLocalmente,
      titulo: 'Compra $comprobante',
      detalle: 'Pago registrado: se confirmará al recuperar la conexión.',
    );
    await _almacen.guardarOperacion(operacion);
    _operaciones = [operacion, ..._operaciones];
    notifyListeners();
    _programarReintento();
    return operacion;
  }

  // --------------------------------------------------------------------------- CU19

  /// Envía lo pendiente. Devuelve false si no pudo (sin red, error o sin preparar).
  Future<bool> sincronizar() async {
    final clave = _clave;
    final dispositivo = _dispositivo;
    if (clave == null || !_enLinea || _sincronizando || dispositivo?.codigoCorto == null) return false;
    final lote = pendientes.take(_loteMaximo).toList();
    if (lote.isEmpty) {
      await _refrescarSinFallar();
      return true;
    }

    _sincronizando = true;
    for (final op in lote) {
      await _actualizar(op.copyWith(estado: EstadoOperacion.enviada));
    }
    try {
      final resultados = await _api.sincronizar(
        dispositivo!.identificador,
        [for (final op in lote) op.paraEnviar()],
        token: _token ?? '',
      );
      var reintentar = false;
      for (final r in resultados) {
        final op = _operaciones.where((o) => o.uuid == r.uuid).firstOrNull;
        if (op == null) continue;
        if (r.estado == 'reintentar') {
          reintentar = true;
          await _actualizar(op.copyWith(estado: EstadoOperacion.registradaLocalmente, mensaje: r.mensaje));
        } else {
          await _actualizar(op.copyWith(
            estado: estadoDesdeServidor(r.estado),
            motivo: r.motivo,
            mensaje: r.mensaje,
            codigoReserva: r.codigoReserva,
          ));
        }
      }
      _reintentos = 0;
      _sincronizando = false;
      notifyListeners();
      try {
        await cargarAvisos();
      } on SinConexionException {
        // La bandeja se consultará en la próxima sincronización.
      }
      if (reintentar || pendientes.isNotEmpty) _programarReintento();
      return !reintentar;
    } on SinConexionException catch (e) {
      // Se conservan como pendientes (RN37) y se reintenta más tarde (A1), salvo sesión expirada (A5).
      for (final op in lote) {
        final actual = _operaciones.where((o) => o.uuid == op.uuid).firstOrNull;
        if (actual?.estado == EstadoOperacion.enviada) {
          await _actualizar(actual!.copyWith(estado: EstadoOperacion.registradaLocalmente));
        }
      }
      _sincronizando = false;
      notifyListeners();
      if (e.codigoHttp != 401) _programarReintento();
      return false;
    }
  }

  /// Trae del servidor cómo van las operaciones (p. ej. el reembolso de un conflicto, CU20 paso 5).
  Future<void> refrescarEstados() async {
    final dispositivo = _dispositivo;
    if (dispositivo?.codigoCorto == null || !_enLinea) return;
    final remotas = await _api.operaciones(dispositivo!.identificador, token: _token ?? '');
    for (final remota in remotas) {
      final local = _operaciones.where((o) => o.uuid == remota.uuid).firstOrNull;
      if (local == null) continue;
      final estado = estadoDesdeServidor(remota.estado);
      if (local.estado != estado || local.estadoConflicto != remota.estadoConflicto) {
        await _actualizar(local.copyWith(
          estado: estado,
          motivo: remota.motivo,
          codigoReserva: remota.codigoReserva,
          estadoConflicto: remota.estadoConflicto,
        ));
      }
    }
  }

  Future<BandejaAvisosDto> cargarAvisos() async {
    final bandeja = await _api.avisos(token: _token ?? '');
    _avisosNoLeidos = bandeja.noLeidos;
    notifyListeners();
    return bandeja;
  }

  Future<void> marcarAvisoLeido(int idAviso) async {
    await _api.marcarAvisoLeido(idAviso, token: _token ?? '');
    if (_avisosNoLeidos > 0) _avisosNoLeidos -= 1;
    notifyListeners();
  }

  // --------------------------------------------------------------------------- red

  Stream<bool> _redDelSistema() => Connectivity()
      .onConnectivityChanged
      .map((resultados) => resultados.any((r) => r != ConnectivityResult.none))
      // Sin el plugin (pruebas, escritorio) se trabaja como «con red» y se detecta el fallo al enviar.
      .handleError((Object _) {});

  Future<void> _alCambiarRed(bool hayRed) async {
    // Con red se comprueba además que el servidor responda (`/health`) antes de sincronizar.
    final enLinea = hayRed && await _api.servidorDisponible();
    if (enLinea == _enLinea) return;
    _enLinea = enLinea;
    notifyListeners();
    if (enLinea) unawaited(sincronizar());
  }

  /// Para las pruebas y para el botón «Reintentar» de la interfaz.
  @visibleForTesting
  Future<void> forzarEstadoDeRed(bool enLinea) async {
    _enLinea = enLinea;
    notifyListeners();
    if (enLinea) await sincronizar();
  }

  // --------------------------------------------------------------------------- apoyo

  Future<void> _refrescarSinFallar() async {
    try {
      await refrescarEstados();
    } on SinConexionException {
      // Se intentará en la próxima sincronización.
    }
  }

  Future<void> _actualizar(OperacionLocal operacion) async {
    await _almacen.guardarOperacion(operacion);
    _operaciones = [for (final o in _operaciones) o.uuid == operacion.uuid ? operacion : o];
    notifyListeners();
  }

  void _programarReintento() {
    _cancelarReintento();
    final segundos = _esperaInicial.inSeconds * (1 << _reintentos.clamp(0, 10));
    final espera = Duration(seconds: segundos.clamp(0, _esperaMaxima.inSeconds));
    _reintentos += 1;
    _temporizador = Timer(espera, () => unawaited(sincronizar()));
  }

  void _cancelarReintento() {
    _temporizador?.cancel();
    _temporizador = null;
  }

  String _exigirClave() {
    final clave = _clave;
    if (clave == null) throw const SinConexionException('No hay una tienda abierta.', codigoHttp: 0);
    return clave;
  }

  @override
  void dispose() {
    _cancelarReintento();
    _suscripcion?.cancel();
    super.dispose();
  }
}
