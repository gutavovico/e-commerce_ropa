import 'package:flutter/material.dart';

import '../../../../core/moneda.dart';
import '../../../../core/sin_conexion/franjas_cita.dart';
import '../../../../core/sin_conexion/modelos_sin_conexion.dart';
import '../../../../core/sin_conexion/sin_conexion_api.dart';
import '../../../../core/sin_conexion/sin_conexion_servicio.dart';
import '../../../../core/theme/app_theme.dart';

/// P2-CU14 (A4) y P2-CU15 (A1) · Catálogo guardado en el teléfono: búsqueda, existencias por sucursal
/// y reserva sin conexión con código provisional. Hoja: se abre con `Navigator.push`.
///
/// Las existencias son las de la última descarga; el servidor las valida al sincronizar.
class PantallaCatalogoSinConexion extends StatefulWidget {
  final SinConexionServicio? servicio;

  const PantallaCatalogoSinConexion({super.key, this.servicio});

  @override
  State<PantallaCatalogoSinConexion> createState() => _PantallaCatalogoSinConexionState();
}

class _PantallaCatalogoSinConexionState extends State<PantallaCatalogoSinConexion> {
  late final SinConexionServicio _servicio = widget.servicio ?? SinConexionServicio.instancia;
  String _texto = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate50,
      appBar: AppBar(
        leading: const BackButton(),
        title: const Text('Catálogo sin conexión'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.slate900,
        elevation: 0,
      ),
      body: AnimatedBuilder(
        animation: _servicio,
        builder: (context, _) {
          final catalogo = _servicio.catalogo;
          if (catalogo == null) {
            return const Center(
              child: Padding(
                padding: AppSpacing.paddingSpace5,
                child: Text(
                  'No hay un catálogo guardado en este teléfono. Abre la tienda con conexión para descargarlo.',
                  textAlign: TextAlign.center,
                  style: AppTypography.body,
                ),
              ),
            );
          }
          final texto = _texto.trim().toLowerCase();
          final productos = catalogo.productos
              .where((p) =>
                  p.variantes.isNotEmpty &&
                  (texto.isEmpty ||
                      p.nombre.toLowerCase().contains(texto) ||
                      (p.descripcion ?? '').toLowerCase().contains(texto)))
              .toList();
          return Column(
            children: [
              Padding(
                padding: AppSpacing.paddingSpace4,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_servicio.guardadoEn != null)
                      Text('Puede estar desactualizado · Datos del ${_fecha(_servicio.guardadoEn!)}',
                          style: AppTypography.caption),
                    AppSpacing.gapVSpace3,
                    TextField(
                      key: const Key('buscar-sin-conexion'),
                      decoration: const InputDecoration(
                        hintText: 'Buscar en el catálogo guardado',
                        prefixIcon: Icon(Icons.search),
                        border: OutlineInputBorder(borderRadius: AppRadius.radiusMedium),
                      ),
                      onChanged: (v) => setState(() => _texto = v),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: productos.isEmpty
                    ? const Center(child: Text('No hay prendas que coincidan.', style: AppTypography.caption))
                    : ListView.separated(
                        padding: AppSpacing.paddingHorizontalSpace4,
                        itemCount: productos.length,
                        separatorBuilder: (_, _) => AppSpacing.gapVSpace3,
                        itemBuilder: (context, i) {
                          final p = productos[i];
                          return ListTile(
                            tileColor: AppColors.white,
                            shape: const RoundedRectangleBorder(borderRadius: AppRadius.radiusLarge),
                            title: Text(p.nombre, maxLines: 1, overflow: TextOverflow.ellipsis),
                            subtitle: Text(catalogo.categorias[p.idCategoria] ?? '',
                                maxLines: 1, overflow: TextOverflow.ellipsis),
                            trailing: Text(formatoImporte(p.precioBase, catalogo.moneda), style: AppTypography.bodyMedium),
                            onTap: () => _abrirReserva(catalogo, p),
                          );
                        },
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _abrirReserva(CatalogoLocal catalogo, ProductoLocal producto) async {
    final codigo = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: AppRadius.circularSheet)),
      builder: (_) => _HojaReservaSinConexion(servicio: _servicio, catalogo: catalogo, producto: producto),
    );
    if (codigo != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        backgroundColor: AppColors.slate900,
        content: Text(_servicio.enLinea
            ? 'Reserva $codigo guardada: la estamos enviando a la tienda.'
            : 'Reserva $codigo guardada: se enviará al recuperar la conexión.'),
      ));
    }
  }

  static String _fecha(DateTime f) {
    final l = f.toLocal();
    String d(int n) => n.toString().padLeft(2, '0');
    return '${d(l.day)}/${d(l.month)}/${l.year} ${d(l.hour)}:${d(l.minute)}';
  }
}

class _HojaReservaSinConexion extends StatefulWidget {
  final SinConexionServicio servicio;
  final CatalogoLocal catalogo;
  final ProductoLocal producto;

  const _HojaReservaSinConexion({required this.servicio, required this.catalogo, required this.producto});

  @override
  State<_HojaReservaSinConexion> createState() => _HojaReservaSinConexionState();
}

class _HojaReservaSinConexionState extends State<_HojaReservaSinConexion> {
  late VarianteLocal _variante = widget.producto.variantes.first;
  int? _sucursal;
  FranjaCita? _franja;
  int _cantidad = 1;
  bool _guardando = false;
  String? _error;
  late final List<FranjaCita> _franjas = franjasDeCita(DateTime.now(), widget.servicio.horasVencimiento);

  String _nombreVariante(VarianteLocal v) =>
      '${widget.catalogo.tallas[v.idTalla] ?? '—'} · ${widget.catalogo.colores[v.idColor] ?? '—'}';

  Future<void> _reservar() async {
    final sucursal = _sucursal;
    final franja = _franja;
    if (sucursal == null || franja == null) {
      setState(() => _error = 'Elige la sucursal y la hora de tu visita.');
      return;
    }
    setState(() {
      _guardando = true;
      _error = null;
    });
    final nombreSucursal = widget.catalogo.sucursales.firstWhere((s) => s.idSucursal == sucursal).nombre;
    try {
      final op = await widget.servicio.reservarSinConexion(
        idSucursal: sucursal,
        fechaHoraAtencion: franja.instante,
        items: [
          {'id_variante': _variante.idVariante, 'cantidad': _cantidad},
        ],
        titulo: widget.producto.nombre,
        detalle: '${_nombreVariante(_variante)} · $nombreSucursal · ${franja.etiqueta}',
      );
      if (mounted) Navigator.of(context).pop(op.codigoProvisional);
    } on SinConexionException catch (e) {
      setState(() => _error = e.mensaje);
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final disponible = _sucursal == null ? 0 : widget.catalogo.disponible(_variante.idVariante, _sucursal!);
    final maximo = disponible.clamp(0, 5);
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: AppSpacing.space5,
          right: AppSpacing.space5,
          top: AppSpacing.space5,
          bottom: MediaQuery.of(context).viewInsets.bottom + AppSpacing.space5,
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(widget.producto.nombre, style: AppTypography.h3),
              if (widget.producto.descripcion != null)
                Text(widget.producto.descripcion!, style: AppTypography.caption),
              AppSpacing.gapVSpace4,
              const Text('TALLA Y COLOR', style: AppTypography.labelSmall),
              DropdownButton<int>(
                isExpanded: true,
                value: _variante.idVariante,
                items: [
                  for (final v in widget.producto.variantes)
                    DropdownMenuItem(
                      value: v.idVariante,
                      child: Text('${_nombreVariante(v)} · ${formatoImporte(v.precio, widget.catalogo.moneda)}',
                          overflow: TextOverflow.ellipsis),
                    ),
                ],
                onChanged: (id) => setState(() {
                  _variante = widget.producto.variantes.firstWhere((v) => v.idVariante == id);
                  _sucursal = null;
                  _cantidad = 1;
                }),
              ),
              AppSpacing.gapVSpace3,
              const Text('SUCURSAL', style: AppTypography.labelSmall),
              for (final s in widget.catalogo.sucursales)
                Builder(builder: (context) {
                  final unidades = widget.catalogo.disponible(_variante.idVariante, s.idSucursal);
                  final elegida = _sucursal == s.idSucursal;
                  return ListTile(
                    contentPadding: AppSpacing.paddingZero,
                    enabled: unidades > 0,
                    selected: elegida,
                    selectedColor: AppColors.slate900,
                    leading: Icon(elegida ? Icons.radio_button_checked : Icons.radio_button_unchecked),
                    onTap: () => setState(() {
                      _sucursal = s.idSucursal;
                      _cantidad = 1;
                    }),
                    title: Text(s.nombre, maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(unidades == 0 ? 'Sin existencias' : '$unidades disponibles'),
                  );
                }),
              if (_sucursal != null) ...[
                AppSpacing.gapVSpace3,
                const Text('HORA DE VISITA', style: AppTypography.labelSmall),
                if (_franjas.isEmpty)
                  const Text('No quedan horas de visita disponibles. Inténtalo más tarde.', style: AppTypography.caption)
                else
                  Wrap(
                    spacing: AppSpacing.space3,
                    runSpacing: AppSpacing.space3,
                    children: [
                      for (final f in _franjas)
                        ChoiceChip(
                          label: Text(f.etiqueta),
                          selected: _franja == f,
                          onSelected: (_) => setState(() => _franja = f),
                        ),
                    ],
                  ),
                AppSpacing.gapVSpace3,
                Row(
                  children: [
                    const Expanded(child: Text('UNIDADES', style: AppTypography.labelSmall)),
                    IconButton(
                      onPressed: _cantidad > 1 ? () => setState(() => _cantidad--) : null,
                      icon: const Icon(Icons.remove),
                    ),
                    Text('$_cantidad', style: AppTypography.bodyMedium),
                    IconButton(
                      onPressed: _cantidad < maximo ? () => setState(() => _cantidad++) : null,
                      icon: const Icon(Icons.add),
                    ),
                  ],
                ),
                Text('La reserva se mantiene ${widget.servicio.horasVencimiento} h desde que la haces.',
                    style: AppTypography.caption),
              ],
              if (_error != null) ...[
                AppSpacing.gapVSpace3,
                Text(_error!, style: AppTypography.body.copyWith(color: AppColors.rose700)),
              ],
              AppSpacing.gapVSpace4,
              if (!widget.servicio.puedeReservarSinConexion)
                const Text('Esta tienda no permite reservar sin conexión, o el teléfono aún no se preparó con conexión.',
                    style: AppTypography.caption)
              else
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    key: const Key('reservar-sin-conexion'),
                    onPressed: _guardando || _sucursal == null || _franja == null ? null : _reservar,
                    style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
                    child: Text(_guardando ? 'Guardando…' : 'Reservar'),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
