import 'package:flutter/material.dart';

/// Pantalla placeholder en blanco para el futuro CU05: Consultar Catálogo Canónico.
/// Se mantiene en blanco deliberadamente para facilitar la futura integración del caso de uso.
class PantallaCatalogoPlaceholder extends StatelessWidget {
  final bool mostrarBottomNav;
  final VoidCallback? alIrAInicio;
  final VoidCallback? alIrABuscar;
  final VoidCallback? alIrAPerfil;

  const PantallaCatalogoPlaceholder({
    super.key,
    this.mostrarBottomNav = true,
    this.alIrAInicio,
    this.alIrABuscar,
    this.alIrAPerfil,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'CATÁLOGO',
          style: TextStyle(
            color: Colors.black,
            fontSize: 14,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.2,
          ),
        ),
      ),
      body: const SizedBox.expand(),
    );
  }
}
