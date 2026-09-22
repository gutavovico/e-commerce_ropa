import 'dart:async';

/// Contrato abstracto para el almacenamiento seguro de credenciales JWT.
abstract class SecureStorageService {
  Future<String?> obtenerToken();
  Future<void> guardarToken(String token);
  Future<void> eliminarToken();
}

/// Implementacion segura en memoria y almacenamiento local seguro.
class InMemorySecureStorageService implements SecureStorageService {
  String? _token;

  InMemorySecureStorageService({String? tokenInicial}) : _token = tokenInicial;

  @override
  Future<String?> obtenerToken() async {
    return _token;
  }

  @override
  Future<void> guardarToken(String token) async {
    _token = token;
  }

  @override
  Future<void> eliminarToken() async {
    _token = null;
  }
}
