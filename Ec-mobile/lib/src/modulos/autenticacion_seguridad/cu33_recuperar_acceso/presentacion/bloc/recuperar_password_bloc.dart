import 'dart:async';
import 'package:flutter/foundation.dart';
import '../../datos/modelos/recuperar_password_dto.dart';
import '../../dominio/repositorios/recuperar_password_repositorio.dart';

enum PasoRecuperacion { solicitar, restablecer }

sealed class RecuperarPasswordEstado {
  const RecuperarPasswordEstado();
}

class RecuperarPasswordInicial extends RecuperarPasswordEstado {
  const RecuperarPasswordInicial();
}

class RecuperarPasswordCargando extends RecuperarPasswordEstado {
  const RecuperarPasswordCargando();
}

class CodigoSolicitadoExitoso extends RecuperarPasswordEstado {
  final String mensaje;
  const CodigoSolicitadoExitoso(this.mensaje);
}

class RestablecimientoExitoso extends RecuperarPasswordEstado {
  final String mensaje;
  const RestablecimientoExitoso(this.mensaje);
}

class RecuperarPasswordError extends RecuperarPasswordEstado {
  final String mensaje;
  const RecuperarPasswordError(this.mensaje);
}

class RecuperarPasswordBloc extends ChangeNotifier {
  final RecuperarPasswordRepositorio _repositorio;

  RecuperarPasswordBloc({RecuperarPasswordRepositorio? repositorio})
      : _repositorio = repositorio ?? RecuperarPasswordRepositorioImpl();

  RecuperarPasswordEstado _estado = const RecuperarPasswordInicial();
  RecuperarPasswordEstado get estado => _estado;

  PasoRecuperacion _pasoActual = PasoRecuperacion.solicitar;
  PasoRecuperacion get pasoActual => _pasoActual;

  String _email = '';
  String get email => _email;

  int _segundosCooldown = 0;
  int get segundosCooldown => _segundosCooldown;

  int _nivelFortaleza = 0;
  int get nivelFortaleza => _nivelFortaleza;

  bool get estaCargando => _estado is RecuperarPasswordCargando;

  Timer? _temporizador;

  void setEmail(String email) {
    _email = email.trim();
  }

  void cambiarPaso(PasoRecuperacion paso) {
    _pasoActual = paso;
    _estado = const RecuperarPasswordInicial();
    notifyListeners();
  }

  void actualizarFortalezaPassword(String password) {
    if (password.isEmpty) {
      _nivelFortaleza = 0;
    } else {
      int score = 0;
      if (password.length >= 8) score++;
      final tieneLetra = RegExp(r'[a-zA-Z]').hasMatch(password);
      final tieneNumero = RegExp(r'[0-9]').hasMatch(password);
      if (tieneLetra && tieneNumero) score++;
      final tieneEspecial = RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(password);
      final tieneMayusYMinus = RegExp(r'[a-z]').hasMatch(password) && RegExp(r'[A-Z]').hasMatch(password);
      if (password.length >= 10 && (tieneEspecial || tieneMayusYMinus)) score++;
      _nivelFortaleza = score.clamp(0, 3);
    }
    notifyListeners();
  }

  Future<void> solicitarCodigo(String emailDestino) async {
    _email = emailDestino.trim();
    if (_email.isEmpty) {
      _estado = const RecuperarPasswordError('Por favor ingresa tu correo electrónico.');
      notifyListeners();
      return;
    }

    _estado = const RecuperarPasswordCargando();
    notifyListeners();

    try {
      final peticion = SolicitarCodigoPeticionDto(email: _email);
      final respuesta = await _repositorio.solicitarCodigo(peticion);
      
      _iniciarCooldown(respuesta.tiempoEsperaSegundos > 0 ? respuesta.tiempoEsperaSegundos : 60);
      _pasoActual = PasoRecuperacion.restablecer;
      _estado = CodigoSolicitadoExitoso(respuesta.mensaje);
      notifyListeners();
    } catch (e) {
      _estado = RecuperarPasswordError(e.toString());
      notifyListeners();
    }
  }

  Future<void> reenviarCodigo() async {
    if (_segundosCooldown > 0 || _email.isEmpty) return;

    _estado = const RecuperarPasswordCargando();
    notifyListeners();

    try {
      final peticion = SolicitarCodigoPeticionDto(email: _email);
      final respuesta = await _repositorio.solicitarCodigo(peticion);
      
      _iniciarCooldown(respuesta.tiempoEsperaSegundos > 0 ? respuesta.tiempoEsperaSegundos : 60);
      _estado = CodigoSolicitadoExitoso(respuesta.mensaje);
      notifyListeners();
    } catch (e) {
      _estado = RecuperarPasswordError(e.toString());
      notifyListeners();
    }
  }

  Future<void> restablecerPassword({
    required String codigo,
    required String nuevaPassword,
    required String confirmarPassword,
  }) async {
    final codigoLimpio = codigo.replaceAll(' ', '').trim();
    if (codigoLimpio.length != 6) {
      _estado = const RecuperarPasswordError('Ingresa los 6 dígitos del código de verificación.');
      notifyListeners();
      return;
    }

    if (nuevaPassword.length < 8) {
      _estado = const RecuperarPasswordError('La nueva contraseña debe tener al menos 8 caracteres.');
      notifyListeners();
      return;
    }

    if (nuevaPassword != confirmarPassword) {
      _estado = const RecuperarPasswordError('Las contraseñas no coinciden.');
      notifyListeners();
      return;
    }

    _estado = const RecuperarPasswordCargando();
    notifyListeners();

    try {
      final peticion = RestablecerPasswordPeticionDto(
        email: _email,
        codigo: codigoLimpio,
        nuevaPassword: nuevaPassword,
        confirmarPassword: confirmarPassword,
      );
      final respuesta = await _repositorio.restablecerPassword(peticion);
      _estado = RestablecimientoExitoso(respuesta.mensaje);
      notifyListeners();
    } catch (e) {
      _estado = RecuperarPasswordError(e.toString());
      notifyListeners();
    }
  }

  void _iniciarCooldown(int segundos) {
    _temporizador?.cancel();
    _segundosCooldown = segundos;
    _temporizador = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_segundosCooldown > 0) {
        _segundosCooldown--;
        notifyListeners();
      } else {
        timer.cancel();
      }
    });
  }

  void reiniciar() {
    _temporizador?.cancel();
    _segundosCooldown = 0;
    _nivelFortaleza = 0;
    _pasoActual = PasoRecuperacion.solicitar;
    _estado = const RecuperarPasswordInicial();
    notifyListeners();
  }

  @override
  void dispose() {
    _temporizador?.cancel();
    super.dispose();
  }
}
