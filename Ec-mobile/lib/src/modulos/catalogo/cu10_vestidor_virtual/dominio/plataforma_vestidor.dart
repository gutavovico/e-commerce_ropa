import 'package:flutter/foundation.dart';

/// El vestidor de la app depende de piezas que solo existen en Android e iOS: ML Kit Pose Detection
/// (Motor 1) y `webview_flutter` (Motor 2). En Flutter Web o escritorio no tienen implementación y
/// fallan con `MissingPluginException` o con la aserción de `WebViewPlatform.instance`.
///
/// Se usa `defaultTargetPlatform` y no `dart:io` `Platform`, que lanza «Unsupported operation» en
/// web. En pruebas se controla con `debugDefaultTargetPlatformOverride`.
bool vestidorSoportadoEnPlataforma() =>
    !kIsWeb && (defaultTargetPlatform == TargetPlatform.android || defaultTargetPlatform == TargetPlatform.iOS);

const String mensajeVestidorNoSoportado =
    'El vestidor virtual de la app necesita un teléfono Android o iOS (cámara, ML Kit y WebView). '
    'En el navegador, usa la web de FASHION STORE.';
