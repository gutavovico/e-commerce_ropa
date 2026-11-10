import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'modelos_sin_conexion.dart';

/// P2-CU14 / CU19 · Base local (SQLite). Sobrevive a reinicios (RNF03). Las claves llevan el código
/// de la tienda: dos tiendas en el mismo teléfono no ven lo de la otra. Las operaciones no se borran
/// al enviarse ni al cerrar sesión (RN37). Cada escritura va en su propia transacción.
abstract class AlmacenLocal {
  Future<DispositivoLocal?> dispositivo(String clave);
  Future<void> guardarDispositivo(DispositivoLocal dispositivo);

  /// Siguiente correlativo del código provisional, leído e incrementado en la misma transacción.
  Future<int> siguienteCorrelativo(String clave);

  Future<(CatalogoLocal, DateTime)?> catalogo(String codigoTienda);

  /// Reemplaza el catálogo de la tienda solo cuando la descarga terminó (CU14 A2).
  Future<void> guardarCatalogo(String codigoTienda, Map<String, dynamic> paqueteJson, DateTime guardadoEn);
  Future<void> borrarCatalogos();

  Future<List<OperacionLocal>> operaciones(String clave);
  Future<void> guardarOperacion(OperacionLocal operacion);
}

class AlmacenSqlite implements AlmacenLocal {
  static const _nombre = 'fashionstore_sin_conexion.db';

  final DatabaseFactory _fabrica;
  final String? _ruta;
  Future<Database>? _bd;

  /// `fabrica` y `ruta` se inyectan en las pruebas (`sqflite_common_ffi`, `inMemoryDatabasePath`).
  AlmacenSqlite({DatabaseFactory? fabrica, String? ruta})
      : _fabrica = fabrica ?? databaseFactory,
        _ruta = ruta;

  static final AlmacenSqlite instancia = AlmacenSqlite();

  Future<Database> _abrir() => _bd ??= () async {
        final ruta = _ruta ?? '${await _fabrica.getDatabasesPath()}/$_nombre';
        return _fabrica.openDatabase(
          ruta,
          options: OpenDatabaseOptions(
            version: 1,
            onCreate: (bd, _) async {
              await bd.execute('CREATE TABLE dispositivos (clave TEXT PRIMARY KEY, json TEXT NOT NULL)');
              await bd.execute(
                  'CREATE TABLE catalogos (codigo TEXT PRIMARY KEY, json TEXT NOT NULL, guardado_en TEXT NOT NULL)');
              await bd.execute(
                  'CREATE TABLE operaciones (uuid TEXT PRIMARY KEY, clave TEXT NOT NULL, json TEXT NOT NULL)');
              await bd.execute('CREATE INDEX idx_operaciones_clave ON operaciones (clave)');
            },
          ),
        );
      }();

  @override
  Future<DispositivoLocal?> dispositivo(String clave) async {
    final filas = await (await _abrir()).query('dispositivos', where: 'clave = ?', whereArgs: [clave]);
    if (filas.isEmpty) return null;
    return DispositivoLocal.fromJson(jsonDecode(filas.first['json'] as String) as Map<String, dynamic>);
  }

  @override
  Future<void> guardarDispositivo(DispositivoLocal dispositivo) async {
    await (await _abrir()).transaction((tx) => tx.insert(
          'dispositivos',
          {'clave': dispositivo.clave, 'json': jsonEncode(dispositivo.toJson())},
          conflictAlgorithm: ConflictAlgorithm.replace,
        ));
  }

  @override
  Future<int> siguienteCorrelativo(String clave) async {
    return (await _abrir()).transaction((tx) async {
      final filas = await tx.query('dispositivos', where: 'clave = ?', whereArgs: [clave]);
      if (filas.isEmpty) throw StateError('Dispositivo sin registrar');
      final actual = DispositivoLocal.fromJson(jsonDecode(filas.first['json'] as String) as Map<String, dynamic>);
      final siguiente = actual.copyWith(correlativo: actual.correlativo + 1);
      await tx.update('dispositivos', {'json': jsonEncode(siguiente.toJson())}, where: 'clave = ?', whereArgs: [clave]);
      return siguiente.correlativo;
    });
  }

  @override
  Future<(CatalogoLocal, DateTime)?> catalogo(String codigoTienda) async {
    final filas = await (await _abrir()).query('catalogos', where: 'codigo = ?', whereArgs: [codigoTienda]);
    if (filas.isEmpty) return null;
    final paquete = CatalogoLocal.fromJson(jsonDecode(filas.first['json'] as String) as Map<String, dynamic>);
    return (paquete, DateTime.parse(filas.first['guardado_en'] as String));
  }

  @override
  Future<void> guardarCatalogo(String codigoTienda, Map<String, dynamic> paqueteJson, DateTime guardadoEn) async {
    await (await _abrir()).transaction((tx) => tx.insert(
          'catalogos',
          {'codigo': codigoTienda, 'json': jsonEncode(paqueteJson), 'guardado_en': guardadoEn.toUtc().toIso8601String()},
          conflictAlgorithm: ConflictAlgorithm.replace,
        ));
  }

  @override
  Future<void> borrarCatalogos() async {
    await (await _abrir()).delete('catalogos');
  }

  @override
  Future<List<OperacionLocal>> operaciones(String clave) async {
    final filas = await (await _abrir()).query('operaciones', where: 'clave = ?', whereArgs: [clave]);
    final lista = [
      for (final f in filas) OperacionLocal.fromJson(jsonDecode(f['json'] as String) as Map<String, dynamic>),
    ];
    lista.sort((a, b) => b.registradaEn.compareTo(a.registradaEn));
    return lista;
  }

  @override
  Future<void> guardarOperacion(OperacionLocal operacion) async {
    await (await _abrir()).transaction((tx) => tx.insert(
          'operaciones',
          {'uuid': operacion.uuid, 'clave': operacion.clave, 'json': jsonEncode(operacion.toJson())},
          conflictAlgorithm: ConflictAlgorithm.replace,
        ));
  }

  Future<void> cerrar() async {
    final bd = _bd;
    _bd = null;
    if (bd != null) await (await bd).close();
  }
}
