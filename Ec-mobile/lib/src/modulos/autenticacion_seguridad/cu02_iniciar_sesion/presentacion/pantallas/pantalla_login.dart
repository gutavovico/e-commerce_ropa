import 'dart:ui';
import 'package:flutter/material.dart';
import '../../datos/modelos/login_dto.dart';
import '../bloc/login_bloc.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu01_registrarse/presentacion/pantallas/pantalla_registro.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/presentacion/pantallas/pantalla_recuperar_password.dart';
import 'package:ec_mobile/api_config.dart';
import 'package:http/http.dart' as http;

class PantallaLogin extends StatefulWidget {
  final VoidCallback? alCompletarLogin;
  final void Function(String token)? alCompletarLoginConToken;
  final void Function(String token, LoginRespuestaDto usuario)? alCompletarLoginConUsuario;
  final LoginBloc? bloc;

  const PantallaLogin({
    super.key,
    this.alCompletarLogin,
    this.alCompletarLoginConToken,
    this.alCompletarLoginConUsuario,
    this.bloc,
  });

  @override
  State<PantallaLogin> createState() => _PantallaLoginState();
}

class _PantallaLoginState extends State<PantallaLogin> {
  final _formKey = GlobalKey<FormState>();
  late final LoginBloc _bloc;

  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _mostrarPassword = false;
  bool _recordarDispositivo = true;

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? LoginBloc();
    _bloc.addListener(_alCambiarEstado);
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    if (widget.bloc == null) {
      _bloc.dispose();
    }
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _alCambiarEstado() {
    final estado = _bloc.estado;
    if (estado is LoginExitoso) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '¡Bienvenido de vuelta, ${estado.respuesta.nombres}!',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          backgroundColor: Colors.black,
          duration: const Duration(seconds: 2),
        ),
      );
      widget.alCompletarLoginConUsuario?.call(estado.respuesta.accessToken, estado.respuesta);
      widget.alCompletarLoginConToken?.call(estado.respuesta.accessToken);
      widget.alCompletarLogin?.call();
    } else if (estado is LoginFallido) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(estado.mensaje),
          backgroundColor: const Color(0xFFBA1A1A),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  void _mostrarConfiguracionServidor() {
    final controller = TextEditingController(text: ApiConfig.baseUrl);
    String estadoConexion = '';
    bool probando = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => Container(
          padding: EdgeInsets.only(
            left: 24,
            right: 24,
            top: 24,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'CONFIGURACION DE SERVIDOR',
                    style: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.0,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              const Text(
                'Seleccione el entorno o ingrese la URL del backend FastAPI:',
                style: TextStyle(fontSize: 12, color: Color(0xFF737373)),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ActionChip(
                    label: const Text('Nube (Render - Autonomo)', style: TextStyle(fontSize: 11)),
                    backgroundColor: controller.text == ApiConfig.productionUrl
                        ? const Color(0xFFE8E0D5)
                        : const Color(0xFFF5F5F5),
                    onPressed: () {
                      setModalState(() {
                        controller.text = ApiConfig.productionUrl;
                        estadoConexion = '';
                      });
                    },
                  ),
                  ActionChip(
                    label: const Text('Wi-Fi Laptop (10.13.137.254)', style: TextStyle(fontSize: 11)),
                    backgroundColor: controller.text == 'http://10.13.137.254:8000'
                        ? const Color(0xFFE8E0D5)
                        : const Color(0xFFF5F5F5),
                    onPressed: () {
                      setModalState(() {
                        controller.text = 'http://10.13.137.254:8000';
                        estadoConexion = '';
                      });
                    },
                  ),
                  ActionChip(
                    label: const Text('Emulador Android (10.0.2.2)', style: TextStyle(fontSize: 11)),
                    backgroundColor: controller.text == 'http://10.0.2.2:8000'
                        ? const Color(0xFFE8E0D5)
                        : const Color(0xFFF5F5F5),
                    onPressed: () {
                      setModalState(() {
                        controller.text = 'http://10.0.2.2:8000';
                        estadoConexion = '';
                      });
                    },
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextField(
                controller: controller,
                decoration: InputDecoration(
                  labelText: 'URL Base del Backend',
                  hintText: 'https://...',
                  filled: true,
                  fillColor: const Color(0xFFF9F9F9),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                style: const TextStyle(fontSize: 13),
              ),
              if (estadoConexion.isNotEmpty) ...[
                const SizedBox(height: 10),
                Text(
                  estadoConexion,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: estadoConexion.startsWith('Conectado')
                        ? const Color(0xFF1B5E20)
                        : const Color(0xFFBA1A1A),
                  ),
                ),
              ],
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.black,
                        side: const BorderSide(color: Color(0xFFD4D4D4)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: probando
                          ? null
                          : () async {
                              setModalState(() {
                                probando = true;
                                estadoConexion = 'Comprobando conexion...';
                              });
                              try {
                                final urlLimpia = controller.text.trim().replaceAll(RegExp(r'/+$'), '');
                                final resp = await http.get(
                                  Uri.parse('$urlLimpia/api/v1/health'),
                                ).timeout(const Duration(seconds: 4));
                                setModalState(() {
                                  probando = false;
                                  estadoConexion = resp.statusCode == 200
                                      ? 'Conectado exitosamente (${resp.statusCode})'
                                      : 'Respuesta del servidor: HTTP ${resp.statusCode}';
                                });
                              } catch (e) {
                                setModalState(() {
                                  probando = false;
                                  estadoConexion = 'Error de conexion: no se pudo alcanzar el servidor';
                                });
                              }
                            },
                      child: probando
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Text('Probar Conexion', style: TextStyle(fontSize: 12)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.black,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: () {
                        ApiConfig.setCustomBaseUrl(controller.text);
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Servidor configurado: ${ApiConfig.baseUrl}'),
                            backgroundColor: Colors.black,
                            duration: const Duration(seconds: 3),
                          ),
                        );
                      },
                      child: const Text('Guardar', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _iniciarSesion() {
    if (_formKey.currentState?.validate() ?? false) {
      final peticion = LoginPeticionDto(
        email: _emailController.text,
        password: _passwordController.text,
        recordarDispositivo: _recordarDispositivo,
      );
      _bloc.iniciarSesion(peticion);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // 1. Imagen de Fondo de Alta Costura
          Positioned.fill(
            child: Image.asset(
              'assets/atelier_bg.jpg',
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) => Container(
                color: const Color(0xFF1E1E1E),
              ),
            ),
          ),

          // 2. Filtro de Desenfoque y Gradiente Cálido
          Positioned.fill(
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
              child: Container(
                color: Colors.black.withValues(alpha: 0.40),
              ),
            ),
          ),

          // 2.1 Boton de Configuracion de Servidor (Discreto)
          Positioned(
            top: 40,
            right: 16,
            child: SafeArea(
              child: IconButton(
                key: const Key('login_server_settings_button'),
                icon: const Icon(Icons.dns_outlined, color: Colors.white70),
                tooltip: 'Configurar Servidor',
                onPressed: _mostrarConfiguracionServidor,
              ),
            ),
          ),

          // 3. Contenido Principal Desplazable
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Badge Superior Flotante FS
                    Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.15),
                            blurRadius: 16,
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
                            fontSize: 22,
                            color: Colors.black,
                            letterSpacing: 1.5,
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Tarjeta Central Inmaculada (Museum Canvas)
                    Container(
                      width: double.infinity,
                      constraints: const BoxConstraints(maxWidth: 420),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 32,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(28),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.20),
                            blurRadius: 32,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            // Subtítulo
                            const Text(
                              '— BIENVENIDO DE VUELTA —',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 2.0,
                                color: Color(0xFF737373),
                              ),
                              textAlign: TextAlign.center,
                            ),

                            const SizedBox(height: 8),

                            // Título de Marca
                            const Text(
                              'FASHION STORE',
                              style: TextStyle(
                                fontFamily: 'Outfit',
                                fontSize: 24,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.2,
                                color: Colors.black,
                              ),
                              textAlign: TextAlign.center,
                            ),

                            const SizedBox(height: 28),

                            // Campo: Correo Electrónico
                            const Text(
                              'CORREO ELECTRÓNICO',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.8,
                                color: Color(0xFF404040),
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextFormField(
                              key: const Key('login_email_field'),
                              controller: _emailController,
                              keyboardType: TextInputType.emailAddress,
                              style: const TextStyle(fontSize: 14, color: Colors.black),
                              validator: (v) {
                                if (v == null || v.trim().isEmpty) {
                                  return 'Por favor ingresa tu correo electrónico';
                                }
                                if (!v.contains('@') || !v.contains('.')) {
                                  return 'Ingresa un correo electrónico válido';
                                }
                                return null;
                              },
                              decoration: InputDecoration(
                                prefixIcon: const Icon(
                                  Icons.alternate_email,
                                  size: 18,
                                  color: Color(0xFF737373),
                                ),
                                hintText: 'nombre@ejemplo.com',
                                hintStyle: const TextStyle(
                                  fontSize: 14,
                                  color: Color(0xFFA3A3A3),
                                ),
                                filled: true,
                                fillColor: const Color(0xFFF5F5F5),
                                contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 14,
                                ),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(color: Color(0xFFE8E8E8)),
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(color: Color(0xFFE8E8E8)),
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(
                                    color: Colors.black,
                                    width: 1.2,
                                  ),
                                ),
                              ),
                            ),

                            const SizedBox(height: 20),

                            // Campo: Contraseña
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Flexible(
                                  child: Text(
                                    'CONTRASEÑA',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 0.8,
                                      color: Color(0xFF404040),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Flexible(
                                  child: GestureDetector(
                                    onTap: () {
                                      Navigator.of(context).push(
                                        MaterialPageRoute(
                                          builder: (_) =>
                                              const PantallaRecuperarPassword(),
                                        ),
                                      );
                                    },
                                    child: const Text(
                                      '¿Olvidaste tu contraseña?',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Color(0xFF737373),
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            TextFormField(
                              key: const Key('login_password_field'),
                              controller: _passwordController,
                              obscureText: !_mostrarPassword,
                              style: const TextStyle(fontSize: 14, color: Colors.black),
                              validator: (v) {
                                if (v == null || v.isEmpty) {
                                  return 'Por favor ingresa tu contraseña';
                                }
                                return null;
                              },
                              decoration: InputDecoration(
                                prefixIcon: const Icon(
                                  Icons.lock_outline,
                                  size: 18,
                                  color: Color(0xFF737373),
                                ),
                                suffixIcon: IconButton(
                                  key: const Key('login_toggle_password_button'),
                                  icon: Icon(
                                    _mostrarPassword
                                        ? Icons.visibility_off_outlined
                                        : Icons.visibility_outlined,
                                    size: 20,
                                    color: const Color(0xFF737373),
                                  ),
                                  onPressed: () {
                                    setState(() {
                                      _mostrarPassword = !_mostrarPassword;
                                    });
                                  },
                                ),
                                hintText: '••••••••••••',
                                hintStyle: const TextStyle(
                                  fontSize: 14,
                                  color: Color(0xFFA3A3A3),
                                ),
                                filled: true,
                                fillColor: const Color(0xFFF5F5F5),
                                contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 14,
                                ),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(color: Color(0xFFE8E8E8)),
                                ),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(color: Color(0xFFE8E8E8)),
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(8),
                                  borderSide: const BorderSide(
                                    color: Colors.black,
                                    width: 1.2,
                                  ),
                                ),
                              ),
                            ),

                            const SizedBox(height: 16),

                            // Casilla: Recordar en este dispositivo
                            Row(
                              children: [
                                SizedBox(
                                  width: 24,
                                  height: 24,
                                  child: Checkbox(
                                    key: const Key('login_remember_checkbox'),
                                    value: _recordarDispositivo,
                                    activeColor: Colors.black,
                                    checkColor: Colors.white,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    onChanged: (val) {
                                      setState(() {
                                        _recordarDispositivo = val ?? false;
                                      });
                                    },
                                  ),
                                ),
                                const SizedBox(width: 8),
                                const Expanded(
                                  child: Text(
                                    'Recordar en este dispositivo',
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: Color(0xFF404040),
                                    ),
                                  ),
                                ),
                              ],
                            ),

                            const SizedBox(height: 24),

                            // Botón de Envío: INICIAR SESIÓN ->
                            AnimatedBuilder(
                              animation: _bloc,
                              builder: (context, _) {
                                final cargando = _bloc.estaCargando;
                                return SizedBox(
                                  width: double.infinity,
                                  height: 48,
                                  child: ElevatedButton(
                                    key: const Key('login_submit_button'),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.black,
                                      foregroundColor: Colors.white,
                                      elevation: 0,
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                    ),
                                    onPressed: cargando ? null : _iniciarSesion,
                                    child: cargando
                                        ? const SizedBox(
                                            width: 20,
                                            height: 20,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: Colors.white,
                                            ),
                                          )
                                        : const Row(
                                            mainAxisAlignment: MainAxisAlignment.center,
                                            children: [
                                              Text(
                                                'INICIAR SESIÓN',
                                                style: TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w600,
                                                  letterSpacing: 1.5,
                                                ),
                                              ),
                                              SizedBox(width: 8),
                                              Icon(Icons.arrow_forward, size: 16),
                                            ],
                                          ),
                                  ),
                                );
                              },
                            ),

                            const SizedBox(height: 24),
                            const Divider(color: Color(0xFFE5E5E5), thickness: 1),
                            const SizedBox(height: 16),

                            // Footer: Redirección a Registro
                            const Text(
                              '¿Aún no tienes una cuenta exclusiva?',
                              style: TextStyle(fontSize: 12, color: Color(0xFF737373)),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 4),
                            GestureDetector(
                              key: const Key('login_register_link'),
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => const PantallaRegistro(),
                                  ),
                                );
                              },
                              child: const Text(
                                'Regístrate aquí',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.black,
                                  decoration: TextDecoration.underline,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 24),

                    // Píldora de Seguridad Inferior
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.shield_outlined,
                          size: 16,
                          color: Colors.white.withValues(alpha: 0.85),
                        ),
                        const SizedBox(width: 6),
                        Flexible(
                          child: Text(
                            'CONEXIÓN CIFRADA & PRIVACIDAD MAISON',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1.4,
                              color: Colors.white.withValues(alpha: 0.85),
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
