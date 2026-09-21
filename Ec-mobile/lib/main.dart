import 'package:flutter/material.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import 'src/navegacion/pantalla_principal_hub.dart';

void main() {
  runApp(const EcMobileApp());
}

class EcMobileApp extends StatelessWidget {
  const EcMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fashion Store',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        fontFamily: 'Outfit',
        scaffoldBackgroundColor: Colors.white,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.black,
          primary: Colors.black,
          surface: Colors.white,
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
        ),
      ),
      home: Builder(
        builder: (ctx) {
          Widget construirLogin() {
            return PantallaLogin(
              alCompletarLoginConUsuario: (token, usuario) {
                final nombreCompleto = '${usuario.nombres} ${usuario.apellidos}'.trim();
                _abrirHub(ctx, token, nombreCompleto, construirLogin);
              },
              alCompletarLoginConToken: (token) {
                _abrirHub(ctx, token, null, construirLogin);
              },
            );
          }

          return construirLogin();
        },
      ),
    );
  }

  static void _abrirHub(
    BuildContext ctx,
    String tokenActivo,
    String? nombreUsuario,
    Widget Function() loginBuilder,
  ) {
    Navigator.of(ctx).pushReplacement(
      MaterialPageRoute(
        builder: (hubCtx) => PantallaPrincipalHub(
          token: tokenActivo,
          nombreUsuario: nombreUsuario,
          alCerrarSesion: () async {
            final repo = LoginRepositorioImpl();
            await repo.cerrarSesion(tokenActivo);
            if (hubCtx.mounted) {
              Navigator.of(hubCtx).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => loginBuilder()),
                (route) => false,
              );
            }
          },
        ),
      ),
    );
  }
}
