import 'empresa_actual.dart';

/// Fix de P2-CU11 · Moneda de la tienda (decisiones M1, M6 y M8).
///
/// El backend envía los importes y nunca se recalculan aquí: solo se les da formato boliviano,
/// `Bs 1.234,50` o `US$ 1.234,50`, con la moneda de la tienda elegida (`EmpresaActual`).
const String monedaPorDefecto = 'BOB';

/// IVA de Bolivia, incluido en el precio (M9). Solo para los textos del desglose.
const String tasaIvaTexto = '13 %';

const Map<String, String> _simbolos = {'BOB': 'Bs', 'USD': r'US$'};

String simboloMoneda([String? moneda]) {
  final codigo = (moneda == null || moneda.isEmpty) ? monedaActual() : moneda;
  return _simbolos[codigo] ?? codigo;
}

/// Moneda de la tienda en la que navega la sesión; BOB sin tienda.
String monedaActual() => EmpresaActual.instancia.empresa?.moneda ?? monedaPorDefecto;

/// `Bs 1.234,50` / `US$ 1.234,50`. Acepta `num` o la cadena decimal que envía FastAPI.
String formatoImporte(Object? valor, [String? moneda]) {
  final numero = valor is num ? valor.toDouble() : double.tryParse('${valor ?? ''}'.trim());
  if (numero == null || numero.isNaN || numero.isInfinite) return '';
  final partes = numero.abs().toStringAsFixed(2).split('.');
  final miles = partes[0].replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => '.');
  final signo = numero < 0 ? '-' : '';
  return '$signo${simboloMoneda(moneda)} $miles,${partes[1]}';
}
