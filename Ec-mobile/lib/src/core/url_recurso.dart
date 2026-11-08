/// Resolución de las URLs de recursos (imágenes) que la base de datos guarda como rutas relativas.
///
/// El navegador completa una ruta relativa con el origen de la página; `Image.network` no puede,
/// así que el móvil debe convertirla en absoluta antes de pintarla.
///
/// Solo se resuelven prefijos **conocidos del servidor**. Todo lo demás se devuelve intacto: URLs
/// absolutas (`https://...`), `file://` y rutas locales del dispositivo. Esto último es deliberado:
/// en Android los archivos de la app también empiezan por `/` (`/data/user/0/...`), y el futuro
/// modo offline guardará imágenes en disco que esta función no debe confundir con rutas web.
library;

import '../../api_config.dart';

/// Recursos estáticos del frontend web (Vercel / `ng serve`), p. ej. `productos.modelo_ar_url`.
const List<String> prefijosRecursoWeb = ['/ar/'];

/// Archivos servidos por el backend (FastAPI), p. ej. las fotos subidas desde el panel (CU22).
const List<String> prefijosRecursoApi = ['/static/'];

String _sinBarraFinal(String base) => base.replaceAll(RegExp(r'/+$'), '');

/// Devuelve la URL lista para `Image.network`, o el valor original si no es una ruta relativa de
/// servidor. `null` se conserva como `null`.
///
/// `baseWeb` y `baseApi` permiten fijar los orígenes en pruebas; por defecto se usan `WEB_URL` y
/// `API_URL` de [ApiConfig].
String? resolverUrlRecurso(String? url, {String? baseWeb, String? baseApi}) {
  if (url == null) return null;
  final limpia = url.trim();
  if (prefijosRecursoWeb.any(limpia.startsWith)) {
    return '${_sinBarraFinal(baseWeb ?? ApiConfig.webBaseUrl)}$limpia';
  }
  if (prefijosRecursoApi.any(limpia.startsWith)) {
    return '${_sinBarraFinal(baseApi ?? ApiConfig.baseUrl)}$limpia';
  }
  return url;
}
