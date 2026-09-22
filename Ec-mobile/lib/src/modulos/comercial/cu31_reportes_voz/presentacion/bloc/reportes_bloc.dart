import 'package:flutter/foundation.dart';
import '../../datos/datasources/reportes_remoto_datasource.dart';
import '../../datos/modelos/reportes_voz_dto.dart';
import '../../datos/repositorios/reportes_repositorio_impl.dart';
import '../../dominio/repositorios/reportes_repositorio.dart';

/// Jerarquia de estados sellados inmutables para reportes y voz en UI
sealed class ReportesEstado {
  const ReportesEstado();
}

class ReportesInicial extends ReportesEstado {
  const ReportesInicial();
}

class ReportesCargando extends ReportesEstado {
  final String? mensaje;
  const ReportesCargando({this.mensaje});
}

class ReportesListo extends ReportesEstado {
  final ReportePrevisualizacionDto previsualizacion;
  final ComandoVozOut? comandoVoz;
  final List<SucursalOpcionDto> sucursales;
  final ArchivoReporteDescargado? archivoExportado;
  final String? mensajeExito;

  const ReportesListo({
    required this.previsualizacion,
    this.comandoVoz,
    this.sucursales = const [],
    this.archivoExportado,
    this.mensajeExito,
  });

  ReportesListo copyWith({
    ReportePrevisualizacionDto? previsualizacion,
    ComandoVozOut? comandoVoz,
    List<SucursalOpcionDto>? sucursales,
    ArchivoReporteDescargado? archivoExportado,
    String? mensajeExito,
    bool resetMensajeExito = false,
  }) {
    return ReportesListo(
      previsualizacion: previsualizacion ?? this.previsualizacion,
      comandoVoz: comandoVoz ?? this.comandoVoz,
      sucursales: sucursales ?? this.sucursales,
      archivoExportado: archivoExportado ?? this.archivoExportado,
      mensajeExito:
          resetMensajeExito ? null : (mensajeExito ?? this.mensajeExito),
    );
  }
}

class ReportesExportando extends ReportesEstado {
  final ReportePrevisualizacionDto previsualizacion;
  const ReportesExportando(this.previsualizacion);
}

class ReportesError extends ReportesEstado {
  final String mensaje;
  final ReportePrevisualizacionDto? ultimaPrevisualizacion;

  const ReportesError(this.mensaje, {this.ultimaPrevisualizacion});
}

/// BLoC / ChangeNotifier para coordinar la logica de negocio de CU31 en Flutter
class ReportesBloc extends ChangeNotifier {
  final ReportesRepositorio _repositorio;

  ReportesBloc({ReportesRepositorio? repositorio})
      : _repositorio = repositorio ?? ReportesRepositorioImpl();

  ReportesEstado _estado = const ReportesInicial();
  ReportesEstado get estado => _estado;

  ReporteFiltrosDto _filtros = const ReporteFiltrosDto(
    modulo: 'ventas',
    formato: 'excel',
    periodo: 'este_mes',
    idSucursal: null,
  );
  ReporteFiltrosDto get filtros => _filtros;

  List<SucursalOpcionDto> _sucursales = const [];
  List<SucursalOpcionDto> get sucursales => _sucursales;

  Future<void> inicializar(String token) async {
    _estado = const ReportesCargando(mensaje: 'Cargando centro de reportes...');
    notifyListeners();

    try {
      _sucursales = await _repositorio.listarSucursales(token);
      final prev = await _repositorio.previsualizar(token, _filtros);
      _estado = ReportesListo(
        previsualizacion: prev,
        sucursales: _sucursales,
      );
      notifyListeners();
    } catch (e) {
      _estado = ReportesError(e.toString());
      notifyListeners();
    }
  }

  Future<void> interpretarVoz(String token, String textoDictado) async {
    if (textoDictado.trim().isEmpty) return;

    _estado = const ReportesCargando(mensaje: 'Interpretando orden de voz...');
    notifyListeners();

    try {
      final resultadoVoz =
          await _repositorio.interpretarVoz(token, textoDictado);

      // Sincronizar filtros reactivos segun la orden parseada
      _filtros = _filtros.copyWith(
        modulo: resultadoVoz.modulo,
        formato: resultadoVoz.formato,
        periodo: resultadoVoz.periodo,
        idSucursal: resultadoVoz.idSucursal,
        resetSucursal: resultadoVoz.idSucursal == null,
        fechaInicio: resultadoVoz.fechaInicio,
        fechaFin: resultadoVoz.fechaFin,
      );

      final prev = await _repositorio.previsualizar(token, _filtros);

      _estado = ReportesListo(
        previsualizacion: prev,
        comandoVoz: resultadoVoz,
        sucursales: _sucursales,
        mensajeExito:
            'Orden interpretada: Modulo ${resultadoVoz.modulo.toUpperCase()}, Formato ${resultadoVoz.formato.toUpperCase()}, Periodo ${resultadoVoz.periodo.toUpperCase()}.',
      );
      notifyListeners();
    } catch (e) {
      _estado = ReportesError(e.toString());
      notifyListeners();
    }
  }

  Future<void> actualizarFiltros({
    required String token,
    String? modulo,
    String? formato,
    String? periodo,
    int? idSucursal,
    bool resetSucursal = false,
  }) async {
    _filtros = _filtros.copyWith(
      modulo: modulo,
      formato: formato,
      periodo: periodo,
      idSucursal: idSucursal,
      resetSucursal: resetSucursal,
    );

    _estado = const ReportesCargando(mensaje: 'Actualizando metricas...');
    notifyListeners();

    try {
      final prev = await _repositorio.previsualizar(token, _filtros);
      _estado = ReportesListo(
        previsualizacion: prev,
        sucursales: _sucursales,
      );
      notifyListeners();
    } catch (e) {
      _estado = ReportesError(e.toString());
      notifyListeners();
    }
  }

  Future<void> exportarReporte(String token) async {
    final estadoActual = _estado;
    ReportePrevisualizacionDto? prevActual;
    if (estadoActual is ReportesListo) {
      prevActual = estadoActual.previsualizacion;
      _estado = ReportesExportando(prevActual);
      notifyListeners();
    } else {
      _estado = const ReportesCargando(mensaje: 'Compilando archivo binario...');
      notifyListeners();
    }

    try {
      final archivo = await _repositorio.exportar(token, _filtros);

      // Volver a calcular previsualizacion fresca tras registro en bitacora
      final prevFresh = await _repositorio.previsualizar(token, _filtros);

      _estado = ReportesListo(
        previsualizacion: prevFresh,
        sucursales: _sucursales,
        archivoExportado: archivo,
        mensajeExito:
            'Archivo ${archivo.nombreArchivo} (${(archivo.bytes.lengthInBytes / 1024).toStringAsFixed(1)} KB) generado exitosamente.',
      );
      notifyListeners();
    } catch (e) {
      _estado = ReportesError(
        e.toString(),
        ultimaPrevisualizacion: prevActual,
      );
      notifyListeners();
    }
  }

  void limpiarMensajes() {
    final estadoActual = _estado;
    if (estadoActual is ReportesListo) {
      _estado = estadoActual.copyWith(resetMensajeExito: true);
      notifyListeners();
    }
  }
}
