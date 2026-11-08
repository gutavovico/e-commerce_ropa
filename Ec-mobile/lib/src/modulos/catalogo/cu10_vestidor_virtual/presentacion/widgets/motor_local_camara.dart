import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../dominio/ajuste_prenda.dart';

/// Motor 1 (CU10): cámara frontal en directo + ML Kit Pose Detection en el dispositivo. La prenda
/// (PNG transparente de `modelo_ar_url`) se coloca, escala y gira sobre la línea de hombros. Ningún
/// fotograma sale del teléfono.
class MotorLocalCamara extends StatefulWidget {
  /// URL absoluta del PNG transparente de la prenda.
  final String? urlPrenda;

  /// Ajuste fino del cliente sobre el seguimiento automático.
  final double escala;
  final double desplazamientoVertical;

  const MotorLocalCamara({
    super.key,
    required this.urlPrenda,
    this.escala = 1.0,
    this.desplazamientoVertical = 0,
  });

  @override
  State<MotorLocalCamara> createState() => _MotorLocalCamaraState();
}

/// Fotogramas seguidos sin hombros fiables antes de dar a la persona por fuera de cuadro.
const int _fotogramasSinCuerpoTolerados = 15;

// `defaultTargetPlatform` y no `dart:io` `Platform`, que lanza «Unsupported operation» en web.
bool get _esAndroid => defaultTargetPlatform == TargetPlatform.android;
bool get _esIOS => defaultTargetPlatform == TargetPlatform.iOS;

const Map<DeviceOrientation, int> _orientaciones = {
  DeviceOrientation.portraitUp: 0,
  DeviceOrientation.landscapeLeft: 90,
  DeviceOrientation.portraitDown: 180,
  DeviceOrientation.landscapeRight: 270,
};

class _MotorLocalCamaraState extends State<MotorLocalCamara> with WidgetsBindingObserver {
  final PoseDetector _detector = PoseDetector(
    options: PoseDetectorOptions(mode: PoseDetectionMode.stream, model: PoseDetectionModel.base),
  );
  final SuavizadorAjuste _suavizador = SuavizadorAjuste();

  CameraController? _camara;
  CameraDescription? _descripcion;
  AjustePrenda? _ajuste;
  Size? _tamanoLienzo;
  String? _error;
  bool _procesando = false;
  int _fotogramasSinCuerpo = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _iniciarCamara();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState estado) {
    // La cámara es un recurso exclusivo: se libera en segundo plano y se recupera al volver.
    if (estado == AppLifecycleState.inactive) {
      _liberarCamara();
    } else if (estado == AppLifecycleState.resumed && _camara == null) {
      _iniciarCamara();
    }
  }

  Future<void> _iniciarCamara() async {
    setState(() => _error = null);
    try {
      final camaras = await availableCameras();
      if (camaras.isEmpty) {
        _mostrarError('No se encontró ninguna cámara en este dispositivo.');
        return;
      }
      final descripcion = camaras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => camaras.first,
      );
      final controlador = CameraController(
        descripcion,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: _esAndroid ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
      );
      await controlador.initialize();
      if (!mounted) {
        await controlador.dispose();
        return;
      }
      await controlador.startImageStream(_procesarFotograma);
      setState(() {
        _camara = controlador;
        _descripcion = descripcion;
      });
    } on CameraException catch (e) {
      _mostrarError(_describirErrorCamara(e.code));
    } catch (e) {
      _mostrarError('No se pudo abrir la cámara: $e');
    }
  }

  String _describirErrorCamara(String codigo) {
    switch (codigo) {
      case 'CameraAccessDenied':
      case 'CameraAccessDeniedWithoutPrompt':
      case 'CameraAccessRestricted':
        return 'Permiso de cámara denegado. Actívelo en los ajustes del teléfono para FASHION STORE y pulse «Reintentar».';
      default:
        return 'No se pudo abrir la cámara ($codigo). Cierre otras apps que la estén usando y pulse «Reintentar».';
    }
  }

  void _mostrarError(String mensaje) {
    if (!mounted) return;
    setState(() => _error = mensaje);
  }

  Future<void> _liberarCamara() async {
    final controlador = _camara;
    _camara = null;
    if (controlador == null) return;
    try {
      if (controlador.value.isStreamingImages) await controlador.stopImageStream();
    } catch (_) {
      // Ya detenida.
    }
    await controlador.dispose();
  }

  Future<void> _procesarFotograma(CameraImage imagen) async {
    final lienzo = _tamanoLienzo;
    if (_procesando || lienzo == null) return;
    _procesando = true;
    try {
      final entrada = _construirEntrada(imagen);
      if (entrada == null) return;
      final poses = await _detector.processImage(entrada);
      if (!mounted) return;
      _actualizarAjuste(poses, entrada.metadata!, lienzo);
    } catch (e) {
      debugPrint('[VESTIDOR] Fallo de ML Kit en un fotograma: $e');
    } finally {
      _procesando = false;
    }
  }

  /// Conversión `CameraImage` → `InputImage` del ejemplo oficial de `google_mlkit`.
  InputImage? _construirEntrada(CameraImage imagen) {
    final controlador = _camara;
    final descripcion = _descripcion;
    if (controlador == null || descripcion == null) return null;

    final orientacionSensor = descripcion.sensorOrientation;
    InputImageRotation? rotacion;
    if (_esIOS) {
      rotacion = InputImageRotationValue.fromRawValue(orientacionSensor);
    } else {
      var compensacion = _orientaciones[controlador.value.deviceOrientation];
      if (compensacion == null) return null;
      compensacion = descripcion.lensDirection == CameraLensDirection.front
          ? (orientacionSensor + compensacion) % 360
          : (orientacionSensor - compensacion + 360) % 360;
      rotacion = InputImageRotationValue.fromRawValue(compensacion);
    }
    if (rotacion == null) return null;

    final formato = InputImageFormatValue.fromRawValue(imagen.format.raw);
    if (formato == null ||
        (_esAndroid && formato != InputImageFormat.nv21) ||
        (_esIOS && formato != InputImageFormat.bgra8888)) {
      return null;
    }
    if (imagen.planes.length != 1) return null;
    final plano = imagen.planes.first;

    return InputImage.fromBytes(
      bytes: plano.bytes,
      metadata: InputImageMetadata(
        size: Size(imagen.width.toDouble(), imagen.height.toDouble()),
        rotation: rotacion,
        format: formato,
        bytesPerRow: plano.bytesPerRow,
      ),
    );
  }

  void _actualizarAjuste(List<Pose> poses, InputImageMetadata metadata, Size lienzo) {
    AjustePrenda? calculado;
    if (poses.isNotEmpty) {
      PuntoCorporal? punto(PoseLandmarkType tipo) {
        final marca = poses.first.landmarks[tipo];
        if (marca == null) return null;
        return PuntoCorporal(
          traducirPunto(
            marca.x,
            marca.y,
            tamanoImagen: metadata.size,
            tamanoLienzo: lienzo,
            rotacionGrados: metadata.rotation.rawValue,
            camaraFrontal: _descripcion?.lensDirection == CameraLensDirection.front,
            esIOS: _esIOS,
          ),
          marca.likelihood,
        );
      }

      final izquierdo = punto(PoseLandmarkType.leftShoulder);
      final derecho = punto(PoseLandmarkType.rightShoulder);
      if (izquierdo != null && derecho != null) {
        calculado = calcularAjustePrenda(PuntosTorso(hombroIzquierdo: izquierdo, hombroDerecho: derecho));
      }
    }

    if (calculado == null) {
      _fotogramasSinCuerpo++;
      if (_fotogramasSinCuerpo == _fotogramasSinCuerpoTolerados) {
        _suavizador.reiniciar();
        setState(() => _ajuste = null);
      }
      return;
    }
    _fotogramasSinCuerpo = 0;
    setState(() => _ajuste = _suavizador.suavizar(calculado!));
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _liberarCamara();
    _detector.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final error = _error;
    if (error != null) return _PanelErrorCamara(mensaje: error, alReintentar: _iniciarCamara);

    final controlador = _camara;
    if (controlador == null || !controlador.value.isInitialized) {
      return const Center(child: CircularProgressIndicator(color: AppColors.secondary500));
    }

    return Center(
      child: CameraPreview(
        controlador,
        child: LayoutBuilder(
          builder: (context, restricciones) {
            _tamanoLienzo = restricciones.biggest;
            return Stack(
              clipBehavior: Clip.hardEdge,
              children: [
                if (widget.urlPrenda != null) _construirPrenda(widget.urlPrenda!, restricciones.biggest),
                if (_ajuste == null)
                  const Positioned(
                    left: AppSpacing.space4,
                    right: AppSpacing.space4,
                    bottom: AppSpacing.space4,
                    child: _Indicacion(texto: 'Colóquese de frente con los hombros visibles para ajustar la prenda.'),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _construirPrenda(String url, Size lienzo) {
    final ajuste = _ajuste;
    // Sin cuerpo detectado, la prenda espera centrada en la parte superior del encuadre.
    final ancho = (ajuste?.ancho ?? lienzo.width * 0.7) * widget.escala;
    final centro = ajuste?.centroHombros ?? Offset(lienzo.width / 2, lienzo.height * 0.28);
    return Positioned(
      left: centro.dx - ancho / 2,
      top: centro.dy - ancho * desfaseCuelloPrenda + widget.desplazamientoVertical,
      width: ancho,
      child: Transform.rotate(
        angle: ajuste?.rotacion ?? 0,
        alignment: Alignment.topCenter,
        child: Opacity(
          opacity: ajuste == null ? 0.55 : 0.95,
          child: Image.network(
            url,
            fit: BoxFit.contain,
            errorBuilder: (context, error, stack) =>
                const _Indicacion(texto: 'No se pudo cargar la imagen de la prenda.'),
          ),
        ),
      ),
    );
  }
}

class _Indicacion extends StatelessWidget {
  final String texto;
  const _Indicacion({required this.texto});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: AppSpacing.paddingSpace3,
      decoration: BoxDecoration(
        color: AppColors.black.withValues(alpha: 0.7),
        borderRadius: AppRadius.radiusSmall,
      ),
      child: Text(
        texto,
        textAlign: TextAlign.center,
        style: AppTypography.caption.copyWith(color: AppColors.white),
      ),
    );
  }
}

class _PanelErrorCamara extends StatelessWidget {
  final String mensaje;
  final VoidCallback alReintentar;
  const _PanelErrorCamara({required this.mensaje, required this.alReintentar});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: AppSpacing.paddingSpace5,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.no_photography_outlined, color: AppColors.slate400, size: AppSpacing.space6),
            AppSpacing.gapVSpace3,
            Text(
              mensaje,
              textAlign: TextAlign.center,
              style: AppTypography.body.copyWith(color: AppColors.slate200),
            ),
            AppSpacing.gapVSpace4,
            OutlinedButton(
              onPressed: alReintentar,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.white,
                side: const BorderSide(color: AppColors.slate500),
              ),
              child: Text('REINTENTAR', style: AppTypography.button.copyWith(color: AppColors.white)),
            ),
          ],
        ),
      ),
    );
  }
}
