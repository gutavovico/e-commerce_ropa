import 'dart:math';

import 'package:flutter/foundation.dart';

import '../../datos/datasources/pago_api.dart';
import '../../datos/datasources/stripe_gateway.dart';
import '../../datos/modelos/pago_dto.dart';

/// Estados sellados del ciclo de pago de CU16.
sealed class PagoEstado {
  const PagoEstado();
}

class PagoInicial extends PagoEstado {
  const PagoInicial();
}

class PagoCargandoResumen extends PagoEstado {
  const PagoCargandoResumen();
}

/// Resumen cargado, listo para que el cliente elija método y confirme.
class PagoListo extends PagoEstado {
  final ResumenPagoDto resumen;
  final String metodoSeleccionado;
  final EscenarioPrueba escenarioPrueba;
  final String? mensajeError;

  const PagoListo({
    required this.resumen,
    this.metodoSeleccionado = 'tarjeta_credito',
    this.escenarioPrueba = EscenarioPrueba.aprobado,
    this.mensajeError,
  });

  PagoListo copyWith({
    ResumenPagoDto? resumen,
    String? metodoSeleccionado,
    EscenarioPrueba? escenarioPrueba,
    String? mensajeError,
    bool limpiarError = false,
  }) {
    return PagoListo(
      resumen: resumen ?? this.resumen,
      metodoSeleccionado: metodoSeleccionado ?? this.metodoSeleccionado,
      escenarioPrueba: escenarioPrueba ?? this.escenarioPrueba,
      mensajeError: limpiarError ? null : (mensajeError ?? this.mensajeError),
    );
  }
}

/// Cobro en vuelo: el botón de confirmar queda inhabilitado mientras dure.
class PagoProcesando extends PagoEstado {
  final ResumenPagoDto resumen;
  final String metodoSeleccionado;

  const PagoProcesando({required this.resumen, required this.metodoSeleccionado});
}

class PagoExitoso extends PagoEstado {
  final PagoConfirmadoDto confirmacion;

  const PagoExitoso(this.confirmacion);
}

/// Rechazo de la pasarela (402): la orden sigue viva y permite reintentar con otro medio.
class PagoRechazado extends PagoEstado {
  final ResumenPagoDto resumen;
  final String metodoSeleccionado;
  final String motivo;

  const PagoRechazado({
    required this.resumen,
    required this.metodoSeleccionado,
    required this.motivo,
  });
}

/// La orden no pudo cargarse, o expiró, o ya fue liquidada: no hay resumen que mostrar.
class PagoError extends PagoEstado {
  final String mensaje;

  const PagoError(this.mensaje);
}

/// Orquesta el ciclo de pago de CU16: consulta el resumen, permite elegir método y cierra el
/// cobro contra Stripe en dos pasos (revisado el 2026-09-28: el backend nunca recibe la tarjeta).
///
/// Para tarjeta/débito, cuando hay un SDK de Stripe real inicializado (`stripeGateway` no nulo o
/// distinto del simulador), la secuencia es: `iniciarPago` (abre el `PaymentIntent`) →
/// `_stripeGateway.confirmarPago` (el `CardField` de la pantalla confirma directamente contra
/// Stripe) → `confirmarPago` (el servidor verifica el desenlace por su cuenta). Bizum/QR y PayPal
/// son simulaciones decorativas del proyecto (nunca pasaron por Stripe) y se aprueban siempre.
class PagoBloc extends ChangeNotifier {
  final PagoApi _api;
  final StripeGateway _stripeGateway;
  final String _token;

  PagoEstado _estado = const PagoInicial();
  PagoEstado get estado => _estado;

  /// Se genera una sola vez por intento de pago: reenviar la misma clave tras un fallo de red
  /// hace que el backend devuelva el cobro ya confirmado en vez de cobrar dos veces.
  String? _claveIdempotencia;

  PagoBloc({PagoApi? api, StripeGateway? stripeGateway, required String token})
      : _api = api ?? PagoApiImpl(),
        _stripeGateway = stripeGateway ?? const StripeGatewayReal(),
        _token = token;

  /// Sin un SDK de Stripe real inicializado, la pantalla muestra el panel de «modo simulador».
  bool get stripeDisponible => _stripeGateway.disponible;

  Future<void> cargarResumen(int idVenta) async {
    _estado = const PagoCargandoResumen();
    notifyListeners();

    try {
      final resumen = await _api.obtenerResumenPago(idVenta, token: _token);
      _estado = PagoListo(resumen: resumen);
    } on PagoException catch (e) {
      _estado = PagoError(e.mensaje);
    }
    notifyListeners();
  }

  void seleccionarMetodo(String metodo) {
    final actual = _estado;
    if (actual is PagoListo) {
      _estado = actual.copyWith(metodoSeleccionado: metodo, limpiarError: true);
      notifyListeners();
    } else if (actual is PagoRechazado) {
      _estado = PagoListo(resumen: actual.resumen, metodoSeleccionado: metodo);
      notifyListeners();
    }
  }

  void seleccionarEscenarioPrueba(EscenarioPrueba escenario) {
    final actual = _estado;
    if (actual is PagoListo) {
      _estado = actual.copyWith(escenarioPrueba: escenario);
      notifyListeners();
    }
  }

  Future<bool> confirmarYPagar() async {
    final actual = _estado;
    final ResumenPagoDto resumen;
    final String metodo;
    final EscenarioPrueba escenarioPrueba;

    if (actual is PagoListo) {
      resumen = actual.resumen;
      metodo = actual.metodoSeleccionado;
      escenarioPrueba = actual.escenarioPrueba;
    } else if (actual is PagoRechazado) {
      resumen = actual.resumen;
      metodo = actual.metodoSeleccionado;
      escenarioPrueba = EscenarioPrueba.aprobado;
    } else {
      return false;
    }

    final esTarjeta = metodo == 'tarjeta_credito' || metodo == 'tarjeta_debito';
    // Bizum/QR y PayPal son simulaciones decorativas del proyecto: nunca pasan por Stripe, con
    // o sin SDK real inicializado, así que siempre se abren con el desenlace "aprobado".
    final usaStripeReal = esTarjeta && stripeDisponible;

    _claveIdempotencia ??= _generarClaveIdempotencia();

    _estado = PagoProcesando(resumen: resumen, metodoSeleccionado: metodo);
    notifyListeners();

    try {
      final intento = await _api.iniciarPago(
        PagoIniciarInDto(
          idVenta: resumen.idVenta,
          metodoPago: metodo,
          claveIdempotencia: _claveIdempotencia,
          escenarioPrueba: usaStripeReal ? null : (esTarjeta ? escenarioPrueba : EscenarioPrueba.aprobado),
        ),
        token: _token,
      );

      if (intento.yaConfirmado && intento.confirmacion != null) {
        _estado = PagoExitoso(intento.confirmacion!);
        notifyListeners();
        return true;
      }

      if (usaStripeReal) {
        final clientSecret = intento.clientSecret;
        if (clientSecret == null) {
          _estado = PagoError('La pasarela no devolvió un cobro que confirmar.');
          notifyListeners();
          return false;
        }

        final resultado = await _stripeGateway.confirmarPago(clientSecret);
        if (!resultado.aprobado) {
          _claveIdempotencia = null;
          _estado = PagoRechazado(
            resumen: resumen,
            metodoSeleccionado: metodo,
            motivo: resultado.mensajeError ?? 'La entidad emisora ha rechazado la tarjeta.',
          );
          notifyListeners();
          return false;
        }
      }

      // El servidor decide el desenlace final por su cuenta, nunca por lo que este cliente
      // reporte: recupera el `PaymentIntent` de Stripe y lo compara.
      final confirmacion = await _api.confirmarPago(intento.idPago, token: _token);
      _estado = PagoExitoso(confirmacion);
      notifyListeners();
      return true;
    } on PagoException catch (e) {
      if (e.esPagoRechazado) {
        // La orden sigue viva: se permite reintentar con el mismo u otro método.
        _claveIdempotencia = null;
        _estado = PagoRechazado(resumen: resumen, metodoSeleccionado: metodo, motivo: e.mensaje);
      } else {
        // Orden expirada, ya liquidada o cualquier otro fallo: no hay nada que reintentar aquí.
        _estado = PagoError(e.mensaje);
      }
      notifyListeners();
      return false;
    }
  }

  String _generarClaveIdempotencia() {
    final aleatorio = Random();
    final marcaTiempo = DateTime.now().microsecondsSinceEpoch;
    final sufijo = aleatorio.nextInt(1 << 32).toRadixString(16);
    return 'movil-$marcaTiempo-$sufijo';
  }
}
