import 'package:flutter/foundation.dart';
import '../../datos/modelos/perfil_dto.dart';
import '../../dominio/repositorios/perfil_repositorio.dart';

/// Jerarquía de estados sellados para la gestión de perfil
sealed class PerfilEstado {
  const PerfilEstado();
}

class PerfilInicial extends PerfilEstado {
  const PerfilInicial();
}

class PerfilCargando extends PerfilEstado {
  const PerfilCargando();
}

class PerfilCargado extends PerfilEstado {
  final PerfilClienteDto perfil;
  const PerfilCargado(this.perfil);
}

class PerfilActualizando extends PerfilEstado {
  final PerfilClienteDto perfilActual;
  const PerfilActualizando(this.perfilActual);
}

class PerfilActualizado extends PerfilEstado {
  final PerfilClienteDto perfil;
  const PerfilActualizado(this.perfil);
}

class PerfilError extends PerfilEstado {
  final String mensaje;
  final String? codigo;
  const PerfilError(this.mensaje, {this.codigo});
}

/// BLoC / ChangeNotifier para coordinar la lógica de negocio de perfil en UI
class PerfilBloc extends ChangeNotifier {
  final PerfilRepositorio _repositorio;

  PerfilBloc({PerfilRepositorio? repositorio})
      : _repositorio = repositorio ?? PerfilRepositorioImpl();

  PerfilEstado _estado = const PerfilInicial();
  PerfilEstado get estado => _estado;

  bool get estaCargando => _estado is PerfilCargando || _estado is PerfilActualizando;

  Future<void> cargarPerfil(String token) async {
    _estado = const PerfilCargando();
    notifyListeners();

    try {
      final perfil = await _repositorio.obtenerPerfil(token);
      _estado = PerfilCargado(perfil);
      notifyListeners();
    } catch (e) {
      _estado = PerfilError(e.toString());
      notifyListeners();
    }
  }

  Future<void> actualizarPerfil(
    String token,
    PerfilClienteUpdateDto datos,
  ) async {
    final estadoActual = _estado;
    if (estadoActual is PerfilCargado) {
      _estado = PerfilActualizando(estadoActual.perfil);
      notifyListeners();
    }

    try {
      final perfilNuevo = await _repositorio.actualizarPerfil(token, datos);
      _estado = PerfilActualizado(perfilNuevo);
      notifyListeners();
      // Transicionar a PerfilCargado con los datos nuevos
      _estado = PerfilCargado(perfilNuevo);
      notifyListeners();
    } catch (e) {
      _estado = PerfilError(e.toString());
      notifyListeners();
    }
  }

  void reiniciar() {
    _estado = const PerfilInicial();
    notifyListeners();
  }
}
