/// Datos de la prenda que el vestidor necesita. Proceden del detalle real del producto (CU07):
/// nada se inventa ni se rellena con valores de respaldo.
class PrendaVestidor {
  final int idProducto;
  final String nombre;
  final String? categoriaNombre;

  /// `productos.modelo_ar_url`: PNG de la prenda sola con fondo transparente (puede ser relativo).
  final String modeloArUrl;
  final String? tallaCodigo;
  final String? colorNombre;

  const PrendaVestidor({
    required this.idProducto,
    required this.nombre,
    required this.modeloArUrl,
    this.categoriaNombre,
    this.tallaCodigo,
    this.colorNombre,
  });
}

/// Lo que devuelve la pantalla del vestidor a la ficha de producto.
enum ResultadoVestidor { cerrado, anadirABolsa }
