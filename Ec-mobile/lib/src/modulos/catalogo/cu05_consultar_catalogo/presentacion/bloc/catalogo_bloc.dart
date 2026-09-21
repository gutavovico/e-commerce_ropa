import 'package:flutter/foundation.dart';
import '../../datos/datasources/catalogo_api.dart';
import '../../datos/modelos/catalogo_dto.dart';

sealed class CatalogoGeneralEstado {
  const CatalogoGeneralEstado();
}

class CatalogoGeneralInicial extends CatalogoGeneralEstado {
  const CatalogoGeneralInicial();
}

class CatalogoGeneralCargando extends CatalogoGeneralEstado {
  const CatalogoGeneralCargando();
}

class CatalogoGeneralCargado extends CatalogoGeneralEstado {
  final CatalogoResponseDto respuesta;
  final int? categoriaSeleccionadaId;
  final int modoColumnas;
  final Set<int> favoritos;
  final bool cargandoMas;
  final List<ProductoCatalogoItemDto> productosAcumulados;

  const CatalogoGeneralCargado({
    required this.respuesta,
    this.categoriaSeleccionadaId,
    this.modoColumnas = 2,
    this.favoritos = const {},
    this.cargandoMas = false,
    this.productosAcumulados = const [],
  });

  List<CategoriaResumenDto> get resumenCategorias =>
      respuesta.resumenCategorias;
  int get totalArticulos => respuesta.totalArticulos;
  int get paginaActual => respuesta.paginaActual;
  int get limite => respuesta.limite;
  int get totalPaginas => respuesta.totalPaginas;
  bool get tieneSiguiente => respuesta.tieneSiguiente;
  bool get tieneAnterior => respuesta.tieneAnterior;

  int get totalGlobalPrendas =>
      resumenCategorias.fold(0, (acc, c) => acc + c.totalPrendas);

  int get prendasRestantes =>
      (totalArticulos - productosAcumulados.length).clamp(0, totalArticulos);

  CatalogoGeneralCargado copyWith({
    CatalogoResponseDto? respuesta,
    int? categoriaSeleccionadaId,
    bool clearCategoria = false,
    int? modoColumnas,
    Set<int>? favoritos,
    bool? cargandoMas,
    List<ProductoCatalogoItemDto>? productosAcumulados,
  }) {
    return CatalogoGeneralCargado(
      respuesta: respuesta ?? this.respuesta,
      categoriaSeleccionadaId: clearCategoria
          ? null
          : (categoriaSeleccionadaId ?? this.categoriaSeleccionadaId),
      modoColumnas: modoColumnas ?? this.modoColumnas,
      favoritos: favoritos ?? this.favoritos,
      cargandoMas: cargandoMas ?? this.cargandoMas,
      productosAcumulados:
          productosAcumulados ?? this.productosAcumulados,
    );
  }
}

class CatalogoGeneralVacio extends CatalogoGeneralEstado {
  final List<CategoriaResumenDto> resumenCategorias;
  final int? categoriaSeleccionadaId;
  final String mensaje;

  const CatalogoGeneralVacio({
    required this.resumenCategorias,
    this.categoriaSeleccionadaId,
    this.mensaje = 'No se encontraron prendas para esta categoría.',
  });

  int get totalGlobalPrendas =>
      resumenCategorias.fold(0, (acc, c) => acc + c.totalPrendas);
}

class CatalogoGeneralError extends CatalogoGeneralEstado {
  final String mensaje;

  const CatalogoGeneralError(this.mensaje);
}

class CatalogoGeneralBloc extends ChangeNotifier {
  final CatalogoApi _api;

  CatalogoGeneralBloc({CatalogoApi? api})
      : _api = api ?? CatalogoApiImpl();

  CatalogoGeneralEstado _estado = const CatalogoGeneralInicial();
  CatalogoGeneralEstado get estado => _estado;

  int? _categoriaSeleccionadaId;
  int? get categoriaSeleccionadaId => _categoriaSeleccionadaId;

  String _ordenarPor = 'recientes';
  String get ordenarPor => _ordenarPor;

  int _modoColumnas = 2;
  int get modoColumnas => _modoColumnas;

  int _paginaActual = 1;
  int get paginaActual => _paginaActual;

  final Set<int> _favoritos = {};
  Set<int> get favoritos => Set.unmodifiable(_favoritos);

  int _cestaCount = 2;
  int get cestaCount => _cestaCount;

  Future<void> cargarCatalogo({
    int? categoriaId,
    String? ordenarPor,
    int pagina = 1,
    int limite = 6,
    bool esCargaMas = false,
  }) async {
    if (categoriaId != null || categoriaId == null && !esCargaMas) {
      _categoriaSeleccionadaId = categoriaId;
    }
    if (ordenarPor != null) {
      _ordenarPor = ordenarPor;
    }
    _paginaActual = pagina;

    if (!esCargaMas) {
      _estado = const CatalogoGeneralCargando();
      notifyListeners();
    } else if (_estado is CatalogoGeneralCargado) {
      final actual = _estado as CatalogoGeneralCargado;
      _estado = actual.copyWith(cargandoMas: true);
      notifyListeners();
    }

    try {
      final res = await _api.consultarCatalogo(
        categoriaId: _categoriaSeleccionadaId,
        ordenarPor: _ordenarPor,
        pagina: _paginaActual,
        limite: limite,
      );

      if (res.totalArticulos == 0 || res.items.isEmpty) {
        _estado = CatalogoGeneralVacio(
          resumenCategorias: res.resumenCategorias,
          categoriaSeleccionadaId: _categoriaSeleccionadaId,
          mensaje: 'Colección no disponible actualmente en esta categoría.',
        );
      } else {
        List<ProductoCatalogoItemDto> productosFinales;
        if (esCargaMas && _estado is CatalogoGeneralCargado) {
          final actual = _estado as CatalogoGeneralCargado;
          // Evitar duplicados por idProducto
          final idsExistentes = actual.productosAcumulados.map((p) => p.idProducto).toSet();
          final nuevos = res.items.where((p) => !idsExistentes.contains(p.idProducto)).toList();
          productosFinales = [...actual.productosAcumulados, ...nuevos];
        } else {
          productosFinales = res.items;
        }

        _estado = CatalogoGeneralCargado(
          respuesta: res,
          categoriaSeleccionadaId: _categoriaSeleccionadaId,
          modoColumnas: _modoColumnas,
          favoritos: Set.from(_favoritos),
          cargandoMas: false,
          productosAcumulados: productosFinales,
        );
      }
    } on CatalogoException catch (e) {
      _estado = CatalogoGeneralError(e.mensaje);
    } catch (e) {
      _estado = CatalogoGeneralError('Error inesperado al cargar el catálogo: $e');
    }

    notifyListeners();
  }

  void seleccionarCategoria(int? idCategoria) {
    if (_categoriaSeleccionadaId == idCategoria) return;
    _categoriaSeleccionadaId = idCategoria;
    cargarCatalogo(categoriaId: idCategoria, pagina: 1);
  }

  void cambiarOrden(String nuevoOrden) {
    if (_ordenarPor == nuevoOrden) return;
    _ordenarPor = nuevoOrden;
    cargarCatalogo(pagina: 1);
  }

  void cambiarModoColumnas(int columnas) {
    if (_modoColumnas == columnas) return;
    _modoColumnas = columnas;
    if (_estado is CatalogoGeneralCargado) {
      _estado = (_estado as CatalogoGeneralCargado).copyWith(
        modoColumnas: columnas,
      );
      notifyListeners();
    }
  }

  Future<void> cargarMas() async {
    if (_estado is! CatalogoGeneralCargado) return;
    final actual = _estado as CatalogoGeneralCargado;
    if (!actual.tieneSiguiente || actual.cargandoMas) return;

    await cargarCatalogo(
      pagina: actual.paginaActual + 1,
      limite: actual.limite,
      esCargaMas: true,
    );
  }

  void irAPagina(int pagina) {
    cargarCatalogo(pagina: pagina, esCargaMas: false);
  }

  void toggleFavorito(int idProducto) {
    if (_favoritos.contains(idProducto)) {
      _favoritos.remove(idProducto);
    } else {
      _favoritos.add(idProducto);
    }

    if (_estado is CatalogoGeneralCargado) {
      _estado = (_estado as CatalogoGeneralCargado).copyWith(
        favoritos: Set.from(_favoritos),
      );
    }
    notifyListeners();
  }

  void agregarACesta(int idProducto) {
    _cestaCount++;
    notifyListeners();
  }
}
