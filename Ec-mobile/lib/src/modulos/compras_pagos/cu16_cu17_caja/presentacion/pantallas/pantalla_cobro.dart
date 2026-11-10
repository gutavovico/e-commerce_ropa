import 'package:flutter/material.dart';

import '../../../../../core/moneda.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../datos/modelos_caja.dart';
import '../bloc/caja_bloc.dart';
import 'pantalla_comprobante.dart';

/// P2-CU17 · Cobro de la venta registrada. Efectivo: monto recibido y el cambio lo calcula el
/// servidor (AC-10). Tarjeta, QR o transferencia: referencia, con «Datáfono rechazó la tarjeta» (AC-11).
class PantallaCobro extends StatefulWidget {
  final CajaBloc bloc;

  const PantallaCobro({super.key, required this.bloc});

  @override
  State<PantallaCobro> createState() => _PantallaCobroState();
}

class _PantallaCobroState extends State<PantallaCobro> {
  String _metodo = 'efectivo';
  final _monto = TextEditingController();
  final _referencia = TextEditingController();

  CajaBloc get _bloc => widget.bloc;
  bool get _esTarjeta => _metodo == 'tarjeta_debito' || _metodo == 'tarjeta_credito';

  @override
  void dispose() {
    _monto.dispose();
    _referencia.dispose();
    super.dispose();
  }

  Future<void> _cobrar({bool aprobado = true}) async {
    final resultado = await _bloc.cobrar(
      metodoPago: _metodo,
      montoRecibido: _metodo == 'efectivo' ? _monto.text.trim().replaceAll(',', '.') : null,
      referencia: _metodo == 'efectivo' ? null : _referencia.text.trim(),
      aprobado: aprobado,
    );
    if (!mounted || resultado == null) {
      _mostrarMensaje();
      return;
    }
    if (!resultado.pendiente) {
      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => PantallaComprobante(venta: resultado)),
      );
    } else {
      _mostrarMensaje();
    }
  }

  void _mostrarMensaje() {
    final mensaje = _bloc.mensaje;
    if (mensaje == null || !mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(mensaje), backgroundColor: AppColors.slate900));
    _bloc.descartarMensaje();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) {
        final venta = _bloc.ventaEnCobro;
        return Scaffold(
          backgroundColor: AppColors.slate50,
          appBar: AppBar(
            leading: const BackButton(),
            title: const Text('Cobrar'),
            backgroundColor: AppColors.white,
            foregroundColor: AppColors.slate900,
            elevation: 0,
          ),
          body: venta == null
              ? const Center(child: Text('No hay una venta por cobrar.', style: AppTypography.body))
              : ListView(
                  padding: AppSpacing.paddingSpace4,
                  children: [
                    if (!_bloc.enLinea)
                      const Padding(
                        padding: EdgeInsets.only(bottom: AppSpacing.space4),
                        child: Text('Sin conexión: el cobro se cerrará al recuperarla.', style: AppTypography.body),
                      ),
                    Text(venta.numeroComprobante, style: AppTypography.caption),
                    Text(key: const Key('total-cobro'), formatoImporte(venta.totales.total), style: AppTypography.h1),
                    if (venta.totales.descuento != '0.00')
                      Text('Ahorro ${formatoImporte(venta.totales.descuento)}', style: AppTypography.caption),
                    AppSpacing.gapVSpace5,
                    const Text('FORMA DE PAGO', style: AppTypography.labelSmall),
                    AppSpacing.gapVSpace2,
                    Wrap(
                      spacing: AppSpacing.space3,
                      runSpacing: AppSpacing.space3,
                      children: [
                        for (final m in metodosCobro)
                          ChoiceChip(
                            label: Text(nombreMetodo[m]!),
                            selected: _metodo == m,
                            onSelected: (_) => setState(() => _metodo = m),
                          ),
                      ],
                    ),
                    AppSpacing.gapVSpace4,
                    if (_metodo == 'efectivo')
                      TextField(
                        key: const Key('campo-monto'),
                        controller: _monto,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                          labelText: 'Monto recibido',
                          prefixText: '${simboloMoneda()} ',
                          border: const OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
                        ),
                      )
                    else
                      TextField(
                        key: const Key('campo-referencia'),
                        controller: _referencia,
                        decoration: const InputDecoration(
                          labelText: 'Referencia (autorización o transacción)',
                          border: OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
                        ),
                      ),
                    AppSpacing.gapVSpace5,
                    FilledButton(
                      key: const Key('btn-confirmar-cobro'),
                      onPressed: _bloc.cobrando || !_bloc.enLinea ? null : _cobrar,
                      style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
                      child: Text(_bloc.cobrando ? 'Procesando…' : 'Confirmar cobro'),
                    ),
                    if (_esTarjeta) ...[
                      AppSpacing.gapVSpace3,
                      OutlinedButton(
                        key: const Key('btn-cobro-rechazado'),
                        onPressed: _bloc.cobrando || !_bloc.enLinea ? null : () => _cobrar(aprobado: false),
                        child: const Text('Datáfono rechazó la tarjeta'),
                      ),
                    ],
                    AppSpacing.gapVSpace4,
                    const Text(
                      'Si sales sin cobrar, la venta queda en «Pendientes» y se anula sola a las 2 h.',
                      style: AppTypography.caption,
                    ),
                  ],
                ),
        );
      },
    );
  }
}
