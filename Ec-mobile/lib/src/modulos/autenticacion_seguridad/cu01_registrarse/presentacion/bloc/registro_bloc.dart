import 'package:flutter/foundation.dart';
import '../../datos/modelos/registro_dto.dart';
import '../../dominio/repositorios/registro_repositorio.dart';

/// Jerarquía de estados para el flujo de registro
sealed class RegistroEstado {
  const RegistroEstado();
}

class RegistroInicial extends RegistroEstado {
  const RegistroInicial();
}

class RegistroCargando extends RegistroEstado {
  const RegistroCargando();
}

class RegistroExitoso extends RegistroEstado {
  final RegistroRespuestaDto respuesta;
  const RegistroExitoso(this.respuesta);
}

class RegistroFallido extends RegistroEstado {
  final String mensaje;
  final String? codigo;
  const RegistroFallido(this.mensaje, {this.codigo});
}

/// BLoC / Controller para gestionar la lógica de presentación del registro
class RegistroBloc extends ChangeNotifier {
  final RegistroRepositorio _repositorio;

  RegistroBloc({RegistroRepositorio? repositorio})
      : _repositorio = repositorio ?? RegistroRepositorioImpl();

  RegistroEstado _estado = const RegistroInicial();
  RegistroEstado get estado => _estado;

  bool get estaCargando => _estado is RegistroCargando;

  Future<void> registrarCliente(RegistroClienteDto datos) async {
    _estado = const RegistroCargando();
    notifyListeners();

    try {
      final respuesta = await _repositorio.registrarCliente(datos);
      _estado = RegistroExitoso(respuesta);
      notifyListeners();
    } catch (e) {
      _estado = RegistroFallido(e.toString());
      notifyListeners();
    }
  }

  void reiniciar() {
    _estado = const RegistroInicial();
    notifyListeners();
  }
}
