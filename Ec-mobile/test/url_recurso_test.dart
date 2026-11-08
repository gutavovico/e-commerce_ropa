import 'dart:convert';

import 'package:ec_mobile/api_config.dart';
import 'package:ec_mobile/src/core/url_recurso.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/datos/modelos/producto_detalle_dto.dart';
import 'package:flutter_test/flutter_test.dart';

// Subconjunto literal de `GET /api/v1/productos/22` (prenda de prueba de CU10).
const String _jsonProducto22 = '{"id_producto": 22, "nombre": "Camiseta básica amarilla de algodón", '
    '"categoria_nombre": "Camisas", "precio_base": "45.00", "precio_final": "45.00", '
    '"imagen_principal": "/ar/camiseta_basica_amarilla.png", "modelo_ar_url": "/ar/camiseta_basica_amarilla_ar.png", '
    '"galeria": [{"url": "/ar/camiseta_basica_amarilla.png", "etiqueta": "FRONTAL", "orden": 1}, '
    '{"url": "/ar/camiseta_basica_amarilla.png?auto=format&fit=crop&w=1000&h=1200&crop=top&q=85", '
    '"etiqueta": "ALGODÓN GIZA", "orden": 2}]}';

void main() {
  group('resolverUrlRecurso', () {
    const web = 'https://web.test/';
    const api = 'https://api.test';

    test('las rutas /ar/ van al frontend web', () {
      expect(resolverUrlRecurso('/ar/x.png', baseWeb: web, baseApi: api), 'https://web.test/ar/x.png');
    });

    test('las rutas /static/ van al backend (fotos subidas desde el panel)', () {
      expect(
        resolverUrlRecurso('/static/uploads/productos/prod_1.png', baseWeb: web, baseApi: api),
        'https://api.test/static/uploads/productos/prod_1.png',
      );
    });

    test('las URLs absolutas no se tocan', () {
      const unsplash = 'https://images.unsplash.com/photo-1?w=800';
      expect(resolverUrlRecurso(unsplash, baseWeb: web, baseApi: api), unsplash);
    });

    test('las rutas locales del dispositivo no se confunden con rutas web (modo offline)', () {
      const android = '/data/user/0/com.ecommerce.ec_mobile/files/camiseta.png';
      const uri = 'file:///data/user/0/com.ecommerce.ec_mobile/files/camiseta.png';
      expect(resolverUrlRecurso(android, baseWeb: web, baseApi: api), android);
      expect(resolverUrlRecurso(uri, baseWeb: web, baseApi: api), uri);
    });

    test('null y vacío se conservan', () {
      expect(resolverUrlRecurso(null), isNull);
      expect(resolverUrlRecurso(''), '');
    });

    test('es idempotente', () {
      final una = resolverUrlRecurso('/ar/x.png', baseWeb: web);
      expect(resolverUrlRecurso(una, baseWeb: web), una);
    });
  });

  test('ProductoDetalleDto resuelve imagen principal, galería y recurso AR contra WEB_URL', () {
    final dto = ProductoDetalleDto.fromJson(jsonDecode(_jsonProducto22) as Map<String, dynamic>);
    final base = ApiConfig.webBaseUrl;

    expect(dto.imagenUrl, '$base/ar/camiseta_basica_amarilla.png');
    expect(dto.modeloArUrl, '$base/ar/camiseta_basica_amarilla_ar.png');
    expect(dto.galeriaAngulos.map((g) => g.url), everyElement(startsWith('$base/ar/camiseta_basica_amarilla.png')));
  });
}
