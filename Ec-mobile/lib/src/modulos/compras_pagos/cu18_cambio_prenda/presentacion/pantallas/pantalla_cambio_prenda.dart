import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../../core/empresa_actual.dart';
import '../../../../../core/moneda.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../cu16_cu17_caja/datos/modelos_caja.dart';
import '../../../cu16_cu17_caja/presentacion/bloc/caja_bloc.dart';
import '../../datos/cambio_prenda_api.dart';
import '../bloc/cambio_prenda_bloc.dart';

/// P2-CU18 · Cambio de prenda en la caja móvil. Hoja abierta desde el menú de la caja: busca la venta
/// por comprobante, elige qué devuelve y qué se lleva, muestra la diferencia del servidor, cobra si
/// paga el cliente y deja el comprobante en pantalla.
class PantallaCambioPrenda extends StatefulWidget {
  /// La caja en curso: aporta la sesión, la sucursal, el buscador de prendas y el estado de la red.
  final CajaBloc caja;
  final String token;
  final CambioPrendaBloc? bloc;

  const PantallaCambioPrenda({super.key, required this.caja, required this.token, this.bloc});

  @override
  State<PantallaCambioPrenda> createState() => _PantallaCambioPrendaState();
}

class _PantallaCambioPrendaState extends State<PantallaCambioPrenda> {
  late final CambioPrendaBloc _bloc = widget.bloc ??
      CambioPrendaBloc(
        token: widget.token,
        idSucursal: widget.caja.sucursal?.idSucursal,
        buscarPrendas: widget.caja.buscarPrendas,
        api: CambioPrendaApi(caja: widget.caja.api),
      );
  final _campoComprobante = TextEditingController();
  final _campoPrenda = TextEditingController();
  final _campoMonto = TextEditingController();
  final _campoReferencia = TextEditingController();
  Timer? _espera;
  List<VarianteCaja> _prendas = const [];
  String _metodo = 'efectivo';

  @override
  void dispose() {
    _espera?.cancel();
    if (widget.bloc == null) _bloc.dispose();
    _campoComprobante.dispose();
    _campoPrenda.dispose();
    _campoMonto.dispose();
    _campoReferencia.dispose();
    super.dispose();
  }

  void _buscarPrendas(String texto) {
    _espera?.cancel();
    _espera = Timer(const Duration(milliseconds: 300), () async {
      try {
        final resultado = await _bloc.buscarPrendas(texto);
        if (mounted) setState(() => _prendas = resultado);
      } catch (_) {
        if (mounted) setState(() => _prendas = const []);
      }
    });
  }

  void _nuevoCambio() {
    _campoComprobante.clear();
    _campoPrenda.clear();
    _campoMonto.clear();
    _campoReferencia.clear();
    setState(() {
      _prendas = const [];
      _metodo = 'efectivo';
    });
    _bloc.reiniciar();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_bloc, widget.caja]),
      builder: (context, _) {
        final estado = _bloc.estado;
        return Scaffold(
          backgroundColor: AppColors.slate50,
          appBar: AppBar(
            leading: const BackButton(),
            title: Text(estado is CambioRegistrado ? 'Comprobante de cambio' : 'Cambio de prenda'),
            backgroundColor: AppColors.white,
            foregroundColor: AppColors.slate900,
            elevation: 0,
          ),
          body: switch (estado) {
            CambioRegistrado(:final cambio) => _comprobante(cambio),
            CambioSinVenta() => _formulario(null),
            CambioEligiendo(:final venta) => _formulario(venta),
          },
          bottomNavigationBar: estado is CambioEligiendo ? _barraDeAccion() : null,
        );
      },
    );
  }

  Widget _formulario(VentaCambiable? venta) {
    final previo = _bloc.previo;
    return ListView(
      padding: AppSpacing.paddingSpace4,
      children: [
        if (!widget.caja.enLinea)
          Container(
            key: const Key('aviso-cambio-sin-conexion'),
            margin: const EdgeInsets.only(bottom: AppSpacing.space4),
            padding: AppSpacing.paddingCard,
            decoration: const BoxDecoration(color: AppColors.slate900, borderRadius: AppRadius.radiusMedium),
            child: Text('Sin conexión: no se puede registrar el cambio.',
                style: AppTypography.body.copyWith(color: AppColors.white)),
          ),
        if (_bloc.error != null)
          Container(
            key: const Key('error-cambio'),
            margin: const EdgeInsets.only(bottom: AppSpacing.space4),
            padding: AppSpacing.paddingCard,
            decoration: const BoxDecoration(color: AppColors.rose50, borderRadius: AppRadius.radiusMedium),
            child: Text(_bloc.error!, style: AppTypography.body.copyWith(color: AppColors.rose800)),
          ),

        // 1. Venta
        const Text('COMPROBANTE DE LA VENTA', style: AppTypography.labelSmall),
        AppSpacing.gapVSpace2,
        TextField(
          key: const Key('campo-comprobante-cambio'),
          controller: _campoComprobante,
          textInputAction: TextInputAction.search,
          decoration: InputDecoration(
            hintText: 'FS-2026-000123',
            border: const OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
            suffixIcon: IconButton(
              key: const Key('btn-buscar-venta-cambio'),
              tooltip: 'Buscar venta',
              icon: _bloc.cargando && venta == null
                  ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.search),
              onPressed: () => _bloc.buscarVenta(_campoComprobante.text),
            ),
          ),
          onSubmitted: _bloc.buscarVenta,
        ),

        if (venta != null) ...[
          AppSpacing.gapVSpace3,
          Text(
            '${venta.numeroComprobante} · ${venta.clienteNombre ?? 'Sin cuenta'} · '
            'hace ${venta.diasTranscurridos} ${venta.diasTranscurridos == 1 ? 'día' : 'días'} (plazo ${venta.plazoDias})',
            style: AppTypography.caption,
          ),

          // 2. Qué devuelve
          AppSpacing.gapVSpace5,
          const Text('QUÉ DEVUELVE', style: AppTypography.labelSmall),
          for (final l in venta.lineas) _lineaDevolucion(l),

          // 3. Qué se lleva
          AppSpacing.gapVSpace5,
          const Text('QUÉ SE LLEVA', style: AppTypography.labelSmall),
          AppSpacing.gapVSpace2,
          TextField(
            key: const Key('campo-prenda-cambio'),
            controller: _campoPrenda,
            decoration: const InputDecoration(
              hintText: 'Nombre, categoría o SKU',
              prefixIcon: Icon(Icons.search),
              border: OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
            ),
            onChanged: _buscarPrendas,
          ),
          for (final v in _prendas)
            ListTile(
              dense: true,
              contentPadding: AppSpacing.paddingZero,
              enabled: v.disponible > 0,
              title: Text('${v.nombreProducto} · ${v.talla} · ${v.color}', maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: Text('${v.disponible} disp.'),
              trailing: Text(formatoImporte(v.precioFinal), style: AppTypography.bodyMedium),
              onTap: () => _bloc.agregarNueva(v),
            ),
          for (final (v, cantidad) in _bloc.nuevas)
            Row(
              children: [
                Expanded(
                  child: Text('$cantidad × ${v.nombreProducto} · ${v.talla} · ${v.color}',
                      maxLines: 1, overflow: TextOverflow.ellipsis, style: AppTypography.body),
                ),
                TextButton(onPressed: () => _bloc.quitarNueva(v.idVariante), child: const Text('Quitar')),
              ],
            ),

          // 4. Diferencia y cobro
          AppSpacing.gapVSpace5,
          if (previo == null)
            Text(
              _bloc.calculando ? 'Calculando…' : 'Elige qué devuelve y qué se lleva para ver la diferencia.',
              style: AppTypography.caption,
            )
          else
            _resumen(previo),
        ],
      ],
    );
  }

  Widget _lineaDevolucion(LineaCambiable l) {
    final cantidad = _bloc.devolver[l.idVentaDetalle] ?? 0;
    return Padding(
      padding: AppSpacing.paddingVerticalSpace2,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${l.nombreProducto} · ${l.talla} · ${l.color}',
                    maxLines: 1, overflow: TextOverflow.ellipsis, style: AppTypography.bodyMedium),
                Text('${l.cambiables} de ${l.vendidas} por cambiar · vale ${formatoImporte(l.valorUnitario)} c/u',
                    maxLines: 2, overflow: TextOverflow.ellipsis, style: AppTypography.caption),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Menos',
            onPressed: cantidad > 0 ? () => _bloc.cambiarDevolucion(l, -1) : null,
            icon: const Icon(Icons.remove_circle_outline),
          ),
          Text('$cantidad', key: Key('devolver-${l.idVentaDetalle}'), style: AppTypography.bodyMedium),
          IconButton(
            key: Key('btn-devolver-${l.sku}'),
            tooltip: 'Devolver ${l.sku}',
            onPressed: cantidad < l.cambiables ? () => _bloc.cambiarDevolucion(l, 1) : null,
            icon: const Icon(Icons.add_circle_outline),
          ),
        ],
      ),
    );
  }

  Widget _resumen(CambioPrenda p) {
    return Container(
      padding: AppSpacing.paddingCard,
      decoration: const BoxDecoration(color: AppColors.white, borderRadius: AppRadius.radiusLarge),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _fila('Devuelve', p.valorDevuelto),
          _fila('Se lleva', p.valorNuevo),
          if (p.pagaElCliente) ...[
            AppSpacing.gapVSpace3,
            Wrap(
              spacing: AppSpacing.space2,
              runSpacing: AppSpacing.space2,
              children: [
                for (final m in nombreMetodo.entries)
                  ChoiceChip(
                    label: Text(m.value),
                    selected: _metodo == m.key,
                    onSelected: (_) => setState(() => _metodo = m.key),
                  ),
              ],
            ),
            AppSpacing.gapVSpace3,
            if (_metodo == 'efectivo')
              TextField(
                key: const Key('campo-monto-cambio'),
                controller: _campoMonto,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Monto recibido',
                  border: OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
                ),
              )
            else
              TextField(
                key: const Key('campo-referencia-cambio'),
                controller: _campoReferencia,
                decoration: const InputDecoration(
                  labelText: 'Referencia de la operación',
                  border: OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
                ),
              ),
          ] else if (p.seDevuelveAlCliente) ...[
            AppSpacing.gapVSpace2,
            const Text('Entrega la diferencia al cliente en efectivo.', style: AppTypography.caption),
          ],
        ],
      ),
    );
  }

  String _sinSigno(String importe) => importe.startsWith('-') ? importe.substring(1) : importe;

  /// Barra de acción (admitida por la directriz Hub-and-Spoke): diferencia del servidor y registrar.
  Widget _barraDeAccion() {
    final p = _bloc.previo;
    final etiqueta = p == null
        ? 'Diferencia'
        : p.pagaElCliente
            ? 'Paga el cliente'
            : p.seDevuelveAlCliente
                ? 'Se devuelve al cliente'
                : 'Sin diferencia';
    return SafeArea(
      child: Container(
        padding: AppSpacing.paddingCard,
        decoration: const BoxDecoration(color: AppColors.white, border: Border(top: BorderSide(color: AppColors.slate200))),
        child: Row(
          children: [
            Expanded(
              child: Wrap(
                key: const Key('diferencia-cambio'),
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: AppSpacing.space3,
                children: [
                  Text(etiqueta, style: AppTypography.caption),
                  Text(p == null ? '—' : formatoImporte(_sinSigno(p.diferencia)), style: AppTypography.h3),
                ],
              ),
            ),
            FilledButton(
              key: const Key('btn-registrar-cambio'),
              onPressed: _bloc.puedeRegistrar(enLinea: widget.caja.enLinea)
                  ? () => _bloc.registrar(
                        metodoPago: _metodo,
                        montoRecibido: _campoMonto.text,
                        referencia: _campoReferencia.text,
                      )
                  : null,
              style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
              child: Text(_bloc.cargando ? 'Registrando…' : 'Registrar cambio'),
            ),
          ],
        ),
      ),
    );
  }

  /// AC-9: comprobante del cambio en pantalla (como el de la venta, decisión E2: sin PDF).
  Widget _comprobante(CambioPrenda c) {
    final fecha = c.creadoEn?.toLocal();
    String d(int n) => n.toString().padLeft(2, '0');
    Widget linea(LineaCambio l) => Padding(
          padding: AppSpacing.paddingVerticalSpace2,
          child: Row(
            children: [
              Expanded(
                child: Text('${l.cantidad} × ${l.nombreProducto} (${l.talla})',
                    maxLines: 2, overflow: TextOverflow.ellipsis, style: AppTypography.body),
              ),
              AppSpacing.gapHSpace3,
              Text(formatoImporte(l.subtotal), style: AppTypography.body),
            ],
          ),
        );
    return ListView(
      padding: AppSpacing.paddingSpace4,
      children: [
        Container(
          key: const Key('comprobante-cambio'),
          padding: AppSpacing.paddingSpace5,
          decoration: const BoxDecoration(color: AppColors.white, borderRadius: AppRadius.radiusLarge),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(EmpresaActual.instancia.marca, style: AppTypography.h3),
              if (c.nombreSucursal != null) Text(c.nombreSucursal!, style: AppTypography.body),
              const Divider(),
              Text('Cambio de prenda ${c.numeroComprobante ?? ''}', style: AppTypography.bodyMedium),
              if (fecha != null)
                Text('${d(fecha.day)}/${d(fecha.month)}/${fecha.year} ${d(fecha.hour)}:${d(fecha.minute)}',
                    style: AppTypography.caption),
              Text('Venta original: ${c.comprobanteVenta ?? ''}', style: AppTypography.caption),
              if (c.atendidoPor != null) Text('Atendió: ${c.atendidoPor}', style: AppTypography.caption),
              const Divider(),
              const Text('DEVUELVE', style: AppTypography.labelSmall),
              for (final l in c.devueltas) linea(l),
              const Text('SE LLEVA', style: AppTypography.labelSmall),
              for (final l in c.nuevas) linea(l),
              const Divider(),
              _fila('Valor devuelto', c.valorDevuelto),
              _fila('Valor nuevo', c.valorNuevo),
              if (c.pagaElCliente) ...[
                _fila('Pagó la diferencia (${nombreMetodo[c.metodoPago] ?? c.metodoPago ?? ''})', c.diferencia,
                    destacado: true),
                if (c.montoRecibido != null) _fila('Recibido', c.montoRecibido!),
                if (c.vuelto != null) _fila('Vuelto', c.vuelto!, destacado: true),
                if (c.referencia != null) Text('Referencia ${c.referencia}', style: AppTypography.caption),
              ] else if ((num.tryParse(c.devueltoAlCliente) ?? 0) > 0)
                _fila('Se le devuelve en efectivo', c.devueltoAlCliente, destacado: true)
              else
                const Text('Sin diferencia', style: AppTypography.body),
            ],
          ),
        ),
        AppSpacing.gapVSpace5,
        FilledButton(
          key: const Key('btn-nuevo-cambio'),
          onPressed: _nuevoCambio,
          style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
          child: const Text('Nuevo cambio'),
        ),
      ],
    );
  }

  Widget _fila(String etiqueta, String importe, {bool destacado = false}) {
    final estilo = destacado ? AppTypography.bodyMedium : AppTypography.body;
    return Padding(
      padding: AppSpacing.paddingVerticalSpace2,
      child: Row(
        children: [
          Expanded(child: Text(etiqueta, maxLines: 2, overflow: TextOverflow.ellipsis, style: estilo)),
          Text(formatoImporte(importe), style: estilo),
        ],
      ),
    );
  }
}
