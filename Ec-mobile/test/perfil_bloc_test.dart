import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/datos/modelos/perfil_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/dominio/repositorios/perfil_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/bloc/perfil_bloc.dart';

class MockPerfilRepositorioExitoso implements PerfilRepositorio {
  final PerfilClienteDto perfilSimulado;

  MockPerfilRepositorioExitoso(this.perfilSimulado);

  @override
  Future<PerfilClienteDto> obtenerPerfil(String token) async {
    return perfilSimulado;
  }

  @override
  Future<PerfilClienteDto> actualizarPerfil(
    String token,
    PerfilClienteUpdateDto datos,
  ) async {
    return PerfilClienteDto(
      idUsuario: perfilSimulado.idUsuario,
      numeroSocio: perfilSimulado.numeroSocio,
      email: perfilSimulado.email,
      rol: perfilSimulado.rol,
      fechaRegistro: perfilSimulado.fechaRegistro,
      miembroDesde: perfilSimulado.miembroDesde,
      nombres: datos.nombres ?? perfilSimulado.nombres,
      apellidos: datos.apellidos ?? perfilSimulado.apellidos,
      telefono: datos.telefono ?? perfilSimulado.telefono,
      tallaPreferida: datos.tallaPreferida ?? perfilSimulado.tallaPreferida,
      genero: datos.genero ?? perfilSimulado.genero,
      aceptaMarketing: datos.aceptaMarketing ?? perfilSimulado.aceptaMarketing,
      resumenAtelier: perfilSimulado.resumenAtelier,
    );
  }
}

class MockPerfilRepositorioFallido implements PerfilRepositorio {
  final String mensajeError;

  MockPerfilRepositorioFallido(this.mensajeError);

  @override
  Future<PerfilClienteDto> obtenerPerfil(String token) async {
    throw Exception(mensajeError);
  }

  @override
  Future<PerfilClienteDto> actualizarPerfil(
    String token,
    PerfilClienteUpdateDto datos,
  ) async {
    throw Exception(mensajeError);
  }
}

void main() {
  const perfilPrueba = PerfilClienteDto(
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

  group('PerfilBloc Tests', () {
    test('estado inicial es PerfilInicial', () {
      final bloc = PerfilBloc(repositorio: MockPerfilRepositorioExitoso(perfilPrueba));
      expect(bloc.estado, isA<PerfilInicial>());
      expect(bloc.estaCargando, isFalse);
    });

    test('cargarPerfil emite PerfilCargando y luego PerfilCargado', () async {
      final bloc = PerfilBloc(repositorio: MockPerfilRepositorioExitoso(perfilPrueba));
      final estados = <PerfilEstado>[];
      bloc.addListener(() => estados.add(bloc.estado));

      await bloc.cargarPerfil('token_valido');

      expect(estados.length, 2);
      expect(estados[0], isA<PerfilCargando>());
      expect(estados[1], isA<PerfilCargado>());
      final cargado = estados[1] as PerfilCargado;
      expect(cargado.perfil.nombres, 'Ana');
    });

    test('cargarPerfil emite PerfilCargando y luego PerfilError ante fallo', () async {
      final bloc = PerfilBloc(repositorio: MockPerfilRepositorioFallido('Token no válido'));
      final estados = <PerfilEstado>[];
      bloc.addListener(() => estados.add(bloc.estado));

      await bloc.cargarPerfil('token_invalido');

      expect(estados.length, 2);
      expect(estados[0], isA<PerfilCargando>());
      expect(estados[1], isA<PerfilError>());
    });

    test('actualizarPerfil actualiza el estado de perfil correctamente', () async {
      final bloc = PerfilBloc(repositorio: MockPerfilRepositorioExitoso(perfilPrueba));
      await bloc.cargarPerfil('token');

      await bloc.actualizarPerfil(
        'token',
        const PerfilClienteUpdateDto(nombres: 'Ana María', tallaPreferida: '40'),
      );

      expect(bloc.estado, isA<PerfilCargado>());
      final estadoCargado = bloc.estado as PerfilCargado;
      expect(estadoCargado.perfil.nombres, 'Ana María');
      expect(estadoCargado.perfil.tallaPreferida, '40');
    });
  });
}
