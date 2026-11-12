import 'dart:async';
import 'dart:io' show Platform;
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../sin_conexion/almacen_local.dart';
import '../sin_conexion/sin_conexion_api.dart';
import '../../modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/pantallas/pantalla_mis_reservas.dart';
import '../../modulos/catalogo/cu19_asistente_chatbot/presentacion/pantallas/pantalla_asistente_estilo.dart';
import '../../modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart';
import '../../modulos/sincronizacion/cu19_sincronizacion/presentacion/pantalla_sincronizacion.dart';
import '../sin_conexion/sin_conexion_servicio.dart';

/// Manejador de mensajes FCM cuando la aplicación está en segundo plano o cerrada.
@pragma('vm:entry-point')
Future<void> manejarMensajeSegundoPlanoFCM(RemoteMessage message) async {
  try {
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp();
    }
  } catch (_) {
    // En ausencia de google-services.json, no bloquea el proceso en segundo plano.
  }
}

/// Datos estructurados de una notificación push recibida (RF37).
class NotificacionPush {
  final String titulo;
  final String cuerpo;
  final Map<String, String> datos;

  const NotificacionPush({
    required this.titulo,
    required this.cuerpo,
    this.datos = const {},
  });

  String? get pantalla => datos['pantalla'];
  String? get idReferencia => datos['id'];

  factory NotificacionPush.fromMap(Map<String, dynamic> mapa) {
    final payloadDatos = (mapa['datos'] as Map?)?.map(
          (k, v) => MapEntry(k.toString(), v.toString()),
        ) ??
        const <String, String>{};

    return NotificacionPush(
      titulo: mapa['titulo']?.toString() ?? 'Fashion Store',
      cuerpo: mapa['cuerpo']?.toString() ?? '',
      datos: payloadDatos,
    );
  }

  factory NotificacionPush.fromRemoteMessage(RemoteMessage message) {
    final datos = message.data.map((k, v) => MapEntry(k, v.toString()));
    final titulo = message.notification?.title ?? datos['titulo'] ?? 'Fashion Store';
    final cuerpo = message.notification?.body ?? datos['cuerpo'] ?? '';
    return NotificacionPush(
      titulo: titulo,
      cuerpo: cuerpo,
      datos: datos,
    );
  }
}

/// Resultado de intentar activar las notificaciones push desde la interfaz móvil.
class ResultadoActivacionPush {
  final bool activadas;
  final bool permisoDenegado;
  final bool firebaseDisponible;
  final String mensaje;

  const ResultadoActivacionPush({
    required this.activadas,
    this.permisoDenegado = false,
    this.firebaseDisponible = false,
    required this.mensaje,
  });
}

/// Orquestador central de notificaciones push para Android (FCM · RF37).
///
/// - H6: Solo Android. El token push se asocia al dispositivo existente.
/// - H9: En primer plano se muestra dentro de la app (barra inferior/banner),
///   sin dependencias externas de notificaciones locales.
/// - AC-C1: Pide permiso y asocia el token al dispositivo registrado en la tienda.
/// - AC-C5: Enruta automáticamente a la pantalla correspondiente al pulsar:
///   * Reserva (1, 2, 3) -> /reservas
///   * Conflicto (4) -> avisos / sincronización
///   * Pedido / Pago (5, 6) -> /compras
///   * Asistente (7) -> /asistente
class ServicioPush extends ChangeNotifier {
  ServicioPush._();
  static final ServicioPush instancia = ServicioPush._();

  static const MethodChannel _canalNativo = MethodChannel('com.ecommerce.ec_mobile/notificaciones');
  static const String _clavePreferencia = '__notificaciones_activas__';
  static const String _clavePreguntado = '__notificaciones_preguntado__';

  String? _tokenFCM;
  bool _firebaseDisponible = false;
  bool _permisoConcedido = false;
  bool _preferenciaActiva = true;
  bool _preguntadoEnDispositivo = false;
  bool _inicializado = false;
  bool _bannerDescartadoEnSesion = false;
  NotificacionPush? _notificacionInicialPendiente;
  final Set<String> _clavesDeduplicadas = <String>{};

  StreamSubscription<RemoteMessage>? _subOnMessage;
  StreamSubscription<RemoteMessage>? _subOnOpenedApp;
  StreamSubscription<String>? _subTokenRefresh;
  Future<void> Function(String tokenPush)? _alRenovarTokenEnServidor;

  final StreamController<NotificacionPush> _controladorPrimerPlano =
      StreamController<NotificacionPush>.broadcast();
  final StreamController<NotificacionPush> _controladorClick =
      StreamController<NotificacionPush>.broadcast();

  String? get tokenFCM => _tokenFCM;
  bool get firebaseDisponible => _firebaseDisponible;
  bool get permisoConcedido => _permisoConcedido;
  bool get preferenciaActiva => _preferenciaActiva;
  bool get notificacionesActivas => _preferenciaActiva && _permisoConcedido;
  bool get inicializado => _inicializado;
  bool get bannerDescartadoEnSesion => _bannerDescartadoEnSesion;
  bool get mostrarBannerActivacion => !notificacionesActivas && !_bannerDescartadoEnSesion;

  Stream<NotificacionPush> get enPrimerPlano => _controladorPrimerPlano.stream;
  Stream<NotificacionPush> get alPulsarNotificacion => _controladorClick.stream;

  /// Inicializa Firebase Messaging (si está configurado) y consulta los permisos reales de Android.
  Future<void> inicializar({
    AlmacenLocal? almacen,
    bool omitirFirebase = false,
  }) async {
    if (_inicializado) return;
    final store = almacen ?? AlmacenSqlite.instancia;

    try {
      final pref = await store.valor(_clavePreferencia);
      if (pref != null && pref.containsKey('activa')) {
        _preferenciaActiva = pref['activa'] == true;
      }
      final preg = await store.valor(_clavePreguntado);
      if (preg != null && preg['preguntado'] == true) {
        _preguntadoEnDispositivo = true;
      }
    } catch (_) {
      // En pruebas o sin SQLite disponible conserva valores por defecto.
    }

    _permisoConcedido = await _verificarPermisoNativo();

    if (!kIsWeb && Platform.isAndroid) {
      _canalNativo.setMethodCallHandler((call) async {
        if (call.method == 'notificacionTocada') {
          final args = call.arguments as Map?;
          if (args != null) {
            tocarNotificacion(
              NotificacionPush(
                titulo: 'Fashion Store',
                cuerpo: '',
                datos: {
                  if (args['pantalla'] != null) 'pantalla': args['pantalla'].toString(),
                  if (args['id'] != null) 'id': args['id'].toString(),
                },
              ),
            );
          }
        }
      });

      try {
        final destinoInicial = await _canalNativo.invokeMapMethod<String, String>('consumirDestinoInicial');
        if (destinoInicial != null && destinoInicial.isNotEmpty) {
          _notificacionInicialPendiente ??= NotificacionPush(
            titulo: 'Fashion Store',
            cuerpo: '',
            datos: destinoInicial,
          );
        }
      } catch (_) {}
    }

    if (!omitirFirebase && !kIsWeb && Platform.isAndroid) {
      await _inicializarFirebaseReal();
    }

    _inicializado = true;
    notifyListeners();
  }

  Future<void> _inicializarFirebaseReal() async {
    try {
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp();
      }
      _firebaseDisponible = true;

      FirebaseMessaging.onBackgroundMessage(manejarMensajeSegundoPlanoFCM);

      final messaging = FirebaseMessaging.instance;
      await messaging.setForegroundNotificationPresentationOptions(
        alert: true,
        badge: true,
        sound: true,
      );

      final settings = await messaging.getNotificationSettings();
      if (settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional) {
        _permisoConcedido = true;
      }

      await _subOnMessage?.cancel();
      _subOnMessage = FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        if (!_preferenciaActiva) return;
        recibirNotificacionEnPrimerPlano(NotificacionPush.fromRemoteMessage(message));
      });

      await _subOnOpenedApp?.cancel();
      _subOnOpenedApp = FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
        tocarNotificacion(NotificacionPush.fromRemoteMessage(message));
      });

      final inicial = await messaging.getInitialMessage();
      if (inicial != null) {
        _notificacionInicialPendiente = NotificacionPush.fromRemoteMessage(inicial);
      }

      await _subTokenRefresh?.cancel();
      _subTokenRefresh = messaging.onRegistered.listen((nuevoToken) {
        _tokenFCM = nuevoToken;
        notifyListeners();
        if (_preferenciaActiva && nuevoToken.isNotEmpty) {
          unawaited(_alRenovarTokenEnServidor?.call(nuevoToken));
        }
      });

      if (_preferenciaActiva && _permisoConcedido) {
        await messaging.register();
      }
    } catch (_) {
      // Si falta google-services.json o estamos en entorno sin Play Services, degradamos con elegancia.
      _firebaseDisponible = false;
    }
  }

  /// Consume la notificación que abrió la app desde estado cerrado (`getInitialMessage`).
  NotificacionPush? consumirNotificacionInicial() {
    final pendiente = _notificacionInicialPendiente;
    _notificacionInicialPendiente = null;
    return pendiente;
  }

  /// Registra el callback que se ejecutará si Firebase rota el token en segundo plano.
  void configurarCallbackRenovacionToken(Future<void> Function(String tokenPush)? callback) {
    _alRenovarTokenEnServidor = callback;
  }

  /// Descarta temporalmente el banner de invitación de la sesión actual.
  void descartarBannerActivacion() {
    _bannerDescartadoEnSesion = true;
    notifyListeners();
  }

  /// Al entrar a una tienda como cliente (`AC-C1`), solicita el permiso si aún no se preguntó.
  Future<void> solicitarAlEntrarTiendaSiCorresponde({
    SinConexionApi? api,
    String? identificadorDispositivo,
    String? tokenAuth,
    AlmacenLocal? almacen,
  }) async {
    if (!_inicializado) {
      await inicializar(almacen: almacen);
    }
    if (_preguntadoEnDispositivo && _permisoConcedido && _preferenciaActiva) {
      await _asegurarTokenYRegistrar(
        api: api,
        identificadorDispositivo: identificadorDispositivo,
        tokenAuth: tokenAuth,
      );
      return;
    }
    if (_preguntadoEnDispositivo || !_preferenciaActiva) return;

    _preguntadoEnDispositivo = true;
    try {
      await (almacen ?? AlmacenSqlite.instancia).guardarValor(_clavePreguntado, {'preguntado': true});
    } catch (_) {}

    await activarNotificaciones(
      api: api,
      identificadorDispositivo: identificadorDispositivo,
      tokenAuth: tokenAuth,
      almacen: almacen,
    );
  }

  /// Solicita permisos al sistema operativo Android, obtiene el token FCM real y lo registra en el backend.
  Future<ResultadoActivacionPush> activarNotificaciones({
    SinConexionApi? api,
    String? identificadorDispositivo,
    String? tokenAuth,
    AlmacenLocal? almacen,
  }) async {
    final store = almacen ?? AlmacenSqlite.instancia;
    _preguntadoEnDispositivo = true;
    try {
      await store.guardarValor(_clavePreguntado, {'preguntado': true});
    } catch (_) {}

    bool concedido = await _solicitarPermisoNativo();

    if (_firebaseDisponible) {
      try {
        final settings = await FirebaseMessaging.instance.requestPermission(
          alert: true,
          badge: true,
          sound: true,
        );
        if (settings.authorizationStatus == AuthorizationStatus.authorized ||
            settings.authorizationStatus == AuthorizationStatus.provisional) {
          concedido = true;
        }
      } catch (_) {}
    }

    _permisoConcedido = concedido;

    if (!concedido) {
      _preferenciaActiva = false;
      try {
        await store.guardarValor(_clavePreferencia, {'activa': false});
      } catch (_) {}
      notifyListeners();
      return ResultadoActivacionPush(
        activadas: false,
        permisoDenegado: true,
        firebaseDisponible: _firebaseDisponible,
        mensaje: 'Permiso de notificaciones denegado en Android. Actívalo desde Ajustes del sistema.',
      );
    }

    _preferenciaActiva = true;
    _bannerDescartadoEnSesion = false;
    try {
      await store.guardarValor(_clavePreferencia, {'activa': true});
    } catch (_) {}

    await _asegurarTokenYRegistrar(
      api: api,
      identificadorDispositivo: identificadorDispositivo,
      tokenAuth: tokenAuth,
    );

    notifyListeners();

    if (_firebaseDisponible && _tokenFCM != null && _tokenFCM!.isNotEmpty) {
      return const ResultadoActivacionPush(
        activadas: true,
        permisoDenegado: false,
        firebaseDisponible: true,
        mensaje: 'Notificaciones push activadas en este dispositivo.',
      );
    }

    return ResultadoActivacionPush(
      activadas: true,
      permisoDenegado: false,
      firebaseDisponible: _firebaseDisponible,
      mensaje: _firebaseDisponible
          ? 'Permiso concedido. Esperando registro de token FCM con Google Play Services.'
          : 'Permiso y canal local activados. Agrega google-services.json al compilar para recibir avisos FCM remotos.',
    );
  }

  Future<void> _asegurarTokenYRegistrar({
    SinConexionApi? api,
    String? identificadorDispositivo,
    String? tokenAuth,
  }) async {
    if (_firebaseDisponible && (_tokenFCM == null || _tokenFCM!.isEmpty)) {
      try {
        final esperaToken = FirebaseMessaging.instance.onRegistered.first.timeout(
          const Duration(seconds: 3),
        );
        await FirebaseMessaging.instance.register();
        final token = await esperaToken;
        if (token.isNotEmpty) {
          _tokenFCM = token;
        }
      } catch (_) {}
    }

    if (api != null &&
        identificadorDispositivo != null &&
        identificadorDispositivo.isNotEmpty &&
        tokenAuth != null &&
        tokenAuth.isNotEmpty &&
        _tokenFCM != null &&
        _tokenFCM!.isNotEmpty) {
      await registrarTokenEnServidor(
        api: api,
        identificadorDispositivo: identificadorDispositivo,
        tokenAuth: tokenAuth,
      );
    }
  }

  /// Desactiva las notificaciones en la app y limpia el token push en el backend.
  Future<void> desactivarNotificaciones({
    SinConexionApi? api,
    String? identificadorDispositivo,
    String? tokenAuth,
    AlmacenLocal? almacen,
  }) async {
    _preferenciaActiva = false;
    try {
      await (almacen ?? AlmacenSqlite.instancia).guardarValor(_clavePreferencia, {'activa': false});
    } catch (_) {}

    if (api != null &&
        identificadorDispositivo != null &&
        identificadorDispositivo.isNotEmpty &&
        tokenAuth != null &&
        tokenAuth.isNotEmpty) {
      try {
        await api.registrarTokenPush(identificadorDispositivo, '', token: tokenAuth);
      } catch (_) {}
    }
    notifyListeners();
  }

  /// Dispara una notificación local real en la barra de Android + banner in-app y prueba en backend si aplica.
  Future<void> enviarNotificacionPruebaLocal({
    SinConexionApi? api,
    String? tokenAuth,
  }) async {
    const titulo = 'Fashion Store · Notificaciones activas';
    const cuerpo = 'Recibirás avisos de tus reservas, pedidos y asistente de estilo.';

    await notificarEvento(
      titulo: titulo,
      cuerpo: cuerpo,
      datos: const {'pantalla': 'reservas'},
    );

    if (api != null && tokenAuth != null && tokenAuth.isNotEmpty && _firebaseDisponible && _tokenFCM != null) {
      try {
        await api.probarPush(token: tokenAuth);
      } catch (_) {}
    }
  }

  /// Emite una notificación real de un evento de negocio (reserva, compra, asistente, aviso).
  ///
  /// Muestra notificación nativa en Android (barra de estado) y el banner in-app boutique (H9),
  /// respetando la preferencia del usuario y evitando duplicados mediante [claveDeduplicacion].
  Future<void> notificarEvento({
    required String titulo,
    required String cuerpo,
    Map<String, String> datos = const {},
    String? claveDeduplicacion,
  }) async {
    if (!_preferenciaActiva) return;
    if (claveDeduplicacion != null && !_clavesDeduplicadas.add(claveDeduplicacion)) {
      return;
    }

    final notif = NotificacionPush(titulo: titulo, cuerpo: cuerpo, datos: datos);
    await mostrarNotificacionLocalSistema(
      titulo: titulo,
      cuerpo: cuerpo,
      pantalla: datos['pantalla'],
      idRef: datos['id'],
    );
    recibirNotificacionEnPrimerPlano(notif);
  }

  /// Muestra una notificación nativa en la barra de estado de Android (solo móvil Android).
  Future<bool> mostrarNotificacionLocalSistema({
    required String titulo,
    required String cuerpo,
    String? pantalla,
    String? idRef,
  }) async {
    if (kIsWeb || !Platform.isAndroid || !_preferenciaActiva) return false;
    try {
      final args = <String, dynamic>{
        'titulo': titulo,
        'cuerpo': cuerpo,
      };
      if (pantalla != null) args['pantalla'] = pantalla;
      if (idRef != null) args['id'] = idRef;
      final res = await _canalNativo.invokeMethod<bool>(
        'mostrarNotificacionLocal',
        args,
      );
      return res ?? false;
    } catch (_) {
      return false;
    }
  }

  /// Abre la pantalla de ajustes de notificaciones de Android para esta aplicación.
  Future<void> abrirAjustesSistema() async {
    if (kIsWeb || !Platform.isAndroid) return;
    try {
      await _canalNativo.invokeMethod('abrirAjustesNotificaciones');
    } catch (_) {}
  }

  Future<bool> _verificarPermisoNativo() async {
    if (kIsWeb || !Platform.isAndroid) return _permisoConcedido;
    try {
      final res = await _canalNativo.invokeMethod<bool>('verificarPermiso');
      return res ?? false;
    } catch (_) {
      return _permisoConcedido;
    }
  }

  Future<bool> _solicitarPermisoNativo() async {
    if (kIsWeb || !Platform.isAndroid) return true;
    try {
      final res = await _canalNativo.invokeMethod<bool>('solicitarPermiso');
      return res ?? false;
    } catch (_) {
      return _permisoConcedido;
    }
  }

  /// Actualiza o establece el token FCM (útil para inyección en pruebas o sincronización manual).
  void fijarTokenFCM(String token) {
    _tokenFCM = token;
    notifyListeners();
  }

  /// Permite ajustar el estado en pruebas unitarias sin plataforma Android real.
  @visibleForTesting
  void configurarEstadoParaPruebas({
    bool? permisoConcedido,
    bool? preferenciaActiva,
    bool? firebaseDisponible,
    bool? inicializado,
    bool? bannerDescartado,
    String? tokenFCM,
  }) {
    if (permisoConcedido != null) _permisoConcedido = permisoConcedido;
    if (preferenciaActiva != null) _preferenciaActiva = preferenciaActiva;
    if (firebaseDisponible != null) _firebaseDisponible = firebaseDisponible;
    if (inicializado != null) _inicializado = inicializado;
    if (bannerDescartado != null) _bannerDescartadoEnSesion = bannerDescartado;
    if (tokenFCM != null) _tokenFCM = tokenFCM;
    notifyListeners();
  }

  /// Recibe un push mientras la aplicación está en primer plano (H9).
  void recibirNotificacionEnPrimerPlano(NotificacionPush notificacion) {
    _controladorPrimerPlano.add(notificacion);
  }

  /// Simula o gestiona el toque del usuario sobre una notificación recibida (AC-C5).
  void tocarNotificacion(NotificacionPush notificacion) {
    _controladorClick.add(notificacion);
  }

  /// Registra el token push en el backend asociado al dispositivo y tienda actual (AC-C1).
  Future<void> registrarTokenEnServidor({
    required SinConexionApi api,
    required String identificadorDispositivo,
    required String tokenAuth,
  }) async {
    final tokenPush = _tokenFCM;
    if (tokenPush == null || tokenPush.isEmpty) return;

    try {
      await api.registrarTokenPush(
        identificadorDispositivo,
        tokenPush,
        token: tokenAuth,
      );
    } catch (_) {
      // Best-effort: si no hay red, se reintentará en la siguiente sincronización
    }
  }

  /// Muestra el aviso in-app en la parte inferior de la pantalla con estilo boutique (H9).
  void mostrarBannerPrimerPlano(
    BuildContext context,
    NotificacionPush notificacion, {
    VoidCallback? alVer,
  }) {
    final messenger = ScaffoldMessenger.maybeOf(context);
    if (messenger == null) return;
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.notifications_active_outlined, color: Colors.white, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    notificacion.titulo,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              notificacion.cuerpo,
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 12,
                color: Colors.grey.shade300,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        backgroundColor: const Color(0xFF0F1116),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: 'VER',
          textColor: const Color(0xFFD4AF37), // Oro boutique
          onPressed: alVer ?? () => tocarNotificacion(notificacion),
        ),
      ),
    );
  }

  /// Navega a la pantalla de destino especificada en el payload de la notificación (AC-C5).
  void navegarADestino({
    required GlobalKey<NavigatorState> navegadorKey,
    required String token,
    required NotificacionPush notificacion,
    bool habilitarImagenesRed = true,
  }) {
    final contexto = navegadorKey.currentContext;
    if (contexto == null) return;

    final navState = navegadorKey.currentState;
    if (navState == null) return;

    final pantalla = notificacion.pantalla?.toLowerCase().trim() ?? '';

    switch (pantalla) {
      case 'reservas':
        navState.push(
          MaterialPageRoute(
            builder: (_) => PantallaMisReservas(
              token: token,
              habilitarImagenesRed: habilitarImagenesRed,
            ),
          ),
        );
        break;

      case 'avisos':
        final servicio = SinConexionServicio.instanciaSiExiste;
        if (servicio != null) {
          navState.push(
            MaterialPageRoute(
              builder: (_) => PantallaSincronizacion(servicio: servicio),
            ),
          );
        } else {
          navState.push(
            MaterialPageRoute(
              builder: (_) => PantallaPerfil(
                token: token,
                habilitarImagenesRed: habilitarImagenesRed,
              ),
            ),
          );
        }
        break;

      case 'compras':
        navState.push(
          MaterialPageRoute(
            builder: (_) => PantallaPerfil(
              token: token,
              habilitarImagenesRed: habilitarImagenesRed,
            ),
          ),
        );
        break;

      case 'asistente':
        navState.push(
          MaterialPageRoute(
            builder: (_) => PantallaAsistenteEstilo(token: token),
          ),
        );
        break;

      default:
        // Por defecto, abre el perfil / centro de usuario
        navState.push(
          MaterialPageRoute(
            builder: (_) => PantallaPerfil(
              token: token,
              habilitarImagenesRed: habilitarImagenesRed,
            ),
          ),
        );
        break;
    }
  }
}
