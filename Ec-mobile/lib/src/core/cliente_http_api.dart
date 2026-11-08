import 'package:http/http.dart' as http;

import 'empresa_actual.dart';

/// P2-CU02 · Cliente HTTP de la API que añade la tienda elegida (`X-Tenant`) a cada petición.
///
/// Los datasources lo usan como cliente por defecto en lugar de `http.Client()`. Así la tienda viaja
/// en todas las peticiones sin repetir la cabecera en cada uno (equivale al `authInterceptor` de la
/// web). Las pruebas siguen pudiendo inyectar su propio cliente.
class ClienteHttpApi extends http.BaseClient {
  final http.Client _interno;
  final EmpresaActual _empresa;

  ClienteHttpApi({http.Client? interno, EmpresaActual? empresa})
      : _interno = interno ?? http.Client(),
        _empresa = empresa ?? EmpresaActual.instancia;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) {
    if (request.url.path.startsWith('/api/')) {
      _empresa.cabeceras().forEach((clave, valor) => request.headers.putIfAbsent(clave, () => valor));
    }
    return _interno.send(request);
  }

  @override
  void close() => _interno.close();
}
