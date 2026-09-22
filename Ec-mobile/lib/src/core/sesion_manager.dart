import 'dart:async';

/// Gestor centralizado de sesión para FashionStore Mobile.
///
/// Proporciona un mecanismo global para notificar la expiración de sesión
/// (HTTP 401 Unauthorized) desde cualquier capa de datos, permitiendo que
/// el widget raíz escuche el evento y redirija automáticamente al login.
///
/// Patrón: Singleton con StreamController broadcast.
class SesionManager {
  SesionManager._();

  static final SesionManager _instancia = SesionManager._();
  static SesionManager get instancia => _instancia;

  final StreamController<SesionEvento> _controlador =
      StreamController<SesionEvento>.broadcast();

  /// Stream al que el widget raíz debe suscribirse para reaccionar
  /// ante eventos de sesión (expiración, cierre forzado, etc.)
  Stream<SesionEvento> get eventos => _controlador.stream;

  bool _sesionExpiradaNotificada = false;

  /// Llamado por cualquier datasource al recibir un HTTP 401.
  /// Emite el evento solo una vez hasta que se reinicie con [reiniciar].
  void notificarSesionExpirada({String? mensaje}) {
    if (_sesionExpiradaNotificada) return;
    _sesionExpiradaNotificada = true;
    _controlador.add(
      SesionEvento(
        tipo: TipoEventoSesion.expirada,
        mensaje: mensaje ?? 'Tu sesión ha expirado. Inicia sesión nuevamente.',
      ),
    );
  }

  /// Reinicia el flag de notificación. Llamar tras un login exitoso.
  void reiniciar() {
    _sesionExpiradaNotificada = false;
  }

  /// Libera recursos. Normalmente no se llama en producción (singleton).
  void dispose() {
    _controlador.close();
  }
}

/// Tipo de evento de sesión.
enum TipoEventoSesion {
  expirada,
}

/// Evento emitido por el [SesionManager].
class SesionEvento {
  final TipoEventoSesion tipo;
  final String mensaje;

  const SesionEvento({
    required this.tipo,
    required this.mensaje,
  });
}
