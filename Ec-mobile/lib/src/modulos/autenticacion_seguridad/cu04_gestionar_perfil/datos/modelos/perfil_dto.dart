/// Modelos y DTOs para CU04 (Gestionar Perfil) y CU17 (Consultar Historial de Compras) en Flutter.
/// Mapeo tipado 1:1 con la respuesta JSON de FastAPI.
library;

class ResumenAtelierDto {
  final int visitasRegistradas;
  final int boutiquesVisitadas;
  final String preferenciaTextil;
  final String estatusMembresia;

  const ResumenAtelierDto({
    required this.visitasRegistradas,
    required this.boutiquesVisitadas,
    required this.preferenciaTextil,
    required this.estatusMembresia,
  });

  factory ResumenAtelierDto.fromJson(Map<String, dynamic> json) {
    return ResumenAtelierDto(
      visitasRegistradas: json['visitas_registradas'] as int? ?? 32,
      boutiquesVisitadas: json['boutiques_visitadas'] as int? ?? 4,
      preferenciaTextil: json['preferencia_textil'] as String? ?? '100% Seda & Lana',
      estatusMembresia: json['estatus_membresia'] as String? ?? 'Nivel Platino',
    );
  }

  Map<String, dynamic> toJson() => {
    'visitas_registradas': visitasRegistradas,
    'boutiques_visitadas': boutiquesVisitadas,
    'preferencia_textil': preferenciaTextil,
    'estatus_membresia': estatusMembresia,
  };
}

class PerfilClienteDto {
  final int idUsuario;
  final String numeroSocio;
  final String email;
  final String rol;
  final String fechaRegistro;
  final String miembroDesde;
  final String? ultimoAcceso;
  final String nombres;
  final String apellidos;
  final String? telefono;
  final String? fechaNacimiento;
  final String? genero;
  final String? tallaPreferida;
  final int? ciudadPreferida;
  final bool aceptaMarketing;
  final ResumenAtelierDto resumenAtelier;

  const PerfilClienteDto({
    required this.idUsuario,
    required this.numeroSocio,
    required this.email,
    required this.rol,
    required this.fechaRegistro,
    required this.miembroDesde,
    this.ultimoAcceso,
    required this.nombres,
    required this.apellidos,
    this.telefono,
    this.fechaNacimiento,
    this.genero,
    this.tallaPreferida,
    this.ciudadPreferida,
    required this.aceptaMarketing,
    required this.resumenAtelier,
  });

  factory PerfilClienteDto.fromJson(Map<String, dynamic> json) {
    return PerfilClienteDto(
      idUsuario: json['id_usuario'] as int? ?? 0,
      numeroSocio: json['numero_socio'] as String? ?? '#8402',
      email: json['email'] as String? ?? '',
      rol: json['rol'] as String? ?? 'cliente',
      fechaRegistro: json['fecha_registro'] as String? ?? '',
      miembroDesde: json['miembro_desde'] as String? ?? 'Octubre 2021',
      ultimoAcceso: json['ultimo_acceso'] as String?,
      nombres: json['nombres'] as String? ?? '',
      apellidos: json['apellidos'] as String? ?? '',
      telefono: json['telefono'] as String?,
      fechaNacimiento: json['fecha_nacimiento'] as String?,
      genero: json['genero'] as String?,
      tallaPreferida: json['talla_preferida'] as String?,
      ciudadPreferida: json['ciudad_preferida'] as int?,
      aceptaMarketing: json['acepta_marketing'] as bool? ?? true,
      resumenAtelier: json['resumen_atelier'] != null
          ? ResumenAtelierDto.fromJson(json['resumen_atelier'] as Map<String, dynamic>)
          : const ResumenAtelierDto(
              visitasRegistradas: 32,
              boutiquesVisitadas: 4,
              preferenciaTextil: '100% Seda & Lana',
              estatusMembresia: 'Nivel Platino',
            ),
    );
  }

  Map<String, dynamic> toJson() => {
    'id_usuario': idUsuario,
    'numero_socio': numeroSocio,
    'email': email,
    'rol': rol,
    'fecha_registro': fechaRegistro,
    'miembro_desde': miembroDesde,
    'ultimo_acceso': ultimoAcceso,
    'nombres': nombres,
    'apellidos': apellidos,
    'telefono': telefono,
    'fecha_nacimiento': fechaNacimiento,
    'genero': genero,
    'talla_preferida': tallaPreferida,
    'ciudad_preferida': ciudadPreferida,
    'acepta_marketing': aceptaMarketing,
    'resumen_atelier': resumenAtelier.toJson(),
  };
}

class PerfilClienteUpdateDto {
  final String? nombres;
  final String? apellidos;
  final String? telefono;
  final String? fechaNacimiento;
  final String? genero;
  final String? tallaPreferida;
  final int? ciudadPreferida;
  final bool? aceptaMarketing;

  const PerfilClienteUpdateDto({
    this.nombres,
    this.apellidos,
    this.telefono,
    this.fechaNacimiento,
    this.genero,
    this.tallaPreferida,
    this.ciudadPreferida,
    this.aceptaMarketing,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (nombres != null) map['nombres'] = nombres;
    if (apellidos != null) map['apellidos'] = apellidos;
    if (telefono != null) map['telefono'] = telefono;
    if (fechaNacimiento != null) map['fecha_nacimiento'] = fechaNacimiento;
    if (genero != null) map['genero'] = genero;
    if (tallaPreferida != null) map['talla_preferida'] = tallaPreferida;
    if (ciudadPreferida != null) map['ciudad_preferida'] = ciudadPreferida;
    if (aceptaMarketing != null) map['acepta_marketing'] = aceptaMarketing;
    return map;
  }
}

class ItemPedidoMovilDto {
  final int idVentaDetalle;
  final int idProducto;
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String? imagenUrl;
  final String talla;
  final String color;
  final String? colorHex;
  final int cantidad;
  final String precioUnitario;
  final String subtotalLinea;
  final String? nombreSucursal;

  const ItemPedidoMovilDto({
    required this.idVentaDetalle,
    required this.idProducto,
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    this.imagenUrl,
    required this.talla,
    required this.color,
    this.colorHex,
    required this.cantidad,
    required this.precioUnitario,
    required this.subtotalLinea,
    this.nombreSucursal,
  });

  factory ItemPedidoMovilDto.fromJson(Map<String, dynamic> json) {
    return ItemPedidoMovilDto(
      idVentaDetalle: json['id_venta_detalle'] as int? ?? 0,
      idProducto: json['id_producto'] as int? ?? 0,
      idVariante: json['id_variante'] as int? ?? 0,
      sku: json['sku'] as String? ?? '',
      nombreProducto: json['nombre_producto'] as String? ?? 'Prenda FashionStore',
      imagenUrl: json['imagen_url'] as String?,
      talla: json['talla'] as String? ?? '-',
      color: json['color'] as String? ?? '-',
      colorHex: json['color_hex'] as String?,
      cantidad: json['cantidad'] as int? ?? 1,
      precioUnitario: '${json['precio_unitario'] ?? '0.00'}',
      subtotalLinea: '${json['subtotal_linea'] ?? '0.00'}',
      nombreSucursal: json['nombre_sucursal'] as String?,
    );
  }
}

class PedidoMovilDto {
  final int idVenta;
  final String numeroComprobante;
  final String fechaVenta;
  final String tipoVenta;
  final String estado;
  final String tipoEntrega;
  final String? nombreSucursal;
  final String? nombreSucursalRetiro;
  final String? direccionEnvio;
  final String? codigoPromocion;
  final String subtotal;
  final String descuento;
  final String total;
  final String? metodoPago;
  final String? referenciaPasarela;
  final List<ItemPedidoMovilDto> items;

  const PedidoMovilDto({
    required this.idVenta,
    required this.numeroComprobante,
    required this.fechaVenta,
    required this.tipoVenta,
    required this.estado,
    required this.tipoEntrega,
    this.nombreSucursal,
    this.nombreSucursalRetiro,
    this.direccionEnvio,
    this.codigoPromocion,
    required this.subtotal,
    required this.descuento,
    required this.total,
    this.metodoPago,
    this.referenciaPasarela,
    this.items = const [],
  });

  factory PedidoMovilDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? const [];
    return PedidoMovilDto(
      idVenta: json['id_venta'] as int? ?? 0,
      numeroComprobante: json['numero_comprobante'] as String? ?? '',
      fechaVenta: json['fecha_venta'] as String? ?? '',
      tipoVenta: json['tipo_venta'] as String? ?? 'digital_movil',
      estado: json['estado'] as String? ?? 'pendiente',
      tipoEntrega: json['tipo_entrega'] as String? ?? 'domicilio',
      nombreSucursal: json['nombre_sucursal'] as String?,
      nombreSucursalRetiro: json['nombre_sucursal_retiro'] as String?,
      direccionEnvio: json['direccion_envio'] as String?,
      codigoPromocion: json['codigo_promocion'] as String?,
      subtotal: '${json['subtotal'] ?? '0.00'}',
      descuento: '${json['descuento'] ?? '0.00'}',
      total: '${json['total'] ?? '0.00'}',
      metodoPago: json['metodo_pago'] as String?,
      referenciaPasarela: json['referencia_pasarela'] as String?,
      items: rawItems
          .map((e) => ItemPedidoMovilDto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class HistorialComprasMovilDto {
  final int totalPedidos;
  final int pedidosCompletados;
  final List<PedidoMovilDto> pedidos;

  const HistorialComprasMovilDto({
    this.totalPedidos = 0,
    this.pedidosCompletados = 0,
    this.pedidos = const [],
  });

  factory HistorialComprasMovilDto.fromJson(Map<String, dynamic> json) {
    final rawPedidos = json['pedidos'] as List<dynamic>? ?? const [];
    return HistorialComprasMovilDto(
      totalPedidos: json['total_pedidos'] as int? ?? 0,
      pedidosCompletados: json['pedidos_completados'] as int? ?? 0,
      pedidos: rawPedidos
          .map((e) => PedidoMovilDto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
