import 'package:flutter/foundation.dart';
import '../../datos/datasources/recomendaciones_api.dart';
import '../../datos/modelos/recomendacion_item_dto.dart';

sealed class InicioEstado {
  const InicioEstado();
}

class InicioInicial extends InicioEstado {
  const InicioInicial();
}

class InicioCargando extends InicioEstado {
  const InicioCargando();
}

class InicioCargado extends InicioEstado {
  final RecomendacionesResponseDto respuesta;

  const InicioCargado(this.respuesta);

  bool get tieneHistorial => respuesta.tieneHistorial;
  List<ProductoRecomendadoDto> get items => respuesta.items;
  String? get motivoGeneral => respuesta.motivoGeneral;
  String get boutiqueReferencia => respuesta.boutiqueReferencia;
  String? get mensajeEmptyState => respuesta.mensajeEmptyState;
}

class InicioError extends InicioEstado {
  final String mensaje;
  const InicioError(this.mensaje);
}

class InicioBloc extends ChangeNotifier {
  final RecomendacionesApi _api;

  InicioBloc({RecomendacionesApi? api}) : _api = api ?? RecomendacionesApiImpl();

  InicioEstado _estado = const InicioInicial();
  InicioEstado get estado => _estado;

  final Set<int> _favoritos = {};
  Set<int> get favoritos => Set.unmodifiable(_favoritos);

  int _cestaCount = 0;
  int get cestaCount => _cestaCount;

  String? _mensajePrendaAgregada;
  String? get mensajePrendaAgregada => _mensajePrendaAgregada;

  String _nombreCliente = 'Ana Valenzuela';
  String get nombreCliente => _nombreCliente;

  void establecerNombreCliente(String nombre) {
    _nombreCliente = nombre;
    notifyListeners();
  }

  Future<void> cargarInicio({String? token, int limite = 6}) async {
    _estado = const InicioCargando();
    notifyListeners();

    try {
      final respuesta = await _api.obtenerRecomendaciones(
        token: token,
        limite: limite,
      );
      _estado = InicioCargado(respuesta);
    } catch (e) {
      _estado = InicioCargado(RecomendacionesResponseDto.emptyState());
    } finally {
      notifyListeners();
    }
  }

  void toggleFavorito(int idProducto) {
    if (_favoritos.contains(idProducto)) {
      _favoritos.remove(idProducto);
    } else {
      _favoritos.add(idProducto);
    }
    notifyListeners();
  }

  void agregarACesta(ProductoRecomendadoDto producto) {
    _cestaCount++;
    _mensajePrendaAgregada = '"${producto.nombre}" ha sido añadida a tu bolsa de compra.';
    notifyListeners();
  }

  void limpiarMensajeToast() {
    _mensajePrendaAgregada = null;
    notifyListeners();
  }
}
