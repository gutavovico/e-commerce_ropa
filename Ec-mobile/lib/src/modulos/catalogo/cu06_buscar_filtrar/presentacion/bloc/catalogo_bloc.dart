import 'package:flutter/foundation.dart';
import '../../datos/modelos/producto_item_dto.dart';
import '../../datos/modelos/paginacion_dto.dart';
import '../../datos/modelos/filtros_disponibles_dto.dart';
import '../../dominio/repositorios/catalogo_repositorio.dart';

sealed class CatalogoEstado {
  const CatalogoEstado();
}

class CatalogoInicial extends CatalogoEstado {
  const CatalogoInicial();
}

class CatalogoCargando extends CatalogoEstado {
  const CatalogoCargando();
}

class CatalogoCargado extends CatalogoEstado {
  final List<ProductoItemDto> productos;
  final PaginacionDto paginacion;

  const CatalogoCargado({
    required this.productos,
    required this.paginacion,
  });
}

class CatalogoError extends CatalogoEstado {
  final String mensaje;
  const CatalogoError(this.mensaje);
}

class CatalogoBloc extends ChangeNotifier {
  final CatalogoRepositorio _repositorio;

  CatalogoBloc({CatalogoRepositorio? repositorio})
      : _repositorio = repositorio ?? CatalogoRepositorioImpl();

  CatalogoEstado _estado = const CatalogoInicial();
  CatalogoEstado get estado => _estado;

  FiltrosDisponiblesDto? _filtrosDisponibles;
  FiltrosDisponiblesDto? get filtrosDisponibles => _filtrosDisponibles;

  // Estado de filtros
  String _terminoBusquedaActivo = '';
  String get terminoBusquedaActivo => _terminoBusquedaActivo;

  String _temporadaSeleccionada = 'Todas las temporadas';
  String get temporadaSeleccionada => _temporadaSeleccionada;

  String _coleccionSeleccionada = '';
  String get coleccionSeleccionada => _coleccionSeleccionada;

  String _tallaSeleccionada = '';
  String get tallaSeleccionada => _tallaSeleccionada;

  String _colorSeleccionado = '';
  String get colorSeleccionado => _colorSeleccionado;

  double _precioMin = 0.0;
  double get precioMin => _precioMin;

  double _precioMax = 2500.0;
  double get precioMax => _precioMax;

  bool _filtroPrecioActivo = false;
  bool get filtroPrecioActivo => _filtroPrecioActivo;

  String _ordenSeleccionado = 'recientes';
  String get ordenSeleccionado => _ordenSeleccionado;

  final Set<int> _favoritosIds = {};
  Set<int> get favoritosIds => Set.unmodifiable(_favoritosIds);

  List<String> _busquedasFrecuentes = [
    'Vestidos de seda',
    'Blazers camel',
    'Cashmere 100%',
    'Colección Cápsula FW24',
    'Trajes sastre fluídos',
  ];
  List<String> get busquedasFrecuentes => List.unmodifiable(_busquedasFrecuentes);

  bool get tieneFiltrosActivos =>
      _terminoBusquedaActivo.isNotEmpty ||
      _temporadaSeleccionada != 'Todas las temporadas' ||
      _coleccionSeleccionada.isNotEmpty ||
      _tallaSeleccionada.isNotEmpty ||
      _colorSeleccionado.isNotEmpty ||
      _filtroPrecioActivo;

  /// Inicializa cargando filtros disponibles del servidor y la primera página del catálogo.
  Future<void> inicializar() async {
    _estado = const CatalogoCargando();
    notifyListeners();

    try {
      final filtros = await _repositorio.obtenerFiltrosDisponibles();
      _filtrosDisponibles = filtros;
      _precioMin = filtros.rangoPrecios.min;
      _precioMax = filtros.rangoPrecios.max;
    } catch (_) {
      // Si falla la carga de filtros auxiliares, continuamos con la búsqueda usando fallbacks
    }

    await _ejecutarConsulta(pagina: 1);
  }

  /// Selecciona temporada en modo borrador y aplica.
  void seleccionarTemporada(String nombre) {
    _temporadaSeleccionada = nombre;
    notifyListeners();
  }

  /// Alterna selección de colección.
  void alternarColeccion(String nombre) {
    _coleccionSeleccionada = _coleccionSeleccionada == nombre ? '' : nombre;
    notifyListeners();
  }

  /// Selecciona talla.
  void seleccionarTalla(String talla) {
    _tallaSeleccionada = _tallaSeleccionada == talla ? '' : talla;
    notifyListeners();
  }

  /// Selecciona color textil.
  void seleccionarColor(String color) {
    _colorSeleccionado = _colorSeleccionado == color ? '' : color;
    notifyListeners();
  }

  /// Ajusta el rango de precio.
  void setRangoPrecios(double min, double max) {
    _precioMin = min;
    _precioMax = max;
    _filtroPrecioActivo = true;
    notifyListeners();
  }

  /// Confirma la búsqueda con el nuevo término (si fue provisto) y aplica todos los filtros seleccionados.
  Future<void> confirmarBusqueda({String? nuevoTermino}) async {
    if (nuevoTermino != null && nuevoTermino.trim().isNotEmpty) {
      _terminoBusquedaActivo = nuevoTermino.trim();
    }
    await _ejecutarConsulta(pagina: 1);
  }

  /// Quita el término de búsqueda activo y re-ejecuta.
  Future<void> quitarTerminoBusqueda() async {
    _terminoBusquedaActivo = '';
    await _ejecutarConsulta(pagina: 1);
  }

  /// Restablece todos los filtros al estado predeterminado.
  Future<void> restablecerFiltros() async {
    _terminoBusquedaActivo = '';
    _temporadaSeleccionada = 'Todas las temporadas';
    _coleccionSeleccionada = '';
    _tallaSeleccionada = '';
    _colorSeleccionado = '';
    _filtroPrecioActivo = false;
    if (_filtrosDisponibles != null) {
      _precioMin = _filtrosDisponibles!.rangoPrecios.min;
      _precioMax = _filtrosDisponibles!.rangoPrecios.max;
    } else {
      _precioMin = 0.0;
      _precioMax = 2500.0;
    }
    _ordenSeleccionado = 'recientes';
    await _ejecutarConsulta(pagina: 1);
  }

  /// Cambia el orden de los resultados.
  Future<void> cambiarOrden(String orden) async {
    _ordenSeleccionado = orden;
    await _ejecutarConsulta(pagina: 1);
  }

  /// Cambia de página.
  Future<void> cambiarPagina(int pagina) async {
    await _ejecutarConsulta(pagina: pagina);
  }

  /// Aplica una búsqueda frecuente desde las píldoras inferiores.
  Future<void> aplicarBusquedaFrecuente(String termino) async {
    _terminoBusquedaActivo = termino;
    await _ejecutarConsulta(pagina: 1);
  }

  /// Limpia la lista de búsquedas frecuentes.
  void limpiarHistorial() {
    _busquedasFrecuentes = [];
    notifyListeners();
  }

  /// Alterna favorito en una prenda.
  void alternarFavorito(int idProducto) {
    if (_favoritosIds.contains(idProducto)) {
      _favoritosIds.remove(idProducto);
    } else {
      _favoritosIds.add(idProducto);
    }
    notifyListeners();
  }

  /// Ejecuta la consulta al repositorio backend con los filtros actuales.
  Future<void> _ejecutarConsulta({required int pagina}) async {
    _estado = const CatalogoCargando();
    notifyListeners();

    try {
      int? tempId;
      if (_temporadaSeleccionada.isNotEmpty &&
          _temporadaSeleccionada != 'Todas las temporadas' &&
          _filtrosDisponibles != null) {
        final match = _filtrosDisponibles!.temporadas.where(
          (t) => t.nombre.toLowerCase() == _temporadaSeleccionada.toLowerCase(),
        );
        if (match.isNotEmpty) tempId = match.first.id;
      }

      int? colId;
      if (_coleccionSeleccionada.isNotEmpty && _filtrosDisponibles != null) {
        final match = _filtrosDisponibles!.colecciones.where(
          (c) => c.nombre.toLowerCase() == _coleccionSeleccionada.toLowerCase(),
        );
        if (match.isNotEmpty) colId = match.first.id;
      }

      final resultado = await _repositorio.buscarProductos(
        q: _terminoBusquedaActivo.isNotEmpty ? _terminoBusquedaActivo : null,
        temporadaId: tempId,
        coleccionId: colId,
        talla: _tallaSeleccionada.isNotEmpty ? _tallaSeleccionada : null,
        color: _colorSeleccionado.isNotEmpty ? _colorSeleccionado : null,
        precioMin: _filtroPrecioActivo ? _precioMin : null,
        precioMax: _filtroPrecioActivo ? _precioMax : null,
        ordenarPor: _ordenSeleccionado,
        pagina: pagina,
        limite: 12,
      );

      _estado = CatalogoCargado(
        productos: resultado.items,
        paginacion: resultado.paginacion,
      );
      notifyListeners();
    } catch (e) {
      _estado = CatalogoError(e.toString());
      notifyListeners();
    }
  }
}
