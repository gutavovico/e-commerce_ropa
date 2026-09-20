import '../../datos/fuentes_datos/login_remoto_datasource.dart';
import '../../datos/modelos/login_dto.dart';

abstract class LoginRepositorio {
  Future<LoginRespuestaDto> autenticarUsuario(LoginPeticionDto datos);
  Future<void> cerrarSesion(String token);
}

class LoginRepositorioImpl implements LoginRepositorio {
  final LoginRemotoDatasource _datasource;

  LoginRepositorioImpl({LoginRemotoDatasource? datasource})
      : _datasource = datasource ?? LoginRemotoDatasource();

  @override
  Future<LoginRespuestaDto> autenticarUsuario(LoginPeticionDto datos) {
    return _datasource.autenticarUsuario(datos);
  }

  @override
  Future<void> cerrarSesion(String token) {
    return _datasource.cerrarSesion(token);
  }
}
