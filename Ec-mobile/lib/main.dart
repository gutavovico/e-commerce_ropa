import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'api_config.dart';
import 'src/core/empresa_actual.dart';
import 'src/core/sesion_manager.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/login_dto.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_seleccion_empresa.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import 'src/modulos/compras_pagos/cu16_cu17_caja/presentacion/pantallas/pantalla_caja.dart';
import 'src/navegacion/pantalla_principal_hub.dart';

/// P2-CU16/CU17 (decisión E1): roles que entran directo a la caja, sin el hub del cliente.
const Set<String> rolesDeCaja = {'administrador', 'admin', 'encargado_sucursal', 'cajero'};

enum DestinoSesion { seleccionDeTienda, caja, hub }

/// A dónde va cada rol tras el login: el cliente elige tienda (P2-CU02), el personal de caja abre la
/// caja (E1) y el resto (super administrador) sigue en el hub.
DestinoSesion destinoTrasLogin(String rol) {
  final normalizado = rol.toLowerCase().trim();
  if (normalizado == 'cliente') return DestinoSesion.seleccionDeTienda;
  if (rolesDeCaja.contains(normalizado)) return DestinoSesion.caja;
  return DestinoSesion.hub;
}

Future<void> main() async {
  // Sin STRIPE_PUBLISHABLE_KEY (--dart-define), no se inicializa el SDK: CU16 cae en su panel de
  // «modo simulador» en vez de intentar montar un CardField sin clave configurada.
  if (ApiConfig.stripePublishableKey.isNotEmpty) {
    WidgetsFlutterBinding.ensureInitialized();
    Stripe.publishableKey = ApiConfig.stripePublishableKey;
    // Requerido por Stripe en cuanto el `PaymentIntent` admite algún método que pueda redirigir
    // (§A.2 de `spec.md`: se quitó `allow_redirects: 'never'` a propósito, para permitir 3DS/SCA).
    // A diferencia de Stripe.js en Web, que recibe `return_url` en cada llamada, el SDK nativo lo
    // resuelve a partir de este esquema global. Para que un redirect real (p. ej. una tarjeta que
    // exige 3D Secure) vuelva a la app, este esquema debe registrarse también en
    // `android/app/src/main/AndroidManifest.xml` (intent-filter) e `ios/Runner/Info.plist`
    // (`CFBundleURLSchemes`) — pendiente de verificar en un dispositivo/emulador real.
    Stripe.urlScheme = 'fashionstore';
    await Stripe.instance.applySettings();
  }
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
    EmpresaActual.instancia.limpiar();
    _navegadorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => _construirLogin()),
      (route) => false,
    );
  }

  Widget _construirLogin() {
    return PantallaLogin(
      alCompletarLoginConUsuario: (token, usuario) {
        SesionManager.instancia.reiniciar();
        _despuesDelLogin(token, usuario);
      },
    );
  }

  /// P2-CU02: el cliente elige la tienda en la que navega (A10, A15); el empleado entra con la de
  /// su cuenta.
  void _despuesDelLogin(String token, LoginRespuestaDto usuario) {
    final nombreCompleto = '${usuario.nombres} ${usuario.apellidos}'.trim();
    final destino = destinoTrasLogin(usuario.rol);
    if (destino == DestinoSesion.seleccionDeTienda) {
      _abrirSeleccionEmpresa(token, nombreCompleto, usuario.empresas);
      return;
    }
    final empresa = usuario.tenant;
    if (empresa != null) {
      EmpresaActual.instancia.elegir(empresa);
    }
    if (destino == DestinoSesion.caja) {
      _abrirCaja(token, nombreCompleto, usuario.rol.toLowerCase().trim());
      return;
    }
    _abrirHub(token, nombreCompleto, esCliente: false);
  }

  /// P2-CU16/CU17: espacio del empleado. Como el cajero en la web (`/admin/pos`), sin el hub.
  void _abrirCaja(String token, String nombreEmpleado, String rol) {
    _navegadorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => PantallaCaja(
          token: token,
          nombreEmpleado: nombreEmpleado,
          rol: rol,
          alCerrarSesion: () => _cerrarSesion(token),
        ),
      ),
      (route) => false,
    );
  }

  /// Pantalla intermedia de selección de tienda. Con [empresas] null («Cambiar de tienda») las pide
  /// al backend.
  void _abrirSeleccionEmpresa(String token, String? nombreUsuario, List<EmpresaTienda>? empresas) {
    _navegadorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => PantallaSeleccionEmpresa(
          token: token,
          nombreUsuario: nombreUsuario,
          empresasIniciales: empresas,
          alElegir: (empresa) {
            EmpresaActual.instancia.elegir(empresa);
            _abrirHub(token, nombreUsuario, esCliente: true);
          },
          alCerrarSesion: () => _cerrarSesion(token),
        ),
      ),
      (route) => false,
    );
  }

  Future<void> _cerrarSesion(String token) async {
    final repo = LoginRepositorioImpl();
    await repo.cerrarSesion(token);
    _volverAlLogin();
  }

  void _abrirHub(String tokenActivo, String? nombreUsuario, {required bool esCliente}) {
    _navegadorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => PantallaPrincipalHub(
          token: tokenActivo,
          nombreUsuario: nombreUsuario,
          alCerrarSesion: () => _cerrarSesion(tokenActivo),
          // CU02 A7: el cliente cambia de tienda sin volver a iniciar sesión
          alCambiarDeTienda: esCliente
              ? () => _abrirSeleccionEmpresa(tokenActivo, nombreUsuario, null)
              : null,
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
