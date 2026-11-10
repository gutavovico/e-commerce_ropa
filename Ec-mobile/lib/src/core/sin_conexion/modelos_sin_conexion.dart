import 'package:flutter/foundation.dart';

/// P2-CU14 / CU15 A1 / CU19 · Contratos del backend (`/api/v1/sin-conexion`, `/api/v1/avisos`) y
/// registros que la app guarda en SQLite. Los importes llegan como cadena (FastAPI serializa
/// `Decimal` así) y se conservan como `String`: se muestran con `formatoImporte`.

int _entero(Object? v, [int porDefecto = 0]) =>
    v is int ? v : (v is num ? v.toInt() : int.tryParse(v?.toString() ?? '') ?? porDefecto);

String _texto(Object? v) => v?.toString() ?? '';

String? _textoONulo(Object? v) => v?.toString();

// ------------------------------------------------------------------------------- API

@immutable
class ParametrosSinConexion {
  final bool operacionOfflineHabilitada;
  final int diasAntiguedadOffline;
  final int horasVencimientoReserva;
  final String moneda;

  const ParametrosSinConexion({
    required this.operacionOfflineHabilitada,
    required this.diasAntiguedadOffline,
    required this.horasVencimientoReserva,
    required this.moneda,
  });

  factory ParametrosSinConexion.fromJson(Map<String, dynamic> j) => ParametrosSinConexion(
        operacionOfflineHabilitada: j['operacion_offline_habilitada'] == true,
        diasAntiguedadOffline: _entero(j['dias_antiguedad_offline'], 7),
        horasVencimientoReserva: _entero(j['horas_vencimiento_reserva'], 24),
        moneda: _textoONulo(j['moneda']) ?? 'BOB',
      );

  Map<String, dynamic> toJson() => {
        'operacion_offline_habilitada': operacionOfflineHabilitada,
        'dias_antiguedad_offline': diasAntiguedadOffline,
        'horas_vencimiento_reserva': horasVencimientoReserva,
        'moneda': moneda,
      };
}

/// Respuesta de `POST /sin-conexion/dispositivos`.
@immutable
class DispositivoDto {
  final int idDispositivo;
  final String identificador;
  final String codigoCorto;
  final ParametrosSinConexion parametros;

  const DispositivoDto({
    required this.idDispositivo,
    required this.identificador,
    required this.codigoCorto,
    required this.parametros,
  });

  factory DispositivoDto.fromJson(Map<String, dynamic> j) => DispositivoDto(
        idDispositivo: _entero(j['id_dispositivo']),
        identificador: _texto(j['identificador']),
        codigoCorto: _texto(j['codigo_corto']),
        parametros: ParametrosSinConexion.fromJson(j),
      );
}

@immutable
class VarianteLocal {
  final int idVariante;
  final String sku;
  final int idTalla;
  final int idColor;
  final String precio;

  const VarianteLocal({
    required this.idVariante,
    required this.sku,
    required this.idTalla,
    required this.idColor,
    required this.precio,
  });

  factory VarianteLocal.fromJson(Map<String, dynamic> j) => VarianteLocal(
        idVariante: _entero(j['id_variante']),
        sku: _texto(j['sku']),
        idTalla: _entero(j['id_talla']),
        idColor: _entero(j['id_color']),
        precio: _texto(j['precio']),
      );
}

@immutable
class ProductoLocal {
  final int idProducto;
  final String nombre;
  final String? descripcion;
  final int idCategoria;
  final String precioBase;
  final String? imagenUrl;
  final List<VarianteLocal> variantes;

  const ProductoLocal({
    required this.idProducto,
    required this.nombre,
    required this.descripcion,
    required this.idCategoria,
    required this.precioBase,
    required this.imagenUrl,
    required this.variantes,
  });

  factory ProductoLocal.fromJson(Map<String, dynamic> j) => ProductoLocal(
        idProducto: _entero(j['id_producto']),
        nombre: _texto(j['nombre']),
        descripcion: _textoONulo(j['descripcion']),
        idCategoria: _entero(j['id_categoria']),
        precioBase: _texto(j['precio_base']),
        imagenUrl: _textoONulo(j['imagen_url']),
        variantes: [
          for (final v in (j['variantes'] as List? ?? const [])) VarianteLocal.fromJson(v as Map<String, dynamic>),
        ],
      );
}

@immutable
class SucursalLocal {
  final int idSucursal;
  final String nombre;
  final String direccion;
  final String? ciudad;

  const SucursalLocal({required this.idSucursal, required this.nombre, required this.direccion, this.ciudad});

  factory SucursalLocal.fromJson(Map<String, dynamic> j) => SucursalLocal(
        idSucursal: _entero(j['id_sucursal']),
        nombre: _texto(j['nombre']),
        direccion: _texto(j['direccion']),
        ciudad: _textoONulo(j['ciudad']),
      );
}

/// Paquete de `GET /sin-conexion/catalogo`. Se guarda tal cual (JSON) y se reconstruye al leerlo.
@immutable
class CatalogoLocal {
  final DateTime generadoEn;
  final String modo;
  final String moneda;
  final List<ProductoLocal> productos;
  final Map<int, String> categorias;
  final Map<int, String> tallas;
  final Map<int, String> colores;
  final List<SucursalLocal> sucursales;

  /// Disponible por `(idVariante, idSucursal)`.
  final Map<(int, int), int> existencias;

  const CatalogoLocal({
    required this.generadoEn,
    required this.modo,
    required this.moneda,
    required this.productos,
    required this.categorias,
    required this.tallas,
    required this.colores,
    required this.sucursales,
    required this.existencias,
  });

  factory CatalogoLocal.fromJson(Map<String, dynamic> j) => CatalogoLocal(
        generadoEn: DateTime.tryParse(_texto(j['generado_en'])) ?? DateTime.fromMillisecondsSinceEpoch(0),
        modo: _textoONulo(j['modo']) ?? 'completo',
        moneda: _textoONulo(j['moneda']) ?? 'BOB',
        productos: [
          for (final p in (j['productos'] as List? ?? const [])) ProductoLocal.fromJson(p as Map<String, dynamic>),
        ],
        categorias: {
          for (final c in (j['categorias'] as List? ?? const []))
            _entero((c as Map)['id_categoria']): _texto(c['nombre']),
        },
        tallas: {
          for (final t in (j['tallas'] as List? ?? const [])) _entero((t as Map)['id_talla']): _texto(t['codigo']),
        },
        colores: {
          for (final c in (j['colores'] as List? ?? const [])) _entero((c as Map)['id_color']): _texto(c['nombre']),
        },
        sucursales: [
          for (final s in (j['sucursales'] as List? ?? const [])) SucursalLocal.fromJson(s as Map<String, dynamic>),
        ],
        existencias: {
          for (final e in (j['existencias'] as List? ?? const []))
            (_entero((e as Map)['id_variante']), _entero(e['id_sucursal'])): _entero(e['cantidad_disponible']),
        },
      );

  int disponible(int idVariante, int idSucursal) => existencias[(idVariante, idSucursal)] ?? 0;
}

/// Un resultado de `POST /sin-conexion/sincronizar`. `reintentar` no se guarda en el servidor.
@immutable
class ResultadoOperacionDto {
  final String uuid;
  final String estado;
  final String? motivo;
  final String? mensaje;
  final String? codigoReserva;
  final int? idVenta;
  final int? idConflicto;
  final bool repetida;

  const ResultadoOperacionDto({
    required this.uuid,
    required this.estado,
    this.motivo,
    this.mensaje,
    this.codigoReserva,
    this.idVenta,
    this.idConflicto,
    this.repetida = false,
  });

  factory ResultadoOperacionDto.fromJson(Map<String, dynamic> j) => ResultadoOperacionDto(
        uuid: _texto(j['uuid']),
        estado: _texto(j['estado']),
        motivo: _textoONulo(j['motivo']),
        mensaje: _textoONulo(j['mensaje']),
        codigoReserva: _textoONulo(j['codigo_reserva']),
        idVenta: j['id_venta'] == null ? null : _entero(j['id_venta']),
        idConflicto: j['id_conflicto'] == null ? null : _entero(j['id_conflicto']),
        repetida: j['repetida'] == true,
      );
}

/// Un elemento de `GET /sin-conexion/operaciones`.
@immutable
class OperacionServidorDto {
  final String uuid;
  final String estado;
  final String? motivo;
  final String? codigoReserva;
  final String? estadoConflicto;

  const OperacionServidorDto({
    required this.uuid,
    required this.estado,
    this.motivo,
    this.codigoReserva,
    this.estadoConflicto,
  });

  factory OperacionServidorDto.fromJson(Map<String, dynamic> j) => OperacionServidorDto(
        uuid: _texto(j['uuid']),
        estado: _texto(j['estado']),
        motivo: _textoONulo(j['motivo']),
        codigoReserva: _textoONulo(j['codigo_reserva']),
        estadoConflicto: _textoONulo(j['estado_conflicto']),
      );
}

@immutable
class AvisoDto {
  final int idAviso;
  final String tipo;
  final String titulo;
  final String mensaje;
  final DateTime? creadoEn;
  final bool leido;

  const AvisoDto({
    required this.idAviso,
    required this.tipo,
    required this.titulo,
    required this.mensaje,
    required this.creadoEn,
    required this.leido,
  });

  factory AvisoDto.fromJson(Map<String, dynamic> j) => AvisoDto(
        idAviso: _entero(j['id_aviso']),
        tipo: _texto(j['tipo']),
        titulo: _texto(j['titulo']),
        mensaje: _texto(j['mensaje']),
        creadoEn: DateTime.tryParse(_texto(j['creado_en'])),
        leido: j['leido'] == true,
      );

  AvisoDto marcadoLeido() =>
      AvisoDto(idAviso: idAviso, tipo: tipo, titulo: titulo, mensaje: mensaje, creadoEn: creadoEn, leido: true);
}

@immutable
class BandejaAvisosDto {
  final int noLeidos;
  final List<AvisoDto> avisos;

  const BandejaAvisosDto({required this.noLeidos, required this.avisos});

  factory BandejaAvisosDto.fromJson(Map<String, dynamic> j) => BandejaAvisosDto(
        noLeidos: _entero(j['no_leidos']),
        avisos: [for (final a in (j['avisos'] as List? ?? const [])) AvisoDto.fromJson(a as Map<String, dynamic>)],
      );
}

// ------------------------------------------------------------------------------- SQLite

/// RN36: `registrada_localmente` y `enviada` solo existen en el dispositivo.
enum EstadoOperacion { registradaLocalmente, enviada, confirmada, rechazada, enConflicto }

EstadoOperacion estadoDesdeServidor(String estado) => switch (estado) {
      'confirmada' => EstadoOperacion.confirmada,
      'rechazada' => EstadoOperacion.rechazada,
      'en_conflicto' => EstadoOperacion.enConflicto,
      'enviada' => EstadoOperacion.enviada,
      _ => EstadoOperacion.registradaLocalmente,
    };

@immutable
class DispositivoLocal {
  /// `codigoTienda:idCliente`: el identificador es por cliente y tienda.
  final String clave;
  final String identificador;
  final String? codigoCorto;
  final int correlativo;
  final ParametrosSinConexion? parametros;

  const DispositivoLocal({
    required this.clave,
    required this.identificador,
    this.codigoCorto,
    this.correlativo = 0,
    this.parametros,
  });

  DispositivoLocal copyWith({String? codigoCorto, int? correlativo, ParametrosSinConexion? parametros}) =>
      DispositivoLocal(
        clave: clave,
        identificador: identificador,
        codigoCorto: codigoCorto ?? this.codigoCorto,
        correlativo: correlativo ?? this.correlativo,
        parametros: parametros ?? this.parametros,
      );

  factory DispositivoLocal.fromJson(Map<String, dynamic> j) => DispositivoLocal(
        clave: _texto(j['clave']),
        identificador: _texto(j['identificador']),
        codigoCorto: _textoONulo(j['codigo_corto']),
        correlativo: _entero(j['correlativo']),
        parametros: j['parametros'] == null
            ? null
            : ParametrosSinConexion.fromJson(j['parametros'] as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        'clave': clave,
        'identificador': identificador,
        'codigo_corto': codigoCorto,
        'correlativo': correlativo,
        'parametros': parametros?.toJson(),
      };
}

@immutable
class OperacionLocal {
  final String uuid;
  final String clave;

  /// `reserva` o `compra_interrumpida` (solo móvil).
  final String tipo;
  final int? idSucursal;
  final DateTime registradaEn;
  final String? codigoProvisional;
  final Map<String, dynamic> datos;
  final EstadoOperacion estado;
  final String? motivo;
  final String? mensaje;
  final String? codigoReserva;
  final String? estadoConflicto;

  /// Para mostrarla sin red: prenda, variante y sucursal (o la compra) tal como se eligieron.
  final String titulo;
  final String detalle;

  const OperacionLocal({
    required this.uuid,
    required this.clave,
    required this.tipo,
    required this.registradaEn,
    required this.datos,
    required this.estado,
    required this.titulo,
    required this.detalle,
    this.idSucursal,
    this.codigoProvisional,
    this.motivo,
    this.mensaje,
    this.codigoReserva,
    this.estadoConflicto,
  });

  bool get pendiente => estado == EstadoOperacion.registradaLocalmente || estado == EstadoOperacion.enviada;

  OperacionLocal copyWith({
    EstadoOperacion? estado,
    String? motivo,
    String? mensaje,
    String? codigoReserva,
    String? estadoConflicto,
  }) =>
      OperacionLocal(
        uuid: uuid,
        clave: clave,
        tipo: tipo,
        idSucursal: idSucursal,
        registradaEn: registradaEn,
        codigoProvisional: codigoProvisional,
        datos: datos,
        estado: estado ?? this.estado,
        motivo: motivo ?? this.motivo,
        mensaje: mensaje ?? this.mensaje,
        codigoReserva: codigoReserva ?? this.codigoReserva,
        estadoConflicto: estadoConflicto ?? this.estadoConflicto,
        titulo: titulo,
        detalle: detalle,
      );

  /// Cuerpo de la operación para `POST /sin-conexion/sincronizar`.
  Map<String, dynamic> paraEnviar() => {
        'uuid': uuid,
        'tipo': tipo,
        'id_sucursal': idSucursal,
        'registrada_en': registradaEn.toUtc().toIso8601String(),
        'codigo_provisional': codigoProvisional,
        'datos': datos,
      };

  factory OperacionLocal.fromJson(Map<String, dynamic> j) => OperacionLocal(
        uuid: _texto(j['uuid']),
        clave: _texto(j['clave']),
        tipo: _texto(j['tipo']),
        idSucursal: j['id_sucursal'] == null ? null : _entero(j['id_sucursal']),
        registradaEn: DateTime.parse(_texto(j['registrada_en'])),
        codigoProvisional: _textoONulo(j['codigo_provisional']),
        datos: Map<String, dynamic>.from(j['datos'] as Map? ?? const {}),
        estado: EstadoOperacion.values.byName(_texto(j['estado'])),
        motivo: _textoONulo(j['motivo']),
        mensaje: _textoONulo(j['mensaje']),
        codigoReserva: _textoONulo(j['codigo_reserva']),
        estadoConflicto: _textoONulo(j['estado_conflicto']),
        titulo: _texto(j['titulo']),
        detalle: _texto(j['detalle']),
      );

  Map<String, dynamic> toJson() => {
        'uuid': uuid,
        'clave': clave,
        'tipo': tipo,
        'id_sucursal': idSucursal,
        'registrada_en': registradaEn.toUtc().toIso8601String(),
        'codigo_provisional': codigoProvisional,
        'datos': datos,
        'estado': estado.name,
        'motivo': motivo,
        'mensaje': mensaje,
        'codigo_reserva': codigoReserva,
        'estado_conflicto': estadoConflicto,
        'titulo': titulo,
        'detalle': detalle,
      };
}
