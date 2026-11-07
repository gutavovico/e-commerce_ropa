import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu19_asistente_chatbot/datos/datasources/chatbot_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu19_asistente_chatbot/datos/modelos/chatbot_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu19_asistente_chatbot/presentacion/bloc/chatbot_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu19_asistente_chatbot/presentacion/pantallas/pantalla_asistente_estilo.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/presentacion/pantallas/pantalla_producto_detalle.dart';
import 'package:ec_mobile/src/navegacion/pantalla_principal_hub.dart';

class MockChatbotApi implements ChatbotApi {
  MensajeChatbotPeticion? ultimaPeticion;
  String? ultimoToken;
  bool simularError = false;
  String mensajeError = 'Fallo de prueba en servidor';

  RespuestaChatbotDto respuestaPorDefecto = const RespuestaChatbotDto(
    idInteraccion: 99,
    respuesta:
        'Le recomiendo nuestro Vestido de Seda Carmín, ideal para una velada distinguida.',
    productosSugeridos: [
      ProductoChatbotSugeridoDto(
        idProducto: 42,
        nombre: 'Vestido de Seda Carmín',
        precio: 850.0,
        categoria: 'Vestidos',
        imagenUrl: '',
        motivo: 'Silueta entallada y tejido de alta costura.',
      ),
    ],
    sucursalesSugeridas: [
      SucursalChatbotSugeridaDto(
        idSucursal: 1,
        nombre: 'Boutique Salamanca',
        direccion: 'Calle Serrano 45',
        ciudad: 'Madrid',
        telefono: '+34 91 123 4567',
        horarioAtencion: '10:00 - 20:30',
      ),
    ],
    sugerenciasRapidas: [
      '¿Tienen opciones en negro?',
      '¿Disponibilidad de citas?',
    ],
    idSucursalDetectada: 1,
  );

  @override
  Future<RespuestaChatbotDto> enviarMensaje(
    MensajeChatbotPeticion peticion, {
    String? token,
  }) async {
    ultimaPeticion = peticion;
    ultimoToken = token;

    if (simularError) {
      throw ChatbotException(mensajeError, codigoHttp: 500);
    }

    return respuestaPorDefecto;
  }
}

void main() {
  group('CU19 Chatbot DTOs', () {
    test('MensajeChatbotPeticion serializa a JSON correctamente', () {
      const peticion = MensajeChatbotPeticion(
        mensaje: '¿Tienen vestidos de gala?',
        canal: 'movil',
        idSucursalPreferida: 2,
      );

      final json = peticion.toJson();
      expect(json['mensaje'], '¿Tienen vestidos de gala?');
      expect(json['canal'], 'movil');
      expect(json['id_sucursal_preferida'], 2);
    });

    test('ProductoChatbotSugeridoDto des-serializa desde JSON', () {
      final json = {
        'id_producto': 10,
        'nombre': 'Blazer Milano',
        'precio': 620.5,
        'categoria': 'Chaquetas',
        'imagen_url': 'https://example.com/blazer.jpg',
        'motivo': 'Corte sartorial impecable',
      };

      final dto = ProductoChatbotSugeridoDto.fromJson(json);
      expect(dto.idProducto, 10);
      expect(dto.nombre, 'Blazer Milano');
      expect(dto.precio, 620.5);
      expect(dto.categoria, 'Chaquetas');
      expect(dto.motivo, 'Corte sartorial impecable');
    });

    test('SucursalChatbotSugeridaDto des-serializa desde JSON', () {
      final json = {
        'id_sucursal': 3,
        'nombre': 'Atelier Diagonal',
        'direccion': 'Passeig de Gràcia 78',
        'ciudad': 'Barcelona',
        'telefono': '+34 93 456 7890',
        'horario_atencion': '10:00 - 20:00',
      };

      final dto = SucursalChatbotSugeridaDto.fromJson(json);
      expect(dto.idSucursal, 3);
      expect(dto.nombre, 'Atelier Diagonal');
      expect(dto.ciudad, 'Barcelona');
      expect(dto.horarioAtencion, '10:00 - 20:00');
    });

    test('RespuestaChatbotDto des-serializa payload completo', () {
      final json = {
        'id_interaccion': 101,
        'respuesta': 'Disponemos de las siguientes opciones...',
        'productos_sugeridos': [
          {
            'id_producto': 1,
            'nombre': 'Pantalón Palazzo',
            'precio': 350.0,
            'categoria': 'Pantalones',
          }
        ],
        'sucursales_sugeridas': [
          {
            'id_sucursal': 1,
            'nombre': 'Boutique Serrano',
            'direccion': 'Calle Serrano 45',
            'ciudad': 'Madrid',
            'telefono': '123456',
          }
        ],
        'sugerencias_rapidas': ['¿Horarios?'],
        'id_sucursal_detectada': 1,
      };

      final dto = RespuestaChatbotDto.fromJson(json);
      expect(dto.idInteraccion, 101);
      expect(dto.productosSugeridos.length, 1);
      expect(dto.productosSugeridos.first.nombre, 'Pantalón Palazzo');
      expect(dto.sucursalesSugeridas.length, 1);
      expect(dto.sugerenciasRapidas, contains('¿Horarios?'));
      expect(dto.idSucursalDetectada, 1);
    });
  });

  group('CU19 ChatbotBloc', () {
    late MockChatbotApi mockApi;
    late ChatbotBloc bloc;

    setUp(() {
      mockApi = MockChatbotApi();
      bloc = ChatbotBloc(api: mockApi, token: 'fake_jwt_token');
    });

    tearDown(() {
      bloc.dispose();
    });

    test('Estado inicial contiene mensaje de bienvenida y sugerencias', () {
      final estado = bloc.estado;
      expect(estado.mensajes.length, 1);
      expect(estado.mensajes.first.esUsuario, false);
      expect(estado.mensajes.first.texto, contains('Bienvenido a Fashion Store'));
      expect(estado.sugerenciasRapidas.isNotEmpty, true);
      expect(estado.cargando, false);
      expect(estado.error, isNull);
    });

    test('enviarMensaje vacío o con sólo espacios no hace nada', () async {
      await bloc.enviarMensaje('   ');
      expect(bloc.estado.mensajes.length, 1);
      expect(mockApi.ultimaPeticion, isNull);
    });

    test('enviarMensaje exitoso agrega mensaje usuario y respuesta del bot',
        () async {
      await bloc.enviarMensaje('Busco un vestido para fiesta');

      expect(mockApi.ultimaPeticion, isNotNull);
      expect(mockApi.ultimaPeticion!.mensaje, 'Busco un vestido para fiesta');
      expect(mockApi.ultimaPeticion!.canal, 'movil');
      expect(mockApi.ultimoToken, 'fake_jwt_token');

      final estado = bloc.estado;
      expect(estado.cargando, false);
      expect(estado.error, isNull);
      // Mensaje de bienvenida + mensaje usuario + respuesta bot = 3
      expect(estado.mensajes.length, 3);

      final msgUsuario = estado.mensajes[1];
      expect(msgUsuario.esUsuario, true);
      expect(msgUsuario.texto, 'Busco un vestido para fiesta');

      final msgBot = estado.mensajes[2];
      expect(msgBot.esUsuario, false);
      expect(msgBot.texto, contains('Vestido de Seda Carmín'));
      expect(msgBot.productos.length, 1);
      expect(msgBot.productos.first.nombre, 'Vestido de Seda Carmín');
      expect(msgBot.sucursales.length, 1);
    });

    test('enviarMensaje maneja excepción de API con mensaje cortés', () async {
      mockApi.simularError = true;

      await bloc.enviarMensaje('Consulta con fallo de red');

      final estado = bloc.estado;
      expect(estado.cargando, false);
      expect(estado.error, isNotNull);
      // Mensaje bienvenida + usuario + respuesta cortesía = 3
      expect(estado.mensajes.length, 3);
      expect(
        estado.mensajes.last.texto,
        contains('servicio de asesoría remota experimenta una pausa'),
      );
    });

    test('reiniciarConversacion limpia la conversación al estado inicial', () async {
      await bloc.enviarMensaje('Hola!');
      expect(bloc.estado.mensajes.length, 3);

      bloc.reiniciarConversacion();
      expect(bloc.estado.mensajes.length, 1);
      expect(bloc.estado.mensajes.first.texto, contains('Bienvenido a Fashion Store'));
    });

    test('add con ChatbotEvento despacha correctamente', () async {
      bloc.add(const ChatbotEventoEnviarMensaje('Hola vía evento'));
      await Future<void>.delayed(const Duration(milliseconds: 50));

      expect(bloc.estado.mensajes.length, 3);
      expect(bloc.estado.mensajes[1].texto, 'Hola vía evento');
    });

    test('mensajesNoLeidos se activa cuando llega respuesta estando cerrado el chat', () async {
      expect(bloc.mensajesNoLeidos, false);
      bloc.marcarChatCerrado();

      await bloc.enviarMensaje('Consulta mientras chat está cerrado');

      expect(bloc.mensajesNoLeidos, true);

      bloc.marcarChatAbierto();
      expect(bloc.mensajesNoLeidos, false);
    });
  });

  group('CU19 PantallaAsistenteEstilo Widget Tests', () {
    late MockChatbotApi mockApi;
    late ChatbotBloc bloc;

    setUp(() {
      mockApi = MockChatbotApi();
      bloc = ChatbotBloc(api: mockApi, token: 'test_token');
    });

    tearDown(() {
      bloc.dispose();
    });

    Widget crearPantallaPrueba() {
      return MaterialApp(
        home: PantallaAsistenteEstilo(
          token: 'test_token',
          habilitarImagenesRed: false,
          bloc: bloc,
        ),
      );
    }

    testWidgets('Renderiza AppBar de alta costura, bienvenida y sugerencias',
        (tester) async {
      await tester.pumpWidget(crearPantallaPrueba());
      await tester.pumpAndSettle();

      expect(find.text('ATELIER VIRTUAL'), findsOneWidget);
      expect(find.text('Asesor de Estilismo IA'), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
      expect(find.textContaining('Bienvenido a Fashion Store'), findsOneWidget);
      expect(find.textContaining('¿Tienen vestidos de noche en Madrid?'), findsOneWidget);
    });

    testWidgets('Tocar un chip de sugerencia rápida envía el mensaje',
        (tester) async {
      await tester.pumpWidget(crearPantallaPrueba());
      await tester.pumpAndSettle();

      final chipFinder =
          find.textContaining('¿Tienen vestidos de noche en Madrid?');
      expect(chipFinder, findsOneWidget);

      await tester.tap(chipFinder);
      await tester.pumpAndSettle();

      expect(mockApi.ultimaPeticion, isNotNull);
      expect(
        mockApi.ultimaPeticion!.mensaje,
        '¿Tienen vestidos de noche en Madrid?',
      );
      // Se muestra la respuesta del bot con producto sugerido
      expect(find.text('Vestido de Seda Carmín'), findsOneWidget);
      expect(find.text('Boutique Salamanca (Madrid)'), findsOneWidget);
    });

    testWidgets('Escribir en el campo de texto y presionar enviar despacha mensaje',
        (tester) async {
      await tester.pumpWidget(crearPantallaPrueba());
      await tester.pumpAndSettle();

      final inputFinder = find.byType(TextField);
      expect(inputFinder, findsOneWidget);

      await tester.enterText(inputFinder, 'Quiero un look para matrimonio');
      await tester.pump();

      final botonEnviar = find.byTooltip('Enviar mensaje');
      await tester.tap(botonEnviar);
      await tester.pumpAndSettle();

      expect(mockApi.ultimaPeticion!.mensaje, 'Quiero un look para matrimonio');
      expect(find.text('Quiero un look para matrimonio'), findsOneWidget);
    });

    testWidgets('Botón de refresh reinicia la conversación',
        (tester) async {
      await tester.pumpWidget(crearPantallaPrueba());
      await tester.pumpAndSettle();

      // Enviamos un mensaje
      await tester.enterText(find.byType(TextField), 'Prueba reset');
      await tester.tap(find.byTooltip('Enviar mensaje'));
      await tester.pumpAndSettle();
      expect(find.text('Prueba reset'), findsOneWidget);

      // Tocamos el botón de reiniciar
      await tester.tap(find.byTooltip('Reiniciar conversación'));
      await tester.pumpAndSettle();

      // El mensaje enviado ya no debe existir
      expect(find.text('Prueba reset'), findsNothing);
      expect(find.textContaining('Bienvenido a Fashion Store'), findsOneWidget);
    });

    testWidgets('Tocar la tarjeta de prenda recomendada navega a detalle del producto',
        (tester) async {
      await tester.pumpWidget(crearPantallaPrueba());
      await tester.pumpAndSettle();

      // Enviar mensaje para que aparezca la prenda recomendada
      await tester.enterText(find.byType(TextField), 'Vestido');
      await tester.tap(find.byTooltip('Enviar mensaje'));
      await tester.pumpAndSettle();

      final prendaFinder = find.text('Vestido de Seda Carmín');
      expect(prendaFinder, findsOneWidget);

      await tester.tap(prendaFinder);
      await tester.pumpAndSettle();

      expect(find.byType(PantallaProductoDetalle), findsOneWidget);
    });

    testWidgets('Presionar atrás y volver a abrir el chat preserva los mensajes intactos',
        (tester) async {
      final blocCompartido = ChatbotBloc.obtenerInstanciaCompartida(api: mockApi, token: 'test_token');

      // 1. Abrir primera vez y enviar mensaje
      await tester.pumpWidget(MaterialApp(
        home: PantallaAsistenteEstilo(
          token: 'test_token',
          habilitarImagenesRed: false,
          bloc: blocCompartido,
        ),
      ));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField), '¿Tienen vestidos de gala?');
      await tester.tap(find.byTooltip('Enviar mensaje'));
      await tester.pumpAndSettle();

      expect(find.text('¿Tienen vestidos de gala?'), findsOneWidget);

      // 2. Simular salir de la pantalla (volver atrás)
      await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Text('Pantalla Principal'))));
      await tester.pumpAndSettle();
      expect(find.text('¿Tienen vestidos de gala?'), findsNothing);

      // 3. Volver a entrar al asistente
      await tester.pumpWidget(MaterialApp(
        home: PantallaAsistenteEstilo(
          token: 'test_token',
          habilitarImagenesRed: false,
          bloc: blocCompartido,
        ),
      ));
      await tester.pumpAndSettle();

      // Los mensajes anteriores persisten intactos
      expect(find.text('¿Tienen vestidos de gala?'), findsOneWidget);
      expect(find.text('Vestido de Seda Carmín'), findsOneWidget);

      // Limpiar al finalizar
      ChatbotBloc.purgarSesion();
    });

    testWidgets('PantallaPrincipalHub muestra círculo de notificación dorado solo cuando hay mensajes no leídos',
        (tester) async {
      final blocCompartido = ChatbotBloc.obtenerInstanciaCompartida(api: mockApi, token: 'test_token');
      blocCompartido.marcarChatCerrado();
      blocCompartido.marcarMensajesNoLeidos(false);

      await tester.pumpWidget(const MaterialApp(
        home: PantallaPrincipalHub(
          token: 'test_token',
          habilitarImagenesRed: false,
        ),
      ));
      await tester.pumpAndSettle();

      // Inicialmente NO existe el círculo de notificación dorado (Container con color #AD8C63)
      final badgeFinder = find.byWidgetPredicate(
        (widget) =>
            widget is Container &&
            widget.decoration is BoxDecoration &&
            (widget.decoration as BoxDecoration).color == const Color(0xFFAD8C63) &&
            (widget.decoration as BoxDecoration).shape == BoxShape.circle,
      );
      expect(badgeFinder, findsNothing);

      // Activamos que llegó un mensaje no leído con el chat cerrado
      blocCompartido.marcarMensajesNoLeidos(true);
      await tester.pump();

      // AHORA SÍ aparece el círculo de notificación arriba a la derecha del botón
      expect(badgeFinder, findsOneWidget);

      // Abrir el chat tocando el botón flotante
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Regresar a la pantalla principal
      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      // Al haber sido abierto, el círculo ya no debe existir
      expect(badgeFinder, findsNothing);

      ChatbotBloc.purgarSesion();
    });
  });
}

