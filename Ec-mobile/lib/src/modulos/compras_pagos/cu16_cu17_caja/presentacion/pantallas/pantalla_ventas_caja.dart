import 'package:flutter/material.dart';

import '../../../../../core/moneda.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../datos/caja_api.dart';
import '../../datos/modelos_caja.dart';
import '../bloc/caja_bloc.dart';
import 'pantalla_cobro.dart';
import 'pantalla_comprobante.dart';

/// P2-CU17 (AC-13) y decisión E3 (AC-14) · Ventas pendientes y cobradas del día en la sucursal, y
/// pedidos web pagados en efectivo que se cobran en mostrador. Hoja con `BackButton`.
class PantallaVentasCaja extends StatefulWidget {
  final CajaBloc bloc;

  const PantallaVentasCaja({super.key, required this.bloc});

  @override
  State<PantallaVentasCaja> createState() => _PantallaVentasCajaState();
}

class _PantallaVentasCajaState extends State<PantallaVentasCaja> {
  CajaBloc get _bloc => widget.bloc;

  @override
  void initState() {
    super.initState();
    _bloc.cargarVentas();
  }

  void _avisar(String texto) => ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(texto), backgroundColor: AppColors.slate900));

  void _avisarError() {
    final m = _bloc.mensaje;
    if (m != null) {
      _avisar(m);
      _bloc.descartarMensaje();
    }
  }

  Future<void> _cobrar(VentaCaja venta) async {
    _bloc.abrirCobro(venta);
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PantallaCobro(bloc: _bloc)));
  }

  Future<void> _verComprobante(VentaCaja venta) async {
    try {
      final completa = await _bloc.obtenerVenta(venta.idVenta);
      if (!mounted) return;
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PantallaComprobante(venta: completa)));
    } on CajaException catch (e) {
      if (mounted) _avisar(e.mensaje);
    }
  }

  /// A3 de CU17: anular una pendiente con motivo (3–250 caracteres).
  Future<void> _anular(VentaCaja venta) async {
    final texto = await showDialog<String>(
      context: context,
      builder: (_) => _DialogoMotivo(titulo: 'Anular ${venta.numeroComprobante}'),
    );
    if (texto == null) return;
    if (await _bloc.anular(venta.idVenta, texto)) {
      if (mounted) _avisar('Venta ${venta.numeroComprobante} anulada.');
    } else {
      _avisarError();
    }
  }

  Future<void> _resolverPedido(PedidoWebEfectivo pedido, {required bool confirmar}) async {
    final seguro = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(confirmar ? 'Confirmar cobro' : 'Cancelar pedido'),
        content: Text(confirmar
            ? '¿El cliente pagó ${formatoImporte(pedido.total)} en efectivo por ${pedido.numeroComprobante}?'
            : 'Se cancela el pago en efectivo de ${pedido.numeroComprobante} y las prendas vuelven a estar disponibles.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Volver')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(confirmar ? 'Confirmar' : 'Cancelar pedido')),
        ],
      ),
    );
    if (seguro != true) return;
    if (await _bloc.resolverPedidoWeb(pedido, confirmar: confirmar)) {
      if (mounted) _avisar(confirmar ? 'Cobro confirmado.' : 'Pedido cancelado.');
    } else {
      _avisarError();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) {
        final cobradas = _bloc.ventasDelDia.where((v) => v.estado == 'pagada').toList();
        return Scaffold(
          backgroundColor: AppColors.slate50,
          appBar: AppBar(
            leading: const BackButton(),
            title: const Text('Ventas de la caja'),
            backgroundColor: AppColors.white,
            foregroundColor: AppColors.slate900,
            elevation: 0,
          ),
          body: RefreshIndicator(
            onRefresh: _bloc.cargarVentas,
            child: ListView(
              padding: AppSpacing.paddingSpace4,
              children: [
                const Text('PENDIENTES DE COBRO', style: AppTypography.labelSmall),
                if (_bloc.pendientes.isEmpty) const Text('No hay ventas pendientes.', style: AppTypography.caption),
                for (final v in _bloc.pendientes)
                  Card(
                    child: ListTile(
                      title: Text(v.numeroComprobante, maxLines: 1, overflow: TextOverflow.ellipsis),
                      subtitle: Text(v.cliente?.nombreCompleto ?? 'Sin cuenta', maxLines: 1, overflow: TextOverflow.ellipsis),
                      trailing: Wrap(
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Text(formatoImporte(v.totales.total), style: AppTypography.bodyMedium),
                          IconButton(
                            tooltip: 'Anular',
                            onPressed: () => _anular(v),
                            icon: const Icon(Icons.cancel_outlined),
                          ),
                        ],
                      ),
                      onTap: _bloc.enLinea ? () => _cobrar(v) : null,
                    ),
                  ),
                AppSpacing.gapVSpace5,
                const Text('PEDIDOS WEB EN EFECTIVO', style: AppTypography.labelSmall),
                if (_bloc.pedidosWeb.isEmpty) const Text('No hay pedidos web por cobrar.', style: AppTypography.caption),
                for (final p in _bloc.pedidosWeb)
                  Card(
                    child: ListTile(
                      title: Text(p.numeroComprobante, maxLines: 1, overflow: TextOverflow.ellipsis),
                      subtitle: Text(p.clienteNombre ?? 'Cliente', maxLines: 1, overflow: TextOverflow.ellipsis),
                      trailing: Wrap(
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Text(formatoImporte(p.total), style: AppTypography.bodyMedium),
                          IconButton(
                            tooltip: 'Confirmar cobro',
                            onPressed: _bloc.enLinea ? () => _resolverPedido(p, confirmar: true) : null,
                            icon: const Icon(Icons.check_circle_outline),
                          ),
                          IconButton(
                            tooltip: 'Cancelar',
                            onPressed: _bloc.enLinea ? () => _resolverPedido(p, confirmar: false) : null,
                            icon: const Icon(Icons.close),
                          ),
                        ],
                      ),
                    ),
                  ),
                AppSpacing.gapVSpace5,
                const Text('COBRADAS HOY', style: AppTypography.labelSmall),
                if (cobradas.isEmpty) const Text('Todavía no hay ventas cobradas hoy.', style: AppTypography.caption),
                for (final v in cobradas)
                  Card(
                    child: ListTile(
                      title: Text(v.numeroComprobante, maxLines: 1, overflow: TextOverflow.ellipsis),
                      subtitle: Text(v.cliente?.nombreCompleto ?? 'Sin cuenta', maxLines: 1, overflow: TextOverflow.ellipsis),
                      trailing: Text(formatoImporte(v.totales.total), style: AppTypography.bodyMedium),
                      onTap: () => _verComprobante(v),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Pide el motivo de la anulación (3–250 caracteres). El diálogo es dueño de su controlador: liberarlo
/// desde fuera mientras el diálogo anima su cierre rompe el árbol de widgets.
class _DialogoMotivo extends StatefulWidget {
  final String titulo;

  const _DialogoMotivo({required this.titulo});

  @override
  State<_DialogoMotivo> createState() => _DialogoMotivoState();
}

class _DialogoMotivoState extends State<_DialogoMotivo> {
  final _motivo = TextEditingController();

  @override
  void dispose() {
    _motivo.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.titulo),
      content: TextField(
        key: const Key('campo-motivo'),
        controller: _motivo,
        maxLength: 250,
        decoration: const InputDecoration(labelText: 'Motivo', helperText: 'Al menos 3 caracteres'),
        onChanged: (_) => setState(() {}),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton(
          onPressed: _motivo.text.trim().length >= 3 ? () => Navigator.pop(context, _motivo.text.trim()) : null,
          child: const Text('Anular'),
        ),
      ],
    );
  }
}
