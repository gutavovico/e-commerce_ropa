import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/datos/modelos/perfil_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/dominio/repositorios/perfil_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/bloc/perfil_bloc.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart';

class MockPerfilRepositorioPruebas implements PerfilRepositorio {
  @override
  Future<PerfilClienteDto> obtenerPerfil(String token) async {
    return const PerfilClienteDto(
      idUsuario: 8402,
      numeroSocio: '#8402',
      email: 'ana.valenzuela@studio.es',
      rol: 'cliente',
      fechaRegistro: '2021-10-15',
      miembroDesde: 'Octubre 2021',
      nombres: 'Ana',
      apellidos: 'Valenzuela',
      telefono: '+34 612 884 901',
      tallaPreferida: '38',
      genero: 'femenino',
      aceptaMarketing: true,
      resumenAtelier: ResumenAtelierDto(
        visitasRegistradas: 32,
        boutiquesVisitadas: 4,
        preferenciaTextil: '100% Seda & Lana',
        estatusMembresia: 'Nivel Platino',
      ),
    );
  }

  @override
  Future<PerfilClienteDto> actualizarPerfil(
    String token,
    PerfilClienteUpdateDto datos,
  ) async {
    return const PerfilClienteDto(
      idUsuario: 8402,
      numeroSocio: '#8402',
      email: 'ana.valenzuela@studio.es',
      rol: 'cliente',
      fechaRegistro: '2021-10-15',
      miembroDesde: 'Octubre 2021',
      nombres: 'Ana Modificada',
      apellidos: 'Valenzuela',
      tallaPreferida: '40',
      aceptaMarketing: true,
      resumenAtelier: ResumenAtelierDto(
        visitasRegistradas: 32,
        boutiquesVisitadas: 4,
        preferenciaTextil: '100% Seda & Lana',
        estatusMembresia: 'Nivel Platino',
      ),
    );
  }
}

void main() {
  testWidgets('PantallaPerfil renderiza elementos visuales clave de Fashion Store', (tester) async {
    final bloc = PerfilBloc(repositorio: MockPerfilRepositorioPruebas());

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaPerfil(
          bloc: bloc,
          habilitarImagenesRed: false,
        ),
      ),
    );
    await tester.pumpAndSettle();

    // 1. Cabecera institucional
    expect(find.text('FASHION STORE  |  PERFIL'), findsOneWidget);
    expect(find.text('Mi Cuenta'), findsOneWidget);
    expect(find.text('• ATELIER VIP'), findsOneWidget);

    // 2. Tarjeta principal de cliente
    expect(find.text('SOCIO PRIVÉ #8402'), findsOneWidget);
    expect(find.text('Ana Valenzuela'), findsOneWidget);
    expect(find.text('ana.valenzuela@studio.es'), findsOneWidget);
    expect(find.text('Editar Información'), findsOneWidget);

    // 3. Banda de métricas
    expect(find.text('32'), findsOneWidget);
    expect(find.text('VISITAS'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);
    expect(find.text('BOUTIQUES'), findsOneWidget);
    expect(find.text('100%'), findsOneWidget);
    expect(find.text('SEDA & LANA'), findsOneWidget);

    // 4. Tarjetas gemelas Wishlist y Bolsa
    expect(find.text('WISHLIST'), findsOneWidget);
    expect(find.text('BOLSA'), findsOneWidget);
    expect(find.text('EXPLORAR PIEZAS →'), findsOneWidget);
    expect(find.text('IR AL CHECKOUT →'), findsOneWidget);

    // 5. Histórico y Preferencias
    expect(find.text('Compras Anteriores y Pedidos'), findsOneWidget);
    expect(find.text('Preferencias y Configuración'), findsOneWidget);
    expect(find.text('Direcciones de entrega'), findsOneWidget);
    expect(find.text('Métodos de pago'), findsOneWidget);
    expect(find.text('Personal Shopper Asignado'), findsOneWidget);

    // 6. Botón de cierre y BottomNavigationBar
    expect(find.text('CERRAR SESIÓN SEGURA'), findsOneWidget);
    expect(find.text('PERFIL'), findsOneWidget);
  });
}
