import '../../datos/fuentes_datos/catalogo_remoto_datasource.dart';
import '../../datos/modelos/producto_paginado_dto.dart';
import '../../datos/modelos/filtros_disponibles_dto.dart';

abstract class CatalogoRepositorio {
  Future<ProductoPaginadoDto> buscarProductos({
    String? q,
    int? temporadaId,
    int? coleccionId,
    int? categoriaId,
    String? talla,
    String? color,
    double? precioMin,
    double? precioMax,
    bool soloEnStock = false,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 12,
  });

  Future<FiltrosDisponiblesDto> obtenerFiltrosDisponibles();
}

class CatalogoRepositorioImpl implements CatalogoRepositorio {
  final CatalogoRemotoDatasource _datasource;

  CatalogoRepositorioImpl({CatalogoRemotoDatasource? datasource})
      : _datasource = datasource ?? CatalogoRemotoDatasource();

  @override
  Future<ProductoPaginadoDto> buscarProductos({
    String? q,
    int? temporadaId,
    int? coleccionId,
    int? categoriaId,
    String? talla,
    String? color,
    double? precioMin,
    double? precioMax,
    bool soloEnStock = false,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 12,
  }) {
    return _datasource.buscarProductos(
      q: q,
      temporadaId: temporadaId,
      coleccionId: coleccionId,
      categoriaId: categoriaId,
      talla: talla,
      color: color,
      precioMin: precioMin,
      precioMax: precioMax,
      soloEnStock: soloEnStock,
      ordenarPor: ordenarPor,
      pagina: pagina,
      limite: limite,
    );
  }

  @override
  Future<FiltrosDisponiblesDto> obtenerFiltrosDisponibles() {
    return _datasource.obtenerFiltrosDisponibles();
  }
}
