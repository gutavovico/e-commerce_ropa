import 'dart:math' as math;
import 'dart:ui' show Offset, Size;

/// Geometría del Motor 1 (CU10): de los puntos corporales de ML Kit a la posición, tamaño y giro
/// de la prenda sobre la vista previa de la cámara. Dart puro, sin dependencias de plataforma.

/// Proporción entre la anchura de hombros y la anchura total de la imagen de la prenda. Las mangas
/// sobresalen de la línea de hombros, así que la prenda es más ancha que ella.
const double proporcionHombrosPrenda = 0.62;

/// Cuánto sube el borde superior de la prenda sobre la línea de hombros, como fracción de su
/// anchura (el cuello queda por encima de los hombros).
const double desfaseCuelloPrenda = 0.10;

/// Confianza mínima de ML Kit para dar un punto por válido.
const double confianzaMinimaPunto = 0.5;

/// Punto corporal ya trasladado al lienzo de la vista previa.
class PuntoCorporal {
  final Offset posicion;
  final double confianza;

  const PuntoCorporal(this.posicion, this.confianza);

  bool get esFiable => confianza >= confianzaMinimaPunto;
}

/// Puntos del torso que usa el ajuste. Solo los hombros: escala, posición y giro salen de ellos, y
/// en un selfie de medio cuerpo las caderas suelen quedar fuera de cuadro.
class PuntosTorso {
  final PuntoCorporal hombroIzquierdo;
  final PuntoCorporal hombroDerecho;

  const PuntosTorso({required this.hombroIzquierdo, required this.hombroDerecho});
}

/// Dónde y cómo dibujar la prenda en el lienzo.
class AjustePrenda {
  /// Punto medio entre hombros.
  final Offset centroHombros;

  /// Anchura total de la imagen de la prenda en el lienzo.
  final double ancho;

  /// Inclinación de la línea de hombros, en radianes (0 = horizontal).
  final double rotacion;

  const AjustePrenda({required this.centroHombros, required this.ancho, required this.rotacion});

  /// Esquina superior izquierda de la prenda antes de girarla.
  Offset get origen => Offset(centroHombros.dx - ancho / 2, centroHombros.dy - ancho * desfaseCuelloPrenda);
}

/// Traduce un punto de ML Kit (espacio de la imagen de la cámara) al lienzo de la vista previa.
///
/// Misma lógica que `coordinates_translator.dart` del ejemplo oficial de `google_mlkit`: con
/// rotación 90/270 el ancho y el alto de la imagen se intercambian en Android (no en iOS), y la
/// cámara frontal se refleja horizontalmente.
Offset traducirPunto(
  double x,
  double y, {
  required Size tamanoImagen,
  required Size tamanoLienzo,
  required int rotacionGrados,
  required bool camaraFrontal,
  required bool esIOS,
}) {
  final rotada = rotacionGrados == 90 || rotacionGrados == 270;
  final anchoFuente = rotada && !esIOS ? tamanoImagen.height : tamanoImagen.width;
  final altoFuente = rotada && !esIOS ? tamanoImagen.width : tamanoImagen.height;

  double tx;
  switch (rotacionGrados) {
    case 90:
      tx = x * tamanoLienzo.width / anchoFuente;
    case 270:
      tx = tamanoLienzo.width - x * tamanoLienzo.width / anchoFuente;
    default:
      final escalado = x * tamanoLienzo.width / anchoFuente;
      tx = camaraFrontal ? tamanoLienzo.width - escalado : escalado;
  }
  final ty = y * tamanoLienzo.height / altoFuente;
  return Offset(tx, ty);
}

/// Calcula el ajuste de la prenda, o `null` si los hombros no son fiables (persona fuera de cuadro).
AjustePrenda? calcularAjustePrenda(PuntosTorso puntos) {
  final izq = puntos.hombroIzquierdo;
  final der = puntos.hombroDerecho;
  if (!izq.esFiable || !der.esFiable) return null;

  // La cámara frontal refleja la imagen: se toma el vector del hombro más a la izquierda en
  // pantalla al más a la derecha, para que la inclinación no salte a ±π.
  var vector = der.posicion - izq.posicion;
  if (vector.dx < 0) vector = -vector;

  final anchoHombros = vector.distance;
  if (anchoHombros < 1) return null;

  return AjustePrenda(
    centroHombros: Offset.lerp(izq.posicion, der.posicion, 0.5)!,
    ancho: anchoHombros / proporcionHombrosPrenda,
    rotacion: math.atan2(vector.dy, vector.dx),
  );
}

/// Media móvil exponencial: evita que la prenda tiemble con el ruido fotograma a fotograma.
class SuavizadorAjuste {
  /// Peso del fotograma nuevo (0–1). Más alto = más reactivo, más bajo = más estable.
  final double alfa;
  AjustePrenda? _ultimo;

  SuavizadorAjuste({this.alfa = 0.35});

  AjustePrenda? get ultimo => _ultimo;

  AjustePrenda suavizar(AjustePrenda nuevo) {
    final previo = _ultimo;
    if (previo == null) return _ultimo = nuevo;
    return _ultimo = AjustePrenda(
      centroHombros: Offset.lerp(previo.centroHombros, nuevo.centroHombros, alfa)!,
      ancho: previo.ancho + (nuevo.ancho - previo.ancho) * alfa,
      rotacion: previo.rotacion + (nuevo.rotacion - previo.rotacion) * alfa,
    );
  }

  void reiniciar() => _ultimo = null;
}
