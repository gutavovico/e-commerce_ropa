import 'package:flutter/material.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import 'src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart';

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
              alCompletarLoginConToken: (token) {
                void abrirPerfil(String tokenActivo) {
                  Navigator.of(ctx).push(
                    MaterialPageRoute(
                      builder: (perfilCtx) => PantallaPerfil(
                        token: tokenActivo,
                        alCerrarSesion: () async {
                          final repo = LoginRepositorioImpl();
                          await repo.cerrarSesion(tokenActivo);
                          if (perfilCtx.mounted) {
                            Navigator.of(perfilCtx).pushAndRemoveUntil(
                              MaterialPageRoute(
                                builder: (_) => construirLogin(),
                              ),
                              (route) => false,
                            );
                          }
                        },
                      ),
                    ),
                  );
                }

                abrirPerfil(token);
              },
            );
          }

          return construirLogin();
        },
      ),
    );
  }
}
