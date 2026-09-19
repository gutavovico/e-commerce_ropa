import '../../datos/fuentes_datos/registro_remoto_datasource.dart';
import '../../datos/modelos/registro_dto.dart';

abstract class RegistroRepositorio {
  Future<RegistroRespuestaDto> registrarCliente(RegistroClienteDto datos);
}

class RegistroRepositorioImpl implements RegistroRepositorio {
  final RegistroRemotoDatasource _datasource;

  RegistroRepositorioImpl({RegistroRemotoDatasource? datasource})
      : _datasource = datasource ?? RegistroRemotoDatasource();

  @override
  Future<RegistroRespuestaDto> registrarCliente(RegistroClienteDto datos) {
    return _datasource.registrarCliente(datos);
  }
}
