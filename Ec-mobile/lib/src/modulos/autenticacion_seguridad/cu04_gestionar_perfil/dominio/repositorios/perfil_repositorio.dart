import '../../datos/fuentes_datos/perfil_remoto_datasource.dart';
import '../../datos/modelos/perfil_dto.dart';

abstract class PerfilRepositorio {
  Future<PerfilClienteDto> obtenerPerfil(String token);
  Future<PerfilClienteDto> actualizarPerfil(String token, PerfilClienteUpdateDto datos);
}

class PerfilRepositorioImpl implements PerfilRepositorio {
  final PerfilRemotoDatasource _datasource;

  PerfilRepositorioImpl({PerfilRemotoDatasource? datasource})
      : _datasource = datasource ?? PerfilRemotoDatasource();

  @override
  Future<PerfilClienteDto> obtenerPerfil(String token) {
    return _datasource.obtenerPerfil(token);
  }

  @override
  Future<PerfilClienteDto> actualizarPerfil(
    String token,
    PerfilClienteUpdateDto datos,
  ) {
    return _datasource.actualizarPerfil(token, datos);
  }
}
