/// Prompt para Decart Lucy VTON (Motor 2). Mismo criterio que la web
/// (`Ec-frontend/.../cu10_vestidor_virtual/servicios/prompt-vton.ts`): la guía de Decart usa
/// «Substitute the current `prenda` with …» o «Add …»; un prompt genérico no indica qué
/// reemplazar. La prenda concreta la aporta la imagen de referencia.
library;

const String _sufijo = 'shown in the reference image';

class _ReglaPrenda {
  final List<String> claves;
  final String prompt;
  const _ReglaPrenda(this.claves, this.prompt);
}

/// El orden importa: la primera regla que coincide gana («vestido» antes que «top»).
const List<_ReglaPrenda> _reglas = [
  _ReglaPrenda(['vestido'], 'Substitute the current outfit with the dress $_sufijo'),
  _ReglaPrenda(['falda'], 'Substitute the current bottom with the skirt $_sufijo'),
  _ReglaPrenda(['bermuda', 'short'], 'Substitute the current pants with the shorts $_sufijo'),
  _ReglaPrenda(['pantalon', 'jean', 'palazzo'], 'Substitute the current pants with the trousers $_sufijo'),
  _ReglaPrenda(
    ['abrigo', 'trench', 'gabardina', 'capa', 'chaqueta', 'blazer', 'saco', 'cardigan', 'chaleco'],
    "Add the jacket $_sufijo over the person's current clothes",
  ),
  _ReglaPrenda(['camiseta', 'polera', 'remera', 't-shirt'], 'Substitute the current top with the t-shirt $_sufijo'),
  _ReglaPrenda(['sueter', 'jersey', 'buzo', 'sudadera'], 'Substitute the current top with the sweater $_sufijo'),
  _ReglaPrenda(['blusa', 'camisa', 'top'], 'Substitute the current top with the blouse $_sufijo'),
];

const String _promptPorDefecto = 'Substitute the current top with the garment $_sufijo';

const Map<String, String> _sinTildes = {
  'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n',
};

String _normalizar(String? texto) {
  final minusculas = (texto ?? '').toLowerCase();
  final buffer = StringBuffer();
  for (final caracter in minusculas.split('')) {
    buffer.write(_sinTildes[caracter] ?? caracter);
  }
  return buffer.toString();
}

_ReglaPrenda? _buscarRegla(String texto) {
  for (final regla in _reglas) {
    for (final clave in regla.claves) {
      if (RegExp('\\b${RegExp.escape(clave)}').hasMatch(texto)) return regla;
    }
  }
  return null;
}

/// Busca primero en el nombre (más específico) y después en la categoría.
String construirPromptVton(String nombre, String? categoria) {
  final regla = _buscarRegla(_normalizar(nombre)) ?? _buscarRegla(_normalizar(categoria));
  return regla?.prompt ?? _promptPorDefecto;
}
