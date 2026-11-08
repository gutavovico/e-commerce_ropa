import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ec_mobile/src/core/cliente_http_api.dart';
import 'package:ec_mobile/src/core/empresa_actual.dart';
import 'package:ec_mobile/src/core/sesion_manager.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/fuentes_datos/empresas_remoto_datasource.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/login_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_seleccion_empresa.dart';

/// P2-CU02 en el móvil (spec §C.3). Los payloads son literales del backend
/// (`LoginOut`, `EmpresaOut`), no objetos armados sobre la interfaz del cliente.
void main() {
  const fashion = EmpresaTienda(codigo: 'fashionstore', nombre: 'FASHION STORE');

  tearDown(() {
    EmpresaActual.instancia.limpiar();
    SesionManager.instancia.reiniciar();
  });

  group('LoginRespuestaDto.fromJson', () {
    test('cliente: sin empresa en la sesión y con sus tiendas', () {
      final json = jsonDecode('''
        {"access_token": "eyJ.x.y", "token_type": "bearer", "id_usuario": 2,
         "email": "clienta@ejemplo.com", "nombres": "Ana", "apellidos": "Pérez", "rol": "cliente",
         "tenant": null,
         "empresas": [{"codigo": "fashionstore", "nombre": "FASHION STORE"},
                      {"codigo": "menshopping", "nombre": "Menshopping"}]}
      ''') as Map<String, dynamic>;
      final dto = LoginRespuestaDto.fromJson(json);
      expect(dto.esCliente, isTrue);
      expect(dto.tenant, isNull);
      expect(dto.empresas.map((e) => e.codigo), ['fashionstore', 'menshopping']);
    });

    test('empleado: con la empresa de su cuenta y sin tiendas', () {
      final json = jsonDecode('''
        {"access_token": "eyJ.x.y", "token_type": "bearer", "id_usuario": 14,
         "email": "cajero@fashionstore.com", "nombres": "Luis", "apellidos": "Gil", "rol": "cajero",
         "tenant": {"codigo": "fashionstore", "nombre": "FASHION STORE"}, "empresas": []}
      ''') as Map<String, dynamic>;
      final dto = LoginRespuestaDto.fromJson(json);
      expect(dto.esCliente, isFalse);
      expect(dto.tenant, fashion);
      expect(dto.empresas, isEmpty);
    });

    test('tolera una respuesta anterior a P2-CU02 sin los campos nuevos', () {
      final dto = LoginRespuestaDto.fromJson({
        'access_token': 't', 'id_usuario': 2, 'email': 'a@b.com', 'nombres': 'A', 'apellidos': 'B', 'rol': 'cliente',
      });
      expect(dto.tenant, isNull);
      expect(dto.empresas, isEmpty);
    });
  });

  group('ClienteHttpApi', () {
    late List<http.BaseRequest> enviadas;
    late ClienteHttpApi cliente;

    setUp(() {
      enviadas = [];
      cliente = ClienteHttpApi(
        interno: MockClient((request) async {
          enviadas.add(request);
          return http.Response('[]', 200);
        }),
      );
    });

    test('sin tienda elegida no envía X-Tenant', () async {
      await cliente.get(Uri.parse('https://api.ejemplo.com/api/v1/productos'));
      expect(enviadas.single.headers.containsKey('X-Tenant'), isFalse);
    });

    test('con tienda elegida envía X-Tenant a la API', () async {
      EmpresaActual.instancia.elegir(fashion);
      await cliente.get(Uri.parse('https://api.ejemplo.com/api/v1/productos'));
      expect(enviadas.single.headers['X-Tenant'], 'fashionstore');
    });

    test('no la añade a recursos fuera de la API (imágenes /ar/, /static/)', () async {
      EmpresaActual.instancia.elegir(fashion);
      await cliente.get(Uri.parse('https://web.ejemplo.com/ar/modelo.glb'));
      expect(enviadas.single.headers.containsKey('X-Tenant'), isFalse);
    });
  });

  group('EmpresasRemotoDatasource', () {
    test('lee GET /api/v1/mis-empresas', () async {
      final datasource = EmpresasRemotoDatasource(
        client: MockClient((request) async {
          expect(request.url.path, '/api/v1/mis-empresas');
          expect(request.headers['Authorization'], 'Bearer tok');
          return http.Response('[{"codigo": "fashionstore", "nombre": "FASHION STORE"}]', 200);
        }),
      );
      expect(await datasource.misEmpresas('tok'), [fashion]);
    });

    test('un 401 notifica la sesión expirada', () async {
      final eventos = <SesionEvento>[];
      final sub = SesionManager.instancia.eventos.listen(eventos.add);
      final datasource = EmpresasRemotoDatasource(
        client: MockClient((_) async => http.Response(
            '{"detail": "Token de acceso invalido o expirado", "code": "TOKEN_INVALIDO"}', 401)),
      );
      await expectLater(datasource.misEmpresas('tok'), throwsA(isA<EmpresasExcepcion>()));
      await Future<void>.delayed(Duration.zero);
      expect(eventos, isNotEmpty);
      await sub.cancel();
    });
  });

  group('PantallaSeleccionEmpresa', () {
    testWidgets('lista las tiendas del login y elige una', (tester) async {
      EmpresaTienda? elegida;
      await tester.pumpWidget(MaterialApp(
        home: PantallaSeleccionEmpresa(
          token: 'tok',
          nombreUsuario: 'Ana Pérez',
          empresasIniciales: const [fashion, EmpresaTienda(codigo: 'menshopping', nombre: 'Menshopping')],
          alElegir: (e) => elegida = e,
          alCerrarSesion: () {},
        ),
      ));
      expect(find.byKey(const Key('seleccion_empresa_lista')), findsOneWidget);
      expect(find.text('FASHION STORE'), findsOneWidget);
      expect(find.text('Menshopping'), findsOneWidget);
      expect(find.byType(BottomNavigationBar), findsNothing); // no es una raíz Hub-and-Spoke

      await tester.tap(find.text('Menshopping'));
      expect(elegida?.codigo, 'menshopping');
    });

    testWidgets('A6: sin tiendas muestra el estado vacío que remite a la web', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: PantallaSeleccionEmpresa(
          token: 'tok',
          empresasIniciales: const [],
          alElegir: (_) {},
          alCerrarSesion: () {},
        ),
      ));
      expect(find.byKey(const Key('seleccion_empresa_vacia')), findsOneWidget);
      expect(find.textContaining('desde la web'), findsOneWidget);
    });
  });
}
