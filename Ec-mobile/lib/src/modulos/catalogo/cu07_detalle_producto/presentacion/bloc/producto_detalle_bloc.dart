import 'package:flutter/foundation.dart';
import '../../datos/datasources/producto_detalle_api.dart';
import '../../datos/modelos/producto_detalle_dto.dart';

sealed class ProductoDetalleEstado {
  const ProductoDetalleEstado();
}

class ProductoDetalleInicial extends ProductoDetalleEstado {
  const ProductoDetalleInicial();
}

class ProductoDetalleCargando extends ProductoDetalleEstado {
  const ProductoDetalleCargando();
}

class ProductoDetalleError extends ProductoDetalleEstado {
  final String mensaje;
  const ProductoDetalleError(this.mensaje);
}

class ProductoDetalleCargado extends ProductoDetalleEstado {
  final ProductoDetalleDto producto;
  final ColorDetalleDto? colorSeleccionado;
  final TallaDetalleDto? tallaSeleccionada;
  final VarianteDetalleDto? varianteActiva;
  final int indiceGaleria;
  final List<SucursalDisponibilidadDto> sucursales;
  final bool cargandoDisponibilidad;
  final bool esFavorito;
  final int bolsaContador;
  final String? mensajeNotificacion;
  final bool reservaEnCurso;
  final ReservaCreadaOutDto? ultimaReserva;

  const ProductoDetalleCargado({
    required this.producto,
    this.colorSeleccionado,
    this.tallaSeleccionada,
    this.varianteActiva,
    this.indiceGaleria = 0,
    this.sucursales = const [],
    this.cargandoDisponibilidad = false,
    this.esFavorito = false,
    this.bolsaContador = 0,
    this.mensajeNotificacion,
    this.reservaEnCurso = false,
    this.ultimaReserva,
  });

  /// Galería de 4 ángulos de la misma prenda auténtica
  List<ImagenAnguloDto> get imagenesGaleria {
    if (producto.galeriaAngulos.length >= 4) {
      return producto.galeriaAngulos;
    }

    // Si faltan ángulos, derivar encuadres de alta costura de la misma prenda
    final baseImg = producto.imagenUrl ??
        (producto.galeriaAngulos.isNotEmpty ? producto.galeriaAngulos.first.url : '');

    if (baseImg.isEmpty) {
      return [
        const ImagenAnguloDto(url: '', etiqueta: 'FRONTAL', orden: 1),
        const ImagenAnguloDto(url: '', etiqueta: 'TEXTURA & SEDA', orden: 2),
        const ImagenAnguloDto(url: '', etiqueta: 'SILUETA & CAÍDA', orden: 3),
        const ImagenAnguloDto(url: '', etiqueta: 'ACABADO & COSTURA', orden: 4),
      ];
    }

    return [
      ImagenAnguloDto(
        url: baseImg,
        etiqueta: 'FRONTAL',
        orden: 1,
      ),
      ImagenAnguloDto(
        url: '$baseImg&crop=center&fit=crop&w=1200&h=1400',
        etiqueta: 'TEXTURA & SEDA',
        orden: 2,
      ),
      ImagenAnguloDto(
        url: '$baseImg&crop=top&fit=crop&w=1200&h=1400',
        etiqueta: 'SILUETA & CAÍDA',
        orden: 3,
      ),
      ImagenAnguloDto(
        url: '$baseImg&crop=bottom&fit=crop&w=1200&h=1400',
        etiqueta: 'ACABADO & COSTURA',
        orden: 4,
      ),
    ];
  }

  /// Verifica si una talla tiene stock para el color actualmente seleccionado
  bool tallaTieneStockParaColorActual(int idTalla) {
    if (colorSeleccionado == null) return true;
    final variante = producto.variantes.cast<VarianteDetalleDto?>().firstWhere(
          (v) => v?.idColor == colorSeleccionado!.idColor && v?.idTalla == idTalla,
          orElse: () => null,
        );
    return variante != null && variante.tieneStock;
  }

  /// Retorna las existencias físicas para una talla en el color actual
  int stockParaTallaEnColorActual(int idTalla) {
    if (colorSeleccionado == null) return 0;
    final variante = producto.variantes.cast<VarianteDetalleDto?>().firstWhere(
          (v) => v?.idColor == colorSeleccionado!.idColor && v?.idTalla == idTalla,
          orElse: () => null,
        );
    return variante?.stockTotalDisponible ?? 0;
  }

  double get precioActual =>
      varianteActiva?.precioFinalVariante ?? producto.precioFinal;

  String get skuActual =>
      varianteActiva?.sku ?? producto.skuBase;

  String get stockAdvertenciaTexto {
    if (varianteActiva == null) {
      return 'Selecciona un tono y talla para verificar existencias.';
    }
    final stock = varianteActiva!.stockTotalDisponible;
    final talla = varianteActiva!.tallaCodigo;
    if (stock <= 0) {
      return '● Talla $talla: Agotada en boutique. Solicita aviso de reposición.';
    } else if (stock <= 3) {
      return '● Talla $talla: Últimas $stock unidades en Flagship Serrano.';
    } else {
      return '● Talla $talla: Disponible para reserva y prueba privada en boutique.';
    }
  }

  ProductoDetalleCargado copyWith({
    ProductoDetalleDto? producto,
    ColorDetalleDto? colorSeleccionado,
    TallaDetalleDto? tallaSeleccionada,
    VarianteDetalleDto? varianteActiva,
    int? indiceGaleria,
    List<SucursalDisponibilidadDto>? sucursales,
    bool? cargandoDisponibilidad,
    bool? esFavorito,
    int? bolsaContador,
    String? mensajeNotificacion,
    bool clearNotificacion = false,
    bool? reservaEnCurso,
    ReservaCreadaOutDto? ultimaReserva,
  }) {
    return ProductoDetalleCargado(
      producto: producto ?? this.producto,
      colorSeleccionado: colorSeleccionado ?? this.colorSeleccionado,
      tallaSeleccionada: tallaSeleccionada ?? this.tallaSeleccionada,
      varianteActiva: varianteActiva ?? this.varianteActiva,
      indiceGaleria: indiceGaleria ?? this.indiceGaleria,
      sucursales: sucursales ?? this.sucursales,
      cargandoDisponibilidad: cargandoDisponibilidad ?? this.cargandoDisponibilidad,
      esFavorito: esFavorito ?? this.esFavorito,
      bolsaContador: bolsaContador ?? this.bolsaContador,
      mensajeNotificacion: clearNotificacion
          ? null
          : (mensajeNotificacion ?? this.mensajeNotificacion),
      reservaEnCurso: reservaEnCurso ?? this.reservaEnCurso,
      ultimaReserva: ultimaReserva ?? this.ultimaReserva,
    );
  }
}

class ProductoDetalleBloc extends ChangeNotifier {
  final ProductoDetalleApi _api;
  ProductoDetalleEstado _estado = const ProductoDetalleInicial();

  ProductoDetalleBloc({ProductoDetalleApi? api})
      : _api = api ?? ProductoDetalleApiImpl();

  ProductoDetalleEstado get estado => _estado;

  /// Carga la ficha de alta costura y la disponibilidad inicial multisede
  Future<void> cargarDetalle(int idProducto) async {
    _estado = const ProductoDetalleCargando();
    notifyListeners();

    try {
      final detalle = await _api.obtenerDetalleProducto(idProducto);

      // 1. Color inicial: primer color disponible
      ColorDetalleDto? colorInit;
      if (detalle.coloresDisponibles.isNotEmpty) {
        colorInit = detalle.coloresDisponibles.firstWhere(
          (c) => c.disponible,
          orElse: () => detalle.coloresDisponibles.first,
        );
      }

      // 2. Talla inicial: primera talla con stock para ese color
      TallaDetalleDto? tallaInit;
      VarianteDetalleDto? varInit;

      if (colorInit != null && detalle.variantes.isNotEmpty) {
        final variantesColor = detalle.variantes
            .where((v) => v.idColor == colorInit!.idColor)
            .toList();

        // Buscar variante con stock
        final conStock = variantesColor.firstWhere(
          (v) => v.tieneStock,
          orElse: () => variantesColor.isNotEmpty
              ? variantesColor.first
              : detalle.variantes.first,
        );
        varInit = conStock;

        tallaInit = detalle.tallasDisponibles.cast<TallaDetalleDto?>().firstWhere(
              (t) => t?.idTalla == conStock.idTalla,
              orElse: () => detalle.tallasDisponibles.isNotEmpty
                  ? detalle.tallasDisponibles.first
                  : null,
            );
      } else if (detalle.tallasDisponibles.isNotEmpty) {
        tallaInit = detalle.tallasDisponibles.first;
      }

      // 3. Consultar disponibilidad por sucursal para la variante inicial
      List<SucursalDisponibilidadDto> sucursales = [];
      try {
        final disp = await _api.consultarDisponibilidad(
          idProducto,
          idVariante: varInit?.idVariante,
        );
        sucursales = disp.sucursales;
      } catch (_) {
        // Fallback a sucursales activas si no hay variante
        try {
          sucursales = await _api.obtenerSucursalesActivas();
        } catch (_) {}
      }

      _estado = ProductoDetalleCargado(
        producto: detalle,
        colorSeleccionado: colorInit,
        tallaSeleccionada: tallaInit,
        varianteActiva: varInit,
        sucursales: sucursales,
      );
      notifyListeners();
    } catch (e) {
      _estado = ProductoDetalleError(e.toString());
      notifyListeners();
    }
  }

  /// Selector cromático en cascada: adapta las tallas disponibles y revalida existencias
  void seleccionarColor(ColorDetalleDto color) {
    if (_estado is! ProductoDetalleCargado) return;
    final actual = _estado as ProductoDetalleCargado;

    // Buscar si la talla actualmente seleccionada tiene stock en el nuevo color
    final variantesNuevoColor = actual.producto.variantes
        .where((v) => v.idColor == color.idColor)
        .toList();

    VarianteDetalleDto? nuevaVar;
    TallaDetalleDto? nuevaTalla = actual.tallaSeleccionada;

    if (actual.tallaSeleccionada != null) {
      nuevaVar = variantesNuevoColor.cast<VarianteDetalleDto?>().firstWhere(
            (v) => v?.idTalla == actual.tallaSeleccionada!.idTalla && v!.tieneStock,
            orElse: () => null,
          );
    }

    // Si la talla actual no está disponible en este color, elegir la primera con stock
    if (nuevaVar == null && variantesNuevoColor.isNotEmpty) {
      nuevaVar = variantesNuevoColor.firstWhere(
        (v) => v.tieneStock,
        orElse: () => variantesNuevoColor.first,
      );
      nuevaTalla = actual.producto.tallasDisponibles
          .cast<TallaDetalleDto?>()
          .firstWhere(
            (t) => t?.idTalla == nuevaVar!.idTalla,
            orElse: () => actual.tallaSeleccionada,
          );
    }

    _estado = actual.copyWith(
      colorSeleccionado: color,
      tallaSeleccionada: nuevaTalla,
      varianteActiva: nuevaVar,
      clearNotificacion: true,
    );
    notifyListeners();

    // Actualizar disponibilidad para la nueva variante
    _actualizarDisponibilidad(actual.producto.idProducto, nuevaVar?.idVariante);
  }

  /// Selector de talla: actualiza la variante activa y recalcula existencias por sede
  void seleccionarTalla(TallaDetalleDto talla) {
    if (_estado is! ProductoDetalleCargado) return;
    final actual = _estado as ProductoDetalleCargado;

    VarianteDetalleDto? nuevaVar;
    if (actual.colorSeleccionado != null) {
      nuevaVar = actual.producto.variantes.cast<VarianteDetalleDto?>().firstWhere(
            (v) =>
                v?.idColor == actual.colorSeleccionado!.idColor &&
                v?.idTalla == talla.idTalla,
            orElse: () => null,
          );
    }

    _estado = actual.copyWith(
      tallaSeleccionada: talla,
      varianteActiva: nuevaVar,
      clearNotificacion: true,
    );
    notifyListeners();

    _actualizarDisponibilidad(actual.producto.idProducto, nuevaVar?.idVariante);
  }

  Future<void> _actualizarDisponibilidad(int idProducto, int? idVariante) async {
    if (_estado is! ProductoDetalleCargado) return;
    final actual = _estado as ProductoDetalleCargado;

    _estado = actual.copyWith(cargandoDisponibilidad: true);
    notifyListeners();

    try {
      final resp = await _api.consultarDisponibilidad(
        idProducto,
        idVariante: idVariante,
      );
      if (_estado is ProductoDetalleCargado) {
        _estado = (_estado as ProductoDetalleCargado).copyWith(
          sucursales: resp.sucursales,
          cargandoDisponibilidad: false,
        );
        notifyListeners();
      }
    } catch (_) {
      if (_estado is ProductoDetalleCargado) {
        _estado = (_estado as ProductoDetalleCargado).copyWith(
          cargandoDisponibilidad: false,
        );
        notifyListeners();
      }
    }
  }

  /// Cambio de fotografía en la galería multiángulo
  void cambiarIndiceGaleria(int nuevoIndice) {
    if (_estado is! ProductoDetalleCargado) return;
    final actual = _estado as ProductoDetalleCargado;
    if (nuevoIndice >= 0 && nuevoIndice < actual.imagenesGaleria.length) {
      _estado = actual.copyWith(indiceGaleria: nuevoIndice);
      notifyListeners();
    }
  }

  /// Wishlist toggle
  void toggleFavorito() {
    if (_estado is! ProductoDetalleCargado) return;
    final actual = _estado as ProductoDetalleCargado;
    final nuevoFav = !actual.esFavorito;
    _estado = actual.copyWith(
      esFavorito: nuevoFav,
      mensajeNotificacion: nuevoFav
          ? 'Prenda guardada en tus Deseos Atelier'
          : 'Retirada de tus Deseos Atelier',
    );
    notifyListeners();
  }

  /// Añadir a la bolsa de alta costura
  void agregarABolsa() {
    if (_estado is! ProductoDetalleCargado) return;
    final actual = _estado as ProductoDetalleCargado;
    final nuevaBolsa = actual.bolsaContador + 1;
    _estado = actual.copyWith(
      bolsaContador: nuevaBolsa,
      mensajeNotificacion: 'Prenda añadida a la bolsa de compras',
    );
    notifyListeners();
  }

  /// Confirmación de cita presencial en boutique (CU12)
  Future<bool> confirmarReserva({
    required int idSucursal,
    required DateTime fechaReserva,
    String? notasCliente,
    String? token,
  }) async {
    if (_estado is! ProductoDetalleCargado) return false;
    final actual = _estado as ProductoDetalleCargado;

    if (actual.varianteActiva == null) {
      _estado = actual.copyWith(
        mensajeNotificacion: 'Debes seleccionar una talla para coordinar la cita.',
      );
      notifyListeners();
      return false;
    }

    _estado = actual.copyWith(reservaEnCurso: true, clearNotificacion: true);
    notifyListeners();

    try {
      final payload = ReservaCrearInDto(
        idSucursal: idSucursal,
        fechaHoraAtencion: fechaReserva,
        canalOrigen: 'movil',
        observacion: notasCliente ?? 'Cita privada de prueba en boutique',
        lineas: [
          ReservaLineaInDto(
            idVariante: actual.varianteActiva!.idVariante,
            cantidad: 1,
          ),
        ],
      );

      final resultado = await _api.crearReserva(payload, token: token);

      _estado = actual.copyWith(
        reservaEnCurso: false,
        ultimaReserva: resultado,
        mensajeNotificacion:
            'Cita de prueba confirmada: ${resultado.codigoReserva}',
      );
      notifyListeners();
      return true;
    } catch (e) {
      _estado = actual.copyWith(
        reservaEnCurso: false,
        mensajeNotificacion: 'Fallo al solicitar reserva: $e',
      );
      notifyListeners();
      return false;
    }
  }

  void limpiarNotificacion() {
    if (_estado is ProductoDetalleCargado) {
      _estado = (_estado as ProductoDetalleCargado).copyWith(clearNotificacion: true);
      notifyListeners();
    }
  }
}
