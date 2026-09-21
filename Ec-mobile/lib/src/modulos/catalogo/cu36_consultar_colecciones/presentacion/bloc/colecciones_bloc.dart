import 'package:flutter/foundation.dart';
import '../../datos/datasources/colecciones_api.dart';
import '../../datos/modelos/coleccion_dto.dart';

sealed class ColeccionesEstado {
  const ColeccionesEstado();
}

class ColeccionesInicial extends ColeccionesEstado {
  const ColeccionesInicial();
}

class ColeccionesCargando extends ColeccionesEstado {
  const ColeccionesCargando();
}

class ColeccionesCargadas extends ColeccionesEstado {
  final ColeccionesActivasResponseDto respuesta;
  final String chipSeleccionado;

  const ColeccionesCargadas({
    required this.respuesta,
    required this.chipSeleccionado,
  });

  String get temporadaNombre =>
      respuesta.temporadaActivaNombre ?? 'Temporada Vigente';
  ColeccionResumenDto? get destacada => respuesta.coleccionDestacada;
  List<ColeccionResumenDto> get otrasColecciones => respuesta.otrasColecciones;
  int get totalColecciones => respuesta.totalColecciones;
}

class DetalleColeccionCargado extends ColeccionesEstado {
  final ColeccionDetalleDto detalle;

  const DetalleColeccionCargado(this.detalle);
}

class ColeccionesError extends ColeccionesEstado {
  final String mensaje;

  const ColeccionesError(this.mensaje);
}

class ColeccionesBloc extends ChangeNotifier {
  final ColeccionesApi _api;

  ColeccionesBloc({ColeccionesApi? api}) : _api = api ?? ColeccionesApiImpl();

  ColeccionesEstado _estado = const ColeccionesInicial();
  ColeccionesEstado get estado => _estado;

  String _chipSeleccionado = 'COLECCIÓN DESTACADA';
  String get chipSeleccionado => _chipSeleccionado;

  final Set<int> _bookmarks = {};
  Set<int> get bookmarks => Set.unmodifiable(_bookmarks);

  int _cestaCount = 0;
  int get cestaCount => _cestaCount;

  String? _mensajeToast;
  String? get mensajeToast => _mensajeToast;

  ColeccionDetalleDto? _detalleActual;
  ColeccionDetalleDto? get detalleActual => _detalleActual;

  bool _cargandoDetalle = false;
  bool get cargandoDetalle => _cargandoDetalle;

  String? _errorDetalle;
  String? get errorDetalle => _errorDetalle;

  Future<void> cargarColeccionesActivas({int limitePiezasClave = 4}) async {
    _estado = const ColeccionesCargando();
    notifyListeners();

    try {
      final respuesta = await _api.obtenerColeccionesActivas(
        limitePiezasClave: limitePiezasClave,
      );
      _estado = ColeccionesCargadas(
        respuesta: respuesta,
        chipSeleccionado: _chipSeleccionado,
      );
    } catch (e) {
      _estado = ColeccionesError(e.toString());
    }
    notifyListeners();
  }

  void seleccionarChip(String chip) {
    if (_chipSeleccionado == chip) return;
    _chipSeleccionado = chip;
    if (_estado is ColeccionesCargadas) {
      final actual = _estado as ColeccionesCargadas;
      _estado = ColeccionesCargadas(
        respuesta: actual.respuesta,
        chipSeleccionado: _chipSeleccionado,
      );
      notifyListeners();
    }
  }

  Future<void> cargarPrendasColeccion(int idColeccion) async {
    _cargandoDetalle = true;
    _errorDetalle = null;
    notifyListeners();

    try {
      _detalleActual = await _api.obtenerPrendasDeColeccion(idColeccion);
      _cargandoDetalle = false;
    } catch (e) {
      _errorDetalle = e.toString();
      _cargandoDetalle = false;
    }
    notifyListeners();
  }

  void alternarBookmark(int idProducto) {
    if (_bookmarks.contains(idProducto)) {
      _bookmarks.remove(idProducto);
    } else {
      _bookmarks.add(idProducto);
    }
    notifyListeners();
  }

  bool esBookmark(int idProducto) => _bookmarks.contains(idProducto);

  void agregarACesta(ProductoColeccionItemDto item) {
    _cestaCount++;
    _mensajeToast = '${item.nombre} añadida a tu cesta privada.';
    notifyListeners();
  }

  void limpiarMensajeToast() {
    _mensajeToast = null;
    notifyListeners();
  }
}
