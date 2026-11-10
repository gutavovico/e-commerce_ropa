import 'dart:convert';

/// Datos públicos del JWT de la sesión (`sub` = id del usuario, `rol`). Solo se leen para separar
/// los datos locales por cliente; la firma la comprueba siempre el servidor.
({int? idUsuario, String? rol}) leerToken(String token) {
  try {
    final partes = token.split('.');
    if (partes.length != 3) return (idUsuario: null, rol: null);
    final carga = jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(partes[1])))) as Map<String, dynamic>;
    return (idUsuario: int.tryParse(carga['sub']?.toString() ?? ''), rol: carga['rol']?.toString());
  } catch (_) {
    return (idUsuario: null, rol: null);
  }
}
