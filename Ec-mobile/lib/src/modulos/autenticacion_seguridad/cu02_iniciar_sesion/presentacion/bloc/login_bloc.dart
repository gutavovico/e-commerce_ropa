import 'package:flutter/foundation.dart';
import '../../datos/modelos/login_dto.dart';
import '../../dominio/repositorios/login_repositorio.dart';

/// Jerarquía de estados sellados para el flujo de autenticación
sealed class LoginEstado {
  const LoginEstado();
}

class LoginInicial extends LoginEstado {
  const LoginInicial();
}

class LoginCargando extends LoginEstado {
  const LoginCargando();
}

class LoginExitoso extends LoginEstado {
  final LoginRespuestaDto respuesta;
  const LoginExitoso(this.respuesta);
}

class LoginFallido extends LoginEstado {
  final String mensaje;
  final String? codigo;
  const LoginFallido(this.mensaje, {this.codigo});
}

/// BLoC / Controller para gestionar la lógica de presentación del login
class LoginBloc extends ChangeNotifier {
  final LoginRepositorio _repositorio;

  LoginBloc({LoginRepositorio? repositorio})
      : _repositorio = repositorio ?? LoginRepositorioImpl();

  LoginEstado _estado = const LoginInicial();
  LoginEstado get estado => _estado;

  bool get estaCargando => _estado is LoginCargando;

  Future<void> iniciarSesion(LoginPeticionDto datos) async {
    _estado = const LoginCargando();
    notifyListeners();

    try {
      final respuesta = await _repositorio.autenticarUsuario(datos);
      _estado = LoginExitoso(respuesta);
      notifyListeners();
    } catch (e) {
      _estado = LoginFallido(e.toString());
      notifyListeners();
    }
  }

  void reiniciar() {
    _estado = const LoginInicial();
    notifyListeners();
  }

  Future<void> cerrarSesion(String token) async {
    try {
      await _repositorio.cerrarSesion(token);
    } catch (_) {
      // Resiliencia ante fallos
    }
    reiniciar();
  }
}
