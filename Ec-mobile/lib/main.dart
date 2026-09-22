import 'dart:async';
import 'package:flutter/material.dart';
import 'src/core/sesion_manager.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import 'src/navegacion/pantalla_principal_hub.dart';

void main() {
  runApp(const EcMobileApp());
}

/// Raíz de la aplicación y propietaria del ciclo de vida de la sesión.
///
/// Escucha [SesionManager.eventos] y redirige automáticamente al login cuando
/// cualquier datasource detecta un HTTP 401 (sesión expirada), replicando la
/// protección que el AuthInterceptor de Angular ofrece en el frontend web.
///
/// La suscripción y la navegación viven aquí, por encima del [Navigator], y actúan
/// mediante [GlobalKey]s. Es deliberado: cuando esta lógica vivía en un widget
/// montado como ruta `home`, navegar al hub reemplazaba esa misma ruta, destruía el
/// estado y cancelaba la suscripción. El resultado era que el listener de 401 solo
/// estaba vivo mientras el usuario permanecía en el login —justo cuando un 401 no
/// puede ocurrir— y que volver a iniciar sesión tras un logout no hacía nada, porque
/// los callbacks apuntaban a un estado ya destruido.
class EcMobileApp extends StatefulWidget {
  const EcMobileApp({super.key});

  @override
  State<EcMobileApp> createState() => _EcMobileAppState();
}

class _EcMobileAppState extends State<EcMobileApp> {
  final GlobalKey<NavigatorState> _navegadorKey = GlobalKey<NavigatorState>();
  final GlobalKey<ScaffoldMessengerState> _mensajeroKey =
      GlobalKey<ScaffoldMessengerState>();

  StreamSubscription<SesionEvento>? _subSesion;

  @override
  void initState() {
    super.initState();
    _subSesion = SesionManager.instancia.eventos.listen(_alExpirarSesion);
  }

  @override
  void dispose() {
    _subSesion?.cancel();
    super.dispose();
  }

  void _alExpirarSesion(SesionEvento evento) {
    // Aviso de cortesía al estilo boutique.
    _mensajeroKey.currentState?.showSnackBar(
      SnackBar(
        content: Text(
          evento.mensaje,
          style: const TextStyle(
            fontFamily: 'Outfit',
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: Colors.white,
          ),
        ),
        backgroundColor: const Color(0xFF0F1116),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        duration: const Duration(seconds: 4),
      ),
    );

    _volverAlLogin();
  }

  /// Devuelve al usuario al login limpiando toda la pila de navegación.
  void _volverAlLogin() {
    // El flag anti-duplicados de SesionManager debe liberarse al volver al login;
    // si no, un 401 posterior quedaría silenciado para siempre.
    SesionManager.instancia.reiniciar();
    _navegadorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => _construirLogin()),
      (route) => false,
    );
  }

  Widget _construirLogin() {
    return PantallaLogin(
      alCompletarLoginConUsuario: (token, usuario) {
        final nombreCompleto = '${usuario.nombres} ${usuario.apellidos}'.trim();
        SesionManager.instancia.reiniciar();
        _abrirHub(token, nombreCompleto);
      },
      alCompletarLoginConToken: (token) {
        SesionManager.instancia.reiniciar();
        _abrirHub(token, null);
      },
    );
  }

  void _abrirHub(String tokenActivo, String? nombreUsuario) {
    _navegadorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => PantallaPrincipalHub(
          token: tokenActivo,
          nombreUsuario: nombreUsuario,
          alCerrarSesion: () async {
            final repo = LoginRepositorioImpl();
            await repo.cerrarSesion(tokenActivo);
            _volverAlLogin();
          },
        ),
      ),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fashion Store',
      debugShowCheckedModeBanner: false,
      navigatorKey: _navegadorKey,
      scaffoldMessengerKey: _mensajeroKey,
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
      home: _construirLogin(),
    );
  }
}
