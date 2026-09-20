import 'producto_item_dto.dart';
import 'paginacion_dto.dart';

/// DTO de respuesta paginada devuelto por GET /api/v1/productos.
class ProductoPaginadoDto {
  final List<ProductoItemDto> items;
  final PaginacionDto paginacion;
  final Map<String, dynamic>? filtrosAplicados;

  const ProductoPaginadoDto({
    required this.items,
    required this.paginacion,
    this.filtrosAplicados,
  });

  factory ProductoPaginadoDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return ProductoPaginadoDto(
      items: rawItems
          .map((i) => ProductoItemDto.fromJson(i as Map<String, dynamic>))
          .toList(),
      paginacion: json['paginacion'] != null
          ? PaginacionDto.fromJson(json['paginacion'] as Map<String, dynamic>)
          : PaginacionDto.vacio(),
      filtrosAplicados: json['filtros_aplicados'] as Map<String, dynamic>?,
    );
  }

  factory ProductoPaginadoDto.vacio() {
    return ProductoPaginadoDto(
      items: const [],
      paginacion: PaginacionDto.vacio(),
    );
  }
}
