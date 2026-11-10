import 'package:flutter/material.dart';

import '../../../../core/sin_conexion/modelos_sin_conexion.dart';
import '../../../../core/sin_conexion/sin_conexion_api.dart';
import '../../../../core/sin_conexion/sin_conexion_servicio.dart';
import '../../../../core/theme/app_theme.dart';
import '../../cu14_catalogo_local/presentacion/pantalla_catalogo_sin_conexion.dart';

const Map<EstadoOperacion, String> etiquetaEstado = {
  EstadoOperacion.registradaLocalmente: 'Registrada en el teléfono',
  EstadoOperacion.enviada: 'Enviada',
  EstadoOperacion.confirmada: 'Confirmada',
  EstadoOperacion.rechazada: 'Rechazada',
  EstadoOperacion.enConflicto: 'En revisión',
};

const Map<String, String> _etiquetaConflicto = {
  'pendiente': 'Pendiente de revisión por la tienda',
  'reembolso_pendiente': 'Reembolso aceptado: se procesa al cierre del mes',
  'resuelto': 'Reembolso procesado',
};

/// P2-CU19 · Hoja «Sincronización»: estado de cada operación hecha sin conexión, sincronización
/// manual, descarga del catálogo y bandeja de avisos (decisión D1: sin notificaciones push).
class PantallaSincronizacion extends StatefulWidget {
  final SinConexionServicio? servicio;

  const PantallaSincronizacion({super.key, this.servicio});

  @override
  State<PantallaSincronizacion> createState() => _PantallaSincronizacionState();
}

class _PantallaSincronizacionState extends State<PantallaSincronizacion> {
  late final SinConexionServicio _servicio = widget.servicio ?? SinConexionServicio.instancia;
  List<AvisoDto> _avisos = const [];
  bool _cargandoAvisos = false;

  @override
  void initState() {
    super.initState();
    _cargarAvisos();
  }

  Future<void> _cargarAvisos() async {
    if (!_servicio.enLinea || !_servicio.preparado) return;
    setState(() => _cargandoAvisos = true);
    try {
      final bandeja = await _servicio.cargarAvisos();
      if (mounted) setState(() => _avisos = bandeja.avisos);
    } on SinConexionException {
      // La bandeja necesita conexión; la lista de operaciones no.
    } finally {
      if (mounted) setState(() => _cargandoAvisos = false);
    }
  }

  void _mostrar(String mensaje) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(mensaje), backgroundColor: AppColors.slate900));
  }

  Future<void> _sincronizar() async {
    if (!_servicio.enLinea) return _mostrar('Sin conexión: se enviará al recuperarla.');
    if (!_servicio.preparado) {
      return _mostrar('Este teléfono aún no está preparado. Vuelve a abrir la tienda con conexión.');
    }
    final ok = await _servicio.sincronizar();
    if (!mounted) return;
    _mostrar(ok ? 'Sincronización completada.' : 'No se pudo sincronizar. Lo intentaremos en unos minutos.');
    await _cargarAvisos();
  }

  Future<void> _descargar() async {
    try {
      await _servicio.descargarCatalogo();
      if (mounted) _mostrar(_servicio.aviso ?? 'Catálogo actualizado.');
    } on SinConexionException catch (e) {
      if (mounted) _mostrar(e.esDeRed ? 'Sin conexión: se conserva el catálogo anterior.' : e.mensaje);
    }
  }

  Future<void> _marcarLeido(AvisoDto aviso) async {
    if (aviso.leido) return;
    try {
      await _servicio.marcarAvisoLeido(aviso.idAviso);
      if (mounted) {
        setState(() => _avisos = [for (final a in _avisos) a.idAviso == aviso.idAviso ? a.marcadoLeido() : a]);
      }
    } on SinConexionException {
      // Sin red: se marcará la próxima vez.
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate50,
      appBar: AppBar(
        leading: const BackButton(),
        title: const Text('Sincronización'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.slate900,
        elevation: 0,
      ),
      body: AnimatedBuilder(
        animation: _servicio,
        builder: (context, _) {
          if (_servicio.clave == null) {
            return const Center(
              child: Padding(
                padding: AppSpacing.paddingSpace5,
                child: Text('Inicia sesión como cliente en una tienda para usarla sin conexión.',
                    textAlign: TextAlign.center, style: AppTypography.body),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: _sincronizar,
            child: ListView(
              padding: AppSpacing.paddingSpace4,
              children: [
                _tarjetaEstado(),
                AppSpacing.gapVSpace5,
                const Text('Operaciones', style: AppTypography.h3),
                AppSpacing.gapVSpace3,
                if (_servicio.operaciones.isEmpty)
                  const Text('No hay operaciones hechas sin conexión.', style: AppTypography.caption)
                else
                  for (final op in _servicio.operaciones) _tarjetaOperacion(op),
                AppSpacing.gapVSpace5,
                Row(
                  children: [
                    const Text('Avisos', style: AppTypography.h3),
                    if (_servicio.avisosNoLeidos > 0) ...[
                      AppSpacing.gapHSpace3,
                      _insignia('${_servicio.avisosNoLeidos}'),
                    ],
                  ],
                ),
                AppSpacing.gapVSpace3,
                if (!_servicio.enLinea)
                  const Text('Los avisos se consultan con conexión.', style: AppTypography.caption)
                else if (_cargandoAvisos && _avisos.isEmpty)
                  const Center(child: CircularProgressIndicator())
                else if (_avisos.isEmpty)
                  const Text('No tienes avisos.', style: AppTypography.caption)
                else
                  for (final a in _avisos) _tarjetaAviso(a),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _tarjetaEstado() {
    final guardado = _servicio.guardadoEn;
    final parametros = _servicio.dispositivo?.parametros;
    return Container(
      padding: AppSpacing.paddingCard,
      decoration: const BoxDecoration(color: AppColors.white, borderRadius: AppRadius.radiusLarge),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(child: Text('CATÁLOGO GUARDADO', style: AppTypography.labelSmall)),
              _insignia(_servicio.enLinea ? 'Con conexión' : 'Sin conexión',
                  fondo: _servicio.enLinea ? AppColors.emerald50 : AppColors.slate900,
                  color: _servicio.enLinea ? AppColors.emerald700 : AppColors.white),
            ],
          ),
          AppSpacing.gapVSpace2,
          Text(guardado == null ? 'Todavía no se descargó.' : 'Datos del ${_fecha(guardado)}', style: AppTypography.body),
          if (_servicio.dispositivo?.codigoCorto != null)
            Text('Teléfono ${_servicio.dispositivo!.codigoCorto}', style: AppTypography.caption),
          if (parametros != null && !parametros.operacionOfflineHabilitada)
            const Text('Esta tienda no permite reservar sin conexión.', style: AppTypography.caption),
          AppSpacing.gapVSpace4,
          Wrap(
            spacing: AppSpacing.space3,
            runSpacing: AppSpacing.space3,
            children: [
              if (_servicio.catalogo != null)
                OutlinedButton(
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => PantallaCatalogoSinConexion(servicio: _servicio))),
                  child: const Text('Ver catálogo'),
                ),
              OutlinedButton(
                onPressed: !_servicio.enLinea || _servicio.descargando ? null : _descargar,
                child: Text(_servicio.descargando ? 'Descargando…' : 'Actualizar catálogo'),
              ),
              FilledButton(
                onPressed: _servicio.sincronizando ? null : _sincronizar,
                style: FilledButton.styleFrom(backgroundColor: AppColors.slate900),
                child: Text(_servicio.sincronizando ? 'Sincronizando…' : 'Sincronizar'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _tarjetaOperacion(OperacionLocal op) {
    final (fondo, color) = switch (op.estado) {
      EstadoOperacion.confirmada => (AppColors.emerald50, AppColors.emerald700),
      EstadoOperacion.rechazada => (AppColors.rose50, AppColors.rose700),
      EstadoOperacion.enConflicto => (AppColors.amber50, AppColors.amber700),
      _ => (AppColors.slate100, AppColors.slate700),
    };
    final conflicto = op.estadoConflicto == null ? null : _etiquetaConflicto[op.estadoConflicto] ?? op.estadoConflicto;
    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.space3),
      padding: AppSpacing.paddingCard,
      decoration: const BoxDecoration(color: AppColors.white, borderRadius: AppRadius.radiusLarge),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(op.titulo, style: AppTypography.bodyMedium, maxLines: 1, overflow: TextOverflow.ellipsis),
                    Text(op.detalle, style: AppTypography.caption, maxLines: 2, overflow: TextOverflow.ellipsis),
                    if (op.codigoReserva != null || op.codigoProvisional != null)
                      Text(op.codigoReserva ?? op.codigoProvisional!, style: AppTypography.caption),
                  ],
                ),
              ),
              AppSpacing.gapHSpace3,
              _insignia(etiquetaEstado[op.estado]!, fondo: fondo, color: color),
            ],
          ),
          if (op.mensaje != null && op.estado != EstadoOperacion.confirmada) ...[
            AppSpacing.gapVSpace2,
            Text(op.mensaje!, style: AppTypography.body),
          ],
          if (conflicto != null) ...[
            AppSpacing.gapVSpace2,
            Text(conflicto, style: AppTypography.caption),
          ],
        ],
      ),
    );
  }

  Widget _tarjetaAviso(AvisoDto aviso) {
    return InkWell(
      onTap: () => _marcarLeido(aviso),
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.space3),
        padding: AppSpacing.paddingCard,
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: AppRadius.radiusLarge,
          border: Border.all(color: aviso.leido ? AppColors.slate100 : AppColors.slate900),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(aviso.titulo, style: AppTypography.bodyMedium),
            AppSpacing.gapVSpace2,
            Text(aviso.mensaje, style: AppTypography.body),
            if (aviso.creadoEn != null) Text(_fecha(aviso.creadoEn!), style: AppTypography.caption),
          ],
        ),
      ),
    );
  }

  Widget _insignia(String texto, {Color fondo = AppColors.slate900, Color color = AppColors.white}) =>
      _Insignia(texto: texto, fondo: fondo, color: color);

  static String _fecha(DateTime f) {
    final l = f.toLocal();
    String d(int n) => n.toString().padLeft(2, '0');
    return '${d(l.day)}/${d(l.month)}/${l.year} ${d(l.hour)}:${d(l.minute)}';
  }
}

class _Insignia extends StatelessWidget {
  final String texto;
  final Color fondo;
  final Color color;

  const _Insignia({required this.texto, required this.fondo, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space3, vertical: AppSpacing.space2),
      decoration: BoxDecoration(color: fondo, borderRadius: AppRadius.radiusMedium),
      child: Text(texto, style: AppTypography.labelSmall.copyWith(color: color)),
    );
  }
}
