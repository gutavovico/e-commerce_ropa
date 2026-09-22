import 'dart:async';

import 'package:flutter/material.dart';

import '../../datos/modelos/carrito_dto.dart';
import '../bloc/carrito_bloc.dart';

/// Pantalla de Bolsa de Compra y Checkout (CU11 + CU15).
///
/// Es una vista secundaria del patrón Hub-and-Spoke: se abre con `Navigator.push`, su `Scaffold`
/// **no declara la barra de navegación de 4 pestañas** y su `AppBar` incluye retorno explícito.
/// La barra inferior fija es una barra de acción, no de navegación: contiene el total y el botón
/// de tramitar, que deben permanecer visibles durante el desplazamiento.
class ShoppingBagScreen extends StatefulWidget {
  final String token;
  final CarritoBloc? bloc;
  final bool habilitarImagenesRed;

  const ShoppingBagScreen({
    super.key,
    required this.token,
    this.bloc,
    this.habilitarImagenesRed = true,
  });

  @override
  State<ShoppingBagScreen> createState() => _ShoppingBagScreenState();
}

class _ShoppingBagScreenState extends State<ShoppingBagScreen> {
  late final CarritoBloc _bloc;
  final TextEditingController _controladorDireccion = TextEditingController();
  final TextEditingController _controladorCupon = TextEditingController();

  Timer? _temporizador;
  int? _segundosRestantes;
  String? _ultimaNotificacion;

  static const Color _negro = Color(0xFF0F1116);
  static const Color _grisTexto = Color(0xFF52525B);
  static const Color _grisSuave = Color(0xFF8A8A8A);
  static const Color _lineaClara = Color(0xFFECEAE6);
  static const Color _fondoSuave = Color(0xFFF7F6F4);
  static const Color _camel = Color(0xFF7A5B15);

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? CarritoBloc(token: widget.token);
    _bloc.addListener(_alCambiarEstado);
    _bloc.cargarCarrito();
  }

  @override
  void dispose() {
    // Sin esta limpieza el temporizador sobrevive a la navegación y sigue llamando a setState
    // sobre un widget ya desmontado.
    _temporizador?.cancel();
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) _bloc.dispose();
    _controladorDireccion.dispose();
    _controladorCupon.dispose();
    super.dispose();
  }

  void _alCambiarEstado() {
    final estado = _bloc.estado;

    if (estado is CarritoCargado) {
      _sincronizarTemporizador(estado.carrito.expiraEn);

      final mensaje = estado.mensajeNotificacion;
      if (mensaje != null && mensaje != _ultimaNotificacion) {
        _ultimaNotificacion = mensaje;
        _mostrarAviso(mensaje);
      }
      if (mensaje == null) _ultimaNotificacion = null;
    } else {
      _detenerTemporizador();
    }

    if (mounted) setState(() {});
  }

  void _mostrarAviso(String mensaje) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            mensaje,
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: Colors.white,
            ),
          ),
          backgroundColor: _negro,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          duration: const Duration(seconds: 4),
        ),
      );
  }

  // -------------------------------------------------------------------
  // Temporizador de la ventana de cortesía
  // -------------------------------------------------------------------

  void _sincronizarTemporizador(DateTime? expiraEn) {
    if (expiraEn == null) {
      _detenerTemporizador();
      return;
    }
    if (_temporizador != null) return;

    void calcular() {
      final restante = expiraEn.difference(DateTime.now()).inSeconds;
      final valor = restante > 0 ? restante : 0;
      if (mounted) setState(() => _segundosRestantes = valor);
      if (valor == 0) _detenerTemporizador();
    }

    calcular();
    _temporizador = Timer.periodic(const Duration(seconds: 1), (_) => calcular());
  }

  void _detenerTemporizador() {
    _temporizador?.cancel();
    _temporizador = null;
  }

  String? get _tiempoRestante {
    final segundos = _segundosRestantes;
    if (segundos == null || segundos <= 0) return null;
    final minutos = segundos ~/ 60;
    final resto = segundos % 60;
    return '$minutos:${resto.toString().padLeft(2, '0')}';
  }

  // -------------------------------------------------------------------
  // Construcción
  // -------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final estado = _bloc.estado;
    final cargado = estado is CarritoCargado ? estado : null;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: _negro,
        elevation: 0,
        // Pantalla hoja: retorno explícito, nunca barra de pestañas.
        leading: const BackButton(),
        title: const Text(
          'Shopping Bag',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 16,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.3,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Container(
                width: 26,
                height: 26,
                decoration: const BoxDecoration(color: _negro, shape: BoxShape.circle),
                alignment: Alignment.center,
                child: Text(
                  '${cargado?.resumen.totalPrendas ?? 0}',
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(child: _construirCuerpo(estado)),
      // Barra de ACCIÓN, no de navegación: el patrón Hub-and-Spoke prohíbe la de pestañas,
      // no un pie fijo con la acción principal de la pantalla.
      bottomNavigationBar: cargado != null && cargado.ordenConfirmada == null
          ? _construirPieFijo(cargado)
          : null,
    );
  }

  Widget _construirCuerpo(CarritoEstado estado) {
    return switch (estado) {
      CarritoInicial() || CarritoCargando() => _construirEsqueleto(),
      CarritoError(mensaje: final mensaje) => _construirError(mensaje),
      CarritoVacio() => _construirBolsaVacia(),
      CarritoCargado(ordenConfirmada: final orden) when orden != null =>
        _construirConfirmacion(orden),
      CarritoCargado() => _construirContenido(estado),
    };
  }

  // -------------------------------------------------------------------
  // Estados
  // -------------------------------------------------------------------

  Widget _construirEsqueleto() {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 3,
      separatorBuilder: (_, _) => const SizedBox(height: 16),
      itemBuilder: (_, _) => Container(
        height: 130,
        decoration: BoxDecoration(
          color: _fondoSuave,
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  Widget _construirError(String mensaje) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 44, color: Color(0xFF991B1B)),
            const SizedBox(height: 16),
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 13,
                color: _grisTexto,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _negro,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
              ),
              onPressed: () => _bloc.cargarCarrito(),
              child: const Text(
                'REINTENTAR',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirBolsaVacia() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: _lineaClara),
              ),
              child: const Icon(Icons.shopping_bag_outlined, size: 28, color: _grisSuave),
            ),
            const SizedBox(height: 20),
            const Text(
              'Tu bolsa está vacía',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 18,
                fontWeight: FontWeight.w400,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Aún no has seleccionado ninguna pieza. Explora el catálogo de alta costura y '
              'añade las prendas que desees probar.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 13,
                color: _grisTexto,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _negro,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
              ),
              onPressed: () => Navigator.of(context).pop(),
              child: const Text(
                'EXPLORAR EL CATÁLOGO',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirConfirmacion(VentaCreadaDto orden) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 24),
          const Icon(Icons.check_circle, size: 56, color: Color(0xFF16A34A)),
          const SizedBox(height: 20),
          Text(
            orden.mensajeConfirmacion,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 17,
              fontWeight: FontWeight.w400,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFFFFFBEB),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                'COMPROBANTE: ${orden.numeroComprobante}',
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: _camel,
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _fondoSuave,
              border: Border.all(color: _lineaClara),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              children: [
                _filaResumen('Prendas', '${orden.totalPrendas}'),
                const SizedBox(height: 8),
                _filaResumen('Total', '${orden.total.toStringAsFixed(2)} €', destacado: true),
                const SizedBox(height: 8),
                _filaResumen(
                  'Entrega',
                  orden.tipoEntrega == 'domicilio' ? 'A domicilio' : 'Recogida en boutique',
                ),
                if (orden.nombreSucursalRetiro != null) ...[
                  const SizedBox(height: 8),
                  _filaResumen('Boutique', orden.nombreSucursalRetiro!),
                ],
              ],
            ),
          ),
          const SizedBox(height: 32),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: _negro,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
            ),
            onPressed: () => Navigator.of(context).pop(),
            child: const Text(
              'CONTINUAR EXPLORANDO',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.8,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Contenido principal
  // -------------------------------------------------------------------

  Widget _construirContenido(CarritoCargado estado) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        if (_tiempoRestante != null) _construirBannerVentana(),
        const SizedBox(height: 16),
        _construirEncabezado(estado),
        const SizedBox(height: 16),
        ...estado.items.map((item) => _construirTarjetaPrenda(item, estado)),
        const SizedBox(height: 24),
        _construirDestinoEnvio(estado),
        const SizedBox(height: 24),
        _construirCupon(estado),
        const SizedBox(height: 24),
        _construirResumen(estado),
        const SizedBox(height: 24),
        _construirGarantias(),
      ],
    );
  }

  Widget _construirBannerVentana() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _fondoSuave,
        border: Border.all(color: _lineaClara),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          const Icon(Icons.hourglass_bottom, size: 16, color: _camel),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Stock verificado en tiempo real. La reserva firme se activa al tramitar.',
              style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _grisTexto),
            ),
          ),
          Text(
            '${_tiempoRestante!} MIN',
            style: const TextStyle(
              fontFamily: 'Outfit',
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: _negro,
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirEncabezado(CarritoCargado estado) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            // `Expanded` + elipsis: el título y el contador comparten una única línea y no
            // pueden desbordarla en pantallas estrechas ni con cifras de varios dígitos.
            const Expanded(
              child: Text(
                'Bolsa de Compra',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 24,
                  fontWeight: FontWeight.w300,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                '(${estado.resumen.totalPrendas} '
                '${estado.resumen.totalPrendas == 1 ? 'prenda' : 'prendas'})',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 13,
                  color: _grisSuave,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        const Text(
          'Revisa tus prendas, variantes y sucursal de preparación antes de tramitar tu orden.',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 12,
            color: _grisTexto,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _construirTarjetaPrenda(CarritoItemDto item, CarritoCargado estado) {
    final enCurso = estado.lineaEnCurso == item.idCarritoDetalle;

    return Opacity(
      opacity: enCurso ? 0.5 : 1.0,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: _lineaClara),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Fotografía
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: SizedBox(
                    width: 72,
                    height: 96,
                    child: (widget.habilitarImagenesRed && item.imagenUrl != null)
                        ? Image.network(
                            item.imagenUrl!,
                            fit: BoxFit.cover,
                            errorBuilder: (_, _, _) => Container(color: _fondoSuave),
                          )
                        : Container(color: _fondoSuave),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Text(
                              '${item.lineaConfeccion ?? 'ALTA COSTURA'} · SKU: ${item.sku}',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 9,
                                letterSpacing: 0.9,
                                color: _grisSuave,
                              ),
                            ),
                          ),
                          IconButton(
                            onPressed:
                                estado.procesando ? null : () => _bloc.eliminar(item),
                            icon: const Icon(Icons.delete_outline, size: 18),
                            color: const Color(0xFF991B1B),
                            visualDensity: VisualDensity.compact,
                            padding: EdgeInsets.zero,
                            constraints: const BoxConstraints(),
                            tooltip: 'Eliminar ${item.nombreProducto}',
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item.nombreProducto,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontFamily: 'Outfit',
                          fontSize: 14,
                          fontWeight: FontWeight.w400,
                          height: 1.25,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Talla: ${item.tallaCodigo} · Color: ${item.colorNombre}',
                        style: const TextStyle(
                          fontFamily: 'Outfit',
                          fontSize: 11,
                          color: _grisTexto,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Text(
                            '${item.precioUnitario.toStringAsFixed(2)} €',
                            style: const TextStyle(
                              fontFamily: 'Outfit',
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          if (item.tieneDescuento) ...[
                            const SizedBox(width: 8),
                            Text(
                              '${item.precioLista.toStringAsFixed(2)} €',
                              style: const TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 12,
                                color: _grisSuave,
                                decoration: TextDecoration.lineThrough,
                              ),
                            ),
                          ],
                        ],
                      ),
                      if (item.tieneDescuento && item.motivoDescuento != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(
                            'Ahorro ${item.descuentoLinea.toStringAsFixed(2)} € por '
                            '${item.motivoDescuento}',
                            style: const TextStyle(
                              fontFamily: 'Outfit',
                              fontSize: 10,
                              color: _camel,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // Sucursal de expedición
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              decoration: BoxDecoration(
                color: _fondoSuave,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                children: [
                  const Icon(Icons.storefront_outlined, size: 13, color: _grisTexto),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Expedición: ${item.nombreSucursal}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 10,
                        color: _grisTexto,
                      ),
                    ),
                  ),
                  Text(
                    '${item.stockDisponible} uds',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10,
                      color: _grisSuave,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            // Controles de cantidad
            Row(
              children: [
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xFFD5D2CD)),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _botonCantidad(
                        icono: Icons.remove,
                        etiqueta: 'Reducir cantidad',
                        activo: item.cantidad > 1 && !estado.procesando,
                        alPulsar: () => _bloc.decrementar(item),
                      ),
                      SizedBox(
                        width: 36,
                        child: Text(
                          '${item.cantidad}',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontFamily: 'Outfit',
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      _botonCantidad(
                        icono: Icons.add,
                        etiqueta: 'Aumentar cantidad',
                        activo: !item.alcanzoElMaximo && !estado.procesando,
                        alPulsar: () => _bloc.incrementar(item),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                if (item.alcanzoElMaximo)
                  const Expanded(
                    child: Text(
                      'Máximo disponible en esta boutique',
                      style: TextStyle(fontFamily: 'Outfit', fontSize: 10, color: _camel),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _botonCantidad({
    required IconData icono,
    required String etiqueta,
    required bool activo,
    required VoidCallback alPulsar,
  }) {
    return Semantics(
      label: etiqueta,
      button: true,
      child: InkWell(
        onTap: activo ? alPulsar : null,
        child: SizedBox(
          width: 36,
          height: 36,
          child: Icon(
            icono,
            size: 16,
            color: activo ? _negro : const Color(0xFFCCCCCC),
          ),
        ),
      ),
    );
  }

  Widget _construirDestinoEnvio(CarritoCargado estado) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Destino del Envío',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),
        _opcionEntrega(
          titulo: 'Entrega a Domicilio',
          subtitulo: 'Entrega estimada: 24-48h con guante blanco',
          seleccionada: estado.tipoEntrega == TipoEntrega.domicilio,
          alSeleccionar: () => _bloc.seleccionarEntrega(TipoEntrega.domicilio),
        ),
        if (estado.tipoEntrega == TipoEntrega.domicilio)
          Padding(
            padding: const EdgeInsets.only(left: 12, top: 8, bottom: 8),
            child: TextField(
              controller: _controladorDireccion,
              maxLines: 2,
              onChanged: _bloc.actualizarDireccion,
              style: const TextStyle(fontFamily: 'Outfit', fontSize: 13),
              decoration: InputDecoration(
                hintText: 'Calle, número, piso, código postal y ciudad',
                hintStyle: const TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 12,
                  color: _grisSuave,
                ),
                contentPadding: const EdgeInsets.all(12),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(4),
                  borderSide: const BorderSide(color: _negro),
                ),
              ),
            ),
          ),
        const SizedBox(height: 8),
        _opcionEntrega(
          titulo: 'Recogida en Boutique Insignia',
          subtitulo: 'Preparación prioritaria lista en 2 horas',
          seleccionada: estado.tipoEntrega == TipoEntrega.recogidaBoutique,
          alSeleccionar: () => _bloc.seleccionarEntrega(TipoEntrega.recogidaBoutique),
        ),
        if (estado.tipoEntrega == TipoEntrega.recogidaBoutique)
          Padding(
            padding: const EdgeInsets.only(left: 12, top: 8),
            child: estado.boutiques.isEmpty
                ? const Text(
                    'No hay boutiques disponibles para recogida en este momento.',
                    style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _camel),
                  )
                : Column(
                    children: estado.boutiques.map((boutique) {
                      final elegida = estado.idSucursalRetiro == boutique.idSucursal;
                      return InkWell(
                        onTap: () => _bloc.seleccionarBoutique(boutique.idSucursal),
                        child: Container(
                          width: double.infinity,
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            border: Border.all(color: elegida ? _negro : _lineaClara),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                boutique.nombre,
                                style: const TextStyle(
                                  fontFamily: 'Outfit',
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                boutique.direccion,
                                style: const TextStyle(
                                  fontFamily: 'Outfit',
                                  fontSize: 11,
                                  color: _grisSuave,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
          ),
      ],
    );
  }

  Widget _opcionEntrega({
    required String titulo,
    required String subtitulo,
    required bool seleccionada,
    required VoidCallback alSeleccionar,
  }) {
    return InkWell(
      onTap: alSeleccionar,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: seleccionada ? _negro : _lineaClara),
          borderRadius: BorderRadius.circular(8),
          color: seleccionada ? const Color(0xFFFAFAF9) : Colors.white,
        ),
        child: Row(
          children: [
            Icon(
              seleccionada ? Icons.radio_button_checked : Icons.radio_button_off,
              size: 18,
              color: seleccionada ? _negro : _grisSuave,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    titulo,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitulo,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11,
                      color: _grisSuave,
                    ),
                  ),
                ],
              ),
            ),
            const Text(
              'GRATUITO',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 9,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
                color: Color(0xFF16A34A),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirCupon(CarritoCargado estado) {
    final cupon = estado.cuponAplicado;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'CÓDIGO DE INVITACIÓN O BONO ATELIER',
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: 10,
            fontWeight: FontWeight.w600,
            letterSpacing: 1.0,
            color: _grisTexto,
          ),
        ),
        const SizedBox(height: 8),
        if (cupon != null)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFFF5EFE4),
              border: Border.all(color: const Color(0xFFE4D9C4)),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    cupon,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: _camel,
                    ),
                  ),
                ),
                InkWell(
                  onTap: _bloc.retirarCupon,
                  child: const Text(
                    'RETIRAR',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                      color: Color(0xFF991B1B),
                    ),
                  ),
                ),
              ],
            ),
          )
        else
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controladorCupon,
                  style: const TextStyle(fontFamily: 'Outfit', fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'Ej. MAISON-2025',
                    hintStyle: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 12,
                      color: _grisSuave,
                    ),
                    contentPadding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _negro,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                ),
                onPressed: () => _bloc.aplicarCupon(_controladorCupon.text),
                child: const Text(
                  'APLICAR',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
            ],
          ),
      ],
    );
  }

  Widget _construirResumen(CarritoCargado estado) {
    final resumen = estado.resumen;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _fondoSuave,
        border: Border.all(color: _lineaClara),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          const Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Resumen de la Orden',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 15,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          const SizedBox(height: 12),
          _filaResumen(
            'Subtotal artículos (${resumen.totalPrendas} '
            '${resumen.totalPrendas == 1 ? 'prenda' : 'prendas'})',
            '${resumen.subtotal.toStringAsFixed(2)} €',
          ),
          if (resumen.tieneDescuento) ...[
            const SizedBox(height: 8),
            _filaResumen(
              'Beneficios y promociones',
              '−${resumen.descuento.toStringAsFixed(2)} €',
              color: _camel,
            ),
          ],
          const SizedBox(height: 8),
          _filaResumen('Envío asegurado', 'GRATUITO'),
          const SizedBox(height: 8),
          _filaResumen(
            'Impuestos estimados (IVA incluido)',
            '${resumen.ivaIncluido.toStringAsFixed(2)} €',
            color: _grisSuave,
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(height: 1, color: _lineaClara),
          ),
          _filaResumen(
            'Total Estimado',
            '${resumen.total.toStringAsFixed(2)} €',
            destacado: true,
          ),
        ],
      ),
    );
  }

  Widget _filaResumen(
    String etiqueta,
    String valor, {
    bool destacado = false,
    Color? color,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Text(
            etiqueta,
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: destacado ? 14 : 12,
              fontWeight: destacado ? FontWeight.w600 : FontWeight.w400,
              color: color ?? _grisTexto,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          valor,
          style: TextStyle(
            fontFamily: 'Outfit',
            fontSize: destacado ? 18 : 12,
            fontWeight: destacado ? FontWeight.w600 : FontWeight.w500,
            color: color ?? (destacado ? _negro : _grisTexto),
          ),
        ),
      ],
    );
  }

  Widget _construirGarantias() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: const [
        Text(
          'Confección y embalaje en funda de algodón transpirable y percha artesanal.',
          style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _grisSuave, height: 1.5),
        ),
        SizedBox(height: 6),
        Text(
          'Devolución gratuita durante 30 días con recogida privada concertada a tu domicilio.',
          style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _grisSuave, height: 1.5),
        ),
      ],
    );
  }

  /// Barra de acción fija: total siempre a la vista y acción principal accesible.
  Widget _construirPieFijo(CarritoCargado estado) {
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: _lineaClara)),
        ),
        child: Row(
          children: [
            // `Flexible` evita el desbordamiento horizontal cuando el importe crece: sin él,
            // un total de cinco cifras empuja el botón fuera de la pantalla.
            Flexible(
              child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'TOTAL PEDIDO',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 9,
                    letterSpacing: 0.9,
                    color: _grisSuave,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${estado.resumen.total.toStringAsFixed(2)} €',
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Text(
                  'IVA incl.',
                  style: TextStyle(fontFamily: 'Outfit', fontSize: 9, color: _grisSuave),
                ),
              ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _negro,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: const Color(0xFFCCCCCC),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                ),
                onPressed: estado.puedeTramitar ? () => _bloc.tramitarPedido() : null,
                child: estado.procesando
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.lock_outline, size: 14),
                          SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              'TRAMITAR PEDIDO',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ),
                        ],
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
