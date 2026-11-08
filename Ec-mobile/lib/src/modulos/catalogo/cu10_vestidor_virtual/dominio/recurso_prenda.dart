import 'dart:convert';
import 'dart:typed_data';

import 'package:image/image.dart' as img;

/// Lado mínimo que Decart recomienda para la imagen de referencia de la prenda.
const int ladoMinimoReferenciaPx = 512;

/// Resuelve `productos.modelo_ar_url` a una URL absoluta. La base de datos guarda los recursos del
/// vestidor como rutas relativas del frontend web (`/ar/<prenda>.png`).
String? resolverUrlRecurso(String? url, String baseWeb) {
  final limpia = url?.trim() ?? '';
  if (limpia.isEmpty) return null;
  if (limpia.startsWith('http://') || limpia.startsWith('https://')) return limpia;
  final base = baseWeb.replaceAll(RegExp(r'/+$'), '');
  return limpia.startsWith('/') ? '$base$limpia' : '$base/$limpia';
}

/// Imagen de referencia lista para Lucy VTON.
class ReferenciaVton {
  /// JPEG en base64, sin el prefijo `data:`.
  final String base64Jpeg;
  final int ancho;
  final int alto;

  const ReferenciaVton({required this.base64Jpeg, required this.ancho, required this.alto});

  bool get cumpleTamanoMinimo => ancho >= ladoMinimoReferenciaPx && alto >= ladoMinimoReferenciaPx;
}

/// Aplana la prenda sobre fondo blanco y la codifica en JPEG.
///
/// Decart pide la prenda sola sobre fondo liso; la transparencia de un PNG no lo es. Se ejecuta
/// con `compute` para no bloquear la interfaz. Lanza [FormatException] si los bytes no son una
/// imagen.
ReferenciaVton prepararReferenciaVton(Uint8List bytes) {
  final original = img.decodeImage(bytes);
  if (original == null) {
    throw const FormatException('El recurso de la prenda no es una imagen válida.');
  }
  final lienzo = img.Image(width: original.width, height: original.height);
  img.fill(lienzo, color: img.ColorRgb8(255, 255, 255));
  img.compositeImage(lienzo, original);
  return ReferenciaVton(
    base64Jpeg: base64Encode(img.encodeJpg(lienzo, quality: 92)),
    ancho: original.width,
    alto: original.height,
  );
}
