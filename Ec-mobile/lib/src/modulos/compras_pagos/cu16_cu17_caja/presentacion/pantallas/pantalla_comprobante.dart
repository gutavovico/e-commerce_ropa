import 'package:flutter/material.dart';

import '../../../../../core/empresa_actual.dart';
import '../../../../../core/moneda.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../datos/modelos_caja.dart';

/// P2-CU17 · Comprobante en pantalla (decisión E2: sin PDF). Todo dato sale de la venta que devolvió
/// el servidor; nada se calcula en el teléfono.
class PantallaComprobante extends StatelessWidget {
  final VentaCaja venta;

  const PantallaComprobante({super.key, required this.venta});

  @override
  Widget build(BuildContext context) {
    final t = venta.totales;
    final pago = venta.pagoConfirmado;
    final fecha = venta.fechaVenta?.toLocal();
    String d(int n) => n.toString().padLeft(2, '0');
    return Scaffold(
      backgroundColor: AppColors.slate50,
      appBar: AppBar(
        leading: const BackButton(),
        title: const Text('Comprobante'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.slate900,
        elevation: 0,
      ),
      body: ListView(
        padding: AppSpacing.paddingSpace4,
        children: [
          Container(
            padding: AppSpacing.paddingSpace5,
            decoration: const BoxDecoration(color: AppColors.white, borderRadius: AppRadius.radiusLarge),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(EmpresaActual.instancia.marca, style: AppTypography.h3),
                Text(venta.nombreSucursal, style: AppTypography.body),
                if (venta.direccionSucursal != null) Text(venta.direccionSucursal!, style: AppTypography.caption),
                const Divider(),
                Text(key: const Key('numero-comprobante'), venta.numeroComprobante, style: AppTypography.bodyMedium),
                if (fecha != null)
                  Text('${d(fecha.day)}/${d(fecha.month)}/${fecha.year} ${d(fecha.hour)}:${d(fecha.minute)}',
                      style: AppTypography.caption),
                if (venta.cajeroNombre != null) Text('Atendió: ${venta.cajeroNombre}', style: AppTypography.caption),
                Text('Cliente: ${venta.cliente?.nombreCompleto ?? 'Venta presencial sin cuenta'}', style: AppTypography.caption),
                if (venta.reservaCodigo != null) Text('Reserva ${venta.reservaCodigo}', style: AppTypography.caption),
                const Divider(),
                for (final l in t.lineas)
                  Padding(
                    padding: AppSpacing.paddingVerticalSpace2,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Text('${l.cantidad} × ${l.nombreProducto} (${l.talla} · ${l.color})',
                              maxLines: 2, overflow: TextOverflow.ellipsis, style: AppTypography.body),
                        ),
                        AppSpacing.gapHSpace3,
                        Text(formatoImporte(l.subtotalLinea), style: AppTypography.body),
                      ],
                    ),
                  ),
                const Divider(),
                _fila('Subtotal', t.subtotal),
                if (t.descuento != '0.00') _fila('Descuento${t.cuponAplicado == null ? '' : ' (${t.cuponAplicado})'}', '-${t.descuento}'),
                _fila('Total', t.total, destacado: true),
                _fila('IVA incluido', t.ivaIncluido),
                if (pago != null) ...[
                  const Divider(),
                  Text('Pago: ${nombreMetodo[pago.metodoPago] ?? pago.metodoPago}', style: AppTypography.body),
                  if (pago.referencia != null) Text('Referencia ${pago.referencia}', style: AppTypography.caption),
                  if (pago.montoRecibido != null) _fila('Recibido', pago.montoRecibido!),
                  if (pago.cambio != null) _fila('Cambio', pago.cambio!, destacado: true),
                ],
              ],
            ),
          ),
          AppSpacing.gapVSpace5,
          FilledButton(
            key: const Key('btn-nueva-venta'),
            onPressed: () => Navigator.of(context).pop(),
            style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
            child: const Text('Nueva venta'),
          ),
        ],
      ),
    );
  }

  Widget _fila(String etiqueta, String importe, {bool destacado = false}) {
    final estilo = destacado ? AppTypography.bodyMedium : AppTypography.body;
    final negativo = importe.startsWith('-');
    return Padding(
      padding: AppSpacing.paddingVerticalSpace2,
      child: Row(
        children: [
          Expanded(child: Text(etiqueta, style: estilo)),
          Text(negativo ? '- ${formatoImporte(importe.substring(1))}' : formatoImporte(importe), style: estilo),
        ],
      ),
    );
  }
}
