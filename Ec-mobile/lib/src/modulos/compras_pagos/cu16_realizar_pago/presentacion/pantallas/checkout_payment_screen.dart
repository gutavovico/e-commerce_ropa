import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart' show CardField, CardFieldInputDetails;

import '../../datos/modelos/pago_dto.dart';
import '../bloc/pago_bloc.dart';

/// Pantalla de Pago Seguro (CU16), abierta desde la Bolsa de Compra tras tramitar el pedido.
///
/// Es una vista secundaria del patrón Hub-and-Spoke: se abre con `Navigator.push`, su `Scaffold`
/// **no declara la barra de navegación de 4 pestañas** y su `AppBar` incluye retorno explícito.
/// La barra inferior fija es una barra de ACCIÓN (monto + `CONFIRMAR Y PAGAR`), no de navegación.
class CheckoutPaymentScreen extends StatefulWidget {
  final int idVenta;
  final String token;
  final PagoBloc? bloc;
  final bool habilitarImagenesRed;

  const CheckoutPaymentScreen({
    super.key,
    required this.idVenta,
    required this.token,
    this.bloc,
    this.habilitarImagenesRed = true,
  });

  @override
  State<CheckoutPaymentScreen> createState() => _CheckoutPaymentScreenState();
}

class _CheckoutPaymentScreenState extends State<CheckoutPaymentScreen> {
  late final PagoBloc _bloc;

  /// `null` mientras no se ha tecleado nada; `.complete` indica que Stripe considera la tarjeta
  /// lista para confirmar. Este componente nunca lee el PAN ni el CVV: `CardField` los captura
  /// directamente en el SDK nativo de Stripe.
  CardFieldInputDetails? _detalleTarjeta;

  Timer? _temporizadorOrden;
  int? _segundosRestantesOrden;

  Timer? _temporizadorQr;
  int _segundosCodigoQr = _segundosCodigoQrInicial;

  static const int _segundosCodigoQrInicial = 5 * 60;

  static const Color _negro = Color(0xFF0F1116);
  static const Color _grisTexto = Color(0xFF52525B);
  static const Color _grisSuave = Color(0xFF8A8A8A);
  static const Color _lineaClara = Color(0xFFECEAE6);
  static const Color _fondoSuave = Color(0xFFF7F6F4);
  static const Color _camel = Color(0xFF7A5B15);
  static const Color _fondoCamel = Color(0xFFF4ECE3);

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? PagoBloc(token: widget.token);
    _bloc.addListener(_alCambiarEstado);
    _bloc.cargarResumen(widget.idVenta);
  }

  @override
  void dispose() {
    _temporizadorOrden?.cancel();
    _temporizadorQr?.cancel();
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) _bloc.dispose();
    super.dispose();
  }

  void _alCambiarEstado() {
    final estado = _bloc.estado;
    if (estado is PagoListo) {
      _sincronizarTemporizadorOrden(estado.resumen.expiraEn);
    } else if (estado is PagoRechazado) {
      _sincronizarTemporizadorOrden(estado.resumen.expiraEn);
    } else {
      _detenerTemporizadorOrden();
    }
    if (mounted) setState(() {});
  }

  // -------------------------------------------------------------------
  // Temporizador de la ventana de la orden (25 min de CU15)
  // -------------------------------------------------------------------

  void _sincronizarTemporizadorOrden(DateTime? expiraEn) {
    if (expiraEn == null) {
      _detenerTemporizadorOrden();
      return;
    }
    if (_temporizadorOrden != null) return;

    void calcular() {
      final restante = expiraEn.difference(DateTime.now()).inSeconds;
      final valor = restante > 0 ? restante : 0;
      if (mounted) setState(() => _segundosRestantesOrden = valor);
      if (valor == 0) _detenerTemporizadorOrden();
    }

    calcular();
    _temporizadorOrden = Timer.periodic(const Duration(seconds: 1), (_) => calcular());
  }

  void _detenerTemporizadorOrden() {
    _temporizadorOrden?.cancel();
    _temporizadorOrden = null;
  }

  String get _tiempoRestanteOrden {
    final segundos = _segundosRestantesOrden;
    if (segundos == null || segundos <= 0) return '00:00';
    final minutos = segundos ~/ 60;
    final resto = segundos % 60;
    return '${minutos.toString().padLeft(2, '0')}:${resto.toString().padLeft(2, '0')}';
  }

  // -------------------------------------------------------------------
  // Cuenta atrás informativa del código Bizum/QR (independiente de la orden)
  // -------------------------------------------------------------------

  void _iniciarCuentaAtrasQr() {
    _temporizadorQr?.cancel();
    setState(() => _segundosCodigoQr = _segundosCodigoQrInicial);
    _temporizadorQr = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_segundosCodigoQr <= 1) {
        setState(() => _segundosCodigoQr = 0);
        _temporizadorQr?.cancel();
      } else {
        setState(() => _segundosCodigoQr -= 1);
      }
    });
  }

  void _detenerCuentaAtrasQr() {
    _temporizadorQr?.cancel();
    _temporizadorQr = null;
  }

  String get _tiempoCodigoQr {
    final minutos = _segundosCodigoQr ~/ 60;
    final resto = _segundosCodigoQr % 60;
    return '${minutos.toString().padLeft(2, '0')}:${resto.toString().padLeft(2, '0')}';
  }

  void _seleccionarMetodo(String metodo) {
    _bloc.seleccionarMetodo(metodo);
    if (metodo == 'qr') {
      _iniciarCuentaAtrasQr();
    } else {
      _detenerCuentaAtrasQr();
    }
  }

  // -------------------------------------------------------------------
  // Confirmar y pagar
  // -------------------------------------------------------------------

  Future<void> _confirmarYPagar() async {
    final estado = _bloc.estado;
    final metodo = switch (estado) {
      PagoListo(metodoSeleccionado: final m) => m,
      PagoRechazado(metodoSeleccionado: final m) => m,
      _ => null,
    };
    if (metodo == null) return;

    final esTarjeta = metodo == 'tarjeta_credito' || metodo == 'tarjeta_debito';
    if (esTarjeta && _bloc.stripeDisponible && (_detalleTarjeta?.complete ?? false) == false) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Revisa los datos de la tarjeta.')),
      );
      return;
    }

    await _bloc.confirmarYPagar();
  }

  // -------------------------------------------------------------------
  // Construcción
  // -------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final estado = _bloc.estado;
    final puedeMostrarAccion = estado is PagoListo || estado is PagoRechazado;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: _negro,
        elevation: 0,
        leading: const BackButton(),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'PAGO SEGURO',
              style: TextStyle(
                fontFamily: 'Outfit',
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            Text(
              'Checkout Payment',
              style: TextStyle(fontFamily: 'Outfit', fontSize: 13, color: _grisTexto),
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _fondoSuave,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: _lineaClara),
                ),
                child: const Text(
                  '256-BIT SSL',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.6,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(child: _construirCuerpo(estado)),
      bottomNavigationBar: puedeMostrarAccion ? _construirBarraDeAccion(estado) : null,
    );
  }

  Widget _construirCuerpo(PagoEstado estado) {
    return switch (estado) {
      PagoInicial() || PagoCargandoResumen() => _construirEsqueleto(),
      PagoError(mensaje: final mensaje) => _construirError(mensaje),
      PagoExitoso(confirmacion: final pago) => _construirConfirmacion(pago),
      PagoListo(resumen: final resumen) => _construirContenido(resumen, estado, null),
      PagoProcesando(resumen: final resumen) => _construirContenido(resumen, null, null),
      PagoRechazado(resumen: final resumen, motivo: final motivo) =>
        _construirContenido(resumen, null, motivo),
    };
  }

  Widget _construirEsqueleto() {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 3,
      separatorBuilder: (_, _) => const SizedBox(height: 16),
      itemBuilder: (_, _) => Container(
        height: 110,
        decoration: BoxDecoration(color: _fondoSuave, borderRadius: BorderRadius.circular(8)),
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
            const Text(
              'No pudimos abrir tu orden de pago',
              style: TextStyle(fontFamily: 'Outfit', fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: const TextStyle(fontFamily: 'Outfit', fontSize: 13, color: _grisTexto, height: 1.4),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _negro,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
              ),
              onPressed: () => Navigator.of(context).pop(),
              child: const Text(
                'VOLVER A LA BOLSA',
                style: TextStyle(fontFamily: 'Outfit', fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.8),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirConfirmacion(PagoConfirmadoDto pago) {
    final etiquetaMetodo = pago.marcaTarjeta != null
        ? '${pago.marcaTarjeta} terminada en ${pago.ultimosDigitos}'
        : switch (pago.metodoPago) {
            'qr' => 'Bizum / Código QR',
            'pasarela_digital' => 'PayPal',
            _ => pago.metodoPago,
          };

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 24),
          const Icon(Icons.check_circle, size: 56, color: Color(0xFF16A34A)),
          const SizedBox(height: 20),
          Text(
            pago.mensajeConfirmacion,
            textAlign: TextAlign.center,
            style: const TextStyle(fontFamily: 'Outfit', fontSize: 17, height: 1.4),
          ),
          const SizedBox(height: 12),
          Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: const Color(0xFFFFFBEB), borderRadius: BorderRadius.circular(4)),
              child: Text(
                'COMPROBANTE: ${pago.numeroComprobante}',
                style: const TextStyle(fontFamily: 'Outfit', fontSize: 12, fontWeight: FontWeight.w600, color: _camel),
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
                _filaResumen('Medio de pago', etiquetaMetodo),
                const SizedBox(height: 8),
                _filaResumen('Total liquidado', '${pago.monto.toStringAsFixed(2)} €', destacado: true),
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
              style: TextStyle(fontFamily: 'Outfit', fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.8),
            ),
          ),
        ],
      ),
    );
  }

  Widget _filaResumen(String etiqueta, String valor, {bool destacado = false}) {
    return Row(
      children: [
        Text(etiqueta, style: const TextStyle(fontFamily: 'Outfit', fontSize: 12, color: _grisTexto)),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            valor,
            textAlign: TextAlign.right,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontFamily: 'Outfit',
              fontSize: destacado ? 15 : 12,
              fontWeight: destacado ? FontWeight.bold : FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  // -------------------------------------------------------------------
  // Contenido principal
  // -------------------------------------------------------------------

  Widget _construirContenido(ResumenPagoDto resumen, PagoEstado? estadoConMetodo, String? motivoRechazo) {
    final metodo = switch (_bloc.estado) {
      PagoListo(metodoSeleccionado: final m) => m,
      PagoRechazado(metodoSeleccionado: final m) => m,
      PagoProcesando(metodoSeleccionado: final m) => m,
      _ => 'tarjeta_credito',
    };

    final sucursales = resumen.items
        .map((i) => i.nombreSucursal)
        .whereType<String>()
        .toSet()
        .toList();

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        // Banner de reserva activa con las boutiques reales de expedición.
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(color: _fondoCamel, borderRadius: BorderRadius.circular(6)),
          child: Row(
            children: [
              const Icon(Icons.timer_outlined, size: 16, color: _camel),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  sucursales.isNotEmpty
                      ? 'Reserva activa: $_tiempoRestanteOrden restantes · ${sucursales.join(' & ')}'
                      : 'Reserva activa: $_tiempoRestanteOrden restantes',
                  style: const TextStyle(fontFamily: 'Outfit', fontSize: 11, fontWeight: FontWeight.w600, color: _camel),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Monto total a liquidar.
        Row(
          children: [
            const Icon(Icons.shopping_bag_outlined, size: 22, color: _negro),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${resumen.total.toStringAsFixed(2)} €',
                    style: const TextStyle(fontFamily: 'Outfit', fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    '${resumen.totalPrendas} prendas exclusivas · IVA y aranceles incluidos',
                    style: const TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _grisSuave),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),

        // Destino de la orden: domicilio o recogida en boutique.
        Row(
          children: [
            const Icon(Icons.local_shipping_outlined, size: 16, color: _grisTexto),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                resumen.esRecogidaBoutique
                    ? 'Recogida: ${resumen.nombreCliente ?? ''} · ${resumen.nombreSucursalRetiro ?? ''}'
                    : 'Entrega: ${resumen.nombreCliente ?? ''} · ${resumen.direccionEnvio ?? ''}',
                style: const TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _grisTexto),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Carrusel de prendas.
        if (resumen.items.isNotEmpty)
          SizedBox(
            height: 56,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: resumen.items.length,
              separatorBuilder: (_, _) => const SizedBox(width: 8),
              itemBuilder: (_, i) {
                final item = resumen.items[i];
                return Tooltip(
                  message: item.nombreProducto,
                  child: CircleAvatar(
                    radius: 28,
                    backgroundColor: _fondoSuave,
                    backgroundImage: (widget.habilitarImagenesRed && item.imagenUrl != null)
                        ? NetworkImage(item.imagenUrl!)
                        : null,
                    child: (!widget.habilitarImagenesRed || item.imagenUrl == null)
                        ? const Icon(Icons.checkroom, size: 20, color: _grisSuave)
                        : null,
                  ),
                );
              },
            ),
          ),
        const SizedBox(height: 24),

        // Encabezado de sección.
        //
        // `RenderFlex overflowed` ya reapareció varias veces en este proyecto (CHANGELOG,
        // entradas 9, 20, 26 y 31): se soluciona con Expanded + ellipsis, no reduciendo fuentes.
        Row(
          children: [
            const Expanded(
              child: Text(
                'Selecciona Forma de Pago',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontFamily: 'Outfit', fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(color: _fondoSuave, borderRadius: BorderRadius.circular(4)),
              child: const Text(
                'CIFRADO SEGURO',
                style: TextStyle(fontFamily: 'Outfit', fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.6),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        if (motivoRechazo != null) _construirBannerRechazo(motivoRechazo),

        _construirOpcionMetodo(
          codigo: 'tarjeta_credito',
          titulo: 'Tarjeta de Crédito / Débito',
          subtitulo: 'VISA · MASTERCARD · AMEX',
          metodoActivo: metodo,
          contenidoExpandido: _construirFormularioTarjeta(),
        ),
        const SizedBox(height: 12),
        _construirOpcionMetodo(
          codigo: 'qr',
          titulo: 'Bizum / Código QR',
          subtitulo: 'Pago exprés e instantáneo',
          metodoActivo: metodo,
          contenidoExpandido: _construirBloqueQr(resumen),
        ),
        const SizedBox(height: 12),
        _construirOpcionMetodo(
          codigo: 'pasarela_digital',
          titulo: 'PayPal',
          subtitulo: 'Saldo PayPal o 3 plazos sin costes',
          metodoActivo: metodo,
          contenidoExpandido: null,
        ),
        const SizedBox(height: 20),

        _construirInsignias(),
      ],
    );
  }

  Widget _construirBannerRechazo(String motivo) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        border: Border(left: BorderSide(color: _negro, width: 4)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Operación no autorizada por la pasarela',
            style: TextStyle(fontFamily: 'Outfit', fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF7F1D1D)),
          ),
          const SizedBox(height: 4),
          Text(motivo, style: const TextStyle(fontFamily: 'Outfit', fontSize: 12, color: _grisTexto)),
          const SizedBox(height: 4),
          const Text(
            'Tus prendas continúan reservadas. Puedes corregir los datos o probar con otro medio.',
            style: TextStyle(fontFamily: 'Outfit', fontSize: 10, color: _grisSuave),
          ),
        ],
      ),
    );
  }

  Widget _construirOpcionMetodo({
    required String codigo,
    required String titulo,
    required String subtitulo,
    required String metodoActivo,
    required Widget? contenidoExpandido,
  }) {
    final activo = metodoActivo == codigo;
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: activo ? _negro : _lineaClara),
        borderRadius: BorderRadius.circular(6),
        color: activo ? Colors.white : Colors.transparent,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            onTap: () => _seleccionarMetodo(codigo),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    width: 18,
                    height: 18,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: activo ? _negro : const Color(0xFFD4D4D8)),
                    ),
                    child: activo
                        ? Center(
                            child: Container(
                              width: 9,
                              height: 9,
                              decoration: const BoxDecoration(shape: BoxShape.circle, color: _negro),
                            ),
                          )
                        : null,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(titulo, style: const TextStyle(fontFamily: 'Outfit', fontSize: 14, fontWeight: FontWeight.w600)),
                        Text(subtitulo, style: const TextStyle(fontFamily: 'Outfit', fontSize: 11, color: _grisSuave)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (activo && contenidoExpandido != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              child: contenidoExpandido,
            ),
        ],
      ),
    );
  }

  Widget _construirFormularioTarjeta() {
    // Tarjeta visual "Atelier Privé Black Card": decorativa desde el 2026-09-28. Ya no refleja
    // en vivo lo tecleado, porque Stripe posee el campo real dentro del SDK nativo y esta
    // pantalla nunca ve el número ni el CVV.
    final blackCard = Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0F1116), Color(0xFF232323)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'ATELIER PRIVÉ BLACK CARD',
            style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: Colors.white70, letterSpacing: 1),
          ),
          SizedBox(height: 20),
          Text(
            '•••• •••• •••• ••••',
            style: TextStyle(fontFamily: 'monospace', fontSize: 16, color: Colors.white, letterSpacing: 2),
          ),
          SizedBox(height: 16),
          Text(
            'Cifrado end-to-end por Stripe',
            style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: Colors.white70),
          ),
        ],
      ),
    );

    if (!_bloc.stripeDisponible) {
      final estado = _bloc.estado;
      final escenarioActual =
          estado is PagoListo ? estado.escenarioPrueba : EscenarioPrueba.aprobado;

      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          blackCard,
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFFFFBEB),
              border: Border.all(color: const Color(0xFFFDE68A)),
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Text(
              'Modo simulador. No hay una STRIPE_PUBLISHABLE_KEY real configurada '
              '(--dart-define), así que no se inicializa el SDK de Stripe. El backend usa el '
              'mismo simulador cuando tampoco tiene STRIPE_SECRET_KEY real. Elige el desenlace '
              'que quieres probar:',
              style: TextStyle(fontFamily: 'Outfit', fontSize: 11, color: Color(0xFF92400E), height: 1.4),
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                label: const Text('✅ Pago Aprobado'),
                selected: escenarioActual == EscenarioPrueba.aprobado,
                onSelected: (_) => _bloc.seleccionarEscenarioPrueba(EscenarioPrueba.aprobado),
              ),
              ChoiceChip(
                label: const Text('❌ Rechazo Genérico'),
                selected: escenarioActual == EscenarioPrueba.rechazado,
                onSelected: (_) => _bloc.seleccionarEscenarioPrueba(EscenarioPrueba.rechazado),
              ),
              ChoiceChip(
                label: const Text('⚠️ Fondos Insuficientes'),
                selected: escenarioActual == EscenarioPrueba.fondosInsuficientes,
                onSelected: (_) =>
                    _bloc.seleccionarEscenarioPrueba(EscenarioPrueba.fondosInsuficientes),
              ),
            ],
          ),
        ],
      );
    }

    // ------------------------------------------------------------------
    // CardField de Stripe: aquí es el SDK nativo el que recolecta la tarjeta. Este widget solo
    // recibe `CardFieldInputDetails.complete` para habilitar el botón, nunca el PAN ni el CVV.
    // ------------------------------------------------------------------
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        blackCard,
        const SizedBox(height: 14),
        CardField(
          onCardChanged: (detalle) => setState(() => _detalleTarjeta = detalle),
          decoration: const InputDecoration(
            labelText: 'Datos de la Tarjeta',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Este formulario lo aloja Stripe directamente: ni el número ni el CVV llegan a '
          'nuestros servidores.',
          style: TextStyle(fontFamily: 'Outfit', fontSize: 10, color: Color(0xFF8A8A8A)),
        ),
      ],
    );
  }

  Widget _construirBloqueQr(ResumenPagoDto resumen) {
    final digitos = resumen.numeroComprobante.replaceAll(RegExp(r'\D'), '');
    final codigoCorto = '#ATEL-${digitos.isNotEmpty ? digitos.substring(digitos.length >= 4 ? digitos.length - 4 : 0) : resumen.numeroComprobante}';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          height: 140,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: _lineaClara),
            borderRadius: BorderRadius.circular(6),
          ),
          // Mismo generador de QR que usa Web para el mismo escenario sandbox: un código real,
          // no un icono decorativo. Se apaga en pruebas con `habilitarImagenesRed: false`.
          child: widget.habilitarImagenesRed
              ? Image.network(
                  'https://api.qrserver.com/v1/create-qr-code/?size=140x140&data='
                  'https://fashionstore.atelier/pago/${widget.idVenta}',
                  width: 120,
                  height: 120,
                  errorBuilder: (_, _, _) => const Icon(Icons.qr_code_2, size: 96, color: _negro),
                )
              : const Icon(Icons.qr_code_2, size: 96, color: _negro),
        ),
        const SizedBox(height: 10),
        Text(
          'Expira en: $_tiempoCodigoQr',
          textAlign: TextAlign.center,
          style: const TextStyle(fontFamily: 'Outfit', fontSize: 12, fontWeight: FontWeight.bold, color: _camel),
        ),
        const SizedBox(height: 10),
        _pasoQr('1', 'Abre tu app bancaria de preferencia o el módulo Bizum.'),
        _pasoQr('2', 'Escanea el código o ingresa el código $codigoCorto.'),
        _pasoQr('3', 'Autoriza el importe exacto de ${resumen.total.toStringAsFixed(2)} €.'),
      ],
    );
  }

  Widget _pasoQr(String numero, String texto) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(numero, style: const TextStyle(fontFamily: 'Outfit', fontSize: 12, fontWeight: FontWeight.bold)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(texto, style: const TextStyle(fontFamily: 'Outfit', fontSize: 12, color: _grisTexto)),
          ),
        ],
      ),
    );
  }

  Widget _construirInsignias() {
    Widget insignia(String titulo, String subtitulo) {
      return Expanded(
        child: Container(
          padding: const EdgeInsets.all(10),
          margin: const EdgeInsets.symmetric(horizontal: 3),
          decoration: BoxDecoration(border: Border.all(color: _lineaClara), borderRadius: BorderRadius.circular(6)),
          child: Column(
            children: [
              Text(titulo, textAlign: TextAlign.center, style: const TextStyle(fontFamily: 'Outfit', fontSize: 9, fontWeight: FontWeight.bold)),
              const SizedBox(height: 2),
              Text(subtitulo, textAlign: TextAlign.center, style: const TextStyle(fontFamily: 'Outfit', fontSize: 8, color: _grisSuave)),
            ],
          ),
        ),
      );
    }

    return Row(
      children: [
        insignia('SSL 256-BIT', 'Conexión cifrada'),
        insignia('PCI-DSS NIVEL 1', 'Máx. certificación'),
        insignia('GARANTÍA ATELIER', 'Devolución 30 días'),
      ],
    );
  }

  Widget _construirBarraDeAccion(PagoEstado estado) {
    final resumen = switch (estado) {
      PagoListo(resumen: final r) => r,
      PagoRechazado(resumen: final r) => r,
      _ => null,
    };
    if (resumen == null) return const SizedBox.shrink();

    final procesando = _bloc.estado is PagoProcesando;

    return SafeArea(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: _lineaClara)),
        ),
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: _negro,
            foregroundColor: Colors.white,
            disabledBackgroundColor: const Color(0xFFCCCCCC),
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
          ),
          onPressed: procesando ? null : _confirmarYPagar,
          child: procesando
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(Colors.white)),
                )
              : Text(
                  'CONFIRMAR Y PAGAR ${resumen.total.toStringAsFixed(2)} €',
                  style: const TextStyle(fontFamily: 'Outfit', fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 0.6),
                ),
        ),
      ),
    );
  }
}
