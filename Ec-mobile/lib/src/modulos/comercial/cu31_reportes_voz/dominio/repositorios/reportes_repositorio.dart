import '../../datos/datasources/reportes_remoto_datasource.dart';
import '../../datos/modelos/reportes_voz_dto.dart';

/// Contrato de repositorio de dominio para reportes ejecutivos y voz (CU31)
abstract class ReportesRepositorio {
  Future<ComandoVozOut> interpretarVoz(String token, String textoDictado);

  Future<ReportePrevisualizacionDto> previsualizar(
    String token,
    ReporteFiltrosDto filtros,
  );

  Future<ArchivoReporteDescargado> exportar(
    String token,
    ReporteFiltrosDto filtros,
  );

  Future<List<SucursalOpcionDto>> listarSucursales(String token);
}
