import 'package:flutter/material.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import '../../datos/modelos/registro_dto.dart';
import '../bloc/registro_bloc.dart';

class PantallaRegistro extends StatefulWidget {
  final VoidCallback? alCompletarRegistro;

  const PantallaRegistro({super.key, this.alCompletarRegistro});

  @override
  State<PantallaRegistro> createState() => _PantallaRegistroState();
}

class _PantallaRegistroState extends State<PantallaRegistro> {
  final _formKey = GlobalKey<FormState>();
  late final RegistroBloc _bloc;

  final _nombreCompletoController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _mostrarPassword = false;
  bool _aceptaTerminos = false;
  bool _deseaNotificaciones = false;
  int _nivelFortaleza = 0;
  String _etiquetaFortaleza = 'Mín. 8 caracteres';

  // Paleta de Alta Costura (White Luxury)
  static const Color _colorFondo = Colors.white;
  static const Color _colorCampoFondo = Color(0xFFF5F5F5);
  static const Color _colorCampoBorde = Color(0xFFE8E8E8);
  static const Color _colorTextoPrincipal = Color(0xFF111111);
  static const Color _colorTextoSecundario = Color(0xFF737373);
  static const Color _colorNegroObsidian = Color(0xFF000000);

  @override
  void initState() {
    super.initState();
    _bloc = RegistroBloc();
    _bloc.addListener(_alCambiarEstado);

    _passwordController.addListener(_evaluarPassword);
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    _passwordController.removeListener(_evaluarPassword);
    _bloc.dispose();
    _nombreCompletoController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _evaluarPassword() {
    final password = _passwordController.text;
    if (password.isEmpty) {
      setState(() {
        _nivelFortaleza = 0;
        _etiquetaFortaleza = 'Mín. 8 caracteres';
      });
      return;
    }

    int puntuacion = 0;
    if (password.length >= 8) puntuacion++;
    if (RegExp(r'[A-Z]').hasMatch(password) && RegExp(r'[a-z]').hasMatch(password)) puntuacion++;
    if (RegExp(r'[0-9]').hasMatch(password)) puntuacion++;
    if (RegExp(r'[^A-Za-z0-9]').hasMatch(password) || password.length >= 12) puntuacion++;

    puntuacion = puntuacion.clamp(1, 4);

    String texto;
    switch (puntuacion) {
      case 1:
        texto = '1/4 DÉBIL';
        break;
      case 2:
        texto = '2/4 MEDIA';
        break;
      case 3:
        texto = '3/4 ROBUSTA';
        break;
      case 4:
        texto = '4/4 EXCELENTE';
        break;
      default:
        texto = 'Mín. 8 caracteres';
    }

    setState(() {
      _nivelFortaleza = puntuacion;
      _etiquetaFortaleza = texto;
    });
  }

  void _alCambiarEstado() {
    final estado = _bloc.estado;
    if (estado is RegistroExitoso) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('¡Cuenta creada con éxito! Bienvenido a FashionStore.'),
          backgroundColor: Color(0xFF1B4D25),
        ),
      );
      if (widget.alCompletarRegistro != null) {
        widget.alCompletarRegistro!();
      } else if (Navigator.canPop(context)) {
        Navigator.pop(context);
      }
    }
  }

  void _enviarFormulario() {
    if (!_aceptaTerminos) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Debes aceptar los Términos de Servicio y la Política de Privacidad.'),
          backgroundColor: Color(0xFF8B1E22),
        ),
      );
      return;
    }

    if (_formKey.currentState?.validate() ?? false) {
      final nombreLimpio = _nombreCompletoController.text.trim();
      final partes = nombreLimpio.split(RegExp(r'\s+'));
      final nombres = partes.isNotEmpty ? partes[0] : 'Cliente';
      final apellidos = partes.length > 1 ? partes.sublist(1).join(' ') : 'FashionStore';

      final dto = RegistroClienteDto(
        nombres: nombres,
        apellidos: apellidos,
        email: _emailController.text.trim().toLowerCase(),
        password: _passwordController.text,
        telefono: null,
        tallaPreferida: null,
      );
      _bloc.registrarCliente(dto);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _colorFondo,
      body: SafeArea(
        child: AnimatedBuilder(
          animation: _bloc,
          builder: (context, _) {
            final estaCargando = _bloc.estaCargando;
            final estado = _bloc.estado;

            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // =================================================================
                    // 1. TARJETA HERO SUPERIOR (FOTOGRAFÍA BOUTIQUE & TITULAR)
                    // =================================================================
                    ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Stack(
                        children: [
                          // Imagen de fondo ambiental
                          Image.asset(
                            'assets/atelier_bg.jpg',
                            height: 180,
                            width: double.infinity,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                height: 180,
                                color: const Color(0xFF1B1B1B),
                              );
                            },
                          ),

                          // Overlay degradado de alto contraste
                          Positioned.fill(
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  begin: Alignment.topCenter,
                                  end: Alignment.bottomCenter,
                                  colors: [
                                    Colors.black.withValues(alpha: 0.2),
                                    Colors.black.withValues(alpha: 0.85),
                                  ],
                                ),
                              ),
                            ),
                          ),

                          // Badge circular translúcido con candado
                          Positioned(
                            top: 14,
                            left: 14,
                            child: Container(
                              width: 32,
                              height: 32,
                              decoration: BoxDecoration(
                                color: Colors.black.withValues(alpha: 0.45),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.lock_outline,
                                color: Colors.white,
                                size: 16,
                              ),
                            ),
                          ),

                          // Textos sobre la tarjeta
                          Positioned(
                            bottom: 16,
                            left: 16,
                            right: 16,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: const [
                                Text(
                                  'REGISTRO PRIVADO',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                    letterSpacing: 2.0,
                                  ),
                                ),
                                SizedBox(height: 4),
                                Text(
                                  '«La pureza del corte. El lujo del tiempo.»',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 17,
                                    fontWeight: FontWeight.w300,
                                    letterSpacing: 0.4,
                                    height: 1.25,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // =================================================================
                    // 2. ENCABEZADO DE MARCA FASHION STORE
                    // =================================================================
                    Column(
                      children: const [
                        Text(
                          'BIENVENIDO A',
                          style: TextStyle(
                            color: _colorTextoSecundario,
                            fontSize: 11,
                            letterSpacing: 3.0,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'FASHION STORE',
                          style: TextStyle(
                            color: _colorTextoPrincipal,
                            fontSize: 24,
                            letterSpacing: 4.5,
                            fontWeight: FontWeight.w300,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'HAUTE COUTURE & READY-TO-WEAR • REGISTRO',
                          style: TextStyle(
                            color: _colorTextoSecundario,
                            fontSize: 9,
                            letterSpacing: 1.8,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // Banner de error si falló la llamada
                    if (estado is RegistroFallido) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFDE8E8),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: const Color(0xFFF8B4B4)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline,
                                color: Color(0xFFC81E1E), size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                estado.mensaje,
                                style: const TextStyle(
                                  color: Color(0xFF9B1C1C),
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // =================================================================
                    // 3. FORMULARIO FIEL AL DISEÑO
                    // =================================================================

                    // Nombre Completo
                    _construirEtiqueta('NOMBRE COMPLETO'),
                    TextFormField(
                      controller: _nombreCompletoController,
                      style: const TextStyle(color: _colorTextoPrincipal, fontSize: 14),
                      decoration: _decoracionCampo(
                        hint: 'Camille Laurent',
                        prefijo: const Icon(Icons.person_outline, size: 18, color: _colorTextoSecundario),
                      ),
                      validator: (v) {
                        if (v == null || v.trim().isEmpty) {
                          return 'Ingresa tu nombre completo';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Correo Electrónico
                    _construirEtiqueta('CORREO ELECTRÓNICO'),
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      style: const TextStyle(color: _colorTextoPrincipal, fontSize: 14),
                      decoration: _decoracionCampo(
                        hint: 'c.laurent@atelier-mode.fr',
                        prefijo: const Icon(Icons.mail_outline, size: 18, color: _colorTextoSecundario),
                      ),
                      validator: (v) {
                        if (v == null || v.trim().isEmpty) {
                          return 'El correo es obligatorio';
                        }
                        if (!v.contains('@') || !v.contains('.')) {
                          return 'Ingresa un correo válido';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Contraseña
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _construirEtiqueta('CONTRASEÑA'),
                        const Text(
                          'Mín. 8 caracteres',
                          style: TextStyle(
                            color: _colorTextoSecundario,
                            fontSize: 10,
                            letterSpacing: 0.5,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: !_mostrarPassword,
                      style: const TextStyle(color: _colorTextoPrincipal, fontSize: 14),
                      decoration: _decoracionCampo(
                        hint: '••••••••••••',
                        prefijo: const Icon(Icons.lock_outline, size: 18, color: _colorTextoSecundario),
                        sufijo: IconButton(
                          icon: Icon(
                            _mostrarPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            color: _colorTextoSecundario,
                            size: 18,
                          ),
                          onPressed: () {
                            setState(() {
                              _mostrarPassword = !_mostrarPassword;
                            });
                          },
                        ),
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) {
                          return 'La contraseña es obligatoria';
                        }
                        if (v.length < 8) {
                          return 'Mínimo 8 caracteres';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 8),

                    // Barras de Fortaleza (4 segmentos)
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            height: 3,
                            decoration: BoxDecoration(
                              color: _nivelFortaleza >= 1
                                  ? _colorNegroObsidian
                                  : const Color(0xFFE5E5E5),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Container(
                            height: 3,
                            decoration: BoxDecoration(
                              color: _nivelFortaleza >= 2
                                  ? _colorNegroObsidian
                                  : const Color(0xFFE5E5E5),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Container(
                            height: 3,
                            decoration: BoxDecoration(
                              color: _nivelFortaleza >= 3
                                  ? _colorNegroObsidian
                                  : const Color(0xFFE5E5E5),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Container(
                            height: 3,
                            decoration: BoxDecoration(
                              color: _nivelFortaleza >= 4
                                  ? const Color(0xFF1B4D25)
                                  : const Color(0xFFE5E5E5),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 6),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'SEGURIDAD',
                          style: TextStyle(
                            color: _colorTextoSecundario,
                            fontSize: 9,
                            letterSpacing: 1.0,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          _etiquetaFortaleza,
                          style: const TextStyle(
                            color: _colorTextoPrincipal,
                            fontSize: 9,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 0.8,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 18),

                    // Checkbox 1: Términos y Privacidad (Obligatorio)
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: 24,
                          height: 24,
                          child: Checkbox(
                            value: _aceptaTerminos,
                            activeColor: Colors.black,
                            checkColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(3),
                            ),
                            onChanged: (val) {
                              setState(() {
                                _aceptaTerminos = val ?? false;
                              });
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: GestureDetector(
                            onTap: () {
                              setState(() {
                                _aceptaTerminos = !_aceptaTerminos;
                              });
                            },
                            child: const Text.rich(
                              TextSpan(
                                text: 'Acepto los ',
                                style: TextStyle(
                                  color: _colorTextoSecundario,
                                  fontSize: 12,
                                  height: 1.35,
                                ),
                                children: [
                                  TextSpan(
                                    text: 'Términos de Servicio',
                                    style: TextStyle(
                                      decoration: TextDecoration.underline,
                                      color: _colorTextoPrincipal,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                  TextSpan(text: ' y la '),
                                  TextSpan(
                                    text: 'Política de Privacidad',
                                    style: TextStyle(
                                      decoration: TextDecoration.underline,
                                      color: _colorTextoPrincipal,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                  TextSpan(text: ' de Fashion Store.'),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),

                    // Checkbox 2: Notificaciones de colecciones cápsula
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: 24,
                          height: 24,
                          child: Checkbox(
                            value: _deseaNotificaciones,
                            activeColor: Colors.black,
                            checkColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(3),
                            ),
                            onChanged: (val) {
                              setState(() {
                                _deseaNotificaciones = val ?? false;
                              });
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: GestureDetector(
                            onTap: () {
                              setState(() {
                                _deseaNotificaciones = !_deseaNotificaciones;
                              });
                            },
                            child: const Text(
                              'Deseo recibir notificaciones de colecciones cápsula, desfiles y eventos privados.',
                              style: TextStyle(
                                color: _colorTextoSecundario,
                                fontSize: 12,
                                height: 1.35,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 28),

                    // Botón Primario: CREAR CUENTA EXCLUSIVA →
                    SizedBox(
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _colorNegroObsidian,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        onPressed: estaCargando ? null : _enviarFormulario,
                        child: estaCargando
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor:
                                      AlwaysStoppedAnimation<Color>(Colors.white),
                                ),
                              )
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: const [
                                  Text(
                                    'CREAR CUENTA EXCLUSIVA',
                                    style: TextStyle(
                                      letterSpacing: 2.2,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  SizedBox(width: 8),
                                  Icon(Icons.arrow_forward, size: 16),
                                ],
                              ),
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Enlace a Iniciar Sesión
                    Center(
                      child: GestureDetector(
                        onTap: () {
                          if (Navigator.canPop(context)) {
                            Navigator.pop(context);
                          } else {
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const PantallaLogin(),
                              ),
                            );
                          }
                        },
                        child: const Text.rich(
                          TextSpan(
                            text: '¿Ya posees una cuenta? ',
                            style: TextStyle(
                              color: _colorTextoSecundario,
                              fontSize: 12,
                            ),
                            children: [
                              TextSpan(
                                text: 'Iniciar sesión',
                                style: TextStyle(
                                  color: _colorTextoPrincipal,
                                  decoration: TextDecoration.underline,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 28),

                    // Píldora de Confianza SSL
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 10,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF1F1F1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(
                              Icons.verified_user_outlined,
                              size: 14,
                              color: _colorTextoSecundario,
                            ),
                            SizedBox(width: 8),
                            Text(
                              '256-BIT SSL SECURED • PRIVACIDAD GARANTIZADA',
                              style: TextStyle(
                                color: _colorTextoSecundario,
                                fontSize: 10,
                                letterSpacing: 1.0,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _construirEtiqueta(String texto) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        texto,
        style: const TextStyle(
          color: _colorTextoPrincipal,
          fontSize: 11,
          letterSpacing: 0.8,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  InputDecoration _decoracionCampo({
    required String hint,
    Widget? prefijo,
    Widget? sufijo,
  }) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Color(0xFF9E9E9E), fontSize: 13),
      prefixIcon: prefijo,
      suffixIcon: sufijo,
      filled: true,
      fillColor: _colorCampoFondo,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: _colorCampoBorde),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: _colorCampoBorde),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: _colorNegroObsidian, width: 1.2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: Color(0xFFC81E1E)),
      ),
    );
  }
}
