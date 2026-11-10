import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../../core/empresa_actual.dart';
import '../../../../../core/moneda.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../comercial/cu31_reportes_voz/presentacion/pantallas/pantalla_reportes_voz.dart';
import '../../datos/modelos_caja.dart';
import '../bloc/caja_bloc.dart';
import 'pantalla_cobro.dart';
import 'pantalla_ventas_caja.dart';

/// P2-CU16 · Caja del empleado (decisión E1): cajero, encargado y administrador entran aquí tras el
/// login, sin el hub del cliente. Busca prendas, asocia cliente, reserva y cupón, muestra los totales
/// que calcula el servidor y registra la venta para cobrarla.
class PantallaCaja extends StatefulWidget {
  final String token;
  final String nombreEmpleado;
  final String rol;
  final VoidCallback? alCerrarSesion;
  final CajaBloc? bloc;

  const PantallaCaja({
    super.key,
    required this.token,
    required this.nombreEmpleado,
    required this.rol,
    this.alCerrarSesion,
    this.bloc,
  });

  @override
  State<PantallaCaja> createState() => _PantallaCajaState();
}

class _PantallaCajaState extends State<PantallaCaja> {
  late final CajaBloc _bloc = widget.bloc ?? CajaBloc(token: widget.token);
  final _campoPrenda = TextEditingController();
  final _campoCliente = TextEditingController();
  final _campoCupon = TextEditingController();
  final _campoReserva = TextEditingController();
  Timer? _espera;
  List<VarianteCaja> _prendas = const [];
  List<ClienteCaja> _clientes = const [];
  List<CuponCaja> _cupones = const [];
  bool _buscandoPrendas = false;

  bool get _puedeVerReportes => const {'administrador', 'admin', 'encargado_sucursal'}.contains(widget.rol);

  @override
  void initState() {
    super.initState();
    _bloc.addListener(_alCambiar);
    _bloc.iniciar();
  }

  @override
  void dispose() {
    _espera?.cancel();
    _bloc.removeListener(_alCambiar);
    if (widget.bloc == null) _bloc.dispose();
    _campoPrenda.dispose();
    _campoCliente.dispose();
    _campoCupon.dispose();
    _campoReserva.dispose();
    super.dispose();
  }

  void _alCambiar() {
    final mensaje = _bloc.mensaje;
    if (mensaje != null && mounted) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(mensaje), backgroundColor: AppColors.slate900));
      _bloc.descartarMensaje();
    }
  }

  /// Búsqueda incremental: espera 300 ms a que se deje de escribir (como la caja web).
  void _conEspera(Future<void> Function() accion) {
    _espera?.cancel();
    _espera = Timer(const Duration(milliseconds: 300), () => accion());
  }

  Future<void> _buscarPrendas(String texto) async {
    setState(() => _buscandoPrendas = true);
    try {
      final resultado = await _bloc.buscarPrendas(texto);
      if (mounted) setState(() => _prendas = resultado);
    } catch (_) {
      if (mounted) setState(() => _prendas = const []);
    } finally {
      if (mounted) setState(() => _buscandoPrendas = false);
    }
  }

  Future<void> _buscarClientes(String texto) async {
    try {
      final resultado = await _bloc.buscarClientes(texto);
      if (mounted) setState(() => _clientes = resultado);
    } catch (_) {
      if (mounted) setState(() => _clientes = const []);
    }
  }

  Future<void> _buscarCupones(String texto) async {
    try {
      final resultado = await _bloc.buscarCupones(texto);
      if (mounted) setState(() => _cupones = resultado);
    } catch (_) {
      if (mounted) setState(() => _cupones = const []);
    }
  }

  Future<void> _registrarYCobrar() async {
    final venta = await _bloc.registrar();
    if (venta == null || !mounted) return;
    _campoCupon.clear();
    setState(() {
      _prendas = const [];
      _clientes = const [];
    });
    _campoPrenda.clear();
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PantallaCobro(bloc: _bloc)));
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _bloc,
      builder: (context, _) => Scaffold(
        backgroundColor: AppColors.slate50,
        appBar: AppBar(
          backgroundColor: AppColors.white,
          foregroundColor: AppColors.slate900,
          elevation: 0,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Caja · ${EmpresaActual.instancia.marca}', maxLines: 1, overflow: TextOverflow.ellipsis),
              Text(
                '${widget.nombreEmpleado}${_bloc.sucursal == null ? '' : ' · ${_bloc.sucursal!.nombre}'}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTypography.caption,
              ),
            ],
          ),
          actions: [
            if (_bloc.sucursal != null)
              IconButton(
                key: const Key('btn-ventas-caja'),
                tooltip: 'Pendientes y ventas del día',
                icon: Badge(
                  isLabelVisible: _bloc.pendientes.isNotEmpty || _bloc.pedidosWeb.isNotEmpty,
                  label: Text('${_bloc.pendientes.length + _bloc.pedidosWeb.length}'),
                  child: const Icon(Icons.receipt_long_outlined),
                ),
                onPressed: () => Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => PantallaVentasCaja(bloc: _bloc))),
              ),
            PopupMenuButton<String>(
              key: const Key('menu-caja'),
              onSelected: (opcion) {
                switch (opcion) {
                  case 'sucursal':
                    _bloc.volverASucursales();
                  case 'reportes':
                    Navigator.of(context)
                        .push(MaterialPageRoute(builder: (_) => PantallaReportesVoz(token: widget.token)));
                  case 'salir':
                    widget.alCerrarSesion?.call();
                }
              },
              itemBuilder: (_) => [
                if (_bloc.puedeCambiarSucursal) const PopupMenuItem(value: 'sucursal', child: Text('Cambiar de sucursal')),
                if (_puedeVerReportes) const PopupMenuItem(value: 'reportes', child: Text('Reportes por voz')),
                const PopupMenuItem(value: 'salir', child: Text('Cerrar sesión')),
              ],
            ),
          ],
        ),
        body: switch (_bloc.estado) {
          CajaCargando() => const Center(child: CircularProgressIndicator()),
          CajaError(:final mensaje) => _error(mensaje),
          CajaEligiendoSucursal(:final sucursales) => _selectorSucursal(sucursales),
          CajaOperando() => _venta(),
        },
        bottomNavigationBar: _bloc.estado is CajaOperando ? _barraDeAccion() : null,
      ),
    );
  }

  Widget _error(String mensaje) => Center(
        child: Padding(
          padding: AppSpacing.paddingSpace5,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(mensaje, textAlign: TextAlign.center, style: AppTypography.body),
              AppSpacing.gapVSpace4,
              FilledButton(
                onPressed: _bloc.iniciar,
                style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      );

  Widget _selectorSucursal(List<SucursalCaja> sucursales) => ListView(
        padding: AppSpacing.paddingSpace4,
        children: [
          const Text('¿En qué sucursal vendes hoy?', style: AppTypography.h3),
          AppSpacing.gapVSpace3,
          for (final s in sucursales)
            Card(
              child: ListTile(
                title: Text(s.nombre, maxLines: 1, overflow: TextOverflow.ellipsis),
                subtitle: Text(s.ciudad),
                trailing: s.esPrincipal ? const Icon(Icons.star_outline) : null,
                onTap: () => _bloc.elegirSucursal(s),
              ),
            ),
        ],
      );

  Widget _venta() {
    final previa = _bloc.previsualizacion;
    return ListView(
      padding: AppSpacing.paddingSpace4,
      children: [
        if (!_bloc.enLinea)
          Container(
            key: const Key('aviso-caja-sin-conexion'),
            margin: const EdgeInsets.only(bottom: AppSpacing.space4),
            padding: AppSpacing.paddingCard,
            decoration: const BoxDecoration(color: AppColors.slate900, borderRadius: AppRadius.radiusMedium),
            child: Text('Sin conexión: no se puede registrar ni cobrar hasta recuperarla.',
                style: AppTypography.body.copyWith(color: AppColors.white)),
          ),

        // 1. Prendas
        const Text('PRENDAS', style: AppTypography.labelSmall),
        AppSpacing.gapVSpace2,
        TextField(
          key: const Key('campo-prenda'),
          controller: _campoPrenda,
          decoration: InputDecoration(
            hintText: 'Nombre, categoría o SKU',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: _buscandoPrendas ? const Padding(padding: AppSpacing.paddingSpace3, child: CircularProgressIndicator(strokeWidth: 2)) : null,
            border: const OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
          ),
          onChanged: (t) => _conEspera(() => _buscarPrendas(t)),
        ),
        for (final v in _prendas)
          ListTile(
            dense: true,
            contentPadding: AppSpacing.paddingZero,
            title: Text('${v.nombreProducto} · ${v.talla} · ${v.color}', maxLines: 1, overflow: TextOverflow.ellipsis),
            subtitle: Text('${v.sku} · ${v.disponible == 0 ? 'Sin existencias' : '${v.disponible} disponibles'}'),
            trailing: Text(formatoImporte(v.precioFinal), style: AppTypography.bodyMedium),
            enabled: v.disponible > 0,
            onTap: () => _bloc.agregar(v),
          ),
        AppSpacing.gapVSpace4,

        // Líneas de la venta (las devuelve el servidor)
        if (previa != null)
          for (final l in previa.lineas)
            Container(
              margin: const EdgeInsets.only(bottom: AppSpacing.space2),
              padding: AppSpacing.paddingCard,
              decoration: const BoxDecoration(color: AppColors.white, borderRadius: AppRadius.radiusMedium),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(l.nombreProducto, maxLines: 1, overflow: TextOverflow.ellipsis, style: AppTypography.bodyMedium),
                        Text('${l.talla} · ${l.color}${l.origen == 'reserva' ? ' · de la reserva' : ''}',
                            maxLines: 1, overflow: TextOverflow.ellipsis, style: AppTypography.caption),
                        if (l.motivoDescuento != null) Text(l.motivoDescuento!, style: AppTypography.caption),
                      ],
                    ),
                  ),
                  if (l.origen == 'caja') ...[
                    IconButton(
                      onPressed: () => _bloc.cambiarCantidad(l.idVariante, (_bloc.lineas[l.idVariante] ?? 1) - 1),
                      icon: const Icon(Icons.remove_circle_outline),
                    ),
                    Text('${l.cantidad}', style: AppTypography.bodyMedium),
                    IconButton(
                      onPressed: () => _bloc.cambiarCantidad(l.idVariante, (_bloc.lineas[l.idVariante] ?? 0) + 1),
                      icon: const Icon(Icons.add_circle_outline),
                    ),
                  ] else
                    Text('× ${l.cantidad}', style: AppTypography.bodyMedium),
                  AppSpacing.gapHSpace3,
                  Text(formatoImporte(l.subtotalLinea), style: AppTypography.bodyMedium),
                ],
              ),
            ),
        AppSpacing.gapVSpace4,

        // 2. Cliente y reserva (AC-7)
        const Text('CLIENTE', style: AppTypography.labelSmall),
        AppSpacing.gapVSpace2,
        if (_bloc.cliente == null) ...[
          TextField(
            key: const Key('campo-cliente'),
            controller: _campoCliente,
            decoration: const InputDecoration(
              hintText: 'Nombre o correo (opcional: sin cliente es venta sin cuenta)',
              prefixIcon: Icon(Icons.person_search_outlined),
              border: OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
            ),
            onChanged: (t) => _conEspera(() => _buscarClientes(t)),
          ),
          for (final c in _clientes)
            ListTile(
              dense: true,
              contentPadding: AppSpacing.paddingZero,
              title: Text(c.nombreCompleto, maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: Text(c.email, maxLines: 1, overflow: TextOverflow.ellipsis),
              onTap: () {
                _campoCliente.clear();
                setState(() => _clientes = const []);
                _bloc.elegirCliente(c);
              },
            ),
        ] else
          InputChip(
            label: Text(_bloc.cliente!.nombreCompleto, overflow: TextOverflow.ellipsis),
            onDeleted: _bloc.quitarCliente,
          ),
        if (_bloc.reserva == null) ...[
          for (final r in _bloc.reservasDelCliente)
            ListTile(
              dense: true,
              contentPadding: AppSpacing.paddingZero,
              title: Text('Reserva ${r.codigo}'),
              subtitle: Text('${r.lineas.length} ${r.lineas.length == 1 ? 'prenda' : 'prendas'}'),
              trailing: TextButton(onPressed: () => _bloc.cargarReserva(r), child: const Text('Cargar')),
            ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const Key('campo-reserva'),
                  controller: _campoReserva,
                  decoration: const InputDecoration(hintText: 'O carga una reserva por código (RES-…)'),
                ),
              ),
              TextButton(
                onPressed: () async {
                  if (await _bloc.cargarReservaPorCodigo(_campoReserva.text)) _campoReserva.clear();
                },
                child: const Text('Cargar'),
              ),
            ],
          ),
        ] else ...[
          AppSpacing.gapVSpace2,
          Row(
            children: [
              Expanded(child: Text('Reserva ${_bloc.reserva!.codigo}', style: AppTypography.bodyMedium)),
              TextButton(onPressed: _bloc.quitarReserva, child: const Text('Quitar')),
            ],
          ),
          for (final l in _bloc.reserva!.lineas)
            CheckboxListTile(
              dense: true,
              contentPadding: AppSpacing.paddingZero,
              value: !_bloc.excluidas.contains(l.idVariante),
              onChanged: (_) => _bloc.alternarExclusion(l.idVariante),
              title: Text('${l.nombreProducto} · ${l.talla} · ${l.color} × ${l.cantidad}',
                  maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: _bloc.excluidas.contains(l.idVariante) ? const Text('No se la lleva') : null,
            ),
        ],
        AppSpacing.gapVSpace4,

        // 3. Cupón (AC-8)
        const Text('CUPÓN', style: AppTypography.labelSmall),
        AppSpacing.gapVSpace2,
        if (_bloc.cupon != null && previa?.cuponAplicado != null)
          InputChip(label: Text(previa!.cuponAplicado!), onDeleted: () => _bloc.aplicarCupon(null))
        else ...[
          TextField(
            key: const Key('campo-cupon'),
            controller: _campoCupon,
            decoration: InputDecoration(
              hintText: 'Código de cupón',
              border: const OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
              suffixIcon: TextButton(
                onPressed: _bloc.hayContenido ? () => _bloc.aplicarCupon(_campoCupon.text) : null,
                child: const Text('Aplicar'),
              ),
            ),
            onTap: () => _buscarCupones(_campoCupon.text),
            onChanged: (t) => _conEspera(() => _buscarCupones(t)),
          ),
          Wrap(
            spacing: AppSpacing.space3,
            children: [
              for (final c in _cupones)
                ActionChip(
                  label: Text(c.codigo),
                  onPressed: _bloc.hayContenido
                      ? () {
                          _campoCupon.text = c.codigo;
                          _bloc.aplicarCupon(c.codigo);
                        }
                      : null,
                ),
            ],
          ),
        ],
        AppSpacing.gapVSpace5,
        if (_bloc.hayContenido)
          TextButton(onPressed: _bloc.limpiarVenta, child: const Text('Descartar venta')),
      ],
    );
  }

  /// Barra de acción (admitida por la directriz Hub-and-Spoke): total del servidor y registrar.
  Widget _barraDeAccion() {
    final previa = _bloc.previsualizacion;
    return SafeArea(
      child: Container(
        padding: AppSpacing.paddingCard,
        decoration: const BoxDecoration(color: AppColors.white, border: Border(top: BorderSide(color: AppColors.slate200))),
        child: Row(
          children: [
            Expanded(
              child: Wrap(
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: AppSpacing.space3,
                children: [
                  const Text('Total', style: AppTypography.caption),
                  Text(
                    key: const Key('total-caja'),
                    previa == null ? '—' : formatoImporte(previa.total),
                    style: AppTypography.h3,
                  ),
                  if (previa != null && previa.descuento != '0.00')
                    Text('Ahorro ${formatoImporte(previa.descuento)}', style: AppTypography.caption),
                ],
              ),
            ),
            FilledButton(
              key: const Key('btn-registrar-venta'),
              onPressed: _bloc.puedeRegistrar ? _registrarYCobrar : null,
              style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
              child: Text(_bloc.registrando ? 'Registrando…' : 'Registrar y cobrar'),
            ),
          ],
        ),
      ),
    );
  }
}
