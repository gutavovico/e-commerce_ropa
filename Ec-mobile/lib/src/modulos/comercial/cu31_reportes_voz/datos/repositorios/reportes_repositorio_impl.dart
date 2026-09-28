import '../../dominio/repositorios/reportes_repositorio.dart';
import '../datasources/reportes_remoto_datasource.dart';
import '../modelos/reportes_voz_dto.dart';

/// Implementacion del repositorio de dominio consumiendo el datasource remoto
class ReportesRepositorioImpl implements ReportesRepositorio {
  final ReportesRemotoDatasource _datasource;

  ReportesRepositorioImpl({ReportesRemotoDatasource? datasource})
      : _datasource = datasource ?? ReportesRemotoDatasource();

  @override
  Future<ComandoVozOut> interpretarVoz(String token, String textoDictado) {
    return _datasource.interpretarComandoVoz(
      token,
      ComandoVozIn(textoDictado: textoDictado),
    );
  }

  @override
  Future<ReportePrevisualizacionDto> previsualizar(
    String token,
    ReporteFiltrosDto filtros,
  ) {
    return _datasource.previsualizarReporte(token, filtros);
  }

  @override
  Future<ArchivoReporteDescargado> exportar(
    String token,
    ReporteFiltrosDto filtros,
  ) {
    return _datasource.exportarReporte(token, filtros);
  }

  @override
  Future<List<SucursalOpcionDto>> listarSucursales(String token) {
    return _datasource.obtenerSucursales(token);
  }
}
