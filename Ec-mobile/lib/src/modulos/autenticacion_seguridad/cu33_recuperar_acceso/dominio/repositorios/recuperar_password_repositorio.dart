import '../../datos/fuentes_datos/recuperar_password_remoto_datasource.dart';
import '../../datos/modelos/recuperar_password_dto.dart';

abstract class RecuperarPasswordRepositorio {
  Future<SolicitarCodigoRespuestaDto> solicitarCodigo(SolicitarCodigoPeticionDto datos);
  Future<RestablecerPasswordRespuestaDto> restablecerPassword(RestablecerPasswordPeticionDto datos);
}

class RecuperarPasswordRepositorioImpl implements RecuperarPasswordRepositorio {
  final RecuperarPasswordRemotoDatasource _datasource;

  RecuperarPasswordRepositorioImpl({RecuperarPasswordRemotoDatasource? datasource})
      : _datasource = datasource ?? RecuperarPasswordRemotoDatasource();

  @override
  Future<SolicitarCodigoRespuestaDto> solicitarCodigo(SolicitarCodigoPeticionDto datos) {
    return _datasource.solicitarCodigo(datos);
  }

  @override
  Future<RestablecerPasswordRespuestaDto> restablecerPassword(RestablecerPasswordPeticionDto datos) {
    return _datasource.restablecerPassword(datos);
  }
}
