import 'package:flutter/foundation.dart';

import '../../datos/datasources/reservas_api.dart';
import '../../datos/modelos/reserva_dto.dart';

/// Estados sellados del ciclo de consulta de CU13/CU14.
sealed class ReservasEstado {
  const ReservasEstado();
}

class ReservasInicial extends ReservasEstado {
  const ReservasInicial();
}

class ReservasCargando extends ReservasEstado {
  const ReservasCargando();
}

class ReservasListo extends ReservasEstado {
  final MisReservasDto misReservas;
  const ReservasListo(this.misReservas);
}

class ReservasError extends ReservasEstado {
  final String mensaje;
  const ReservasError(this.mensaje);
}

/// Orquesta CU13 (consultar y cancelar reservas) y CU14 (consultar estado de reserva): un único
/// `GET /reservas/mias` cubre ambos, igual que en Web (`MisReservasService`).
class MisReservasBloc extends ChangeNotifier {
  final ReservasApi _api;
  final String _token;

  ReservasEstado _estado = const ReservasInicial();
  ReservasEstado get estado => _estado;

  /// Cobertura propia, separada del estado del listado: cancelar no debe hacer desaparecer la
  /// lista ya cargada mientras la petición está en vuelo.
  bool _cancelando = false;
  bool get cancelando => _cancelando;

  String? _errorCancelacion;
  String? get errorCancelacion => _errorCancelacion;

  MisReservasBloc({ReservasApi? api, required String token})
      : _api = api ?? ReservasApiImpl(),
        _token = token;

  Future<void> cargarMisReservas() async {
    _estado = const ReservasCargando();
    notifyListeners();

    try {
      final datos = await _api.obtenerMisReservas(token: _token);
      _estado = ReservasListo(datos);
    } on ReservaException catch (e) {
      _estado = ReservasError(e.mensaje);
    }
    notifyListeners();
  }

  /// Cancela una reserva propia. Tras el éxito, se recarga la lista completa: es el servidor
  /// quien decide el nuevo reparto entre "próximas" e "historial", no este cliente.
  Future<bool> cancelarReserva(int idReserva, String motivo) async {
    _cancelando = true;
    _errorCancelacion = null;
    notifyListeners();

    try {
      await _api.cancelarReserva(idReserva, motivo, token: _token);
      await cargarMisReservas();
      _cancelando = false;
      notifyListeners();
      return true;
    } on ReservaException catch (e) {
      _errorCancelacion = e.mensaje;
      _cancelando = false;
      notifyListeners();
      return false;
    }
  }

  void limpiarErrorCancelacion() {
    _errorCancelacion = null;
    notifyListeners();
  }
}
