import 'dart:async';
import 'package:flutter/material.dart';

import '../sin_conexion/sin_conexion_api.dart';
import '../../modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/pantallas/pantalla_mis_reservas.dart';
import '../../modulos/catalogo/cu19_asistente_chatbot/presentacion/pantallas/pantalla_asistente_estilo.dart';
import '../../modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart';
import '../../modulos/sincronizacion/cu19_sincronizacion/presentacion/pantalla_sincronizacion.dart';
import '../sin_conexion/sin_conexion_servicio.dart';

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
}

/// Orquestador central de notificaciones push para Android (FCM · RF37).
///
/// - H6: Solo Android. El token push se asocia al dispositivo existente.
/// - H9: En primer plano se muestra dentro de la app (barra inferior/banner),
///   sin dependencias externas de notificaciones locales.
/// - AC-C1: Asocia el token al dispositivo registrado en la tienda.
/// - AC-C5: Enruta automáticamente a la pantalla correspondiente al pulsar:
///   * Reserva (1, 2, 3) -> /reservas
///   * Conflicto (4) -> avisos / sincronización
///   * Pedido / Pago (5, 6) -> /compras
///   * Asistente (7) -> /asistente
class ServicioPush {
  ServicioPush._();
  static final ServicioPush instancia = ServicioPush._();

  String? _tokenFCM = 'fcm_token_simulado_${DateTime.now().millisecondsSinceEpoch}';
  final StreamController<NotificacionPush> _controladorPrimerPlano =
      StreamController<NotificacionPush>.broadcast();
  final StreamController<NotificacionPush> _controladorClick =
      StreamController<NotificacionPush>.broadcast();

  String? get tokenFCM => _tokenFCM;
  Stream<NotificacionPush> get enPrimerPlano => _controladorPrimerPlano.stream;
  Stream<NotificacionPush> get alPulsarNotificacion => _controladorClick.stream;

  /// Actualiza o establece el token FCM obtenido de Firebase Messaging.
  void fijarTokenFCM(String token) {
    _tokenFCM = token;
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
    final messenger = ScaffoldMessenger.of(context);
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
