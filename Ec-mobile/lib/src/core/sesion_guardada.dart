import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'empresa_actual.dart';
import 'sin_conexion/almacen_local.dart';

/// Sesión que sobrevive a cerrar la app (defecto del bloque 3: sin ella, sin internet no se podía
/// volver a entrar al catálogo local ni reservar).
@immutable
class SesionPersistida {
  final String token;
  final String nombreUsuario;
  final String rol;

  /// Tienda en la que navega (cliente) o la de su cuenta (empleado). Nula: cliente sin tienda elegida.
  final EmpresaTienda? empresa;

  const SesionPersistida({required this.token, required this.nombreUsuario, required this.rol, this.empresa});

  factory SesionPersistida.fromJson(Map<String, dynamic> j) => SesionPersistida(
        token: j['token'] as String? ?? '',
        nombreUsuario: j['nombre_usuario'] as String? ?? '',
        rol: j['rol'] as String? ?? '',
        empresa: j['empresa'] is Map<String, dynamic> ? EmpresaTienda.fromJson(j['empresa'] as Map<String, dynamic>) : null,
      );

  Map<String, dynamic> toJson() =>
      {'token': token, 'nombre_usuario': nombreUsuario, 'rol': rol, 'empresa': empresa?.toJson()};
}

/// Vencimiento (`exp`) del JWT, sin comprobar la firma: eso lo hace siempre el servidor.
DateTime? vencimientoToken(String token) {
  try {
    final partes = token.split('.');
    if (partes.length != 3) return null;
    final carga = jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(partes[1])))) as Map<String, dynamic>;
    final exp = carga['exp'];
    return exp is num ? DateTime.fromMillisecondsSinceEpoch(exp.toInt() * 1000, isUtc: true) : null;
  } catch (_) {
    return null;
  }
}

/// Guarda, lee y borra la sesión en la base local. Un fallo de la base nunca impide entrar: se trata
/// como «sin sesión guardada» y se muestra el login.
class SesionGuardada {
  static const _clave = '__sesion__';

  final AlmacenLocal _almacen;
  final DateTime Function() _ahora;

  SesionGuardada({AlmacenLocal? almacen, DateTime Function()? ahora})
      : _almacen = almacen ?? AlmacenSqlite.instancia,
        _ahora = ahora ?? DateTime.now;

  static final SesionGuardada instancia = SesionGuardada();

  /// La sesión guardada si su token no ha vencido; si venció, la borra (AC-A3).
  Future<SesionPersistida?> leerVigente() async {
    try {
      final datos = await _almacen.valor(_clave);
      if (datos == null) return null;
      final sesion = SesionPersistida.fromJson(datos);
      final vence = vencimientoToken(sesion.token);
      if (sesion.token.isEmpty || vence == null || !vence.isAfter(_ahora().toUtc())) {
        await borrar();
        return null;
      }
      return sesion;
    } catch (_) {
      return null;
    }
  }

  Future<void> guardar(SesionPersistida sesion) async {
    try {
      await _almacen.guardarValor(_clave, sesion.toJson());
    } catch (_) {}
  }

  /// Solo borra la sesión: las operaciones pendientes se conservan (RN37).
  Future<void> borrar() async {
    try {
      await _almacen.borrarValor(_clave);
    } catch (_) {}
  }
}
