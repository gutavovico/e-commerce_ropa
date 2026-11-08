import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:webview_flutter_wkwebview/webview_flutter_wkwebview.dart';

import '../../../../../core/theme/app_theme.dart';
import '../bloc/vestidor_bloc.dart';

/// Página local con el SDK de JavaScript de Decart (`@decartai/sdk`): no hay SDK para Flutter.
const String rutaPaginaDecart = 'assets/vestidor/decart_vton.html';

/// Motor 2 (CU10): WebView que ejecuta Decart Lucy VTON en tiempo real.
///
/// Flutter entrega a la página el token efímero, el prompt y la prenda (JPEG base64 sobre fondo
/// blanco); la página devuelve sus eventos por el canal `Vestidor`.
class MotorRealistaWebView extends StatefulWidget {
  final DatosSesionRealista datos;
  final void Function(Map<String, dynamic> evento) alEvento;

  /// Token nuevo para cada re-marcación del SDK (el anterior caduca a los 60 s).
  final Future<String?> Function() solicitarToken;

  const MotorRealistaWebView({
    super.key,
    required this.datos,
    required this.alEvento,
    required this.solicitarToken,
  });

  @override
  State<MotorRealistaWebView> createState() => _MotorRealistaWebViewState();
}

class _MotorRealistaWebViewState extends State<MotorRealistaWebView> {
  late final WebViewController _controlador;

  @override
  void initState() {
    super.initState();
    final PlatformWebViewControllerCreationParams parametros = WebViewPlatform.instance is WebKitWebViewPlatform
        // iOS: vídeo en línea y sin gesto previo, o el stream remoto no se reproduce.
        ? WebKitWebViewControllerCreationParams(
            allowsInlineMediaPlayback: true,
            mediaTypesRequiringUserAction: const <PlaybackMediaTypes>{},
          )
        : const PlatformWebViewControllerCreationParams();

    _controlador = WebViewController.fromPlatformCreationParams(
      parametros,
      // `getUserMedia` dentro del WebView: se concede solo la cámara.
      onPermissionRequest: (solicitud) {
        if (solicitud.types.contains(WebViewPermissionResourceType.camera)) {
          solicitud.grant();
        } else {
          solicitud.deny();
        }
      },
    )
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(AppColors.black)
      ..addJavaScriptChannel('Vestidor', onMessageReceived: _alMensaje);

    final plataforma = _controlador.platform;
    if (plataforma is AndroidWebViewController) {
      plataforma.setMediaPlaybackRequiresUserGesture(false);
    }
    _controlador.loadFlutterAsset(rutaPaginaDecart);
  }

  Future<void> _alMensaje(JavaScriptMessage mensaje) async {
    final Map<String, dynamic> evento;
    try {
      evento = jsonDecode(mensaje.message) as Map<String, dynamic>;
    } catch (_) {
      return;
    }

    switch (evento['tipo']) {
      case 'lista':
        final datos = widget.datos;
        final argumentos = jsonEncode({
          'token': datos.tokenInicial,
          'prompt': datos.prompt,
          'imagenBase64': datos.referenciaBase64,
        });
        await _controlador.runJavaScript('window.iniciar($argumentos)');
      case 'token':
        final token = await widget.solicitarToken();
        if (!mounted) return;
        await _controlador.runJavaScript('window.entregarToken(${jsonEncode(token)})');
      default:
        widget.alEvento(evento);
    }
  }

  @override
  void dispose() {
    // Cierra la sesión de Decart (deja de facturar) y suelta la cámara del WebView.
    unawaited(_controlador.runJavaScript('window.detener && window.detener()').catchError((_) {}));
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => WebViewWidget(controller: _controlador);
}
