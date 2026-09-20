import 'package:flutter/material.dart';
import '../bloc/recuperar_password_bloc.dart';

class PantallaRecuperarPassword extends StatefulWidget {
  final RecuperarPasswordBloc? bloc;

  const PantallaRecuperarPassword({super.key, this.bloc});

  @override
  State<PantallaRecuperarPassword> createState() => _PantallaRecuperarPasswordState();
}

class _PantallaRecuperarPasswordState extends State<PantallaRecuperarPassword> {
  late final RecuperarPasswordBloc _bloc;
  bool _propioBloc = false;

  final _formSolicitarKey = GlobalKey<FormState>();
  final _formRestablecerKey = GlobalKey<FormState>();

  final _emailController = TextEditingController();
  final _codigoController = TextEditingController();
  final _nuevaPasswordController = TextEditingController();
  final _confirmarPasswordController = TextEditingController();

  bool _mostrarNuevaPassword = false;
  bool _mostrarConfirmarPassword = false;

  @override
  void initState() {
    super.initState();
    if (widget.bloc != null) {
      _bloc = widget.bloc!;
    } else {
      _bloc = RecuperarPasswordBloc();
      _propioBloc = true;
    }

    _nuevaPasswordController.addListener(() {
      _bloc.actualizarFortalezaPassword(_nuevaPasswordController.text);
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _codigoController.dispose();
    _nuevaPasswordController.dispose();
    _confirmarPasswordController.dispose();
    if (_propioBloc) {
      _bloc.dispose();
    }
    super.dispose();
  }

  void _onSolicitarCodigo() {
    if (_formSolicitarKey.currentState?.validate() ?? false) {
      _bloc.solicitarCodigo(_emailController.text);
    }
  }

  void _onRestablecerPassword() {
    if (_formRestablecerKey.currentState?.validate() ?? false) {
      _bloc.restablecerPassword(
        codigo: _codigoController.text,
        nuevaPassword: _nuevaPasswordController.text,
        confirmarPassword: _confirmarPasswordController.text,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _bloc,
      builder: (context, _) {
        final estado = _bloc.estado;

        // Feedback de errores y éxito
        if (estado is RecuperarPasswordError) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(estado.mensaje),
                backgroundColor: const Color(0xFFDC2626),
                behavior: SnackBarBehavior.floating,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            );
          });
        } else if (estado is RestablecimientoExitoso) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(estado.mensaje),
                backgroundColor: const Color(0xFF16A34A),
                behavior: SnackBarBehavior.floating,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            );
            Navigator.of(context).pop();
          });
        }

        return Scaffold(
          backgroundColor: const Color(0xFFF9F9FB),
          body: Stack(
            children: [
              // Fondo Difuminado Suave Editorial
              Positioned.fill(
                child: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Color(0xFFF7F7F9),
                        Color(0xFFEFEFED),
                      ],
                    ),
                  ),
                ),
              ),

              // Contenido Desplazable Centrado
              SafeArea(
                child: Center(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // 1. Badge Superior Flotante FS
                        Container(
                          width: 54,
                          height: 54,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: const Color(0xFFE5E7EB),
                              width: 1,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.06),
                                blurRadius: 14,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: const Center(
                            child: Text(
                              'FS',
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontWeight: FontWeight.bold,
                                fontSize: 18,
                                color: Color(0xFF18181B),
                                letterSpacing: 1.5,
                              ),
                            ),
                          ),
                        ),

                        const SizedBox(height: 18),

                        // 2. Tarjeta Central Inmaculada
                        Container(
                          width: double.infinity,
                          constraints: const BoxConstraints(maxWidth: 420),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 30,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(28),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.08),
                                blurRadius: 28,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              // Subtítulo Editorial
                              const Text(
                                '— RESTABLECER ACCESO —',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: 2.0,
                                  color: Color(0xFF71717A),
                                ),
                              ),
                              const SizedBox(height: 6),

                              // Título FASHION STORE
                              const Text(
                                'FASHION STORE',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontFamily: 'Outfit',
                                  fontSize: 22,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 1.8,
                                  color: Color(0xFF18181B),
                                ),
                              ),
                              const SizedBox(height: 10),

                              // Texto Explicativo
                              Text(
                                _bloc.pasoActual == PasoRecuperacion.solicitar
                                    ? 'Introduce tu correo electrónico registrado para enviarte un código de verificación seguro.'
                                    : 'Introduce el código enviado a tu correo para restablecer tu contraseña y proteger tu cuenta.',
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  fontSize: 13,
                                  color: Color(0xFF52525B),
                                  height: 1.45,
                                ),
                              ),
                              const SizedBox(height: 24),

                              // Renderizado Condicional de Pasos
                              if (_bloc.pasoActual == PasoRecuperacion.solicitar)
                                _construirFormularioSolicitar()
                              else
                                _construirFormularioRestablecer(),

                              const SizedBox(height: 22),

                              // Separador con Punto Central
                              Row(
                                children: [
                                  Expanded(
                                    child: Divider(
                                      color: Colors.grey.shade200,
                                      thickness: 1,
                                    ),
                                  ),
                                  const Padding(
                                    padding: EdgeInsets.symmetric(horizontal: 10),
                                    child: Text(
                                      '•',
                                      style: TextStyle(
                                        color: Color(0xFFD4D4D8),
                                        fontSize: 14,
                                      ),
                                    ),
                                  ),
                                  Expanded(
                                    child: Divider(
                                      color: Colors.grey.shade200,
                                      thickness: 1,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),

                              // Enlace Regresar a Iniciar sesión
                              Center(
                                child: GestureDetector(
                                  onTap: () => Navigator.of(context).pop(),
                                  child: Text.rich(
                                    const TextSpan(
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Color(0xFF71717A),
                                      ),
                                      children: [
                                        TextSpan(text: 'regresar a '),
                                        TextSpan(
                                          text: 'Iniciar sesión',
                                          style: TextStyle(
                                            fontWeight: FontWeight.w600,
                                            color: Color(0xFF18181B),
                                            decoration: TextDecoration.underline,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 22),

                        // 3. Icono de Escudo de Seguridad Inferior
                        const Icon(
                          Icons.shield_outlined,
                          size: 16,
                          color: Color(0xFF9CA3AF),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _construirFormularioSolicitar() {
    return Form(
      key: _formSolicitarKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'CORREO ELECTRÓNICO',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.6,
              color: Color(0xFF27272A),
            ),
          ),
          const SizedBox(height: 6),
          TextFormField(
            key: const Key('recuperar_email_field'),
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            style: const TextStyle(fontSize: 14, color: Color(0xFF18181B)),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Ingresa tu correo electrónico';
              }
              if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim())) {
                return 'Ingresa un formato de correo válido';
              }
              return null;
            },
            decoration: _construirInputDecoration(
              hintText: 'nombre@ejemplo.com',
              prefixIcon: const Icon(Icons.alternate_email, size: 18, color: Color(0xFF71717A)),
            ),
          ),
          const SizedBox(height: 20),
          _construirBotonAccion(
            texto: 'ENVIAR CÓDIGO →',
            onPressed: _onSolicitarCodigo,
          ),
        ],
      ),
    );
  }

  Widget _construirFormularioRestablecer() {
    return Form(
      key: _formRestablecerKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Campo 1: CÓDIGO DE VERIFICACIÓN (6 DÍGITOS) con enlace REENVIAR
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Flexible(
                child: Text(
                  'CÓDIGO DE VERIFICACIÓN (6 DÍGITOS)',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                    color: Color(0xFF27272A),
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              _bloc.segundosCooldown > 0
                  ? Text(
                      'REENVIAR (${_bloc.segundosCooldown}s)',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                        color: Color(0xFFA1A1AA),
                      ),
                    )
                  : GestureDetector(
                      onTap: _bloc.estaCargando ? null : () => _bloc.reenviarCodigo(),
                      child: const Text(
                        'REENVIAR',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.5,
                          color: Color(0xFF18181B),
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ),
            ],
          ),
          const SizedBox(height: 6),
          TextFormField(
            key: const Key('recuperar_codigo_field'),
            controller: _codigoController,
            keyboardType: TextInputType.number,
            maxLength: 8,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Color(0xFF18181B),
              letterSpacing: 2.0,
            ),
            validator: (value) {
              final v = (value ?? '').replaceAll(' ', '').trim();
              if (v.length != 6) {
                return 'Ingresa los 6 dígitos del código';
              }
              return null;
            },
            decoration: _construirInputDecoration(
              hintText: 'ej. 849 201',
              counterText: '',
              prefixIcon: const Icon(Icons.pin_outlined, size: 18, color: Color(0xFF71717A)),
            ),
          ),
          const SizedBox(height: 14),

          // Campo 2: NUEVA CONTRASEÑA
          const Text(
            'NUEVA CONTRASEÑA',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.6,
              color: Color(0xFF27272A),
            ),
          ),
          const SizedBox(height: 6),
          TextFormField(
            key: const Key('recuperar_nueva_password_field'),
            controller: _nuevaPasswordController,
            obscureText: !_mostrarNuevaPassword,
            style: const TextStyle(fontSize: 14, color: Color(0xFF18181B)),
            validator: (value) {
              if (value == null || value.length < 8) {
                return 'Mínimo 8 caracteres (A-Z, 0-9)';
              }
              return null;
            },
            decoration: _construirInputDecoration(
              hintText: 'Mínimo 8 caracteres',
              prefixIcon: const Icon(Icons.lock_outline, size: 18, color: Color(0xFF71717A)),
              suffixIcon: IconButton(
                icon: Icon(
                  _mostrarNuevaPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                  size: 20,
                  color: const Color(0xFF71717A),
                ),
                onPressed: () {
                  setState(() {
                    _mostrarNuevaPassword = !_mostrarNuevaPassword;
                  });
                },
              ),
            ),
          ),
          const SizedBox(height: 6),

          // Medidor de Fortaleza en 3 Barras Horizontales
          Row(
            children: [
              _construirBarraFortaleza(segmento: 1),
              const SizedBox(width: 4),
              _construirBarraFortaleza(segmento: 2),
              const SizedBox(width: 4),
              _construirBarraFortaleza(segmento: 3),
            ],
          ),
          const SizedBox(height: 14),

          // Campo 3: CONFIRMAR CONTRASEÑA
          const Text(
            'CONFIRMAR CONTRASEÑA',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.6,
              color: Color(0xFF27272A),
            ),
          ),
          const SizedBox(height: 6),
          TextFormField(
            key: const Key('recuperar_confirmar_password_field'),
            controller: _confirmarPasswordController,
            obscureText: !_mostrarConfirmarPassword,
            style: const TextStyle(fontSize: 14, color: Color(0xFF18181B)),
            validator: (value) {
              if (value != _nuevaPasswordController.text) {
                return 'Las contraseñas no coinciden';
              }
              return null;
            },
            decoration: _construirInputDecoration(
              hintText: 'Repite tu contraseña',
              prefixIcon: const Icon(Icons.lock_outline, size: 18, color: Color(0xFF71717A)),
              suffixIcon: IconButton(
                icon: Icon(
                  _mostrarConfirmarPassword
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  size: 20,
                  color: const Color(0xFF71717A),
                ),
                onPressed: () {
                  setState(() {
                    _mostrarConfirmarPassword = !_mostrarConfirmarPassword;
                  });
                },
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Botón ACTUALIZAR Y ACCEDER →
          _construirBotonAccion(
            texto: 'ACTUALIZAR Y ACCEDER →',
            onPressed: _onRestablecerPassword,
          ),
        ],
      ),
    );
  }

  Widget _construirBarraFortaleza({required int segmento}) {
    final fortaleza = _bloc.nivelFortaleza;
    Color colorBarra = const Color(0xFFE4E4E7);

    if (segmento == 1) {
      if (fortaleza == 1) colorBarra = const Color(0xFFEF4444);
      if (fortaleza == 2) colorBarra = const Color(0xFFF59E0B);
      if (fortaleza >= 3) colorBarra = const Color(0xFF10B981);
    } else if (segmento == 2) {
      if (fortaleza == 2) colorBarra = const Color(0xFFF59E0B);
      if (fortaleza >= 3) colorBarra = const Color(0xFF10B981);
    } else if (segmento == 3) {
      if (fortaleza >= 3) colorBarra = const Color(0xFF10B981);
    }

    return Expanded(
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        height: 3.5,
        decoration: BoxDecoration(
          color: colorBarra,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }

  InputDecoration _construirInputDecoration({
    required String hintText,
    String? counterText,
    Widget? prefixIcon,
    Widget? suffixIcon,
  }) {
    return InputDecoration(
      hintText: hintText,
      hintStyle: const TextStyle(fontSize: 13, color: Color(0xFFA1A1AA)),
      counterText: counterText,
      prefixIcon: prefixIcon,
      suffixIcon: suffixIcon,
      filled: true,
      fillColor: const Color(0xFFF4F4F5),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: Color(0xFFF4F4F5)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: Color(0xFF18181B), width: 1.2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: Color(0xFFEF4444), width: 1),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: Color(0xFFDC2626), width: 1.2),
      ),
    );
  }

  Widget _construirBotonAccion({
    required String texto,
    required VoidCallback onPressed,
  }) {
    return SizedBox(
      height: 48,
      child: ElevatedButton(
        key: const Key('recuperar_boton_submit'),
        onPressed: _bloc.estaCargando ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF09090B),
          foregroundColor: Colors.white,
          disabledBackgroundColor: const Color(0xFFA1A1AA),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
        ),
        child: _bloc.estaCargando
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(
                texto,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                ),
              ),
      ),
    );
  }
}
