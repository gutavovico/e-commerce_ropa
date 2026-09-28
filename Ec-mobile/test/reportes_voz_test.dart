import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/comercial/cu31_reportes_voz/datos/datasources/reportes_remoto_datasource.dart';
import 'package:ec_mobile/src/modulos/comercial/cu31_reportes_voz/datos/modelos/reportes_voz_dto.dart';
import 'package:ec_mobile/src/modulos/comercial/cu31_reportes_voz/dominio/repositorios/reportes_repositorio.dart';
import 'package:ec_mobile/src/modulos/comercial/cu31_reportes_voz/presentacion/bloc/reportes_bloc.dart';
import 'package:ec_mobile/src/modulos/comercial/cu31_reportes_voz/presentacion/pantallas/pantalla_reportes_voz.dart';

class MockReportesRepositorio implements ReportesRepositorio {
  bool fueInterpretado = false;
  bool fueExportado = false;

  final ReportePrevisualizacionDto mockPrev = const ReportePrevisualizacionDto(
    modulo: 'ventas',
    formato: 'excel',
    totalRegistros: 29,
    fechaCorte: '2026-09-22T10:00:00Z',
    nombreArchivoSugerido: 'reporte_ventas_20260922.xlsx',
    resumenFinanciero: {
      'monto_total_bob': 49748.0,
      'ventas_promedio_bob': 1715.45,
    },
  );

  final List<SucursalOpcionDto> mockSucursales = const [
    SucursalOpcionDto(idSucursal: 1, nombre: 'Atelier Serrano - Madrid'),
    SucursalOpcionDto(idSucursal: 2, nombre: 'Boutique Central - Santa Cruz'),
    SucursalOpcionDto(idSucursal: 3, nombre: 'Boutique Central Equipetrol'),
  ];

  @override
  Future<ComandoVozOut> interpretarVoz(String token, String textoDictado) async {
    fueInterpretado = true;
    return ComandoVozOut(
      textoDictado: textoDictado,
      intencion: 'exportar',
      modulo: 'ventas',
      formato: 'excel',
      periodo: 'este_mes',
      idSucursal: null,
      nombreSucursal: null,
      confianza: 0.95,
      accionRecomendada: 'ejecutar_exportacion',
    );
  }

  @override
  Future<ReportePrevisualizacionDto> previsualizar(
    String token,
    ReporteFiltrosDto filtros,
  ) async {
    return mockPrev;
  }

  @override
  Future<ArchivoReporteDescargado> exportar(
    String token,
    ReporteFiltrosDto filtros,
  ) async {
    fueExportado = true;
    return ArchivoReporteDescargado(
      bytes: Uint8List.fromList([1, 2, 3, 4, 5]),
      nombreArchivo: 'reporte_ventas_mock.xlsx',
      mediaType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    );
  }

  @override
  Future<List<SucursalOpcionDto>> listarSucursales(String token) async {
    return mockSucursales;
  }
}

void main() {
  group('CU31 Mobile - DTO Tests', () {
    test('ComandoVozIn serializa correctamente a JSON', () {
      const dto = ComandoVozIn(textoDictado: 'ventas de hoy');
      final json = dto.toJson();
      expect(json['texto_dictado'], 'ventas de hoy');
    });

    test('ComandoVozOut deserializa correctamente desde JSON', () {
      final json = {
        'texto_dictado': 'ventas en madrid en pdf',
        'intencion': 'exportar',
        'modulo': 'ventas',
        'formato': 'pdf',
        'periodo': 'este_mes',
        'id_sucursal': 1,
        'nombre_sucursal': 'Atelier Serrano - Madrid',
        'confianza': 0.95,
        'accion_recomendada': 'ejecutar_exportacion',
      };
      final out = ComandoVozOut.fromJson(json);
      expect(out.modulo, 'ventas');
      expect(out.formato, 'pdf');
      expect(out.idSucursal, 1);
      expect(out.nombreSucursal, 'Atelier Serrano - Madrid');
      expect(out.confianza, 0.95);
    });

    test('ReporteFiltrosDto serializa y aplica copyWith correctamente', () {
      const filtros = ReporteFiltrosDto(modulo: 'inventario', formato: 'pdf');
      expect(filtros.modulo, 'inventario');
      expect(filtros.formato, 'pdf');

      final modificados = filtros.copyWith(formato: 'csv', idSucursal: 2);
      expect(modificados.modulo, 'inventario');
      expect(modificados.formato, 'csv');
      expect(modificados.idSucursal, 2);

      final json = modificados.toJson();
      expect(json['formato'], 'csv');
      expect(json['id_sucursal'], 2);
    });

    test('ReportePrevisualizacionDto deserializa metricas financieras', () {
      final json = {
        'modulo': 'ventas',
        'formato': 'excel',
        'total_registros': 29,
        'fecha_corte': '2026-09-22T10:00:00Z',
        'nombre_archivo_sugerido': 'reporte_ventas_20260922.xlsx',
        'resumen_financiero': {
          'monto_total_bob': 49748.0,
          'ventas_promedio_bob': 1715.45,
        },
      };
      final dto = ReportePrevisualizacionDto.fromJson(json);
      expect(dto.totalRegistros, 29);
      expect(dto.resumenFinanciero?['monto_total_bob'], 49748.0);
    });
  });

  group('CU31 Mobile - BLoC Tests', () {
    test('inicializar carga sucursales y previsualizacion inicial', () async {
      final repo = MockReportesRepositorio();
      final bloc = ReportesBloc(repositorio: repo);

      expect(bloc.estado, isA<ReportesInicial>());

      await bloc.inicializar('token_test');

      expect(bloc.estado, isA<ReportesListo>());
      final listo = bloc.estado as ReportesListo;
      expect(listo.previsualizacion.totalRegistros, 29);
      expect(listo.sucursales.length, 3);
    });

    test('interpretarVoz actualiza filtros y emite mensaje de exito', () async {
      final repo = MockReportesRepositorio();
      final bloc = ReportesBloc(repositorio: repo);
      await bloc.inicializar('token_test');

      await bloc.interpretarVoz('token_test', 'ventas de este mes');

      expect(repo.fueInterpretado, isTrue);
      expect(bloc.estado, isA<ReportesListo>());
      final listo = bloc.estado as ReportesListo;
      expect(listo.mensajeExito, isNotNull);
      expect(listo.comandoVoz?.modulo, 'ventas');
    });

    test('exportarReporte genera archivo binario y actualiza estado', () async {
      final repo = MockReportesRepositorio();
      final bloc = ReportesBloc(repositorio: repo);
      await bloc.inicializar('token_test');

      await bloc.exportarReporte('token_test');

      expect(repo.fueExportado, isTrue);
      expect(bloc.estado, isA<ReportesListo>());
      final listo = bloc.estado as ReportesListo;
      expect(listo.archivoExportado, isNotNull);
      expect(listo.archivoExportado?.nombreArchivo, 'reporte_ventas_mock.xlsx');
    });
  });

  group('CU31 Mobile - Widget Tests', () {
    testWidgets('PantallaReportesVoz renderiza cabecera, tarjeta de voz y previsualizacion',
        (WidgetTester tester) async {
      final repo = MockReportesRepositorio();
      final bloc = ReportesBloc(repositorio: repo);

      await tester.pumpWidget(
        MaterialApp(
          home: PantallaReportesVoz(
            token: 'token_mock',
            bloc: bloc,
          ),
        ),
      );

      // Esperar a que inicialice
      await tester.pumpAndSettle();

      // Verificar cabecera oficial
      expect(find.text('Generar reportes ejecutivos y consultas por voz'), findsOneWidget);
      expect(find.text('CONSULTA Y DICTADO POR VOZ'), findsOneWidget);
      expect(find.text('PREVISUALIZACION DE DATOS'), findsOneWidget);
      expect(find.text('CONFIGURACION DEL REPORTE'), findsOneWidget);
      expect(find.text('EXPORTAR REPORTE BINARIO'), findsOneWidget);

      // Verificar total de registros
      expect(find.text('29'), findsOneWidget);
      expect(find.text('Bs 49748.00'), findsOneWidget);
    });

    testWidgets('Tocar un chip de orden sugerida procesa la consulta de voz',
        (WidgetTester tester) async {
      final repo = MockReportesRepositorio();
      final bloc = ReportesBloc(repositorio: repo);

      await tester.pumpWidget(
        MaterialApp(
          home: PantallaReportesVoz(
            token: 'token_mock',
            bloc: bloc,
          ),
        ),
      );

      await tester.pumpAndSettle();

      final chipFinder = find.text('Ventas de este mes en Excel');
      expect(chipFinder, findsOneWidget);

      await tester.tap(chipFinder);
      await tester.pumpAndSettle();

      expect(repo.fueInterpretado, isTrue);
    });
  });
}
