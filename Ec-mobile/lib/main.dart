import 'package:flutter/material.dart';
import 'src/modulos/autenticacion_seguridad/cu01_registrarse/presentacion/pantallas/pantalla_registro.dart';

void main() {
  runApp(const EcMobileApp());
}

class EcMobileApp extends StatelessWidget {
  const EcMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fashion Store',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: Colors.white,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.black,
          primary: Colors.black,
          surface: Colors.white,
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
        ),
      ),
      home: const PantallaRegistro(),
    );
  }
}
