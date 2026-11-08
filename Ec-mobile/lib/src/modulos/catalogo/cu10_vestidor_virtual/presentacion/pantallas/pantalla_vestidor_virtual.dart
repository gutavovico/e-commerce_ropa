import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../dominio/plataforma_vestidor.dart';
import '../../dominio/prenda_vestidor.dart';
import '../bloc/vestidor_bloc.dart';
import '../widgets/motor_local_camara.dart';
import '../widgets/motor_realista_webview.dart';

typedef ConstructorMotorLocal = Widget Function(
  BuildContext context,
  VestidorBloc bloc, {
  required double escala,
  required double desplazamientoVertical,
});

typedef ConstructorMotorRealista = Widget Function(
  BuildContext context,
  VestidorBloc bloc,
  DatosSesionRealista datos,
);

/// CU10 · Vestidor virtual. Pantalla hoja (Hub-and-Spoke): `BackButton`, sin navegación principal
/// y con barra de acción inferior. Devuelve [ResultadoVestidor] a la ficha de producto.
class PantallaVestidorVirtual extends StatefulWidget {
  final String token;
  final PrendaVestidor prenda;
  final VestidorBloc? bloc;

  /// Sustituibles en pruebas (cámara, ML Kit y WebView necesitan dispositivo real).
  final ConstructorMotorLocal? constructorMotorLocal;
  final ConstructorMotorRealista? constructorMotorRealista;

  const PantallaVestidorVirtual({
    super.key,
    required this.token,
    required this.prenda,
    this.bloc,
    this.constructorMotorLocal,
    this.constructorMotorRealista,
  });

  @override
  State<PantallaVestidorVirtual> createState() => _PantallaVestidorVirtualState();
}

class _PantallaVestidorVirtualState extends State<PantallaVestidorVirtual> {
  late final VestidorBloc _bloc;
  late final bool _blocPropio;
  double _escala = 1.0;
  double _desplazamiento = 0;

  @override
  void initState() {
    super.initState();
    _blocPropio = widget.bloc == null;
    _bloc = widget.bloc ?? VestidorBloc(prenda: widget.prenda, token: widget.token);
    _bloc.addListener(_alCambiar);
    _bloc.iniciar();
  }

  void _alCambiar() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    // Salir sin comprar también es una prueba: se registra (una sola vez) al cerrar.
    unawaited(_bloc.registrarSesion());
    _bloc.removeListener(_alCambiar);
    if (_blocPropio) _bloc.dispose();
    super.dispose();
  }

  Future<void> _anadirABolsa() async {
    await _bloc.registrarSesion(generoInteres: true);
    if (mounted) Navigator.of(context).pop(ResultadoVestidor.anadirABolsa);
  }

  @override
  Widget build(BuildContext context) {
    final estado = _bloc.estado;
    return Scaffold(
      backgroundColor: AppColors.black,
      appBar: AppBar(
        leading: const BackButton(),
        backgroundColor: AppColors.black,
        foregroundColor: AppColors.white,
        title: Text('VESTIDOR VIRTUAL', style: AppTypography.labelSmall.copyWith(color: AppColors.white)),
        actions: [
          Padding(
            padding: AppSpacing.paddingHorizontalSpace4,
            child: Center(
              child: Text(
                '${_bloc.segundosSesion}s',
                style: AppTypography.caption.copyWith(color: AppColors.slate300),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Stack(
              fit: StackFit.expand,
              children: [
                _construirMotor(estado),
                Positioned(
                  top: AppSpacing.space3,
                  left: AppSpacing.space3,
                  right: AppSpacing.space3,
                  child: _EtiquetaMotor(estado: estado),
                ),
              ],
            ),
          ),
          _construirPanel(estado),
        ],
      ),
      bottomNavigationBar: _construirBarraAccion(estado),
    );
  }

  Widget _construirMotor(EstadoVestidor estado) {
    // Sin motores sustitutos (pruebas), cámara/ML Kit/WebView solo existen en Android e iOS.
    final motoresReales = widget.constructorMotorLocal == null || widget.constructorMotorRealista == null;
    if (motoresReales && !vestidorSoportadoEnPlataforma()) {
      return Center(
        child: Padding(
          padding: AppSpacing.paddingSpace5,
          child: Text(
            mensajeVestidorNoSoportado,
            textAlign: TextAlign.center,
            style: AppTypography.body.copyWith(color: AppColors.slate200),
          ),
        ),
      );
    }
    switch (estado) {
      case VestidorMotorLocal():
      case VestidorPreparandoRealista():
        final local = (widget.constructorMotorLocal ?? _motorLocalPorDefecto)(
          context,
          _bloc,
          escala: _escala,
          desplazamientoVertical: _desplazamiento,
        );
        if (estado is VestidorMotorLocal) return local;
        return Stack(fit: StackFit.expand, children: [local, const _Cargando(texto: 'Preparando el modo realista…')]);
      case VestidorConectandoRealista(:final datos):
        return Stack(
          fit: StackFit.expand,
          children: [_motorRealista(datos), const _Cargando(texto: 'Conectando con Decart Lucy VTON…')],
        );
      case VestidorRealistaEnCurso(:final datos):
        // Mismo árbol que «conectando» para conservar el WebView y su sesión.
        return Stack(fit: StackFit.expand, children: [_motorRealista(datos)]);
    }
  }

  Widget _motorRealista(DatosSesionRealista datos) => KeyedSubtree(
        key: ObjectKey(datos),
        child: (widget.constructorMotorRealista ?? _motorRealistaPorDefecto)(context, _bloc, datos),
      );

  static Widget _motorLocalPorDefecto(
    BuildContext context,
    VestidorBloc bloc, {
    required double escala,
    required double desplazamientoVertical,
  }) =>
      MotorLocalCamara(urlPrenda: bloc.urlRecursoPrenda, escala: escala, desplazamientoVertical: desplazamientoVertical);

  static Widget _motorRealistaPorDefecto(BuildContext context, VestidorBloc bloc, DatosSesionRealista datos) =>
      MotorRealistaWebView(
        datos: datos,
        alEvento: bloc.procesarEventoRealista,
        solicitarToken: bloc.solicitarTokenAdicional,
      );

  Widget _construirPanel(EstadoVestidor estado) {
    final error = _bloc.errorFallback;
    final aviso = _bloc.aviso;
    final prenda = widget.prenda;
    final detalle = [prenda.tallaCodigo, prenda.colorNombre].whereType<String>().join(' · ');

    return Container(
      width: double.infinity,
      color: AppColors.primaryDark,
      padding: AppSpacing.paddingSpace4,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            prenda.nombre,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: AppTypography.bodyMedium.copyWith(color: AppColors.white),
          ),
          if (detalle.isNotEmpty)
            Text(detalle, style: AppTypography.caption.copyWith(color: AppColors.slate400)),
          if (error != null) ...[
            AppSpacing.gapVSpace3,
            _Banner(texto: error, color: AppColors.amber600),
          ],
          if (aviso != null) ...[
            AppSpacing.gapVSpace3,
            _Banner(texto: aviso, color: AppColors.slate500),
          ],
          if (estado is VestidorMotorLocal) ...[
            AppSpacing.gapVSpace3,
            _Deslizador(
              etiqueta: 'TAMAÑO',
              valor: _escala,
              min: 0.7,
              max: 1.5,
              alCambiar: (v) => setState(() => _escala = v),
            ),
            _Deslizador(
              etiqueta: 'ALTURA',
              valor: _desplazamiento,
              min: -AppSpacing.space7,
              max: AppSpacing.space7,
              alCambiar: (v) => setState(() => _desplazamiento = v),
            ),
          ],
        ],
      ),
    );
  }

  Widget _construirBarraAccion(EstadoVestidor estado) {
    final enLocal = estado is VestidorMotorLocal;
    final ocupado = estado is VestidorPreparandoRealista;
    return SafeArea(
      top: false,
      child: Container(
        color: AppColors.primaryDark,
        padding: AppSpacing.paddingSpace3,
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: ocupado ? null : (enLocal ? _bloc.activarModoRealista : _bloc.volverAMotorLocal),
                icon: Icon(enLocal ? Icons.auto_awesome : Icons.videocam_outlined, size: AppSpacing.space4),
                label: Text(
                  enLocal ? 'MODO REALISTA IA' : 'MOTOR LOCAL',
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.button.copyWith(color: AppColors.white),
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.white,
                  side: const BorderSide(color: AppColors.secondary500),
                  padding: AppSpacing.paddingVerticalSpace3,
                ),
              ),
            ),
            AppSpacing.gapHSpace3,
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _anadirABolsa,
                icon: const Icon(Icons.shopping_bag_outlined, size: AppSpacing.space4),
                label: Text(
                  'AÑADIR A LA BOLSA',
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.button.copyWith(color: AppColors.black),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.white,
                  foregroundColor: AppColors.black,
                  padding: AppSpacing.paddingVerticalSpace3,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EtiquetaMotor extends StatelessWidget {
  final EstadoVestidor estado;
  const _EtiquetaMotor({required this.estado});

  @override
  Widget build(BuildContext context) {
    final texto = switch (estado) {
      VestidorRealistaEnCurso(:final segundosRestantes) => 'MOTOR 2 · DECART LUCY VTON · ${segundosRestantes}s',
      VestidorConectandoRealista() || VestidorPreparandoRealista() => 'MOTOR 2 · CONECTANDO',
      VestidorMotorLocal() => 'MOTOR 1 · LOCAL EN EL DISPOSITIVO',
    };
    final realista = estado is! VestidorMotorLocal;
    return Align(
      alignment: Alignment.topLeft,
      child: Container(
        padding: AppSpacing.paddingSpace2,
        decoration: BoxDecoration(
          color: AppColors.black.withValues(alpha: 0.7),
          borderRadius: AppRadius.radiusSmall,
          border: Border.all(color: realista ? AppColors.secondary500 : AppColors.emerald600),
        ),
        child: Text(texto, style: AppTypography.tag.copyWith(color: AppColors.white)),
      ),
    );
  }
}

class _Cargando extends StatelessWidget {
  final String texto;
  const _Cargando({required this.texto});

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: AppColors.black.withValues(alpha: 0.75),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: AppColors.secondary500),
            AppSpacing.gapVSpace4,
            Text(texto, style: AppTypography.caption.copyWith(color: AppColors.white)),
          ],
        ),
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  final String texto;
  final Color color;
  const _Banner({required this.texto, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: AppSpacing.paddingSpace3,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        border: Border.all(color: color),
        borderRadius: AppRadius.radiusSmall,
      ),
      child: Text(texto, style: AppTypography.caption.copyWith(color: AppColors.white)),
    );
  }
}

class _Deslizador extends StatelessWidget {
  final String etiqueta;
  final double valor;
  final double min;
  final double max;
  final ValueChanged<double> alCambiar;

  const _Deslizador({
    required this.etiqueta,
    required this.valor,
    required this.min,
    required this.max,
    required this.alCambiar,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: AppSpacing.space7,
          child: Text(etiqueta, style: AppTypography.tag.copyWith(color: AppColors.slate400)),
        ),
        Expanded(
          child: Slider(
            value: valor.clamp(min, max),
            min: min,
            max: max,
            activeColor: AppColors.secondary500,
            onChanged: alCambiar,
          ),
        ),
      ],
    );
  }
}
